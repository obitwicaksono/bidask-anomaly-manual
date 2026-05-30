"""
Signal Generator
Logika sinyal trading dari anomaly bid/ask spread
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import config


class SignalGenerator:
    """
    Generator sinyal trading berdasarkan analisis anomaly bid/ask
    """
    
    def __init__(self):
        self.spread_threshold = config.BID_ASK_SPREAD_THRESHOLD
        self.volume_threshold = config.VOLUME_SPIKE_THRESHOLD
        self.price_history = {}  # Menyimpan history price untuk analisis trend
        
    def analyze_orderbook(self, orderbook: Dict) -> Dict:
        """
        Menganalisis orderbook untuk mendeteksi anomaly
        
        Args:
            orderbook: Format dari CLOB API
                {
                    'bids': [{'price': x, 'size': y}, ...],
                    'asks': [{'price': x, 'size': y}, ...]
                }
        
        Returns:
            Dict dengan hasil analisis
        """
        if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
            return {'signal': 'NEUTRAL', 'confidence': 0}
        
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        
        if not bids or not asks:
            return {'signal': 'NEUTRAL', 'confidence': 0}
        
        # Get best bid dan ask
        best_bid = float(bids[0]['price'])
        best_ask = float(asks[0]['price'])
        
        # Calculate spread
        mid_price = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        spread_percent = (spread / mid_price) * 100 if mid_price > 0 else 0
        
        # Calculate order book imbalance
        bid_volume = sum(float(bid['size']) for bid in bids[:5])  # Top 5 bids
        ask_volume = sum(float(ask['size']) for ask in asks[:5])  # Top 5 asks
        total_volume = bid_volume + ask_volume
        
        imbalance = 0
        if total_volume > 0:
            imbalance = (bid_volume - ask_volume) / total_volume
        
        # Detect anomaly
        signal_data = {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'mid_price': mid_price,
            'spread': spread,
            'spread_percent': spread_percent,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'imbalance': imbalance,
            'signal': 'NEUTRAL',
            'confidence': 0,
            'reason': ''
        }
        
        # Logika sinyal berdasarkan anomaly detection
        
        # 1. Wide Spread Anomaly (spread > threshold)
        if spread_percent > self.spread_threshold:
            signal_data['signal'] = 'WAIT'
            signal_data['confidence'] = min(100, spread_percent * 2)
            signal_data['reason'] = f'Spread terlalu lebar: {spread_percent:.2f}%'
            
            # Jika spread sangat lebar, bisa jadi opportunity
            if spread_percent > self.spread_threshold * 2:
                signal_data['signal'] = 'OPPORTUNITY'
                signal_data['reason'] = f'Spread sangat lebar - potensi arbitrage'
        
        # 2. Order Book Imbalance
        elif abs(imbalance) > 0.6:  # 60% imbalance
            if imbalance > 0:
                # Lebih banyak buy pressure
                signal_data['signal'] = 'BULLISH'
                signal_data['confidence'] = abs(imbalance) * 100
                signal_data['reason'] = f'Buy pressure kuat: {imbalance*100:.1f}% imbalance'
            else:
                # Lebih banyak sell pressure
                signal_data['signal'] = 'BEARISH'
                signal_data['confidence'] = abs(imbalance) * 100
                signal_data['reason'] = f'Sell pressure kuat: {abs(imbalance)*100:.1f}% imbalance'
        
        # 3. Normal market conditions
        else:
            signal_data['signal'] = 'NEUTRAL'
            signal_data['confidence'] = 50
            signal_data['reason'] = 'Kondisi market normal'
        
        return signal_data
    
    def detect_price_anomaly(self, token_id: str, current_price: float, 
                            window_size: int = 10) -> Dict:
        """
        Mendeteksi anomaly harga berdasarkan historical data
        
        Args:
            token_id: ID token/market
            current_price: Harga saat ini
            window_size: Ukuran window untuk moving average
        
        Returns:
            Dict dengan hasil deteksi anomaly
        """
        # Simpan price ke history
        if token_id not in self.price_history:
            self.price_history[token_id] = []
        
        self.price_history[token_id].append({
            'price': current_price,
            'timestamp': self._get_timestamp()
        })
        
        # Keep only last N prices
        if len(self.price_history[token_id]) > window_size * 2:
            self.price_history[token_id] = self.price_history[token_id][-window_size*2:]
        
        # Butuh minimal window_size data points
        if len(self.price_history[token_id]) < window_size:
            return {
                'anomaly': False,
                'type': None,
                'deviation': 0
            }
        
        prices = [p['price'] for p in self.price_history[token_id][-window_size:]]
        avg_price = np.mean(prices)
        std_price = np.std(prices)
        
        # Hitung deviation dari average
        deviation = (current_price - avg_price) / avg_price * 100 if avg_price > 0 else 0
        
        anomaly_result = {
            'anomaly': False,
            'type': None,
            'deviation': deviation,
            'avg_price': avg_price,
            'std_price': std_price,
            'current_price': current_price
        }
        
        # Deteksi anomaly jika deviation > 2 standar deviasi
        if std_price > 0 and abs(deviation) > 2 * std_price / avg_price * 100:
            anomaly_result['anomaly'] = True
            anomaly_result['type'] = 'SPIKE_UP' if deviation > 0 else 'SPIKE_DOWN'
        
        return anomaly_result
    
    def generate_trade_signal(self, orderbook_analysis: Dict, 
                             price_anomaly: Dict) -> Dict:
        """
        Generate sinyal trade final berdasarkan kombinasi analisis
        
        Args:
            orderbook_analysis: Hasil analisis orderbook
            price_anomaly: Hasil deteksi price anomaly
        
        Returns:
            Dict dengan sinyal trade final
        """
        signal = 'HOLD'
        confidence = 0
        reasons = []
        
        # Kombinasi sinyal dari orderbook dan price anomaly
        ob_signal = orderbook_analysis.get('signal', 'NEUTRAL')
        ob_confidence = orderbook_analysis.get('confidence', 0)
        
        is_anomaly = price_anomaly.get('anomaly', False)
        anomaly_type = price_anomaly.get('type', None)
        deviation = price_anomaly.get('deviation', 0)
        
        # Logic combination
        if ob_signal == 'BULLISH' and not is_anomaly:
            signal = 'BUY'
            confidence = ob_confidence
            reasons.append(orderbook_analysis.get('reason', ''))
            
        elif ob_signal == 'BEARISH' and not is_anomaly:
            signal = 'SELL'
            confidence = ob_confidence
            reasons.append(orderbook_analysis.get('reason', ''))
            
        elif is_anomaly and anomaly_type == 'SPIKE_DOWN' and ob_signal != 'BEARISH':
            # Price spike down tapi tidak ada sell pressure di orderbook
            # Potensi bounce back
            signal = 'BUY'
            confidence = min(80, abs(deviation) * 2)
            reasons.append(f'Price spike down {deviation:.2f}% - potensi reversal')
            
        elif is_anomaly and anomaly_type == 'SPIKE_UP' and ob_signal != 'BULLISH':
            # Price spike up tapi tidak ada buy pressure di orderbook
            # Potensi pullback
            signal = 'SELL'
            confidence = min(80, abs(deviation) * 2)
            reasons.append(f'Price spike up {deviation:.2f}% - potensi pullback')
            
        elif ob_signal == 'OPPORTUNITY':
            signal = 'CONSIDER'
            confidence = ob_confidence
            reasons.append(orderbook_analysis.get('reason', ''))
            
        elif ob_signal == 'WAIT':
            signal = 'WAIT'
            confidence = ob_confidence
            reasons.append(orderbook_analysis.get('reason', ''))
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'timestamp': self._get_timestamp(),
            'orderbook_signal': ob_signal,
            'price_anomaly': is_anomaly
        }
    
    def _get_timestamp(self) -> int:
        """Get current timestamp"""
        import time
        return int(time.time())
    
    def reset_history(self, token_id: str = None):
        """Reset price history"""
        if token_id:
            self.price_history[token_id] = []
        else:
            self.price_history = {}
