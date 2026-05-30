"""
Profit/Loss Calculator
Menghitung keuntungan/kerugian seperti di website Polymarket
"""

from typing import Dict, List, Optional


class ProfitCalculator:
    """Kalkulator untuk menghitung P&L dan metrik trading lainnya"""
    
    @staticmethod
    def calculate_roi(entry_price: float, current_price: float) -> float:
        """
        Menghitung Return on Investment (ROI) dalam persen
        ROI = ((current_price - entry_price) / entry_price) * 100
        """
        if entry_price == 0:
            return 0.0
        return ((current_price - entry_price) / entry_price) * 100
    
    @staticmethod
    def calculate_pnl(positions: List[Dict], current_prices: Dict[str, float]) -> Dict:
        """
        Menghitung total P&L untuk semua posisi
        
        Args:
            positions: List posisi dengan format:
                {
                    'market': 'market_id',
                    'outcome': 'YES' atau 'NO',
                    'quantity': jumlah shares,
                    'avg_price': harga rata-rata entry (dalam cents)
                }
            current_prices: Dict dengan current price untuk setiap token_id
        
        Returns:
            Dict dengan total_pnl, total_invested, total_value, roi
        """
        total_invested = 0.0
        total_value = 0.0
        position_details = []
        
        for pos in positions:
            quantity = float(pos.get('quantity', 0))
            avg_price = float(pos.get('avg_price', 0))
            market = pos.get('market', '')
            outcome = pos.get('outcome', 'YES')
            
            # Construct token_id
            token_id = f"{market}_{outcome}"
            
            # Get current price
            current_price = current_prices.get(token_id, avg_price)
            
            # Calculate invested amount (quantity * avg_price / 100)
            invested = quantity * avg_price / 100
            
            # Calculate current value (quantity * current_price / 100)
            value = quantity * current_price / 100
            
            # Calculate P&L
            pnl = value - invested
            
            # Calculate ROI
            roi = ProfitCalculator.calculate_roi(avg_price, current_price)
            
            total_invested += invested
            total_value += value
            
            position_details.append({
                'market': market,
                'outcome': outcome,
                'quantity': quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'invested': invested,
                'current_value': value,
                'pnl': pnl,
                'roi': roi,
                'token_id': token_id
            })
        
        total_pnl = total_value - total_invested
        overall_roi = ProfitCalculator.calculate_roi(total_invested, total_value) if total_invested > 0 else 0
        
        return {
            'total_invested': total_invested,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'overall_roi': overall_roi,
            'positions': position_details
        }
    
    @staticmethod
    def calculate_break_even_price(position: Dict) -> float:
        """
        Menghitung harga break-even untuk suatu posisi
        Break-even price adalah harga dimana P&L = 0
        """
        # Untuk Polymarket, break-even adalah avg_price itu sendiri
        # karena tidak ada fee yang diperhitungkan di sini
        return float(position.get('avg_price', 0))
    
    @staticmethod
    def calculate_position_size(usd_amount: float, price_cents: float) -> int:
        """
        Menghitung jumlah shares yang bisa dibeli dengan USD tertentu
        
        Args:
            usd_amount: Jumlah USD yang ingin diinvestasikan
            price_cents: Harga per share dalam cents (0-100)
        
        Returns:
            Jumlah shares yang bisa dibeli
        """
        if price_cents <= 0:
            return 0
        
        # Shares = (USD * 100) / price_in_cents
        shares = int((usd_amount * 100) / price_cents)
        return shares
    
    @staticmethod
    def calculate_target_price(entry_price: float, target_roi: float) -> float:
        """
        Menghitung harga target untuk mencapai ROI tertentu
        
        Args:
            entry_price: Harga entry dalam cents
            target_roi: Target ROI dalam persen (misal 20 untuk 20%)
        
        Returns:
            Harga target dalam cents
        """
        return entry_price * (1 + target_roi / 100)
    
    @staticmethod
    def calculate_stop_loss_price(entry_price: float, max_loss: float) -> float:
        """
        Menghitung harga stop-loss untuk membatasi loss maksimum
        
        Args:
            entry_price: Harga entry dalam cents
            max_loss: Maximum loss dalam persen (misal 10 untuk 10% loss)
        
        Returns:
            Harga stop-loss dalam cents
        """
        return entry_price * (1 - max_loss / 100)
    
    @staticmethod
    def calculate_potential_profit(position: Dict, target_price: float) -> float:
        """
        Menghitung potensi profit jika harga mencapai target
        
        Args:
            position: Dict posisi
            target_price: Harga target dalam cents
        
        Returns:
            Potensi profit dalam USD
        """
        quantity = float(position.get('quantity', 0))
        avg_price = float(position.get('avg_price', 0))
        
        potential_value = quantity * target_price / 100
        invested = quantity * avg_price / 100
        
        return potential_value - invested
    
    @staticmethod
    def calculate_fee(amount: float, fee_rate: float = 0.02) -> float:
        """
        Menghitung trading fee (default 2% untuk Polymarket)
        
        Args:
            amount: Jumlah transaksi dalam USD
            fee_rate: Fee rate (default 2%)
        
        Returns:
            Fee amount dalam USD
        """
        return amount * fee_rate
    
    @staticmethod
    def format_currency(amount: float, decimals: int = 2) -> str:
        """Format angka menjadi string currency"""
        return f"${amount:,.{decimals}f}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """Format angka menjadi string percentage"""
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.{decimals}f}%"
