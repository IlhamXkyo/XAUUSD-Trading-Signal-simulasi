# XAUUSD Trading Signal Dashboard

Dashboard sinyal trading teknikal berbasis aturan untuk pasangan XAUUSD (emas vs dolar AS) menggunakan kombinasi moving average, RSI, dan konvergensi momentum MACD.

## Fitur

- Indikator teknikal utama: MA20, MA50, RSI (14), dan MACD.
- Evaluasi sinyal harian (Swing): skor akumulasi sinyal untuk rekomendasi Buy, Sell, atau Hold.
- Analisis momentum intraday: kalkulasi pola candle jangka pendek untuk estimasi arah pergerakan harga.
- Sumber data fleksibel: integrasi Yahoo Finance dan Alpha Vantage dengan mekanisme fallback otomatis saat kuota API tercapai.

## Instalasi dan Menjalankan

1. Clone repositori dan masuk ke direktori:
   ```bash
   git clone https://github.com/IlhamXkyo/XAUUSD-Trading-Signal-simulasi.git
   cd XAUUSD-Trading-Signal-simulasi
   ```

2. Pasang dependensi:
   ```bash
   pip install -r requirements.txt
   ```

3. Jalankan dashboard:
   ```bash
   streamlit run app.py
   ```

## Sumber Data

- **Yahoo Finance (GLD)**: Sumber bawaan tanpa kunci API, menggunakan ETF GLD sebagai data proksi pergerakan harga emas.
- **Alpha Vantage**: Opsi memasukkan kunci API di sidebar untuk data langsung FX_DAILY dan FX_INTRADAY.
- **Fallback**: Jika kedua penyedia data mengalami kendala jaringan atau limit kuota, aplikasi memuat data simulasi terstruktur agar antarmuka tetap dapat diuji.

## Disclaimer

Aplikasi ini dibuat murni untuk kebutuhan studi analisis teknikal dan pengujian algoritma sinyal, bukan nasihat investasi keuangan. Segala keputusan transaksi pasar menjadi tanggung jawab masing-masing pengguna.

## Lisensi

MIT License.
