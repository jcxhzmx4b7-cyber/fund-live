import time
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="基金准实时估值（按基金）", layout="wide")
st.title("📌 基金准实时估值（按基金）")

# ========== 工具函数 ==========
@st.cache_data(ttl=60)  # 60秒缓存，避免频繁请求被限流
def yf_hist_2d(ticker: str):
    return yf.Ticker(ticker).history(period="5d")

def quote_change_pct(ticker: str):
    try:
        data = yf_hist_2d(ticker)
        if data is None or len(data) < 2:
            return None, None, None
        last = float(data["Close"].iloc[-1])
        prev = float(data["Close"].iloc[-2])
        chg = (last - prev) / prev * 100
        return last, chg, data.index[-1]
    except:
        return None, None, None

def weighted_estimate(components):
    """
    components: [{"ticker": "...", "w": 0.5, "name":"..."}]
    返回：估算涨跌幅、可用成分数、明细列表
    """
    detail = []
    acc = 0.0
    wsum = 0.0

    for c in components:
        last, chg, ts = quote_change_pct(c["ticker"])
        detail.append({
            "name": c["name"],
            "ticker": c["ticker"],
            "weight": c["w"],
            "last": last,
            "chg_pct": chg,
        })
        if chg is not None:
            acc += chg * c["w"]
            wsum += c["w"]

    if wsum == 0:
        return None, 0, detail
    return acc / wsum, int(sum(1 for d in detail if d["chg_pct"] is not None)), detail


# ========== 你的基金清单（你可以继续加） ==========
# 说明：
# - QDII：用指数（^NDX / ^SOX）最准
# - A股主题混合：用主题ETF/行业ETF做“实时代理”
# - 黄金：GC=F（国际金价）通常比国内金价更快
FUNDS = [
    {
        "fund": "南方纳斯达克100(QDII)A 016452",
        "tag": "QDII/美股",
        "components": [
            {"name":"纳斯达克100", "ticker":"^NDX", "w": 1.0},
        ],
    },
    {
        "fund": "景顺长城全球半导体(QDII) 016668",
        "tag": "QDII/半导体",
        "components": [
            {"name":"费城半导体", "ticker":"^SOX", "w": 0.75},
            {"name":"英伟达", "ticker":"NVDA", "w": 0.25},
        ],
    },
    {
        "fund": "国泰黄金ETF联接C 004253",
        "tag": "黄金",
        "components": [
            {"name":"国际金价", "ticker":"GC=F", "w": 1.0},
        ],
    },
    {
        "fund": "华宝中证有色金属ETF联接A 017140",
        "tag": "有色",
        "components": [
            {"name":"有色ETF(代理)", "ticker":"512400.SS", "w": 0.8},
            {"name":"铜(代理)", "ticker":"HG=F", "w": 0.2},
        ],
    },
    {
        "fund": "永赢先进制造智选混合C 018125",
        "tag": "先进制造/机器人",
        "components": [
            {"name":"创业板ETF(代理)", "ticker":"159915.SZ", "w": 0.6},
            {"name":"科创50ETF(代理)", "ticker":"588000.SS", "w": 0.4},
        ],
    },
    {
        "fund": "永赢高端装备智选混合C 015790",
        "tag": "高端装备/军工",
        "components": [
            {"name":"军工ETF(代理)", "ticker":"512660.SS", "w": 0.7},
            {"name":"创业板ETF(代理)", "ticker":"159915.SZ", "w": 0.3},
        ],
    },
    {
        "fund": "永赢国证商用卫星通信产业ETF联接C 024195",
        "tag": "卫星/通信",
        "components": [
            {"name":"通信ETF(代理)", "ticker":"515880.SS", "w": 0.7},
            {"name":"军工ETF(代理)", "ticker":"512660.SS", "w": 0.3},
        ],
    },
    {
        "fund": "德邦稳盈增长灵活配置混合C 018463",
        "tag": "AI/科技混合",
        "components": [
            {"name":"创业板ETF(代理)", "ticker":"159915.SZ", "w": 0.6},
            {"name":"科创50ETF(代理)", "ticker":"588000.SS", "w": 0.4},
        ],
    },
    # 你截图里还有 012920 / 012922 / 022365 等（可继续补充更精准代理）
    {
        "fund": "易方达全球成长精选(QDII)A 012920",
        "tag": "QDII/全球成长",
        "components": [
            {"name":"纳指100", "ticker":"^NDX", "w": 0.6},
            {"name":"标普500", "ticker":"^GSPC", "w": 0.4},
        ],
    },
    {
        "fund": "易方达全球成长精选(QDII)C 012922",
        "tag": "QDII/全球成长",
        "components": [
            {"name":"纳指100", "ticker":"^NDX", "w": 0.6},
            {"name":"标普500", "ticker":"^GSPC", "w": 0.4},
        ],
    },
    {
        "fund": "永赢科技智选混合C 022365",
        "tag": "AI/科技",
        "components": [
            {"name":"纳指100", "ticker":"^NDX", "w": 0.5},
            {"name":"创业板ETF(代理)", "ticker":"159915.SZ", "w": 0.5},
        ],
    },
]

# ========== 顶部控制 ==========
colA, colB, colC = st.columns([1.2, 1.2, 1])
with colA:
    auto = st.toggle("自动刷新（60秒）", value=True)
with colB:
    tag_filter = st.selectbox("筛选分类", ["全部"] + sorted(list({f["tag"] for f in FUNDS})))
with colC:
    if st.button("手动刷新"):
        st.cache_data.clear()

if auto:
    st.caption("⏱️ 已开启自动刷新：每 60 秒更新一次")
    st.write("")  # spacing

# ========== 主表 ==========
rows = []
for f in FUNDS:
    if tag_filter != "全部" and f["tag"] != tag_filter:
        continue
    est, ok_n, detail = weighted_estimate(f["components"])
    rows.append({
        "基金": f["fund"],
        "分类": f["tag"],
        "估算涨跌幅%": None if est is None else round(est, 2),
        "可用成分": ok_n,
        "成分数": len(f["components"]),
    })

df = pd.DataFrame(rows)
if not df.empty:
    df = df.sort_values(by="估算涨跌幅%", ascending=False, na_position="last")
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ========== 详情展开 ==========
st.subheader("🔍 单只基金详情（看驱动）")
pick = st.selectbox("选择一只基金查看成分细节", [f["fund"] for f in FUNDS])

target = next(x for x in FUNDS if x["fund"] == pick)
est, ok_n, detail = weighted_estimate(target["components"])

left, right = st.columns([1.2, 1])
with left:
    st.markdown(f"**{target['fund']}**  ·  分类：`{target['tag']}`")
with right:
    if est is None:
        st.metric("估算涨跌幅", "暂无数据", "—")
    else:
        st.metric("估算涨跌幅", f"{est:.2f}%", f"可用成分 {ok_n}/{len(detail)}")

dff = pd.DataFrame(detail)
if not dff.empty:
    dff["chg_pct"] = dff["chg_pct"].map(lambda x: None if x is None else round(x, 2))
    st.dataframe(dff.rename(columns={
        "name":"成分",
        "ticker":"代码",
        "weight":"权重",
        "last":"最新价",
        "chg_pct":"涨跌幅%",
    }), use_container_width=True, hide_index=True)

st.caption("注：这是一套“实时代理估算”。基金最终净值仍以 T+1 官方公布为准，但盘中方向判断会非常好用。")

# 自动刷新（放在最后）
if auto:
    time.sleep(0.1)
    st.experimental_rerun()
