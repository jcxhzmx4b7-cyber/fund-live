import streamlit as st
import yfinance as yf

st.set_page_config(page_title="我的基金实时估值", layout="wide")
st.title("📈 基金准实时估值面板")

def show_metric(name, ticker):
    data = yf.Ticker(ticker).history(period="2d")
    price = data["Close"].iloc[-1]
    prev = data["Close"].iloc[-2]
    change = (price - prev) / prev * 100
    st.metric(name, f"{price:.2f}", f"{change:.2f}%")

st.header("🌍 海外 / QDII")

col1, col2, col3 = st.columns(3)
with col1:
    show_metric("纳斯达克100", "^NDX")
with col2:
    show_metric("费城半导体", "^SOX")
with col3:
    show_metric("国际金价", "GC=F")

st.header("🇨🇳 A股核心指数")

col4, col5, col6 = st.columns(3)
with col4:
    show_metric("创业板指", "399006.SZ")
with col5:
    show_metric("军工指数", "399967.SZ")
with col6:
    show_metric("中证有色", "000932.SS")

st.header("🔥 权重股风向")

col7, col8, col9 = st.columns(3)
with col7:
    show_metric("英伟达", "NVDA")
with col8:
    show_metric("微软", "MSFT")
with col9:
    show_metric("苹果", "AAPL")
