import streamlit as st
import yfinance as yf
import ta  # Switched from pandas-ta to ta for easier installation
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIG ---
st.set_page_config(page_title="Swing Terminal 2026", layout="wide")
st.title("📈 Swing Trading Command Center")

# --- 1. SESSION STATE ---
if 'portfolio_df' not in st.session_state:
    st.session_state.portfolio_df = pd.DataFrame([
        {"Ticker": "AAPL", "Shares": 10, "Avg_Cost": 175.00, "Date_Bought": datetime.now().date() - timedelta(days=10)},
        {"Ticker": "NVDA", "Shares": 5, "Avg_Cost": 850.00, "Date_Bought": datetime.now().date() - timedelta(days=5)}
    ])

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_all_data(tickers):
    data_dict = {}
    for t in tickers:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if not df.empty:
                # Calculate Indicators using the 'ta' library
                df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
                df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
                df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
                df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
                data_dict[t] = df
        except:
            continue
    return data_dict

active_tickers = st.session_state.portfolio_df['Ticker'].unique().tolist()
watchlist = list(set(active_tickers + ["MSFT", "AMD", "GOOGL", "AMZN", "COIN", "PLTR"]))
all_market_data = fetch_all_data(watchlist)

# --- 3. TABS ---
tab1, tab2, tab3 = st.tabs(["🔍 Global Scanner", "📊 Technical Analysis", "💼 Portfolio Manager"])

# --- TAB 1: SCANNER ---
with tab1:
    st.subheader("Market Pulse")
    scanner_list = []
    for t in watchlist:
        if t in all_market_data:
            df = all_market_data[t]
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            signal = "Neutral"
            if last['RSI_14'] < 30: signal = "💎 Oversold"
            elif last['RSI_14'] > 70: signal = "🔥 Overbought"
            elif (prev['SMA_20'] < prev['SMA_50']) and (last['SMA_20'] > last['SMA_50']): signal = "🚀 Golden Cross"
            
            scanner_list.append({
                "Ticker": t, "Price": f"${last['Close'].item():.2f}", 
                "RSI": round(last['RSI_14'].item(), 1), "Signal": signal
            })
    st.dataframe(pd.DataFrame(scanner_list), use_container_width=True)

# --- TAB 2: TECH ANALYSIS ---
with tab2:
    target = st.selectbox("Select Ticker:", watchlist)
    if target in all_market_data:
        df = all_market_data[target]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name="20 SMA", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="50 SMA", line=dict(color='blue')), row=1, col=1)
        
        v_colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=v_colors), row=2, col=1)
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: PORTFOLIO ---
with tab3:
    st.subheader("Holdings Editor")
    edited_df = st.data_editor(st.session_state.portfolio_df, num_rows="dynamic", use_container_width=True)
    st.session_state.portfolio_df = edited_df
    
    perf_data = []
    for _, row in edited_df.iterrows():
        t = row['Ticker']
        if t in all_market_data:
            curr_price = all_market_data[t].iloc[-1]['Close'].item()
            total_cost = row['Shares'] * row['Avg_Cost']
            p_l = (curr_price * row['Shares']) - total_cost
            days_held = (datetime.now().date() - row['Date_Bought']).days
            
            perf_data.append({
                "Ticker": t, "Current": f"${curr_price:.2f}", "P/L $": round(p_l, 2),
                "P/L %": f"{(p_l/total_cost)*100:.2f}%", "Days Held": days_held,
                "Stop Loss": f"${curr_price - (2 * all_market_data[t].iloc[-1]['ATR'].item()):.2f}"
            })
    if perf_data:
        st.table(pd.DataFrame(perf_data))
