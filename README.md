# Crypto Agent - AI-Powered Crypto Intelligence

A modern, sleek crypto information agent with a React frontend and Python backend. Features real-time market data, AI-powered analysis, and dynamic function calling for comprehensive crypto insights.

## Features

- **Ultra-Modern UI**: Notion-inspired design with black and white theme
- **Split-Screen Interface**: Light chatbot on left, dark function panel on right
- **Real-Time Data**: WebSocket connection for live crypto updates
- **AI Agent**: Intelligent crypto analysis with function calling
- **Interactive Charts**: Dynamic price charts and market visualizations
- **Responsive Design**: Modern shadows, rounded corners, hover effects

## Technology Stack

### Frontend
- React 18 with Vite
- Framer Motion for animations
- Recharts for data visualization
- Lucide React for icons
- WebSocket for real-time updates

### Backend
- FastAPI for high-performance API
- WebSocket support for real-time communication
- Async/await for concurrent processing
- Mock crypto data generators

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crypto-agent
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd .. # Back to project root
   npm install
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   python main.py
   ```
   The backend will be available at `http://localhost:8000`

2. **Start the frontend development server**
   ```bash
   # In a new terminal, from project root
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000`

## Usage

1. **Initial Screen**: Start by typing any crypto-related query in the input bar
2. **Screen Split**: The interface automatically splits into chat (left) and function panel (right)
3. **Ask Questions**: Try queries like:
   - "Show me Bitcoin price trends"
   - "Analyze Ethereum DeFi metrics"
   - "Market overview and top movers"
4. **Real-Time Updates**: Watch as the agent calls functions and displays live data

## API Endpoints

### REST API
- `GET /`: Health check
- `GET /api/crypto/{symbol}`: Get crypto price data
- `GET /api/defi/{symbol}`: Get DeFi metrics
- `GET /api/market/overview`: Market overview
- `GET /api/chart/{symbol}`: Chart data
- `POST /api/chat`: Process chat messages

### WebSocket
- `ws://localhost:8000/ws`: Real-time communication

## Architecture

### Frontend Structure
```
src/
├── components/
│   ├── InitialScreen.jsx      # Landing page with input
│   ├── ChatInterface.jsx      # Left side chat
│   ├── FunctionPanel.jsx      # Right side functions
│   ├── CryptoChart.jsx        # Chart component
│   └── *.css                  # Component styles
├── hooks/
│   └── useWebSocket.js        # WebSocket management
├── App.jsx                    # Main application
└── index.css                  # Global styles
```

### Backend Structure
```
backend/
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
└── README.md                  # Backend documentation
```

## Key Features

### AI Function Calling
The agent intelligently analyzes user queries and triggers appropriate function calls:
- **Price Charts**: Real-time crypto price data with interactive charts
- **DeFi Metrics**: Total Value Locked, gas prices, staking rates
- **Market Overview**: Market cap, dominance, fear & greed index

### Real-Time Updates
- WebSocket connection for instant communication
- Live price updates every 30 seconds
- Automatic reconnection with exponential backoff
- Connection status indicators

### Modern UI/UX
- Smooth animations with Framer Motion
- Glass morphism effects
- Responsive design for all devices
- Accessibility-focused components
- Dark/light theme contrast

## Development

### Frontend Development
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Backend Development
```bash
python main.py       # Start with auto-reload
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Customization

### Adding New Function Types
1. Define the function in `backend/main.py`
2. Add the corresponding component in `FunctionPanel.jsx`
3. Update the mock data generators as needed

### Styling
- Global styles in `src/index.css`
- Component-specific styles in respective `.css` files
- CSS variables for consistent theming

## Deployment

### Frontend (Vercel/Netlify)
1. Build the project: `npm run build`
2. Deploy the `dist` folder

### Backend (Railway/Heroku)
1. Ensure `requirements.txt` is up to date
2. Create a `Procfile` with: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Deploy to your platform of choice

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on the repository or contact the development team.

---

**Note**: This application uses mock data for demonstration. For production use, integrate with real crypto APIs like CoinGecko, CoinMarketCap, or blockchain node providers.