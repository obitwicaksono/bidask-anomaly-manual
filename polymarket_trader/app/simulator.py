import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"

class Side(Enum):
    BUY = "buy"   # YES
    SELL = "sell" # NO

@dataclass
class SimulatedOrder:
    id: str
    market_id: str
    side: Side
    order_type: OrderType
    price: float  # in cents
    size: float   # in USD
    status: str = "open"  # open, filled, cancelled
    timestamp: datetime = field(default_factory=datetime.now)
    fill_price: Optional[float] = None
    filled_at: Optional[datetime] = None

@dataclass
class Position:
    market_id: str
    side: Side
    entry_price: float
    size: float
    current_price: float
    pnl: float = 0.0
    roi: float = 0.0
    tp_price: Optional[float] = None
    sl_price: Optional[float] = None

@dataclass
class MarketData:
    market_id: str
    bid: float
    ask: float
    last_price: float
    volume: float
    timestamp: datetime

class MarketSimulator:
    """Simulates market movements for Polymarket 5min crypto UP/DOWN"""
    
    def __init__(self, initial_price: float = 50.0, volatility: float = 2.0):
        self.initial_price = initial_price
        self.current_price = initial_price
        self.volatility = volatility
        self.bid_ask_spread = 1.0  # cents
        self.anomaly_active = False
        self.anomaly_duration = 0
        
    def generate_tick(self) -> MarketData:
        """Generate next market tick with random walk + anomaly logic"""
        
        # Random walk
        change = random.gauss(0, self.volatility / 10)
        
        # Anomaly injection (10% chance to start, lasts 5-15 ticks)
        if not self.anomaly_active and random.random() < 0.05:
            self.anomaly_active = True
            self.anomaly_duration = random.randint(5, 15)
            self.anomaly_direction = random.choice([-1, 1])
        
        if self.anomaly_active:
            change += self.anomaly_direction * (self.volatility / 2)
            self.anomaly_duration -= 1
            if self.anomaly_duration <= 0:
                self.anomaly_active = False
        
        # Update price (clamp between 1 and 99 cents)
        self.current_price = max(1.0, min(99.0, self.current_price + change))
        
        # Generate bid/ask around mid price
        spread = self.bid_ask_spread
        if self.anomaly_active:
            spread *= 2.5  # Wider spread during anomaly
            
        mid = self.current_price
        bid = max(0.5, mid - spread/2)
        ask = min(99.5, mid + spread/2)
        
        return MarketData(
            market_id="sim_crypto_5m",
            bid=round(bid, 2),
            ask=round(ask, 2),
            last_price=round(mid, 2),
            volume=random.uniform(1000, 50000),
            timestamp=datetime.now()
        )

class SimulationEngine:
    """Main simulation controller"""
    
    def __init__(self, initial_balance: float = 1000.0):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.market = MarketSimulator()
        self.orders: List[SimulatedOrder] = []
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.is_running = False
        self.speed_multiplier = 1.0  # 1x = real-time simulation speed
        
    def start(self):
        self.is_running = True
        
    def stop(self):
        self.is_running = False
        
    def reset(self):
        self.balance = self.initial_balance
        self.orders = []
        self.positions = {}
        self.trade_history = []
        self.market = MarketSimulator()
        
    def place_order(self, side: str, order_type: str, price: float, size: float, 
                   tp_percent: Optional[float] = None, sl_percent: Optional[float] = None) -> SimulatedOrder:
        """Place a simulated order"""
        order = SimulatedOrder(
            id=f"sim_{len(self.orders)}_{int(time.time())}",
            market_id="sim_crypto_5m",
            side=Side.BUY if side == "buy" else Side.SELL,
            order_type=OrderType.MARKET if order_type == "market" else OrderType.LIMIT,
            price=price,
            size=size
        )
        self.orders.append(order)
        
        # Try immediate fill for market orders
        if order.order_type == OrderType.MARKET:
            self._try_fill_order(order)
            
        # Setup TP/SL if specified
        if order.status == "filled" and order.market_id in self.positions:
            pos = self.positions[order.market_id]
            if tp_percent:
                if side == "buy":
                    pos.tp_price = min(99.0, pos.entry_price * (1 + tp_percent/100))
                else:
                    pos.tp_price = max(1.0, pos.entry_price * (1 - tp_percent/100))
            if sl_percent:
                if side == "buy":
                    pos.sl_price = max(1.0, pos.entry_price * (1 - sl_percent/100))
                else:
                    pos.sl_price = min(99.0, pos.entry_price * (1 + sl_percent/100))
                    
        return order
        
    def _try_fill_order(self, order: SimulatedOrder):
        """Attempt to fill an order based on current market data"""
        market_data = self.market.generate_tick()
        
        can_fill = False
        fill_price = 0.0
        
        if order.order_type == OrderType.MARKET:
            can_fill = True
            fill_price = market_data.ask if order.side == Side.BUY else market_data.bid
        elif order.order_type == OrderType.LIMIT:
            if order.side == Side.BUY and market_data.ask <= order.price:
                can_fill = True
                fill_price = order.price
            elif order.side == Side.SELL and market_data.bid >= order.price:
                can_fill = True
                fill_price = order.price
                
        if can_fill:
            # Check balance
            cost = (fill_price / 100.0) * order.size
            if order.side == Side.SELL:
                cost = (1 - fill_price/100.0) * order.size
                
            if cost <= self.balance:
                order.status = "filled"
                order.fill_price = fill_price
                order.filled_at = datetime.now()
                self.balance -= cost
                
                # Create/update position
                self._update_position(order, fill_price)
                
    def _update_position(self, order: SimulatedOrder, fill_price: float):
        """Update or create position"""
        market_id = order.market_id
        
        if market_id in self.positions:
            pos = self.positions[market_id]
            # Average in if same side, close if opposite (simplified: just replace for now)
            pos.entry_price = fill_price
            pos.size = order.size
            pos.side = order.side
        else:
            self.positions[market_id] = Position(
                market_id=market_id,
                side=order.side,
                entry_price=fill_price,
                size=order.size,
                current_price=fill_price
            )
            
    def run_simulation_step(self) -> Dict:
        """Run one simulation step (tick)"""
        if not self.is_running:
            return self.get_status()
            
        market_data = self.market.generate_tick()
        
        # Update existing orders
        for order in self.orders:
            if order.status == "open":
                self._try_fill_order(order)
                
        # Update positions P&L
        for market_id, pos in self.positions.items():
            pos.current_price = market_data.last_price
            
            # Calculate P&L
            if pos.side == Side.BUY:
                pnl_pct = (pos.current_price - pos.entry_price) / pos.entry_price
            else:
                pnl_pct = (pos.entry_price - pos.current_price) / pos.entry_price
                
            pos.pnl = pos.size * pnl_pct
            pos.roi = pnl_pct * 100
            
            # Check TP/SL
            self._check_tp_sl(pos, market_data)
            
        return {
            "balance": round(self.balance, 2),
            "equity": round(self.balance + sum(p.pnl for p in self.positions.values()), 2),
            "market_data": {
                "bid": market_data.bid,
                "ask": market_data.ask,
                "last": market_data.last_price,
                "spread": round(market_data.ask - market_data.bid, 2),
                "anomaly": self.market.anomaly_active
            },
            "positions": [
                {
                    "market_id": p.market_id,
                    "side": p.side.value,
                    "entry": p.entry_price,
                    "current": p.current_price,
                    "size": p.size,
                    "pnl": round(p.pnl, 2),
                    "roi": round(p.roi, 2),
                    "tp": p.tp_price,
                    "sl": p.sl_price
                }
                for p in self.positions.values()
            ],
            "orders": [
                {
                    "id": o.id,
                    "side": o.side.value,
                    "type": o.order_type.value,
                    "price": o.price,
                    "size": o.size,
                    "status": o.status,
                    "fill_price": o.fill_price
                }
                for o in self.orders[-10:]  # Last 10 orders
            ]
        }
        
    def _check_tp_sl(self, pos: Position, market_data: MarketData):
        """Check and execute TP/SL"""
        should_close = False
        close_reason = ""
        close_price = 0.0
        
        if pos.tp_price and pos.current_price >= pos.tp_price and pos.side == Side.BUY:
            should_close = True
            close_reason = "TP Hit"
            close_price = pos.tp_price
        elif pos.tp_price and pos.current_price <= pos.tp_price and pos.side == Side.SELL:
            should_close = True
            close_reason = "TP Hit"
            close_price = pos.tp_price
        elif pos.sl_price and pos.current_price <= pos.sl_price and pos.side == Side.BUY:
            should_close = True
            close_reason = "SL Hit"
            close_price = pos.sl_price
        elif pos.sl_price and pos.current_price >= pos.sl_price and pos.side == Side.SELL:
            should_close = True
            close_reason = "SL Hit"
            close_price = pos.sl_price
            
        if should_close:
            # Close position
            payout = 0.0
            if pos.side == Side.BUY:
                payout = (close_price / 100.0) * pos.size
            else:
                payout = (1 - close_price/100.0) * pos.size
                
            self.balance += payout
            
            # Record trade
            self.trade_history.append({
                "timestamp": datetime.now(),
                "side": pos.side.value,
                "entry": pos.entry_price,
                "exit": close_price,
                "size": pos.size,
                "pnl": pos.pnl,
                "roi": pos.roi,
                "reason": close_reason
            })
            
            # Remove position
            del self.positions[pos.market_id]
            
    def get_status(self) -> Dict:
        """Get current simulation status"""
        market_data = self.market.generate_tick()
        return {
            "balance": round(self.balance, 2),
            "equity": round(self.balance + sum(p.pnl for p in self.positions.values()), 2),
            "initial_balance": self.initial_balance,
            "total_pnl": round(self.balance - self.initial_balance, 2),
            "market_data": {
                "bid": market_data.bid,
                "ask": market_data.ask,
                "last": market_data.last_price,
                "spread": round(market_data.ask - market_data.bid, 2),
                "anomaly": self.market.anomaly_active
            },
            "positions": [
                {
                    "market_id": p.market_id,
                    "side": p.side.value,
                    "entry": p.entry_price,
                    "current": p.current_price,
                    "size": p.size,
                    "pnl": round(p.pnl, 2),
                    "roi": round(p.roi, 2)
                }
                for p in self.positions.values()
            ],
            "trade_history": self.trade_history[-20:],  # Last 20 trades
            "is_running": self.is_running
        }

# Global simulator instance
simulator = SimulationEngine(initial_balance=1000.0)
