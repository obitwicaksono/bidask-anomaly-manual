"""
Polymarket CLOB V2 API Client
Menangani semua komunikasi dengan Polymarket CLOB V2 API
"""

import hmac
import hashlib
import time
import requests
from typing import Optional, Dict, List, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import jwt
import config


class ClobClient:
    """Client untuk berinteraksi dengan Polymarket CLOB V2 API"""
    
    def __init__(self, api_key: str = None, secret: str = None, passphrase: str = None):
        self.api_key = api_key or config.POLYMARKET_API_KEY
        self.secret = secret or config.POLYMARKET_SECRET
        self.passphrase = passphrase or config.POLYMARKET_PASSPHRASE
        
        self.base_url = config.CLOB_SANDBOX_URL if config.USE_SANDBOX else config.CLOB_API_URL
        self.session = requests.Session()
        
    def _generate_signature(self, method: str, request_path: str, body: str = "") -> str:
        """Generate signature untuk autentikasi API"""
        timestamp = str(int(time.time()))
        message = timestamp + method + request_path + body
        signature = hmac.new(
            self.secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        """Generate headers untuk request API"""
        signature = self._generate_signature(method, request_path, body)
        return {
            'POLY-API-KEY': self.api_key,
            'POLY-SIGNATURE': signature,
            'POLY-TIMESTAMP': str(int(time.time())),
            'POLY-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Melakukan HTTP request ke API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(method, endpoint, str(data) if data else "")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = self.session.post(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers, json=data)
            else:
                raise ValueError(f"Method {method} tidak didukung")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}
    
    # === Market Data Endpoints ===
    
    def get_markets(self, condition_id: str = None) -> List[Dict]:
        """Mendapatkan list markets"""
        params = {}
        if condition_id:
            params['condition_id'] = condition_id
        return self._request('GET', '/markets', data=params)
    
    def get_market_orders(self, token_id: str) -> Dict:
        """Mendapatkan orderbook untuk suatu market"""
        return self._request('GET', f'/book/{token_id}')
    
    def get_ticker(self, token_id: str) -> Dict:
        """Mendapatkan ticker price untuk suatu market"""
        return self._request('GET', f'/ticker/{token_id}')
    
    def get_trades(self, token_id: str, limit: int = 100) -> List[Dict]:
        """Mendapatkan riwayat trades"""
        params = {'market': token_id, 'limit': limit}
        return self._request('GET', '/trades', data=params)
    
    # === Order Management ===
    
    def create_order(self, token_id: str, side: str, size: float, 
                     price: float = None, order_type: str = 'GTC') -> Dict:
        """
        Membuat order baru
        side: 'BUY' atau 'SELL'
        order_type: 'GTC' (limit), 'IOC' (market)
        """
        data = {
            'tokenID': token_id,
            'side': side,
            'size': str(size),
            'orderType': order_type
        }
        
        if price and order_type == 'GTC':
            data['price'] = str(price)
        
        return self._request('POST', '/order', data=data)
    
    def cancel_order(self, order_id: str) -> Dict:
        """Membatalkan order"""
        return self._request('DELETE', '/order', data={'orderID': order_id})
    
    def cancel_all_orders(self, market: str = None) -> Dict:
        """Membatalkan semua order"""
        data = {}
        if market:
            data['market'] = market
        return self._request('DELETE', '/cancel-all', data=data)
    
    # === Portfolio & Positions ===
    
    def get_balance(self) -> Dict:
        """Mendapatkan balance user"""
        return self._request('GET', '/balance')
    
    def get_positions(self, market: str = None) -> List[Dict]:
        """Mendapatkan posisi yang sedang terbuka"""
        params = {}
        if market:
            params['market'] = market
        return self._request('GET', '/position', data=params)
    
    def get_fills(self, market: str = None, limit: int = 100) -> List[Dict]:
        """Mendapatkan riwayat fills/orders yang executed"""
        params = {'limit': limit}
        if market:
            params['market'] = market
        return self._request('GET', '/fills', data=params)
    
    # === Helper Methods ===
    
    def get_yes_token_id(self, market_id: str) -> str:
        """Mendapatkan token ID untuk outcome YES"""
        # Format: market_id + '_YES'
        return f"{market_id}_YES"
    
    def get_no_token_id(self, market_id: str) -> str:
        """Mendapatkan token ID untuk outcome NO"""
        # Format: market_id + '_NO'
        return f"{market_id}_NO"
    
    def calculate_position_value(self, position: Dict, current_price: float) -> float:
        """Menghitung nilai posisi dalam USD"""
        shares = float(position.get('quantity', 0))
        avg_price = float(position.get('avg_price', 0))
        
        # Nilai posisi = shares * current_price (dalam cents)
        return shares * current_price / 100
    
    def calculate_pnl(self, position: Dict, current_price: float) -> float:
        """Menghitung profit/loss untuk suatu posisi"""
        shares = float(position.get('quantity', 0))
        avg_price = float(position.get('avg_price', 0))
        
        # P&L = (current_price - avg_price) * shares / 100
        pnl = (current_price - avg_price) * shares / 100
        return pnl
    
    def check_connection(self) -> bool:
        """Mengecek koneksi ke API"""
        try:
            result = self._request('GET', '/status')
            return 'error' not in result
        except:
            return False
