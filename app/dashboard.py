import streamlit as st
from streamlit_extras.jupyterlite import jupyterlite
import pandas as pd
import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime, timedelta, timezone
import plotly.graph_objects as go


def conn():
    return psycopg2.connect(
        dbname="silverbugs_db",
        user="elias_m",
        password="KSefPQeAhZJZM2x7jTdDHFT8i2gwGcnC",  # Replace with your actual password
        host="dpg-d1rfk1emcj7s73e3689g-a.oregon-postgres.render.com",
        port=5432
    )


st.title("📊 Interactive EDA App with Yahoo Finance")


# Sidebar settings
st.sidebar.header("Data Settings")

# Sidebar date inputs
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2000-08-30"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Load all data once and cache it
@st.cache_data
def load_data():
    tickers = ["SI=F", "GC=F", "^GSPC"]
    data = yf.download(tickers, start="2000-08-30", end=datetime.today())["Close"]
    return data


data = load_data()

data.index = data.index.tz_localize(None)


st.sidebar.header("Select Assets to Display")
show_silver = st.sidebar.checkbox("Silver", value=True)
show_gold = st.sidebar.checkbox("Gold", value=True)
show_sp500 = st.sidebar.checkbox("S&P 500", value=True)


st.subheader("24h Performance")

assets = ["SI=F","GC=F","^GSPC"]

cols = st.columns(len(assets))
for i, asset in enumerate(assets):
    latest_price = data[asset].iloc[-1]
    prev_price = data[asset].iloc[-2]
    abs_change = latest_price - prev_price
    pct_change = (abs_change / prev_price) * 100
    cols[i].metric(
        label = asset,
        value = f"${latest_price:.2f}",
        delta = f"{abs_change:+.2f} ({pct_change:+.2f}%)"
    )



# Spot Sales


st.subheader("Community Spot Sales")
st.link_button("View r/Pmsforsale", "https://www.reddit.com/r/Pmsforsale/")



# Quick Date Range buttons on top as radio buttons
now = datetime.now()
preset = st.radio(
    "Quick Date Range",
    ("Custom", "1 Week", "1 Month", "3 Months", "6 Months", "1 Year", "5 Years"),
    horizontal=True,
    index=5
)


if preset == "1 Week":
    start_date, end_date = now - timedelta(days=5), now
    filtered_data = data.loc[start_date:end_date]
elif preset == "1 Month":
    start_date, end_date = now - timedelta(days=30), now
    filtered_data = data.loc[start_date:end_date]
elif preset == "3 Months":
    start_date, end_date = now - timedelta(days=90), now
    filtered_data = data.loc[start_date:end_date]
elif preset == "6 Months":
    start_date, end_date = now - timedelta(days=180), now
    filtered_data = data.loc[start_date:end_date]
elif preset == "1 Year":
    start_date, end_date = now - timedelta(days=365), now
    filtered_data = data.loc[start_date:end_date]
elif preset == "5 Years":
    start_date, end_date = now - timedelta(days=1825), now
    filtered_data = data.loc[start_date:end_date]
else:  # Custom slider
    min_date = data.index.min().to_pydatetime()
    max_date = data.index.max().to_pydatetime()
    start_date, end_date = st.slider(
        "Select Custom Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )
    filtered_data = data.loc[start_date:end_date]



# --- Performance Summary Panel ---
st.subheader("Performance Summary")

perf_assets = []
if show_silver: perf_assets.append("SI=F")
if show_gold: perf_assets.append("GC=F")
if show_sp500: perf_assets.append("^GSPC")



# Normalize function: base 100 at start of filtered range
def normalize(series):
    base = series.iloc[0]
    return ((series / base) - 1) * 100

if len(perf_assets) > 0 and not filtered_data.empty:
    cols = st.columns(len(perf_assets))
    for idx, asset in enumerate(perf_assets):
        first_val = filtered_data[asset].iloc[0]
        last_val = filtered_data[asset].iloc[-1]
        abs_change = last_val - first_val
        pct_change = (abs_change / first_val) * 100
        cols[idx].metric(
            label=asset,
            value=f"${last_value:.2f}",
            delta=f"{abs_change:+.2f} ({pct_change:+.2f}%)"
        )
else:
    st.warning("Select at an asset.")


# Build Plotly figure
fig = go.Figure()

if show_silver and "SI=F" in filtered_data:
    fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=normalize(filtered_data["SI=F"]),
        mode='lines',
        name="Silver",
        line=dict(color='silver')
    ))

if show_gold and "GC=F" in filtered_data:
    fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=normalize(filtered_data["GC=F"]),
        mode='lines',
        name="Gold",
        line=dict(color='gold')
    ))

if show_sp500 and "^GSPC" in filtered_data:
    fig.add_trace(go.Scatter(
        x=filtered_data.index,
        y=normalize(filtered_data["^GSPC"]),
        mode='lines',
        name="S&P 500",
        line=dict(color='green')
    ))

fig.update_layout(
    title="Percent Change",
    xaxis_title="Date",
    yaxis_title="Value Change",
    height=600,
    legend=dict(x=0.01, y=1.05, orientation="h"),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

fig = go.Figure()


