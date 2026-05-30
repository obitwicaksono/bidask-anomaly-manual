# Polymarket CLOB V2 Trading Bot

Aplikasi web Python untuk trading di Polymarket menggunakan CLOB V2, khusus untuk pasar crypto UP/DOWN 5 menit.

## Fitur

1. **Order Execution**: 1-tap, Limit, Market order
2. **Take Profit**: Otomatis close posisi saat target profit tercapai
3. **Stop Loss**: Otomatis close posisi saat loss mencapai batas
4. **Kalkulasi Keuntungan**: Real-time P&L seperti di website Polymarket
5. **Bid/Ask Monitor**: Monitoring harga bid/ask dalam cent per token
6. **Signal Trading**: Logika sinyal dari anomaly bid/ask spread
7. **SIMULATION MODE**: Mode simulasi untuk testing strategi tanpa risiko! 🎮

## Struktur Project

```
polymarket_trader/
├── app/
│   ├── __init__.py
│   ├── clob_client.py      # Client untuk Polymarket CLOB V2
│   ├── trading_engine.py   # Logika trading dan eksekusi order
│   ├── signal_generator.py # Generator sinyal dari anomaly bid/ask
│   ├── calculator.py       # Kalkulator profit/loss
│   └── simulator.py        # Simulasi market & trading (NEW!)
├── templates/
│   └── index.html          # UI utama aplikasi
├── static/
│   ├── css/
│   │   └── style.css       # Styling aplikasi
│   └── js/
│       └── main.js         # Frontend logic dan WebSocket
├── requirements.txt        # Dependencies Python
├── config.py              # Konfigurasi API keys dan settings
└── run.py                 # Entry point aplikasi
```

## Instalasi

### Prasyarat
- Python 3.8 atau lebih baru
- pip (Python package manager)

### Langkah-langkah

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Konfigurasi Environment Variables:**

   Salin file contoh dan edit dengan kredensial Anda:
   ```bash
   cp .env.example .env
   ```
   
   Edit file `.env`:
   ```ini
   # POLYMARKET CLOB V2 CONFIGURATION (untuk LIVE mode)
   POLYMARKET_API_KEY=your_api_key_here
   POLYMARKET_SECRET_KEY=your_secret_key_here
   POLYMARKET_PASSPHRASE=your_passphrase_here
   POLYMARKET_WALLET_PRIVATE_KEY=your_wallet_private_key_here
   
   # APP CONFIGURATION
   FLASK_ENV=development
   SECRET_KEY=supersecretkey_change_this
   PORT=5000
   
   # SIMULATION CONFIG
   SIMULATION_INITIAL_BALANCE=1000
   ```

   > **⚠️ PENTING:** Jangan commit file `.env` ke repository publik! File ini sudah ada di `.gitignore`.

3. **Jalankan aplikasi:**
```bash
python run.py
```

4. **Buka browser** di `http://localhost:5000`

## Cara Menggunakan

### SIMULATION MODE (Recommended for Testing) 🎮
1. Klik tombol **"SIMULATION"** di header untuk masuk ke mode simulasi
2. Balance awal $1000 akan diberikan secara virtual
3. Pilih tipe order (1-tap, Limit, Market)
4. Set Take Profit (%) dan Stop Loss (%) 
5. Klik **BUY YES** atau **BUY NO** untuk eksekusi
6. Monitor posisi, P&L, dan trade history secara real-time
7. Market akan bergerak otomatis dengan anomaly detection
8. Klik **Reset Simulation** untuk memulai ulang

### LIVE MODE (Real Trading) ⚠️
1. Pastikan API credentials sudah dikonfigurasi
2. Klik tombol **"LIVE Trading"** di header
3. Pilih market crypto UP/DOWN 5 menit dari dropdown
4. Monitor bid/ask price dan sinyal trading
5. Pilih tipe order (1-tap, Limit, Market)
6. Set Take Profit dan Stop Loss jika diperlukan
7. Eksekusi order YES atau NO

## Mode Simulasi - Fitur Lengkap

- ✅ **Virtual Balance**: Mulai dengan $1000 uang virtual
- ✅ **Market Simulation**: Price movement dengan random walk + anomaly injection
- ✅ **Auto TP/SL**: Take Profit dan Stop Loss otomatis dieksekusi
- ✅ **Real-time P&L**: Update profit/loss setiap tick
- ✅ **Trade History**: Riwayat semua trade yang dilakukan
- ✅ **Anomaly Detection**: Sistem mendeteksi anomali bid/ask spread
- ✅ **Risk-Free**: Test strategi tanpa kehilangan uang asli!

## Catatan Penting

- **SIMULATION MODE tidak memerlukan API credentials** - bisa langsung digunakan!
- Untuk LIVE trading, pastikan Anda memiliki akun Polymarket dan API credentials
- Trading melibatkan risiko, gunakan dengan bijak
- Gunakan simulation mode untuk testing strategi sebelum trading dengan uang asli
- Aplikasi ini menggunakan Polymarket CLOB V2 API untuk live trading

## Troubleshooting

**Masalah: Tidak bisa connect ke Polymarket (Live Mode)**
- Periksa kembali API Key dan Secret Key di file `.env`
- Pastikan IP address Anda tidak diblokir oleh Polymarket
- Cek log terminal untuk pesan error spesifik dari API

**Masalah: Port 5000 sudah digunakan**
- Ubah variabel `PORT` di file `.env` menjadi angka lain (misal: 5001)
- Atau matikan aplikasi lain yang menggunakan port tersebut

**Masalah: ModuleNotFoundError**
- Pastikan Anda sudah mengaktifkan virtual environment (jika digunakan)
- Jalankan ulang `pip install -r requirements.txt`

## Lisensi

Project ini dibuat untuk tujuan edukasi dan pengembangan pribadi. Silakan dimodifikasi sesuai kebutuhan.
