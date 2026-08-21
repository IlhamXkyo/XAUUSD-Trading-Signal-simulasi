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
from datetime import datetime, timedelta

# ---------- KONFIGURASI HALAMAN ----------
st.set_page_config(page_title="🥇 XAUUSD Trading Signal Pro", layout="wide")

# ---------- FUNGSI CACHE (AGAR TIDAK BOROS KUOTA API) ----------
@st.cache_data(ttl=300, show_spinner="🔄 Mengambil data pasar...")
def get_data(source, api_key, mode, interval="1d", period="6mo"):
    """
    Mengambil data dari sumber yang dipilih (Yahoo Finance atau Alpha Vantage).
    mode: "daily" atau "intraday"
    interval: "1d", "15m", "30m", "1h", dll (sesuai dukungan Yahoo)
    """
    df = None
    if mode == "daily":
        if source == "Alpha Vantage" and api_key:
            df = fetch_alpha_vantage_daily(api_key)
        elif source == "Yahoo Finance (GC=F)":
            df = fetch_yfinance(symbol="GC=F", period=period, interval=interval)
        min_len = 60
    else:  # intraday
        if source == "Alpha Vantage" and api_key:
            df = fetch_alpha_vantage_intraday(api_key, interval=interval)
        elif source == "Yahoo Finance (GC=F)":
            df = fetch_yfinance_intraday(symbol="GC=F", period=period, interval=interval)
        min_len = 30

    if df is None or len(df) < min_len:
        freq = "D" if mode == "daily" else interval
        st.warning(f"⚠️ Gagal mengambil data live. Menggunakan data simulasi (interval {freq}).")
        return generate_simulated_data(freq=freq), True
    return df, False

# ---------- DATA FETCHING ----------
def fetch_yfinance(symbol="GC=F", period="6mo", interval="1d"):
    """Ambil data dari Yahoo Finance."""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        df = df.reset_index()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        date_col = "Date" if "Date" in df.columns else "Datetime"
        df = df.rename(columns={
            date_col: "date",
            "Close": "close",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Volume": "volume"
        })
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        st.error(f"Error Yahoo Finance: {e}")
        return None

def fetch_yfinance_intraday(symbol="GC=F", period="5d", interval="15m"):
    """Ambil data intraday dari Yahoo Finance."""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        df = df.reset_index()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        date_col = "Datetime" if "Datetime" in df.columns else "Date"
        df = df.rename(columns={
            date_col: "date",
            "Close": "close",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Volume": "volume"
        })
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        st.error(f"Error Yahoo Finance Intraday: {e}")
        return None

def fetch_alpha_vantage_daily(api_key):
    """Ambil data harian XAU/USD dari Alpha Vantage."""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "FX_DAILY",
            "from_symbol": "XAU",
            "to_symbol": "USD",
            "apikey": api_key,
            "outputsize": "compact"
        }
        r = requests.get(url, params=params, timeout=10)
        data_json = r.json()
        if "Note" in data_json:
            st.warning(f"⚠️ Alpha Vantage limit: {data_json['Note']}")
            return None
        if "Error" in data_json:
            st.warning(f"⚠️ Alpha Vantage error: {data_json['Error']}")
            return None
        data = data_json.get("Time Series FX (Daily)")
        if not data:
            return None
        df = pd.DataFrame(data).T.reset_index()
        df.columns = ["date", "open", "high", "low", "close"]
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        df["volume"] = 0
        return df.sort_values("date").reset_index(drop=True)
    except Exception as e:
        st.error(f"Error Alpha Vantage: {e}")
        return None

def fetch_alpha_vantage_intraday(api_key, interval="15min"):
    """Ambil data intraday XAU/USD dari Alpha Vantage."""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": "XAU",
            "to_symbol": "USD",
            "interval": interval,
            "apikey": api_key,
            "outputsize": "compact"
        }
        r = requests.get(url, params=params, timeout=10)
        data_json = r.json()
        if "Note" in data_json:
            st.warning(f"⚠️ Alpha Vantage limit: {data_json['Note']}")
            return None
        if "Error" in data_json:
            st.warning(f"⚠️ Alpha Vantage error: {data_json['Error']}")
            return None
        key = f"Time Series FX ({interval})"
        data = data_json.get(key)
        if not data:
            return None
        df = pd.DataFrame(data).T.reset_index()
        df.columns = ["date", "open", "high", "low", "close"]
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        df["volume"] = 0
        return df.sort_values("date").reset_index(drop=True)
    except Exception as e:
        st.error(f"Error Alpha Vantage Intraday: {e}")
        return None

def generate_simulated_data(freq="D", n=180, start_price=2000.0):
    """Buat data simulasi untuk fallback jika API gagal."""
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

# ---------- INDIKATOR TEKNIKAL ----------
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

def calc_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

# ---------- SINYAL HARIAN (SWING) ----------
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
        reasons.append(f"RSI overbought ({last['RSI']:.1f}), potensi koreksi turun.")
    elif last["RSI"] < 30:
        score += 1
        reasons.append(f"RSI oversold ({last['RSI']:.1f}), potensi rebound naik.")
    else:
        reasons.append(f"RSI netral ({last['RSI']:.1f}), belum ekstrem.")

    if last["MACD"] > last["MACD_signal"]:
        score += 1
        reasons.append("MACD di atas signal line — momentum bullish.")
    else:
        score -= 1
        reasons.append("MACD di bawah signal line — momentum bearish.")

    if score >= 2:
        signal = "BUY"
    elif score <= -2:
        signal = "SELL"
    else:
        signal = "HOLD"
    return signal, reasons, score

# ---------- PREDIKSI POLA GENERAL (FLEKSIBEL) ----------
def pattern_forecast_general(df, window, forward, top_n=15):
    """
    🔮 Prediksi berdasarkan pola historis.
    - window: jumlah candle untuk pola acuan
    - forward: jumlah candle ke depan yang diprediksi
    """
    prices = df['close'].values
    if len(prices) < window + forward + 30:
        return None, None, 0, "Data tidak cukup"

    current_window = prices[-window:]
    norm_current = (current_window / current_window[0]) - 1

    distances = []
    for i in range(0, len(prices) - window - forward - 5):
        hist_window = prices[i:i+window]
        norm_hist = (hist_window / hist_window[0]) - 1
        dist = np.mean((norm_current - norm_hist) ** 2)
        future_ret = (prices[i+window+forward] / prices[i+window]) - 1
        distances.append((dist, future_ret))

    if not distances:
        return None, None, 0, "Tidak ada pola historis"

    distances.sort(key=lambda x: x[0])
    top_matches = distances[:top_n]
    
    avg_return = np.mean([x[1] for x in top_matches]) * 100
    win_rate = sum(1 for x in top_matches if x[1] > 0) / len(top_matches) * 100

    # Arah dominan
    if avg_return > 0.5:
        direction = "📈 NAIK (BULLISH)"
    elif avg_return < -0.5:
        direction = "📉 TURUN (BEARISH)"
    else:
        direction = "➖ NETRAL / SIDEWAYS"

    return avg_return, win_rate, len(top_matches), direction

# ---------- CHART ----------
def plot_chart(df, title="XAUUSD - Harga & Moving Average"):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Harga"
    ))
    fig.add_trace(go.Scatter(x=df["date"], y=df["MA20"], name="MA20", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["MA50"], name="MA50", line=dict(width=1)))
    fig.update_layout(title=title, xaxis_rangeslider_visible=False, height=420)
    return fig

def plot_rsi_macd(df):
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df["date"], y=df["RSI"], name="RSI"))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
    fig_rsi.update_layout(title="RSI (14)", height=250)

    fig_macd = go.Figure()
    fig_macd.add_trace(go.Bar(x=df["date"], y=df["MACD_hist"], name="Histogram"))
    fig_macd.add_trace(go.Scatter(x=df["date"], y=df["MACD"], name="MACD"))
    fig_macd.add_trace(go.Scatter(x=df["date"], y=df["MACD_signal"], name="Signal"))
    fig_macd.update_layout(title="MACD", height=250)
    return fig_rsi, fig_macd

# ---------- MAIN APP ----------
def main():
    st.title("🥇 XAUUSD Trading Signal Pro")
    st.caption("Sinyal berbasis aturan + Prediksi pola historis dengan pilihan periode fleksibel. Bukan saran finansial.")

    # ---------- SIDEBAR ----------
    st.sidebar.header("⚙️ Pengaturan")
    source = st.sidebar.selectbox("Sumber Data", ["Yahoo Finance (GC=F)", "Alpha Vantage"])
    api_key = None
    if source == "Alpha Vantage":
        api_key = st.sidebar.text_input("Alpha Vantage API Key", type="password")

    # --- Pilihan Periode Prediksi ---
    st.sidebar.header("📅 Periode Prediksi")
    pred_options = {
        "30 Menit": {"mode": "intraday", "interval": "5m", "period": "2d", "window": 6, "forward": 6, "label": "30 menit"},
        "1 Jam":    {"mode": "intraday", "interval": "15m", "period": "5d", "window": 4, "forward": 4, "label": "1 jam"},
        "2 Jam":    {"mode": "intraday", "interval": "15m", "period": "5d", "window": 8, "forward": 8, "label": "2 jam"},
        "4 Jam":    {"mode": "intraday", "interval": "15m", "period": "5d", "window": 16, "forward": 16, "label": "4 jam"},
        "1 Hari":   {"mode": "daily", "interval": "1d", "period": "6mo", "window": 5, "forward": 1, "label": "1 hari"},
        "5 Hari":   {"mode": "daily", "interval": "1d", "period": "6mo", "window": 10, "forward": 5, "label": "5 hari"},
        "10 Hari":  {"mode": "daily", "interval": "1d", "period": "6mo", "window": 10, "forward": 10, "label": "10 hari"},
        "30 Hari":  {"mode": "daily", "interval": "1d", "period": "1y", "window": 20, "forward": 30, "label": "30 hari"},
    }
    selected_pred = st.sidebar.selectbox("Pilih Periode", list(pred_options.keys()), index=5)  # default 5 hari
    pred_config = pred_options[selected_pred]

    if st.sidebar.button("🔄 Muat / Refresh Data") or "df" not in st.session_state:
        raw_df, sim = get_data(
            source, api_key,
            mode=pred_config["mode"],
            interval=pred_config["interval"],
            period=pred_config["period"]
        )
        st.session_state["df"] = add_indicators(raw_df)
        st.session_state["sim"] = sim
        st.session_state["pred_config"] = pred_config  # simpan config untuk dipakai di UI
        st.session_state["selected_pred"] = selected_pred

    # Cek apakah data sudah ada
    if "df" not in st.session_state:
        st.warning("⏳ Klik tombol 'Muat / Refresh Data' untuk memulai.")
        return

    df = st.session_state["df"]
    config = st.session_state["pred_config"]
    if st.session_state.get("sim"):
        st.info("⚠️ Data simulasi (fallback), bukan data pasar real.")

    # ---------- TAMPILKAN INFORMASI PERIODE ----------
    st.subheader(f"📊 Analisis untuk periode: **{selected_pred}**")
    st.caption(f"Data interval: {config['interval']} | Window: {config['window']} candle | Forward: {config['forward']} candle")

    # ---------- SINYAL BERDASARKAN INDIKATOR ----------
    signal, reasons, score = generate_signal(df)
    last_price = df['close'].iloc[-1]

    col1, col2 = st.columns([1, 2])
    with col1:
        color = {"BUY": "green", "SELL": "red", "HOLD": "orange"}[signal]
        st.markdown(f"### 📊 Rekomendasi :{color}[{signal}]")
        st.metric("Harga Terakhir", f"{last_price:.2f}")
        st.metric("Skor Sinyal", score)

        # ATR + SL/TP
        atr_series = calc_atr(df)
        atr = atr_series.iloc[-1] if not atr_series.isna().all() else 0
        if atr > 0 and signal != "HOLD":
            if signal == "BUY":
                sl = last_price - (2 * atr)
                tp = last_price + (3 * atr)
            else:
                sl = last_price + (2 * atr)
                tp = last_price - (3 * atr)
            st.metric("Stop Loss (2x ATR)", f"{sl:.2f}")
            st.metric("Take Profit (3x ATR)", f"{tp:.2f}")
        else:
            st.caption("ATR tidak tersedia atau sinyal HOLD.")

        st.write("**Alasan:**")
        for r in reasons:
            st.write(f"- {r}")

    with col2:
        st.plotly_chart(plot_chart(df, title=f"XAUUSD - {selected_pred}"), use_container_width=True)

    # ---------- CHART RSI & MACD ----------
    fig_rsi, fig_macd = plot_rsi_macd(df)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_rsi, use_container_width=True)
    c2.plotly_chart(fig_macd, use_container_width=True)

    # ---------- 🔮 PREDIKSI POLA HISTORIS (sesuai periode) ----------
    st.divider()
    st.subheader(f"🔮 Prediksi Berdasarkan Pola Historis ({selected_pred})")

    with st.spinner("Menganalisis pola..."):
        avg_ret, win_rate, matched, direction = pattern_forecast_general(
            df,
            window=config["window"],
            forward=config["forward"],
            top_n=15
        )

        if avg_ret is not None and matched > 0:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(f"📈 Rata-rata Return ({config['label']})", f"{avg_ret:.2f}%", delta=f"{matched} pola mirip")
            col_b.metric("🎯 Akurasi Pola Naik", f"{win_rate:.1f}%")
            col_c.metric("🔮 Arah Dominan", direction)

            if "NAIK" in direction:
                st.success(f"✅ Kecenderungan harga **NAIK** dalam {config['label']} ke depan. (Rata-rata +{avg_ret:.2f}%)")
            elif "TURUN" in direction:
                st.error(f"❌ Kecenderungan harga **TURUN** dalam {config['label']} ke depan. (Rata-rata {avg_ret:.2f}%)")
            else:
                st.warning(f"➖ Kecenderungan **NETRAL / SIDEWAYS** dalam {config['label']} ke depan. (Rata-rata {avg_ret:.2f}%)")
        else:
            st.info("⏳ Data historis belum cukup untuk prediksi pola.")

    # ---------- DATA MENTAH ----------
    with st.expander("📄 Lihat Data Mentah"):
        st.dataframe(df.tail(30))

if __name__ == "__main__":
    main()
