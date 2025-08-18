// src/widgets/JustLendWidget.jsx
import './JustLendWidget.css'

export default function JustLendWidget({ data }) {
  if (!data) return <div className="jl-card">No JustLend data yet.</div>

  const { view, payload } = data

  if (view === 'list') {
    const rows = payload?.markets || []
    console.log('🎨 [JL Widget] Rendering markets list:', { payload, rows })
    
    if (rows.length === 0) {
      return (
        <div className="jl-card">
          <div className="jl-header">
            <h3>JustLend Markets</h3>
            <span className="jl-sub">{payload?.network?.toUpperCase() || 'UNKNOWN'}</span>
          </div>
          <div className="jl-loading">No markets available or still loading...</div>
        </div>
      )
    }
    
    return (
      <div className="jl-card">
        <div className="jl-header">
          <h3>JustLend Markets</h3>
          <span className="jl-sub">{payload?.network?.toUpperCase() || 'UNKNOWN'}</span>
        </div>
        <div className="jl-table">
          <div className="jl-row jl-head">
            <div>Symbol</div><div>Collateral %</div><div>Supply APY</div><div>Borrow APY</div>
          </div>
          {rows.map((m, idx) => (
            <div className="jl-row" key={m.address || `market-${idx}`}>
              <div>{m.symbol || 'Unknown'}</div>
              <div>{(m.collateral_factor_pct || 0).toFixed(2)}%</div>
              <div>{m.supply_apy_pct_approx || 0}%</div>
              <div>{m.borrow_apy_pct_approx || 0}%</div>
            </div>
          ))}
        </div>
        <div className="jl-footer">
          <small>Count: {payload?.count || rows.length} markets</small>
        </div>
      </div>
    )
  }

  if (view === 'detail') {
    const m = payload?.market
    if (!m) return <div className="jl-card">Market not found.</div>
    return (
      <div className="jl-card">
        <div className="jl-header">
          <h3>{m.symbol}</h3>
          <span className="jl-sub">{payload?.network?.toUpperCase()}</span>
        </div>
        <div className="jl-grid">
          <div className="jl-item"><span>Collateral</span><b>{m.collateral_factor_pct.toFixed(2)}%</b></div>
          <div className="jl-item"><span>Supply APY</span><b>{m.supply_apy_pct_approx}%</b></div>
          <div className="jl-item"><span>Borrow APY</span><b>{m.borrow_apy_pct_approx}%</b></div>
          <div className="jl-item"><span>Exchange Rate</span><b>{m.exchange_rate_mantissa}</b></div>
          <div className="jl-item"><span>Total Borrows</span><b>{m.total_borrows_mantissa}</b></div>
        </div>
        <div className="jl-foot mono">{m.address}</div>
      </div>
    )
  }

  if (view === 'user') {
    const p = payload
    const pos = p?.positions || []
    return (
      <div className="jl-card">
        <div className="jl-header">
          <h3>Your JustLend Position</h3>
          <span className="jl-sub">{p?.network?.toUpperCase()}</span>
        </div>
        <div className="jl-table">
          <div className="jl-row jl-head">
            <div>Symbol</div><div>TokenBal (mant.)</div><div>BorrowBal (mant.)</div><div>ExchRate</div>
          </div>
          {pos.map((x) => (
            <div className="jl-row" key={x.jtoken}>
              <div>{x.symbol}</div>
              <div>{x.token_balance_mantissa}</div>
              <div>{x.borrow_balance_mantissa}</div>
              <div>{x.exchange_rate_mantissa}</div>
            </div>
          ))}
        </div>
        <div className="jl-grid mt">
          <div className="jl-item"><span>Liquidity</span><b>{p.liquidity_mantissa}</b></div>
          <div className="jl-item"><span>Shortfall</span><b className={p.shortfall_mantissa > 0 ? 'bad' : ''}>{p.shortfall_mantissa}</b></div>
        </div>
        <div className="jl-foot mono">{p?.address}</div>
      </div>
    )
  }

  return <div className="jl-card">Unsupported view.</div>
}
