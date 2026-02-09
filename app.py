import streamlit as st
import yfinance as yf

st.set_page_config(page_title="基金准实时估值", layout="wide")
st.title("📈 基金准实时估值面板")

def safe_metric(name, ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if len(data) < 2:
            st.metric(name, "暂无数据", "—")
            return
        price = data["Close"].iloc[-1]
        prev = data["Close"].iloc[-2]
        change = (price - prev) / prev * 100
        st.metric(name, f"{price:.2f}", f"{change:.2f}%")
    except:
        st.metric(name, "获取失败", "—")

st.header("🌍 海外 / QDII")
c1, c2, c3 = st.columns(3)
with c1: safe_metric("纳斯达克100", "^NDX")
with c2: safe_metric("费城半导体", "^SOX")
with c3: safe_metric("国际金价", "GC=F")

st.header("🇨🇳 A股ETF替代指数（更准）")
c4, c5, c6 = st.columns(3)
with c4: safe_metric("创业板ETF", "159915.SZ")
with c5: safe_metric("军工ETF", "512660.SS")
with c6: safe_metric("有色ETF", "512400.SS")

st.header("🔥 权重股风向标")
c7, c8, c9 = st.columns(3)
with c7: safe_metric("英伟达", "NVDA")
with c8: safe_metric("微软", "MSFT")
with c9: safe_metric("苹果", "AAPL")
