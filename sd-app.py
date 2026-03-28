import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# Page Config
st.set_page_config(page_title="Swing Terminal 2026", layout="wide")
st.title("🚀 Swing Trading Command Center")

# --- 1. SETUP & DATA ---
# Your 30-Stock Watchlist & Portfolio Mockup
watchlist = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "GOOGL", "META", "AMZN", "NFLX", "COIN", "U", "PLTR", "SNOW"]
portfolio_data = {
    "Ticker": ["AAPL", "NVDA", "TSLA"],
    "Shares": [10, 5, 15],
    "Avg_Cost": [175.00, 450.00, 180.00]
}
my_holdings = pd.DataFrame(portfolio_data)

@st.cache_data(ttl=3600) # Cache for 1 hour to save API hits
def fetch_data(tickers):
    data_dict = {}
    for t in tickers:
        df = yf.download(t, period="1y", interval="1d")
        if not df.empty:
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.rsi(length=14, append=True)
            data_dict[t] = df
    return data_dict

all_data = fetch_data(watchlist)

# --- 2. TABS LAYOUT ---
tab1, tab2, tab3 = st.tabs(["🔍 Global Scanner", "📈 Technical Chart", "💼 Portfolio View"])

# --- TAB 1: MASS SCREENING ---
with tab1:
    st.header("Daily Swing Signals")
    scanner_results = []
    
    for t, df in all_data.items():
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Logic: RSI Oversold or SMA Cross
        status = "Neutral"
        if last['RSI_14'] < 35: status = "💎 Oversold (Buy Zone)"
        elif last['RSI_14'] > 70: status = "🔥 Overbought (Trim)"
        elif (prev['SMA_20'] < prev['SMA_50']) and (last['SMA_20'] > last['SMA_50']): status = "🚀 Golden Cross"
        
        scanner_results.append({"Ticker": t, "Price": round(last['Close'], 2), "RSI": round(last['RSI_14'], 2), "Signal": status})
    
    st.table(pd.DataFrame(scanner_results).sort_values(by="RSI"))

# --- TAB 2: TECHNICAL CHART & VOLUME ---
with tab2:
    selected_ticker = st.selectbox("View Deep Dive:", watchlist)
    df = all_data[selected_ticker]
    
    # Create Subplot: Chart on top, Volume on bottom
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.03, row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                 low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    # Moving Averages
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20 SMA", line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="50 SMA", line=dict(color='blue')), row=1, col=1)
    
    # Volume Bars
    colors = ['green' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else 'red' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=colors), row=2, col=1)

    fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: PORTFOLIO VIEW ---
with tab3:
    st.header("Current Performance")
    
    # Calculate Live P/L
    summary = []
    for _, row in my_holdings.iterrows():
        current_price = all_data[row['Ticker']].iloc[-1]['Close']
        p_l = (current_price - row['Avg_Cost']) * row['Shares']
        summary.append({
            "Ticker": row['Ticker'],
            "Current Price": round(current_price, 2),
            "Avg Cost": row['Avg_Cost'],
            "P/L ($)": round(p_l, 2),
            "P/L (%)": round((p_l / (row['Avg_Cost'] * row['Shares'])) * 100, 2)
        })
    
    st.dataframe(pd.DataFrame(summary), use_container_width=True)
    st.metric("Total Portfolio P/L", f"${sum(item['P/L ($)'] for item in summary):.2f}")