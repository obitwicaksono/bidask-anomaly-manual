"""
Konfigurasi untuk Polymarket Trading Bot
Load dari environment variables (.env file)
"""

import os
from dotenv import load_dotenv

# Load environment variables dari .env file
load_dotenv()

# Polymarket CLOB V2 API Configuration
POLYMARKET_API_KEY = os.getenv("POLYMARKET_API_KEY", "")
POLYMARKET_SECRET = os.getenv("POLYMARKET_SECRET_KEY", "")
POLYMARKET_PASSPHRASE = os.getenv("POLYMARKET_PASSPHRASE", "")
POLYMARKET_WALLET_PRIVATE_KEY = os.getenv("POLYMARKET_WALLET_PRIVATE_KEY", "")

# API Endpoints
CLOB_API_URL = "https://clob.polymarket.com"
CLOB_SANDBOX_URL = "https://sandbox.clob.polymarket.com"

# Gunakan sandbox untuk testing, production untuk live trading
USE_SANDBOX = os.getenv("FLASK_ENV", "development") == "development"

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

# Simulation Configuration
SIMULATION_INITIAL_BALANCE = float(os.getenv("SIMULATION_INITIAL_BALANCE", "1000"))

# Flask Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
PORT = int(os.getenv("PORT", "5000"))
FLASK_ENV = os.getenv("FLASK_ENV", "development")

# WebSocket Async Mode
WEBSOCKET_ASYNC_MODE = os.getenv("WEBSOCKET_ASYNC_MODE", "eventlet")
