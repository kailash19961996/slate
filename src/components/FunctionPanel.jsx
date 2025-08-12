import { motion, AnimatePresence } from 'framer-motion'
import { X, TrendingUp, BarChart3, Activity, DollarSign, Zap, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import CryptoChart from './CryptoChart'
import './FunctionPanel.css'

const FunctionPanel = ({ functions, onClearFunction }) => {
  const renderFunctionContent = (func) => {
    switch (func.type) {
      case 'price_chart':
        return <PriceChartWidget data={func.data} />
      case 'defi_metrics':
        return <DeFiMetricsWidget data={func.data} />
      case 'market_overview':
        return <MarketOverviewWidget data={func.data} />
      default:
        return <div>Unknown function type</div>
    }
  }

  return (
    <div className="function-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Zap className="w-5 h-5" />
          <h2>Function Calls</h2>
        </div>
        <div className="panel-status">
          <div className="status-indicator">
            <div className="status-dot active"></div>
            {functions.length} Active
          </div>
        </div>
      </div>

      <div className="functions-container">
        {functions.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Activity className="w-12 h-12" />
            </div>
            <h3>Ready for Action</h3>
            <p>Function calls will appear here when the agent processes your requests</p>
          </div>
        ) : (
          <AnimatePresence>
            {functions.map((func) => (
              <motion.div
                key={func.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="function-card"
              >
                <div className="function-header">
                  <div className="function-title">
                    {func.type === 'price_chart' && <TrendingUp className="w-4 h-4" />}
                    {func.type === 'defi_metrics' && <BarChart3 className="w-4 h-4" />}
                    {func.type === 'market_overview' && <Activity className="w-4 h-4" />}
                    <span>{getFunctionTitle(func.type)}</span>
                  </div>
                  <button
                    onClick={() => onClearFunction(func.id)}
                    className="close-btn"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="function-content">
                  {renderFunctionContent(func)}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  )
}

const getFunctionTitle = (type) => {
  switch (type) {
    case 'price_chart':
      return 'Price Chart'
    case 'defi_metrics':
      return 'DeFi Metrics'
    case 'market_overview':
      return 'Market Overview'
    default:
      return 'Function Call'
  }
}

const PriceChartWidget = ({ data }) => {
  const isPositive = data.change > 0

  return (
    <div className="price-widget">
      <div className="price-header">
        <div className="symbol">{data.symbol}</div>
        <div className={`change ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
          {Math.abs(data.change)}%
        </div>
      </div>
      
      <div className="price-main">
        <div className="price-value">
          ${data.price.toLocaleString()}
        </div>
        <div className="volume">
          Volume: {data.volume}
        </div>
      </div>

      <div className="chart-container">
        <CryptoChart symbol={data.symbol} />
      </div>

      <div className="price-stats">
        <div className="stat">
          <span className="stat-label">24h High</span>
          <span className="stat-value">${(data.price * 1.05).toLocaleString()}</span>
        </div>
        <div className="stat">
          <span className="stat-label">24h Low</span>
          <span className="stat-value">${(data.price * 0.95).toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}

const DeFiMetricsWidget = ({ data }) => {
  return (
    <div className="defi-widget">
      <div className="defi-header">
        <div className="symbol">{data.symbol}</div>
        <div className="protocol-count">12 Protocols</div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">
            <DollarSign className="w-5 h-5" />
          </div>
          <div className="metric-content">
            <div className="metric-label">Total TVL</div>
            <div className="metric-value">${data.tvl}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon gas">
            <Zap className="w-5 h-5" />
          </div>
          <div className="metric-content">
            <div className="metric-label">Gas Price</div>
            <div className="metric-value">{data.gasPrice} gwei</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon staking">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div className="metric-content">
            <div className="metric-label">Staking APR</div>
            <div className="metric-value">{data.stakingRate}%</div>
          </div>
        </div>
      </div>

      <div className="protocol-list">
        <h4>Top DeFi Protocols</h4>
        <div className="protocols">
          {['Uniswap', 'Aave', 'Compound', 'Curve'].map((protocol, index) => (
            <div key={protocol} className="protocol-item">
              <div className="protocol-name">{protocol}</div>
              <div className="protocol-tvl">${(Math.random() * 10 + 1).toFixed(1)}B</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const MarketOverviewWidget = ({ data }) => {
  return (
    <div className="market-widget">
      <div className="market-header">
        <h3>Market Overview</h3>
        <div className="market-cap">
          Total Cap: ${data.totalCap}
        </div>
      </div>

      <div className="dominance-chart">
        <h4>Market Dominance</h4>
        <div className="dominance-bars">
          <div className="dominance-item">
            <div className="dominance-label">
              <span>Bitcoin</span>
              <span>{data.dominance.BTC}%</span>
            </div>
            <div className="dominance-bar">
              <div 
                className="dominance-fill btc" 
                style={{ width: `${data.dominance.BTC}%` }}
              ></div>
            </div>
          </div>
          
          <div className="dominance-item">
            <div className="dominance-label">
              <span>Ethereum</span>
              <span>{data.dominance.ETH}%</span>
            </div>
            <div className="dominance-bar">
              <div 
                className="dominance-fill eth" 
                style={{ width: `${data.dominance.ETH}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div className="fear-greed">
        <h4>Fear & Greed Index</h4>
        <div className="fear-greed-gauge">
          <div className="gauge-value">{data.fearGreed}</div>
          <div className="gauge-label">Greed</div>
        </div>
      </div>

      <div className="market-movers">
        <h4>Top Movers (24h)</h4>
        <div className="movers-list">
          {[
            { symbol: 'SOL', change: 8.5 },
            { symbol: 'AVAX', change: -3.2 },
            { symbol: 'MATIC', change: 12.1 },
            { symbol: 'ADA', change: -1.8 }
          ].map((mover) => (
            <div key={mover.symbol} className="mover-item">
              <span className="mover-symbol">{mover.symbol}</span>
              <span className={`mover-change ${mover.change > 0 ? 'positive' : 'negative'}`}>
                {mover.change > 0 ? '+' : ''}{mover.change}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default FunctionPanel