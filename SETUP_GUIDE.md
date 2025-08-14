# SLATE - AI-Powered TRON Blockchain Assistant

## Overview

SLATE is an organized, production-ready AI agent that orchestrates blockchain operations using LangGraph and provides a modern React frontend. The system is designed for wallet management, DeFi operations, and cryptocurrency analysis on the TRON network.

## Project Structure

```
SLATE/slate/
├── backend/                 # Python backend with LangGraph
│   ├── main.py             # Main orchestrator agent
│   ├── util.py             # Utility functions
│   ├── prompt.py           # All agent prompts
│   ├── tools.py            # LangGraph tools
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
├── src/                    # React frontend
│   ├── pages/              # Page components
│   │   ├── InitialPage.jsx # Landing page
│   │   └── ChatPage.jsx    # Main chat interface
│   ├── components/         # Reusable components
│   │   ├── ChatInterface.jsx
│   │   └── FunctionPanel.jsx
│   └── hooks/              # Custom React hooks
│       └── useWebSocket.js
└── TEST/                   # Reference implementations
    ├── wallet_connection.jsx
    ├── justlend.py
    └── phase*.py
```

## Features

### Backend (LangGraph Agent)
- **Agent Orchestration**: Main agent that handles all user interactions
- **Wallet Management**: Secure wallet connection and balance checking
- **DeFi Integration**: Analysis of TRON DeFi opportunities
- **Market Analysis**: Real-time crypto price and market data
- **Tool System**: Modular tools for different blockchain operations
- **Memory Management**: Persistent conversation memory
- **WebSocket Support**: Real-time communication with frontend

### Frontend (React)
- **Two-Page Structure**: Initial landing page + main chat interface
- **Dynamic Function Panel**: Renders different widgets based on agent responses
- **Wallet Integration**: Visual wallet connection and balance display
- **Real-time Communication**: WebSocket integration with backend
- **Modern UI**: Glass morphism design with smooth animations
- **Responsive Design**: Mobile-friendly interface

### Key Workflows

#### Wallet Connection Workflow
1. User asks to connect wallet
2. Agent requests wallet address through chat
3. Frontend shows pending input state
4. User provides TRON address
5. Agent validates and connects wallet
6. Function panel displays wallet info and balance
7. Agent provides personalized recommendations

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd SLATE/slate/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # OPENAI_API_KEY=your_openai_api_key_here
   # OPENAI_MODEL=gpt-4o-mini
   ```

5. **Run the backend:**
   ```bash
   python main.py
   ```
   Backend will start on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd SLATE/slate
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```
   Frontend will start on `http://localhost:5173`

## Usage

### Basic Usage
1. Open `http://localhost:5173` in your browser
2. Choose a quick action or type a message
3. The AI agent will process your request and display results

### Wallet Connection Example
1. Click "Connect Wallet" or type "I want to connect my wallet"
2. Agent will ask for your TRON wallet address
3. Provide a valid TRON address (starts with 'T', 34 characters)
4. Agent will connect and show wallet balance and token holdings
5. Function panel will display wallet information and available actions

### Market Analysis Example
1. Type "Show me TRX price and market overview"
2. Agent will fetch real-time data and display charts
3. Function panel will show price charts, market metrics, and trends

## API Endpoints

### Backend API
- `GET /` - Health check
- `POST /api/chat` - Process chat messages
- `POST /api/wallet/connect` - Handle wallet connections
- `WebSocket /ws/{session_id}` - Real-time communication

### WebSocket Messages
- `chat` - Send chat message to agent
- `wallet_address` - Provide wallet address for connection
- `ai_response` - Receive agent responses
- `function_call` - Receive function call data for frontend rendering

## Development Notes

### Adding New Tools
1. Create tool function in `tools.py`
2. Add to `get_all_tools()` function
3. Update prompts in `prompt.py` if needed
4. Add frontend widget in `FunctionPanel.jsx` if required

### Adding New Frontend Widgets
1. Create widget component in `FunctionPanel.jsx`
2. Add to `renderFunctionContent()` switch statement
3. Update `getFunctionTitle()` for proper titles
4. Add CSS styles to `FunctionPanel.css`

### Environment Variables
- `OPENAI_API_KEY` - Required for LLM functionality
- `OPENAI_MODEL` - Model to use (default: gpt-4o-mini)
- `TRON_RPC_URL` - TRON network RPC endpoint
- `CORS_ORIGINS` - Frontend URLs for CORS

## Security Considerations

- **Never request private keys** - Only use public wallet addresses
- **Input validation** - All user inputs are validated and sanitized
- **Rate limiting** - API endpoints have rate limiting protection
- **CORS configuration** - Properly configured for frontend origins
- **Environment variables** - Sensitive data stored in environment variables

## Testing

### Backend Testing
```bash
cd backend
pytest tests/  # When tests are added
```

### Frontend Testing
```bash
npm run test  # When tests are added
```

### Manual Testing
1. Test wallet connection flow
2. Test various chat interactions
3. Test function panel widgets
4. Test WebSocket connectivity
5. Test error handling

## Deployment

### Backend Deployment
- Use Gunicorn or Uvicorn for production
- Configure environment variables
- Set up proper logging and monitoring
- Use reverse proxy (nginx) for production

### Frontend Deployment
- Build production bundle: `npm run build`
- Deploy to CDN or static hosting
- Configure API endpoints for production

## Troubleshooting

### Common Issues
1. **WebSocket connection fails**: Check backend is running on correct port
2. **OpenAI API errors**: Verify API key is set correctly
3. **Wallet validation fails**: Ensure proper TRON address format
4. **Function panel not updating**: Check WebSocket message handling

### Debug Mode
- Set `DEBUG=true` in backend environment
- Check browser console for frontend errors
- Use WebSocket debugging tools for message inspection

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation for new features
4. Use consistent naming conventions
5. Follow React and Python best practices

## License

This project is for educational and development purposes. Ensure compliance with relevant blockchain and financial regulations in your jurisdiction.
