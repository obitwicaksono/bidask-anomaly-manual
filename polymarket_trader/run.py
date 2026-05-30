"""
Flask Web Application untuk Polymarket Trading Bot
Supports both LIVE trading and SIMULATION mode
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import config
from app.clob_client import ClobClient
from app.trading_engine import TradingEngine
from app.signal_generator import SignalGenerator
from app.calculator import ProfitCalculator
from app.simulator import SimulationEngine, simulator as sim_engine

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'polymarket-trading-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize components for LIVE mode
clob_client = ClobClient()
trading_engine = TradingEngine(clob_client)
signal_generator = SignalGenerator()
calculator = ProfitCalculator()

# Global state
markets_cache = []
price_cache = {}
running = True
simulation_mode = False  # Toggle between LIVE and SIMULATION


def fetch_markets():
    """Fetch crypto UP/DOWN 5M markets periodically (LIVE mode only)"""
    global markets_cache, running
    
    while running:
        if not simulation_mode:
            try:
                # Get all markets
                result = clob_client.get_markets()
                
                if isinstance(result, list):
                    # Filter for crypto UP/DOWN 5M markets
                    filtered = []
                    for market in result:
                        title = market.get('title', '').upper()
                        if any(keyword in title for keyword in config.MARKET_KEYWORDS):
                            if '5M' in title or '5 MIN' in title or '5MENIT' in title:
                                filtered.append(market)
                    
                    markets_cache = filtered[:20]  # Limit to 20 markets
            except Exception as e:
                print(f"Error fetching markets: {e}")
        
        time.sleep(30)  # Update every 30 seconds


def broadcast_live_market_data():
    """Broadcast real-time market data via WebSocket (LIVE mode)"""
    global running
    
    while running:
        if not simulation_mode:
            try:
                if markets_cache:
                    # Get first market for demo (in production, allow user selection)
                    market = markets_cache[0]
                    market_id = market.get('id', '')
                    
                    if market_id:
                        # Get YES and NO token prices
                        yes_token = f"{market_id}_YES"
                        no_token = f"{market_id}_NO"
                        
                        # Get orderbook for both tokens
                        yes_book = clob_client.get_market_orders(yes_token)
                        no_book = clob_client.get_market_orders(no_token)
                        
                        # Extract best bid/ask
                        data = {
                            'market': market,
                            'yes_bid': float(yes_book.get('bids', [{}])[0].get('price', 0)),
                            'yes_ask': float(yes_book.get('asks', [{}])[0].get('price', 0)),
                            'no_bid': float(no_book.get('bids', [{}])[0].get('price', 0)),
                            'no_ask': float(no_book.get('asks', [{}])[0].get('price', 0)),
                        }
                        
                        # Generate signals
                        orderbook_analysis = signal_generator.analyze_orderbook(yes_book)
                        price_anomaly = signal_generator.detect_price_anomaly(
                            yes_token, 
                            data['yes_bid']
                        )
                        trade_signal = signal_generator.generate_trade_signal(
                            orderbook_analysis,
                            price_anomaly
                        )
                        
                        data['signal'] = trade_signal
                        
                        # Get user positions and calculate P&L
                        positions = clob_client.get_positions()
                        current_prices = {
                            yes_token: data['yes_bid'],
                            no_token: data['no_bid']
                        }
                        pnl_data = calculator.calculate_pnl(positions, current_prices)
                        data['pnl'] = pnl_data
                        
                        # Broadcast to all clients
                        socketio.emit('market_update', data)
            except Exception as e:
                print(f"Error broadcasting data: {e}")
        
        time.sleep(2)  # Update every 2 seconds


def broadcast_simulation_data():
    """Broadcast simulated market data via WebSocket (SIMULATION mode)"""
    global running
    
    while running:
        if simulation_mode:
            try:
                # Run simulation step
                sim_data = sim_engine.run_simulation_step()
                
                # Add simulated signal based on anomaly detection
                market_data = sim_data['market_data']
                signal = "HOLD"
                signal_strength = 0
                
                if market_data['anomaly']:
                    spread = market_data['spread']
                    if spread > 3.0:  # Wide spread indicates opportunity
                        signal = "BUY" if market_data['last'] < 50 else "SELL"
                        signal_strength = min(100, int((spread - 2) * 20))
                
                sim_data['signal'] = {
                    'action': signal,
                    'strength': signal_strength,
                    'reason': 'Anomaly detected' if market_data['anomaly'] else 'Normal market'
                }
                
                # Broadcast to all clients
                socketio.emit('simulation_update', sim_data)
                
            except Exception as e:
                print(f"Error broadcasting simulation data: {e}")
        
        time.sleep(1)  # Update every 1 second in simulation


# Background threads - start immediately when module loads
def start_background_tasks():
    """Start background threads for real-time updates"""
    thread1 = threading.Thread(target=fetch_markets, daemon=True)
    thread1.start()
    
    thread2 = threading.Thread(target=broadcast_live_market_data, daemon=True)
    thread2.start()
    
    thread3 = threading.Thread(target=broadcast_simulation_data, daemon=True)
    thread3.start()

# Start background tasks
start_background_tasks()


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', simulation_mode=simulation_mode)


@app.route('/api/markets')
def get_markets():
    """API endpoint to get available markets"""
    return jsonify({
        'success': True,
        'markets': markets_cache
    })


@app.route('/api/mode', methods=['GET'])
def get_mode():
    """Get current trading mode (LIVE or SIMULATION)"""
    return jsonify({
        'success': True,
        'simulation_mode': simulation_mode
    })


@app.route('/api/mode', methods=['POST'])
def set_mode():
    """Set trading mode (LIVE or SIMULATION)"""
    global simulation_mode
    data = request.json
    simulation_mode = data.get('mode', False) == 'simulation'
    
    # Reset simulator if switching to simulation mode
    if simulation_mode:
        sim_engine.reset()
        sim_engine.start()
    else:
        sim_engine.stop()
    
    return jsonify({
        'success': True,
        'simulation_mode': simulation_mode
    })


@app.route('/api/sim/order', methods=['POST'])
def place_sim_order():
    """Place a simulated order"""
    data = request.json
    
    side = data.get('side', 'buy')
    order_type = data.get('order_type', 'market')
    price = float(data.get('price', 50))
    size = float(data.get('size', 10))
    tp_percent = data.get('tp_percent')
    sl_percent = data.get('sl_percent')
    
    if tp_percent:
        tp_percent = float(tp_percent)
    if sl_percent:
        sl_percent = float(sl_percent)
    
    order = sim_engine.place_order(
        side=side,
        order_type=order_type,
        price=price,
        size=size,
        tp_percent=tp_percent,
        sl_percent=sl_percent
    )
    
    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'side': order.side.value,
            'type': order.order_type.value,
            'price': order.price,
            'size': order.size,
            'status': order.status,
            'fill_price': order.fill_price
        }
    })


@app.route('/api/sim/reset', methods=['POST'])
def reset_simulation():
    """Reset simulation"""
    sim_engine.reset()
    return jsonify({
        'success': True,
        'message': 'Simulation reset'
    })


@app.route('/api/sim/status')
def get_sim_status():
    """Get simulation status"""
    status = sim_engine.get_status()
    return jsonify(status)


@app.route('/api/order', methods=['POST'])
def place_order():
    """Place a new order"""
    data = request.json
    
    token_id = data.get('token_id')
    side = data.get('side')  # BUY or SELL
    size = float(data.get('size', config.DEFAULT_POSITION_SIZE))
    order_type = data.get('order_type', 'MARKET')  # MARKET, LIMIT, ONE_TAP
    price = data.get('price')
    
    if not token_id or not side:
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    if order_type == 'MARKET':
        result = trading_engine.execute_market_order(token_id, side, size)
    elif order_type == 'LIMIT':
        if not price:
            return jsonify({'success': False, 'error': 'Price required for limit order'})
        result = trading_engine.execute_limit_order(token_id, side, size, float(price))
    elif order_type == 'ONE_TAP':
        result = trading_engine.execute_one_tap_order(token_id, side, size)
    else:
        return jsonify({'success': False, 'error': 'Invalid order type'})
    
    return jsonify(result)


@app.route('/api/tp-sl', methods=['POST'])
def set_tp_sl():
    """Set take profit and stop loss"""
    data = request.json
    
    position_id = data.get('position_id')
    token_id = data.get('token_id')
    entry_price = float(data.get('entry_price', 50))
    tp_percent = float(data.get('tp_percent', config.DEFAULT_TAKE_PROFIT))
    sl_percent = float(data.get('sl_percent', config.DEFAULT_STOP_LOSS))
    
    # Calculate TP and SL prices
    tp_price = trading_engine.calculate_tp_price(entry_price, tp_percent)
    sl_price = trading_engine.calculate_sl_price(entry_price, sl_percent)
    
    # Set TP and SL
    tp_set = trading_engine.set_take_profit(position_id, token_id, tp_price)
    sl_set = trading_engine.set_stop_loss(position_id, token_id, sl_price)
    
    return jsonify({
        'success': tp_set and sl_set,
        'tp_price': tp_price,
        'sl_price': sl_price,
        'tp_percent': tp_percent,
        'sl_percent': sl_percent
    })


@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    positions = clob_client.get_positions()
    return jsonify({
        'success': True,
        'positions': positions
    })


@app.route('/api/balance')
def get_balance():
    """Get account balance"""
    balance = clob_client.get_balance()
    return jsonify({
        'success': True,
        'balance': balance
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to Polymarket Trading Bot'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    finally:
        running = False
