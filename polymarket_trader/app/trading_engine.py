"""
Trading Engine
Mengelola eksekusi order, take profit, dan stop loss
"""

from typing import Dict, List, Optional
from datetime import datetime
import config


class TradingEngine:
    """
    Engine untuk mengelola trading operations
    termasuk order execution, TP/SL monitoring
    """
    
    def __init__(self, clob_client):
        self.client = clob_client
        self.active_orders = {}  # Menyimpan order yang aktif dengan TP/SL
        self.position_tracking = {}  # Track posisi untuk TP/SL
        
    def execute_market_order(self, token_id: str, side: str, size_usd: float) -> Dict:
        """
        Eksekusi market order (IOC - Immediate or Cancel)
        
        Args:
            token_id: ID token untuk ditradingkan
            side: 'BUY' atau 'SELL'
            size_usd: Ukuran order dalam USD
        
        Returns:
            Result dari order execution
        """
        # Untuk market order, kita gunakan orderType IOC
        # Harga akan dieksekusi pada harga market terbaik
        
        result = self.client.create_order(
            token_id=token_id,
            side=side,
            size=size_usd,
            order_type='IOC'  # Market order
        )
        
        if result and 'orderID' in result:
            return {
                'success': True,
                'order_id': result['orderID'],
                'type': 'MARKET',
                'side': side,
                'size_usd': size_usd,
                'token_id': token_id,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'type': 'MARKET'
            }
    
    def execute_limit_order(self, token_id: str, side: str, 
                           size_usd: float, price_cents: float) -> Dict:
        """
        Eksekusi limit order (GTC - Good Till Cancelled)
        
        Args:
            token_id: ID token untuk ditradingkan
            side: 'BUY' atau 'SELL'
            size_usd: Ukuran order dalam USD
            price_cents: Harga limit dalam cents
        
        Returns:
            Result dari order execution
        """
        result = self.client.create_order(
            token_id=token_id,
            side=side,
            size=size_usd,
            price=price_cents,
            order_type='GTC'  # Limit order
        )
        
        if result and 'orderID' in result:
            return {
                'success': True,
                'order_id': result['orderID'],
                'type': 'LIMIT',
                'side': side,
                'size_usd': size_usd,
                'price': price_cents,
                'token_id': token_id,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'type': 'LIMIT'
            }
    
    def execute_one_tap_order(self, token_id: str, side: str, 
                             size_usd: float = None) -> Dict:
        """
        Eksekusi 1-tap order (instant buy/sell di harga market)
        Ini adalah quick order tanpa konfirmasi tambahan
        
        Args:
            token_id: ID token untuk ditradingkan
            side: 'BUY' atau 'SELL'
            size_usd: Ukuran order dalam USD (default dari config)
        
        Returns:
            Result dari order execution
        """
        if size_usd is None:
            size_usd = config.DEFAULT_POSITION_SIZE
        
        # 1-tap langsung eksekusi market order
        return self.execute_market_order(token_id, side, size_usd)
    
    def set_take_profit(self, position_id: str, token_id: str, 
                       target_price: float, size_to_close: float = None) -> bool:
        """
        Set take profit level untuk suatu posisi
        
        Args:
            position_id: ID unik untuk posisi
            token_id: ID token
            target_price: Harga target untuk TP (dalam cents)
            size_to_close: Jumlah yang akan ditutup (default: semua)
        
        Returns:
            True jika berhasil diset
        """
        self.active_orders[position_id] = {
            'type': 'TAKE_PROFIT',
            'token_id': token_id,
            'target_price': target_price,
            'size': size_to_close,
            'created_at': datetime.now(),
            'status': 'ACTIVE'
        }
        return True
    
    def set_stop_loss(self, position_id: str, token_id: str,
                     stop_price: float, size_to_close: float = None) -> bool:
        """
        Set stop loss level untuk suatu posisi
        
        Args:
            position_id: ID unik untuk posisi
            token_id: ID token
            stop_price: Harga stop loss (dalam cents)
            size_to_close: Jumlah yang akan ditutup (default: semua)
        
        Returns:
            True jika berhasil diset
        """
        self.active_orders[position_id] = {
            'type': 'STOP_LOSS',
            'token_id': token_id,
            'stop_price': stop_price,
            'size': size_to_close,
            'created_at': datetime.now(),
            'status': 'ACTIVE'
        }
        return True
    
    def check_tp_sl_triggers(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Cek apakah ada TP/SL yang trigger berdasarkan harga saat ini
        
        Args:
            current_prices: Dict harga saat ini untuk setiap token_id
        
        Returns:
            List order yang perlu dieksekusi
        """
        triggered_orders = []
        
        for position_id, order_data in list(self.active_orders.items()):
            if order_data['status'] != 'ACTIVE':
                continue
            
            token_id = order_data['token_id']
            current_price = current_prices.get(token_id)
            
            if not current_price:
                continue
            
            triggered = False
            
            # Check Take Profit
            if order_data['type'] == 'TAKE_PROFIT':
                target_price = order_data['target_price']
                
                # Untuk long position: trigger jika current >= target
                # Untuk short position: trigger jika current <= target
                # Simplifikasi: asumsikan long position
                if current_price >= target_price:
                    triggered = True
                    order_data['triggered_at'] = datetime.now()
            
            # Check Stop Loss
            elif order_data['type'] == 'STOP_LOSS':
                stop_price = order_data['stop_price']
                
                # Untuk long position: trigger jika current <= stop
                if current_price <= stop_price:
                    triggered = True
                    order_data['triggered_at'] = datetime.now()
            
            if triggered:
                order_data['status'] = 'TRIGGERED'
                triggered_orders.append({
                    'position_id': position_id,
                    'order_data': order_data,
                    'current_price': current_price
                })
        
        return triggered_orders
    
    def execute_tp_sl_order(self, position_id: str, token_id: str, 
                           side: str, size: float) -> Dict:
        """
        Eksekusi order untuk menutup posisi saat TP/SL trigger
        
        Args:
            position_id: ID posisi
            token_id: ID token
            side: Sisi order (SELL untuk close long, BUY untuk close short)
            size: Ukuran yang akan ditutup
        
        Returns:
            Result dari eksekusi
        """
        # Eksekusi market order untuk close posisi
        result = self.execute_market_order(token_id, side, size)
        
        if result['success']:
            # Update status order
            if position_id in self.active_orders:
                self.active_orders[position_id]['status'] = 'EXECUTED'
                self.active_orders[position_id]['executed_at'] = datetime.now()
        
        return result
    
    def get_active_tp_sl(self) -> List[Dict]:
        """Mendapatkan semua TP/SL yang masih aktif"""
        active = []
        for position_id, order_data in self.active_orders.items():
            if order_data['status'] == 'ACTIVE':
                active.append({
                    'position_id': position_id,
                    **order_data
                })
        return active
    
    def cancel_tp_sl(self, position_id: str) -> bool:
        """Membatalkan TP/SL untuk suatu posisi"""
        if position_id in self.active_orders:
            self.active_orders[position_id]['status'] = 'CANCELLED'
            return True
        return False
    
    def calculate_tp_price(self, entry_price: float, target_roi_percent: float) -> float:
        """
        Hitung harga take profit berdasarkan target ROI
        
        Args:
            entry_price: Harga entry (dalam cents)
            target_roi_percent: Target ROI dalam persen
        
        Returns:
            Harga take profit dalam cents
        """
        return entry_price * (1 + target_roi_percent / 100)
    
    def calculate_sl_price(self, entry_price: float, max_loss_percent: float) -> float:
        """
        Hitung harga stop loss berdasarkan maximum loss yang diinginkan
        
        Args:
            entry_price: Harga entry (dalam cents)
            max_loss_percent: Maximum loss dalam persen
        
        Returns:
            Harga stop loss dalam cents
        """
        return entry_price * (1 - max_loss_percent / 100)
