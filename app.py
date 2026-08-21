"""
Instalasi:
pip install -r requirements.txt
streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="XAUUSD Trading Signal", layout="wide")

# ---------- DATA FETCHING ----------
def fetch_yfinance(symbol="GLD", period="6mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        df = df.reset_index()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.rename(columns={"Date": "date", "Datetime": "date", "Close": "close",
                                 "Open": "open", "High": "high", "Low": "low", "Volume": "volume"})
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None

def fetch_alpha_vantage_daily(api_key):
    try:
        url = "https://www.alphavantage.co/query"
        params = {"function": "FX_DAILY", "from_symbol": "XAU", "to_symbol": "USD",
                   "apikey": api_key, "outputsize": "compact"}
        r = requests.get(url, params=params, timeout=10)
        data = r.json().get("Time Series FX (Daily)")
        if not data:
            return None
        df = pd.DataFrame(data).T.reset_index()
        df.columns = ["date", "open", "high", "low", "close"]
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        df["volume"] = 0
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None

def fetch_alpha_vantage_intraday(api_key, interval="15min"):
    try:
        url = "https://www.alphavantage.co/query"
        params = {"function": "FX_INTRADAY", "from_symbol": "XAU", "to_symbol": "USD",
                   "interval": interval, "apikey": api_key, "outputsize": "compact"}
        r = requests.get(url, params=params, timeout=10)
        key = f"Time Series FX ({interval})"
        data = r.json().get(key)
        if not data:
            return None
        df = pd.DataFrame(data).T.reset_index()
        df.columns = ["date", "open", "high", "low", "close"]
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        df["volume"] = 0
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None

def fetch_yfinance_intraday(symbol="GLD", period="5d", interval="15m"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        df = df.reset_index()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        date_col = "Datetime" if "Datetime" in df.columns else "Date"
        df = df.rename(columns={date_col: "date", "Close": "close",
                                 "Open": "open", "High": "high", "Low": "low", "Volume": "volume"})
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None

def generate_simulated_data(n=180, freq="D", start_price=2000.0):
    dates = pd.date_range(end=datetime.today(), periods=n, freq=freq)
    np.random.seed(42)
    step = 8 if freq == "D" else 2.5
    price = start_price + np.cumsum(np.random.normal(0, step, n))
    df = pd.DataFrame({
        "date": dates,
        "close": price,
        "open": price + np.random.normal(0, step * 0.4, n),
        "high": price + np.abs(np.random.normal(step * 0.6, step * 0.4, n)),
        "low": price - np.abs(np.random.normal(step * 0.6, step * 0.4, n)),
        "volume": np.random.randint(1000, 5000, n)
    })
    return df

def get_data(source, api_key, mode):
    df = None
    if mode == "daily":
        if source == "Alpha Vantage" and api_key:
            df = fetch_alpha_vantage_daily(api_key)
        elif source == "Yahoo Finance (GLD)":
            df = fetch_yfinance()
        min_len = 60
    else:
        if source == "Alpha Vantage" and api_key:
            df = fetch_alpha_vantage_intraday(api_key, "15min")
        elif source == "Yahoo Finance (GLD)":
            df = fetch_yfinance_intraday()
        min_len = 30

    if df is None or len(df) < min_len:
        freq = "D" if mode == "daily" else "15min"
        return generate_simulated_data(freq=freq), True
    return df, False

# ---------- INDICATORS ----------
def add_indicators(df):
    df = df.copy()
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA50"] = df["close"].rolling(50).mean()
    df["RSI"] = calc_rsi(df["close"], 14)
    macd, signal, hist = calc_macd(df["close"])
    df["MACD"] = macd
    df["MACD_signal"] = signal
    df["MACD_hist"] = hist
    return df

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    return macd, signal_line, hist

# ---------- SIGNAL LOGIC (DAILY / SWING) ----------
def generate_signal(df):
    last = df.iloc[-1]
    reasons = []
    score = 0

    if last["close"] > last["MA20"] > last["MA50"]:
        score += 1
        reasons.append(f"Harga ({last['close']:.2f}) di atas MA20 ({last['MA20']:.2f}) dan MA50 ({last['MA50']:.2f}) — tren naik.")
    elif last["close"] < last["MA20"] < last["MA50"]:
        score -= 1
        reasons.append(f"Harga ({last['close']:.2f}) di bawah MA20 ({last['MA20']:.2f}) dan MA50 ({last['MA50']:.2f}) — tren turun.")
    else:
        reasons.append("MA20 dan MA50 belum menunjukkan tren jelas — kondisi sideways.")

    if last["RSI"] > 70:
        score -= 1
        reasons.append(f"RSI menunjukkan overbought ({last['RSI']:.1f}), potensi koreksi turun.")
    elif last["RSI"] < 30:
        score += 1
        reasons.append(f"RSI menunjukkan oversold ({last['RSI']:.1f}), potensi rebound naik.")
    else:
        reasons.append(f"RSI netral ({last['RSI']:.1f}), belum ekstrem.")

    if last["MACD"] > last["MACD_signal"]:
        score += 1
        reasons.append("MACD di atas signal line — momentum bullish.")
    else:
        score -= 1
        reasons.append("MACD di bawah signal line — momentum bearish.")

    signal = "BUY" if score >= 2 else "SELL" if score <= -2 else "HOLD"
    return signal, reasons, score

# ---------- SIGNAL KUAT JANGKA PENDEK (~2 JAM) ----------
def generate_short_term_signal(df_intraday):
    """
    Dihitung dari data intraday (candle ~15 menit).
    'Kuat' berarti mayoritas indikator + momentum candle terakhir searah.
    Perkiraan cakupan waktu ~2 jam ke depan (8 candle x 15 menit), BUKAN jaminan harga.
    """
    d = add_indicators(df_intraday)
    last = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else last
    reasons = []
    score = 0

    # Momentum candle terakhir
    momentum = last["close"] - prev["close"]
    if momentum > 0:
        score += 1
        reasons.append(f"Candle terakhir naik ({momentum:+.2f}), momentum jangka pendek positif.")
    else:
        score -= 1
        reasons.append(f"Candle terakhir turun ({momentum:+.2f}), momentum jangka pendek negatif.")

    # MA jangka pendek
    if last["close"] > last["MA20"]:
        score += 1
        reasons.append(f"Harga masih di atas MA20 intraday ({last['MA20']:.2f}).")
    else:
        score -= 1
        reasons.append(f"Harga di bawah MA20 intraday ({last['MA20']:.2f}).")

    # RSI intraday
    if last["RSI"] > 70:
        score -= 1
        reasons.append(f"RSI intraday overbought ({last['RSI']:.1f}), rawan koreksi cepat.")
    elif last["RSI"] < 30:
        score += 1
        reasons.append(f"RSI intraday oversold ({last['RSI']:.1f}), peluang rebound cepat.")
    else:
        reasons.append(f"RSI intraday netral ({last['RSI']:.1f}).")

    # MACD histogram arah
    if last["MACD_hist"] > 0 and last["MACD_hist"] > prev["MACD_hist"]:
        score += 1
        reasons.append("Histogram MACD positif dan menguat — dorongan naik bertambah.")
    elif last["MACD_hist"] < 0 and last["MACD_hist"] < prev["MACD_hist"]:
        score -= 1
        reasons.append("Histogram MACD negatif dan melemah — tekanan turun bertambah.")
    else:
        reasons.append("Histogram MACD belum menunjukkan percepatan momentum yang jelas.")

    abs_score = abs(score)
    if score >= 3:
        label, strength = "BUY", "KUAT"
    elif score == 2:
        label, strength = "BUY", "SEDANG"
    elif score <= -3:
        label, strength = "SELL", "KUAT"
    elif score == -2:
        label, strength = "SELL", "SEDANG"
    else:
        label, strength = "HOLD", "LEMAH"

    confidence = min(95, 50 + abs_score * 12)
    return label, strength, confidence, reasons, score

# ---------- CHART ----------
def plot_chart(df, title="XAUUSD - Harga & Moving Average"):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["date"], open=df["open"], high=df["high"],
                                  low=df["low"], close=df["close"], name="Harga"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["MA20"], name="MA20", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["MA50"], name="MA50", line=dict(width=1)))
    fig.update_layout(title=title, xaxis_rangeslider_visible=False, height=420)
    return fig

def plot_rsi_macd(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["RSI"], name="RSI"))
    fig.add_hline(y=70, line_dash="dash", line_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="green")
    fig.update_layout(title="RSI (14)", height=250)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df["date"], y=df["MACD_hist"], name="Histogram"))
    fig2.add_trace(go.Scatter(x=df["date"], y=df["MACD"], name="MACD"))
    fig2.add_trace(go.Scatter(x=df["date"], y=df["MACD_signal"], name="Signal"))
    fig2.update_layout(title="MACD", height=250)
    return fig, fig2

# ---------- MAIN APP ----------
def main():
    st.title("🥇 XAUUSD Trading Signal Dashboard")
    st.caption("Rekomendasi rule-based berdasarkan MA, RSI, dan MACD. Bukan saran finansial — selalu gunakan manajemen risiko.")

    st.sidebar.header("Pengaturan Data")
    source = st.sidebar.selectbox("Sumber Data", ["Yahoo Finance (GLD)", "Alpha Vantage"])
    api_key = None
    if source == "Alpha Vantage":
        api_key = st.sidebar.text_input("Alpha Vantage API Key", type="password")

    if st.sidebar.button("Muat / Refresh Data") or "df_daily" not in st.session_state:
        raw_daily, sim_daily = get_data(source, api_key, "daily")
        raw_intra, sim_intra = get_data(source, api_key, "intraday")
        st.session_state["df_daily"] = add_indicators(raw_daily)
        st.session_state["df_intra"] = raw_intra
        st.session_state["sim_daily"] = sim_daily
        st.session_state["sim_intra"] = sim_intra

    df_daily = st.session_state["df_daily"]
    df_intra = st.session_state["df_intra"]

    if st.session_state.get("sim_daily") or st.session_state.get("sim_intra"):
        st.info("⚠️ Sebagian atau seluruh data adalah DATA SIMULASI (fallback), bukan data pasar real.")

    # ---- Sinyal Kuat 2 Jam (tampil paling atas, sesuai permintaan) ----
    st_label, st_strength, st_conf, st_reasons, st_score = generate_short_term_signal(df_intra)
    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    st.subheader(f"⚡ Saran Hari Ini — Perkiraan 2 Jam ke Depan ({now_str})")
    box_color = {"BUY": "green", "SELL": "red", "HOLD": "orange"}[st_label]
    st.markdown(
        f"## :{box_color}[{st_label}] — Kekuatan Sinyal: **{st_strength}** "
        f"(estimasi keyakinan {st_conf}%)"
    )
    with st.container(border=True):
        st.write("**Alasan sinyal jangka pendek:**")
        for r in st_reasons:
            st.write(f"- {r}")
        st.caption("Estimasi ~2 jam dihitung dari 4 candle terakhir (15 menit). Bersifat probabilistik, bukan jaminan. "
                    "Selalu gunakan stop-loss.")

    st.divider()

    # ---- Sinyal Harian / Swing ----
    signal, reasons, score = generate_signal(df_daily)
    col1, col2 = st.columns([1, 2])
    with col1:
        color = {"BUY": "green", "SELL": "red", "HOLD": "orange"}[signal]
        st.markdown(f"### Rekomendasi Harian (Swing): :{color}[{signal}]")
        st.metric("Harga Terakhir (Daily)", f"{df_daily['close'].iloc[-1]:.2f}")
        st.metric("Skor Sinyal Harian", score)
        st.write("**Alasan:**")
        for r in reasons:
            st.write(f"- {r}")

    with col2:
        st.plotly_chart(plot_chart(df_daily), use_container_width=True)

    fig_rsi, fig_macd = plot_rsi_macd(df_daily)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_rsi, use_container_width=True)
    c2.plotly_chart(fig_macd, use_container_width=True)

    with st.expander("Lihat Data Intraday (untuk sinyal 2 jam)"):
        st.dataframe(df_intra.tail(30))
    with st.expander("Lihat Data Harian Mentah"):
        st.dataframe(df_daily.tail(30))

if __name__ == "__main__":
    main()
