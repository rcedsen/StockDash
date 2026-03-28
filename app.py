import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Swing Terminal 2026", layout="wide")
st.title("📈 Swing Trading Command Center")

# --- 1. SESSION STATE FOR PORTFOLIO ---
# This keeps your ticker, cost, and shares associated in one place
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = pd.DataFrame([
        {"Ticker": "AAPL", "Shares": 10, "Avg_Cost": 175.00, "Date_Bought": datetime.now().date() - timedelta(days=10)},
        {"Ticker": "NVDA", "Shares": 5, "Avg_Cost": 850.00, "Date_Bought": datetime.now().date() - timedelta(days=5)},
        {"Ticker": "TSLA", "Shares": 15, "Avg_Cost": 180.00, "Date_Bought": datetime.now().date() - timedelta(days=25)}
    ])

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_all_data(tickers):
    data_dict = {}
    for t in tickers:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if not df.empty:
                # Indicators
                df.ta.sma(length=20, append=True)
                df.ta.sma(length=50, append=True)
                df.ta.rsi(length=14, append=True)
                df.ta.atr(length=14, append=True)
                data_dict[t] = df
        except:
            continue
    return data_dict

# Extract unique tickers from the portfolio to fetch data
active_tickers = st.session_state.portfolio_df['Ticker'].unique().tolist()
# Add some default watchlist tickers if you want more variety
watchlist = list(set(active_tickers + ["MSFT", "AMD", "GOOGL", "AMZN", "COIN", "PLTR"]))
all_market_data = fetch_all_data(watchlist)

# --- 3. DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs(["🔍 Global Scanner", "📊 Technical Analysis", "💼 Portfolio Manager"])

# --- TAB 1: GLOBAL SCANNER (Mass Screening) ---
with tab1:
    st.subheader("Market Pulse & Signals")
    scanner_list = []
    for t in watchlist:
        if t in all_market_data:
            df = all_market_data[t]
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Signal Logic
            signal = "Neutral"
            if last['RSI_14'] < 30: signal = "💎 Oversold"
            elif last['RSI_14'] > 70: signal = "🔥 Overbought"
            elif (prev['SMA_20'] < prev['SMA_50']) and (last['SMA_20'] > last['SMA_50']): signal = "🚀 Golden Cross"
            
            scanner_list.append({
                "Ticker": t,
                "Price": f"${last['Close']:.2f}",
                "RSI": round(last['RSI_14'], 1),
                "SMA 20/50": "Bullish" if last['SMA_20'] > last['SMA_50'] else "Bearish",
                "Signal": signal
            })
    st.dataframe(pd.DataFrame(scanner_list), use_container_width=True)

# --- TAB 2: TECHNICAL ANALYSIS (Chart + Volume) ---
with tab2:
    target = st.selectbox("Select Ticker for Deep Dive:", watchlist)
    if target in all_market_data:
        df = all_market_data[target]
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # Candlesticks
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                     low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        # SMAs
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20 SMA", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="50 SMA", line=dict(color='blue')), row=1, col=1)
        
        # Volume with Color
        v_colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=v_colors), row=2, col=1)

        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: PORTFOLIO MANAGER (Integrated Associations) ---
with tab3:
    st.subheader("Active Holdings Editor")
    
    # The Spreadsheet UI
    edited_df = st.data_editor(
        st.session_state.portfolio_df,
        num_rows="dynamic",
        use_container_width=True,
        key="main_portfolio_editor"
    )
    st.session_state.portfolio_df = edited_df

    st.divider()