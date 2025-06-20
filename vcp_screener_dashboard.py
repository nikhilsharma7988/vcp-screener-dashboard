import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import requests
from bs4 import BeautifulSoup
import io

st.set_page_config(page_title="VCP Screener Dashboard", layout="wide")

st.markdown("""
    <div style='display: flex; align-items: center;'>
        <div style='font-size: 28px; font-weight: bold; color: #FF6600; margin-right: 10px;'>NS</div>
        <div style='font-size: 24px; font-weight: bold;'>NIKHIL SHARMA</div>
    </div>
""", unsafe_allow_html=True)

menu = ["VCP Screener", "Company Fundamentals", "Sector Rotation", "News & Events", "Export"]
choice = st.selectbox("Select Dashboard Tab", menu)

stocks = {
    "RELIANCE.NS": "Energy",
    "TCS.NS": "Technology",
    "INFY.NS": "Technology",
    "HDFCBANK.NS": "Financials",
    "BAJAJ-AUTO.NS": "Automotive"
}

def fetch_data(ticker):
    end = datetime.date.today()
    start = end - datetime.timedelta(days=365)
    df = yf.download(ticker, start=start, end=end)
    return df

def is_vcp(df):
    if df is None or df.empty:
        return False
    recent = df.tail(30)
    ranges = recent['High'] - recent['Low']
    std = ranges.std()
    sma50 = df['Close'].rolling(window=50).mean()
    sma200 = df['Close'].rolling(window=200).mean()
    breakout = df['Close'].iloc[-1] > sma50.iloc[-1] > sma200.iloc[-1]
    return std < 15 and breakout

def fetch_fundamentals(symbol):
    try:
        url = f"https://www.screener.in/company/{symbol.replace('.NS','')}/"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        ratios = soup.select_one(".company-ratios")
        return ratios.text if ratios else "Data not available"
    except:
        return "Error fetching data"

def fetch_news(symbol):
    try:
        url = f"https://www.moneycontrol.com/news/tags/{symbol.replace('.NS','')}.html"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        headlines = soup.select(".clearfix h2")
        return [h.get_text(strip=True) for h in headlines[:5]]
    except:
        return ["No news available"]

if choice == "VCP Screener":
    st.title("VCP Screener")
    results = []
    for symbol, sector in stocks.items():
        df = fetch_data(symbol)
        if is_vcp(df):
            results.append({
                "Stock": symbol,
                "Sector": sector,
                "Latest Close": df['Close'].iloc[-1],
                "VCP Score": "✔"
            })

    if results:
        result_df = pd.DataFrame(results)
        st.dataframe(result_df, use_container_width=True)
        st.session_state['vcp_data'] = result_df
    else:
        st.warning("No VCP patterns detected today.")

elif choice == "Company Fundamentals":
    st.title("Company Fundamentals")
    symbol = st.selectbox("Choose stock", list(stocks.keys()))
    st.subheader(f"Fundamentals for {symbol}")
    fundamentals = fetch_fundamentals(symbol)
    st.code(fundamentals)

elif choice == "Sector Rotation":
    st.title("Sector Rotation Analysis")
    df_sector = pd.DataFrame([{
        "Sector": sector,
        "Avg Close": fetch_data(s)["Close"].mean()
    } for s, sector in stocks.items()])
    st.bar_chart(df_sector.set_index("Sector"))

elif choice == "News & Events":
    st.title("News & Events")
    symbol = st.selectbox("Select stock for news", list(stocks.keys()))
    st.subheader(f"Recent headlines for {symbol}")
    for news in fetch_news(symbol):
        st.markdown(f"- {news}")

elif choice == "Export":
    st.title("Export Screener Results")
    if 'vcp_data' in st.session_state:
        df = st.session_state['vcp_data']
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='VCP Screener')
        st.download_button("Download Excel", data=buffer.getvalue(), file_name="vcp_screener.xlsx")
    else:
        st.warning("Run the VCP screener first.")
