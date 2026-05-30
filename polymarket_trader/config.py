"""
Konfigurasi untuk Polymarket Trading Bot
"""

# Polymarket CLOB V2 API Configuration
POLYMARKET_API_KEY = "your_api_key_here"
POLYMARKET_SECRET = "your_secret_here"
POLYMARKET_PASSPHRASE = "your_passphrase_here"

# API Endpoints
CLOB_API_URL = "https://clob.polymarket.com"
CLOB_SANDBOX_URL = "https://sandbox.clob.polymarket.com"

# Gunakan sandbox untuk testing, production untuk live trading
USE_SANDBOX = True

# Trading Configuration
DEFAULT_POSITION_SIZE = 100  # USD
DEFAULT_TAKE_PROFIT = 20  # persen
DEFAULT_STOP_LOSS = 10  # persen

# Signal Configuration
BID_ASK_SPREAD_THRESHOLD = 5  # persen, threshold untuk anomaly detection
VOLUME_SPIKE_THRESHOLD = 3  # kali lipat dari average

# WebSocket Configuration
WS_URL = "wss://ws.clob.polymarket.com"

# Market Filter - Crypto UP/DOWN 5 menit
MARKET_KEYWORDS = ["CRYPTO", "UP", "DOWN", "5M"]
