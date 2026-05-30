// Polymarket Trading Bot - Frontend JavaScript

let socket = null;
let currentMarket = null;
let selectedOrderType = 'ONE_TAP';
let isSimulationMode = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    loadMarkets();
    setupEventListeners();
    checkMode();
    
    if (!isSimulationMode) {
        updateBalance();
    }
});

// Socket.IO Connection
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus('connected');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus('disconnected');
    });
    
    socket.on('market_update', function(data) {
        if (!isSimulationMode) {
            handleMarketUpdate(data);
        }
    });
    
    socket.on('simulation_update', function(data) {
        if (isSimulationMode) {
            handleSimulationUpdate(data);
        }
    });
}

function updateConnectionStatus(status) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    statusDot.className = 'status-dot ' + status;
    
    if (status === 'connected') {
        statusText.textContent = 'Connected';
    } else if (status === 'disconnected') {
        statusText.textContent = 'Disconnected';
    } else {
        statusText.textContent = 'Connecting...';
    }
}

// Check current mode
async function checkMode() {
    try {
        const response = await fetch('/api/mode');
        const data = await response.json();
        
        if (data.success) {
            isSimulationMode = data.simulation_mode;
            updateModeUI();
        }
    } catch (error) {
        console.error('Error checking mode:', error);
    }
}

// Update mode UI
function updateModeUI() {
    const simPanel = document.getElementById('simControlPanel');
    const tradeHistorySection = document.getElementById('tradeHistorySection');
    const btnLive = document.getElementById('btnLiveMode');
    const btnSim = document.getElementById('btnSimMode');
    
    if (isSimulationMode) {
        simPanel.style.display = 'block';
        tradeHistorySection.style.display = 'block';
        btnSim.classList.add('active');
        btnLive.classList.remove('active');
        // Hide market selector in simulation
        document.querySelector('.market-selector').style.display = 'none';
    } else {
        simPanel.style.display = 'none';
        tradeHistorySection.style.display = 'none';
        btnLive.classList.add('active');
        btnSim.classList.remove('active');
        document.querySelector('.market-selector').style.display = 'block';
    }
}

// Handle Simulation Update
function handleSimulationUpdate(data) {
    // Update market data
    const marketData = data.market_data;
    document.getElementById('yesBid').textContent = marketData.bid.toFixed(2);
    document.getElementById('yesAsk').textContent = marketData.ask.toFixed(2);
    document.getElementById('noBid').textContent = (100 - marketData.ask).toFixed(2);
    document.getElementById('noAsk').textContent = (100 - marketData.bid).toFixed(2);
    
    // Calculate spread
    const spread = marketData.spread;
    document.getElementById('yesSpread').textContent = spread.toFixed(2);
    document.getElementById('noSpread').textContent = spread.toFixed(2);
    
    // Update signal
    updateSignalDisplay(data.signal);
    
    // Update positions
    if (data.positions && data.positions.length > 0) {
        updateSimulationPositions(data.positions);
    }
    
    // Update balance/equity
    document.getElementById('balanceDisplay').textContent = formatCurrency(data.equity || data.balance);
    
    // Update sim stats
    document.getElementById('simInitialBalance').textContent = formatCurrency(data.initial_balance);
    document.getElementById('simTotalPnl').textContent = formatCurrency(data.total_pnl);
    
    const pnlEl = document.getElementById('simTotalPnl');
    if (data.total_pnl >= 0) {
        pnlEl.className = 'stat-value pnl-positive';
    } else {
        pnlEl.className = 'stat-value pnl-negative';
    }
    
    // Update orders
    if (data.orders) {
        // Could show active orders here
    }
    
    // Update trade history
    if (data.trade_history && data.trade_history.length > 0) {
        updateTradeHistory(data.trade_history);
        document.getElementById('simTradeCount').textContent = data.trade_history.length;
    }
}

// Update Simulation Positions
function updateSimulationPositions(positions) {
    const positionsList = document.getElementById('positionsList');
    
    if (positions.length > 0) {
        positionsList.innerHTML = '';
        
        positions.forEach(pos => {
            const positionItem = document.createElement('div');
            positionItem.className = 'position-item';
            
            const pnlClass = pos.pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
            const pnlSign = pos.pnl >= 0 ? '+' : '';
            const sideText = pos.side === 'buy' ? 'YES' : 'NO';
            
            positionItem.innerHTML = `
                <div class="position-info">
                    <strong>${sideText}</strong> @ ${pos.entry.toFixed(2)}¢ → ${pos.current.toFixed(2)}¢
                    <br>Size: $${pos.size}
                    ${pos.tp ? `<br>TP: ${pos.tp.toFixed(2)}¢` : ''}
                    ${pos.sl ? `<br>SL: ${pos.sl.toFixed(2)}¢` : ''}
                </div>
                <div class="position-pnl ${pnlClass}">
                    ${pnlSign}$${pos.pnl.toFixed(2)} (${pos.roi.toFixed(2)}%)
                </div>
            `;
            
            positionsList.appendChild(positionItem);
        });
    } else {
        positionsList.innerHTML = '<div class="empty-state">No open positions</div>';
    }
}

// Update Trade History
function updateTradeHistory(trades) {
    const tradeHistoryList = document.getElementById('tradeHistoryList');
    
    if (trades.length > 0) {
        tradeHistoryList.innerHTML = '';
        
        // Show last 10 trades, newest first
        trades.slice().reverse().slice(0, 10).forEach(trade => {
            const tradeItem = document.createElement('div');
            tradeItem.className = `trade-item ${trade.side}`;
            
            const pnlClass = trade.pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
            const pnlSign = trade.pnl >= 0 ? '+' : '';
            const sideText = trade.side === 'buy' ? 'BUY YES' : 'SELL NO';
            
            tradeItem.innerHTML = `
                <div class="trade-details">
                    <strong>${sideText}</strong> @ ${trade.exit.toFixed(2)}¢
                    <br>Entry: ${trade.entry.toFixed(2)}¢ | Size: $${trade.size}
                    <br><small>${trade.reason}</small>
                </div>
                <div class="trade-pnl ${pnlClass}">
                    ${pnlSign}$${trade.pnl.toFixed(2)} (${trade.roi.toFixed(2)}%)
                </div>
            `;
            
            tradeHistoryList.appendChild(tradeItem);
        });
    } else {
        tradeHistoryList.innerHTML = '<div class="empty-state">No trades yet</div>';
    }
}
// Load Markets
async function loadMarkets() {
    if (isSimulationMode) return; // Skip in simulation mode
    
    try {
        const response = await fetch('/api/markets');
        const data = await response.json();
        
        const select = document.getElementById('marketSelect');
        select.innerHTML = '';
        
        if (data.success && data.markets.length > 0) {
            data.markets.forEach(market => {
                const option = document.createElement('option');
                option.value = market.id;
                option.textContent = market.title || market.id;
                select.appendChild(option);
            });
            
            // Select first market by default
            if (data.markets.length > 0) {
                select.value = data.markets[0].id;
                currentMarket = data.markets[0];
            }
        } else {
            select.innerHTML = '<option value="">No markets available</option>';
        }
    } catch (error) {
        console.error('Error loading markets:', error);
        const select = document.getElementById('marketSelect');
        select.innerHTML = '<option value="">Error loading markets</option>';
    }
}

// Handle Market Data Update
function handleMarketUpdate(data) {
    // Update YES prices
    document.getElementById('yesBid').textContent = data.yes_bid.toFixed(2);
    document.getElementById('yesAsk').textContent = data.yes_ask.toFixed(2);
    
    // Calculate YES spread
    const yesSpread = ((data.yes_ask - data.yes_bid) / data.yes_bid * 100) || 0;
    document.getElementById('yesSpread').textContent = yesSpread.toFixed(2);
    
    // Update NO prices
    document.getElementById('noBid').textContent = data.no_bid.toFixed(2);
    document.getElementById('noAsk').textContent = data.no_ask.toFixed(2);
    
    // Calculate NO spread
    const noSpread = ((data.no_ask - data.no_bid) / data.no_bid * 100) || 0;
    document.getElementById('noSpread').textContent = noSpread.toFixed(2);
    
    // Update signal
    updateSignalDisplay(data.signal);
    
    // Update P&L
    if (data.pnl) {
        updatePnlDisplay(data.pnl);
    }
    
    // Update positions periodically
    if (Math.random() < 0.3) { // 30% chance to avoid too many updates
        updatePositions();
    }
}

// Update Signal Display
function updateSignalDisplay(signal) {
    const indicator = document.querySelector('.signal-indicator');
    const confidence = document.querySelector('.signal-confidence');
    const reason = document.getElementById('signalReason');
    
    // Set signal text
    indicator.textContent = signal.signal;
    
    // Set confidence
    confidence.textContent = `Confidence: ${signal.confidence.toFixed(0)}%`;
    
    // Set reason
    reason.textContent = signal.reasons?.[0] || 'No signal';
    
    // Update styling based on signal
    indicator.className = 'signal-indicator';
    
    switch(signal.signal.toUpperCase()) {
        case 'BUY':
            indicator.classList.add('buy');
            break;
        case 'SELL':
            indicator.classList.add('sell');
            break;
        case 'BULLISH':
            indicator.classList.add('bullish');
            break;
        case 'BEARISH':
            indicator.classList.add('bearish');
            break;
        default:
            indicator.classList.add('neutral');
    }
}

// Update P&L Display
function updatePnlDisplay(pnl) {
    document.getElementById('totalInvested').textContent = formatCurrency(pnl.total_invested);
    document.getElementById('currentValue').textContent = formatCurrency(pnl.total_value);
    
    const pnlElement = document.getElementById('totalPnl');
    const roiElement = document.getElementById('totalRoi');
    
    pnlElement.textContent = formatCurrency(pnl.total_pnl);
    roiElement.textContent = formatPercentage(pnl.overall_roi);
    
    // Update color based on positive/negative
    if (pnl.total_pnl >= 0) {
        pnlElement.className = 'pnl-value pnl-positive';
        roiElement.className = 'pnl-value pnl-positive';
    } else {
        pnlElement.className = 'pnl-value pnl-negative';
        roiElement.className = 'pnl-value pnl-negative';
    }
}

// Update Positions
async function updatePositions() {
    try {
        const response = await fetch('/api/positions');
        const data = await response.json();
        
        const positionsList = document.getElementById('positionsList');
        
        if (data.success && data.positions.length > 0) {
            positionsList.innerHTML = '';
            
            data.positions.forEach(pos => {
                const positionItem = document.createElement('div');
                positionItem.className = 'position-item';
                
                const pnlClass = pos.pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
                const pnlSign = pos.pnl >= 0 ? '+' : '';
                
                positionItem.innerHTML = `
                    <div class="position-info">
                        <strong>${pos.outcome}</strong> - ${pos.quantity} shares @ ${pos.avg_price}¢
                    </div>
                    <div class="position-pnl ${pnlClass}">
                        ${pnlSign}$${pos.pnl.toFixed(2)} (${pos.roi.toFixed(2)}%)
                    </div>
                `;
                
                positionsList.appendChild(positionItem);
            });
        } else {
            positionsList.innerHTML = '<div class="empty-state">No open positions</div>';
        }
    } catch (error) {
        console.error('Error updating positions:', error);
    }
}

// Update Balance
async function updateBalance() {
    try {
        const response = await fetch('/api/balance');
        const data = await response.json();
        
        const balanceDisplay = document.getElementById('balanceDisplay');
        
        if (data.success) {
            const balance = data.balance?.balance || 0;
            balanceDisplay.textContent = formatCurrency(balance);
        } else {
            balanceDisplay.textContent = 'Unable to load balance';
        }
    } catch (error) {
        console.error('Error updating balance:', error);
        document.getElementById('balanceDisplay').textContent = 'Error loading balance';
    }
}

// Place Order
async function placeOrder(side) {
    if (!currentMarket) {
        alert('Please select a market first');
        return;
    }
    
    const size = parseFloat(document.getElementById('orderSize').value);
    const tokenSuffix = side === 'YES' ? '_YES' : '_NO';
    const token_id = currentMarket.id + tokenSuffix;
    
    const orderData = {
        token_id: token_id,
        side: 'BUY', // Always BUY for opening position
        size: size,
        order_type: selectedOrderType
    };
    
    if (selectedOrderType === 'LIMIT') {
        orderData.price = parseFloat(document.getElementById('limitPrice').value);
    }
    
    try {
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Order placed successfully!\nOrder ID: ${result.order_id}`);
            // Refresh positions after short delay
            setTimeout(() => updatePositions(), 1000);
        } else {
            alert(`Order failed: ${result.error}`);
        }
    } catch (error) {
        console.error('Error placing order:', error);
        alert('Error placing order. Please try again.');
    }
}

// Set TP/SL
async function setTpSl() {
    if (!currentMarket) {
        alert('Please select a market first');
        return;
    }
    
    const tpPercent = parseFloat(document.getElementById('tpPercent').value);
    const slPercent = parseFloat(document.getElementById('slPercent').value);
    
    // Get current position (simplified - in production, get from positions list)
    const positions = await getPositions();
    
    if (positions.length === 0) {
        alert('No open positions to set TP/SL');
        return;
    }
    
    // Use first position for demo
    const position = positions[0];
    const entryPrice = position.avg_price;
    
    const tpSlData = {
        position_id: position.token_id,
        token_id: position.token_id,
        entry_price: entryPrice,
        tp_percent: tpPercent,
        sl_percent: slPercent
    };
    
    try {
        const response = await fetch('/api/tp-sl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tpSlData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('tpSlStatus').innerHTML = `
                <strong>TP/SL Set Successfully!</strong><br>
                Take Profit: ${result.tp_price.toFixed(2)}¢ (+${result.tp_percent}%)<br>
                Stop Loss: ${result.sl_price.toFixed(2)}¢ (-${result.sl_percent}%)
            `;
        } else {
            alert('Failed to set TP/SL');
        }
    } catch (error) {
        console.error('Error setting TP/SL:', error);
        alert('Error setting TP/SL. Please try again.');
    }
}

// Helper: Get Positions
async function getPositions() {
    try {
        const response = await fetch('/api/positions');
        const data = await response.json();
        return data.success ? data.positions : [];
    } catch (error) {
        console.error('Error getting positions:', error);
        return [];
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Mode toggle buttons
    document.getElementById('btnLiveMode').addEventListener('click', async function() {
        await setMode('live');
    });
    
    document.getElementById('btnSimMode').addEventListener('click', async function() {
        await setMode('simulation');
    });
    
    // Reset simulation button
    document.getElementById('btnResetSim').addEventListener('click', async function() {
        if (confirm('Reset simulation? This will clear all positions and trade history.')) {
            await resetSimulation();
        }
    });
    
    // Order type selection
    document.querySelectorAll('.order-type-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.order-type-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedOrderType = this.dataset.type;
            
            // Show/hide limit price input
            const limitPriceGroup = document.querySelector('.limit-price-group');
            if (selectedOrderType === 'LIMIT') {
                limitPriceGroup.style.display = 'block';
            } else {
                limitPriceGroup.style.display = 'none';
            }
        });
    });
    
    // Buy YES button
    document.getElementById('btnBuyYes').addEventListener('click', function() {
        if (isSimulationMode) {
            placeSimOrder('buy');
        } else {
            placeOrder('YES');
        }
    });
    
    // Buy NO button
    document.getElementById('btnBuyNo').addEventListener('click', function() {
        if (isSimulationMode) {
            placeSimOrder('sell');
        } else {
            placeOrder('NO');
        }
    });
    
    // Set TP/SL button
    document.getElementById('btnSetTpSl').addEventListener('click', function() {
        if (isSimulationMode) {
            alert('TP/SL is automatically managed in simulation mode based on order parameters.');
        } else {
            setTpSl();
        }
    });
    
    // Market selection change
    document.getElementById('marketSelect').addEventListener('change', function() {
        const selectedValue = this.value;
        // In production, fetch full market details
        currentMarket = { id: selectedValue, title: this.options[this.selectedIndex].text };
    });
}

// Set Mode
async function setMode(mode) {
    try {
        const response = await fetch('/api/mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mode: mode })
        });
        
        const result = await response.json();
        
        if (result.success) {
            isSimulationMode = result.simulation_mode;
            updateModeUI();
            
            if (!isSimulationMode) {
                updateBalance();
                loadMarkets();
            }
        }
    } catch (error) {
        console.error('Error setting mode:', error);
        alert('Failed to switch mode');
    }
}

// Place Simulation Order
async function placeSimOrder(side) {
    const size = parseFloat(document.getElementById('orderSize').value);
    const tpPercent = parseFloat(document.getElementById('tpPercent').value);
    const slPercent = parseFloat(document.getElementById('slPercent').value);
    
    const orderData = {
        side: side,
        order_type: selectedOrderType,
        size: size,
        tp_percent: tpPercent || null,
        sl_percent: slPercent || null
    };
    
    if (selectedOrderType === 'LIMIT') {
        orderData.price = parseFloat(document.getElementById('limitPrice').value);
    }
    
    try {
        const response = await fetch('/api/sim/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Simulation order placed:', result.order);
            // No need for alert - UI updates automatically via WebSocket
        } else {
            alert(`Order failed: ${result.error}`);
        }
    } catch (error) {
        console.error('Error placing simulation order:', error);
        alert('Error placing order. Please try again.');
    }
}

// Reset Simulation
async function resetSimulation() {
    try {
        const response = await fetch('/api/sim/reset', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clear UI
            document.getElementById('positionsList').innerHTML = '<div class="empty-state">No open positions</div>';
            document.getElementById('tradeHistoryList').innerHTML = '<div class="empty-state">No trades yet</div>';
            document.getElementById('simTradeCount').textContent = '0';
            document.getElementById('simTotalPnl').textContent = '$0.00';
            document.getElementById('balanceDisplay').textContent = '$1000.00';
        }
    } catch (error) {
        console.error('Error resetting simulation:', error);
    }
}

// Utility Functions
function formatCurrency(amount) {
    return '$' + amount.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

function formatPercentage(value) {
    const sign = value >= 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}
