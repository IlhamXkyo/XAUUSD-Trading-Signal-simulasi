# XAUUSD Trading Signal Dashboard

Dashboard sinyal trading rule-based untuk XAUUSD (emas vs USD): indikator MA20/MA50, RSI(14), MACD, plus **sinyal kuat perkiraan 2 jam ke depan** dari data intraday.

## Instalasi
```bash
pip install -r requirements.txt
streamlit run app.py
```
 
## Sumber Data
- **Yahoo Finance (GLD)**: default, tanpa API key (ETF GLD sebagai proxy harga emas; daily + intraday 15m).
- **Alpha Vantage**: masukkan API key gratis dari https://www.alphavantage.co/support/#api-key di sidebar (FX_DAILY & FX_INTRADAY).
- **Fallback**: jika kedua sumber gagal/limit, aplikasi otomatis memakai data simulasi agar dashboard tetap bisa ditampilkan.

## Fitur Sinyal
1. **Rekomendasi Harian (Swing)** — dari MA20/MA50, RSI, MACD data harian. Skor ≥2 → BUY, ≤-2 → SELL, selain itu → HOLD.
2. **Saran Kuat 2 Jam** — dihitung dari 4 candle 15-menit terakhir (momentum, MA20 intraday, RSI intraday, akselerasi histogram MACD). Menghasilkan label BUY/SELL/HOLD + level kekuatan (LEMAH/SEDANG/KUAT) + estimasi keyakinan (%).

## Disclaimer
Aplikasi ini untuk tujuan edukasi/analisis teknikal semata, bukan nasihat investasi. Estimasi "2 jam ke depan" bersifat probabilistik berbasis pola historis, **bukan jaminan pergerakan harga**. Selalu gunakan manajemen risiko (stop-loss) dan lakukan riset mandiri sebelum trading nyata.
