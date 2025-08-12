import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { useEffect, useState } from 'react'

const CryptoChart = ({ symbol }) => {
  const [data, setData] = useState([])

  useEffect(() => {
    // Generate mock chart data
    const generateData = () => {
      const basePrice = symbol === 'BTC' ? 43000 : 2800
      const dataPoints = []
      
      for (let i = 0; i < 24; i++) {
        const variation = (Math.random() - 0.5) * 0.1
        const price = basePrice * (1 + variation * (i / 24))
        
        dataPoints.push({
          time: `${i}:00`,
          price: price,
          volume: Math.random() * 1000000
        })
      }
      
      setData(dataPoints)
    }

    generateData()
    
    // Update data every 5 seconds to simulate real-time
    const interval = setInterval(generateData, 5000)
    
    return () => clearInterval(interval)
  }, [symbol])

  const isPositive = data.length > 1 && data[data.length - 1].price > data[0].price

  return (
    <div className="crypto-chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <defs>
            <linearGradient id={`gradient-${symbol}`} x1="0" y1="0" x2="0" y2="1">
              <stop 
                offset="5%" 
                stopColor={isPositive ? "#10b981" : "#ef4444"} 
                stopOpacity={0.3}
              />
              <stop 
                offset="95%" 
                stopColor={isPositive ? "#10b981" : "#ef4444"} 
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          
          <XAxis 
            dataKey="time" 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: 'rgba(255, 255, 255, 0.5)' }}
            interval="preserveStartEnd"
          />
          
          <YAxis 
            domain={['dataMin - 100', 'dataMax + 100']}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: 'rgba(255, 255, 255, 0.5)' }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
          />
          
          <Area
            type="monotone"
            dataKey="price"
            stroke={isPositive ? "#10b981" : "#ef4444"}
            strokeWidth={2}
            fill={`url(#gradient-${symbol})`}
            dot={false}
            activeDot={{ 
              r: 4, 
              fill: isPositive ? "#10b981" : "#ef4444",
              strokeWidth: 0
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default CryptoChart