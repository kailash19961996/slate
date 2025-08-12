"""
Crypto Agent Backend - FastAPI server with WebSocket support for real-time crypto data
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


app = FastAPI(
    title="Crypto Agent API",
    description="AI-powered crypto intelligence backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection was closed, remove it
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[datetime] = None

class CryptoPrice(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume_24h: str
    market_cap: str

class DeFiMetrics(BaseModel):
    symbol: str
    tvl: str
    gas_price: int
    staking_rate: float
    protocols: List[Dict[str, str]]

class MarketOverview(BaseModel):
    total_market_cap: str
    dominance: Dict[str, float]
    fear_greed_index: int
    top_movers: List[Dict[str, float]]

# Mock data generators
def generate_price_data(symbol: str) -> CryptoPrice:
    """Generate mock price data for a cryptocurrency"""
    base_prices = {
        "BTC": 43000,
        "ETH": 2800,
        "SOL": 85,
        "AVAX": 28,
        "MATIC": 0.95,
        "ADA": 0.48
    }
    
    base_price = base_prices.get(symbol, 100)
    variation = random.uniform(-0.1, 0.1)
    current_price = base_price * (1 + variation)
    change_24h = random.uniform(-15, 15)
    
    return CryptoPrice(
        symbol=symbol,
        price=round(current_price, 2),
        change_24h=round(change_24h, 2),
        volume_24h=f"{random.uniform(1, 50):.1f}B",
        market_cap=f"{random.uniform(10, 800):.1f}B"
    )

def generate_defi_metrics(symbol: str) -> DeFiMetrics:
    """Generate mock DeFi metrics"""
    protocols = [
        {"name": "Uniswap", "tvl": f"{random.uniform(5, 15):.1f}B"},
        {"name": "Aave", "tvl": f"{random.uniform(8, 20):.1f}B"},
        {"name": "Compound", "tvl": f"{random.uniform(3, 12):.1f}B"},
        {"name": "Curve", "tvl": f"{random.uniform(2, 8):.1f}B"},
    ]
    
    return DeFiMetrics(
        symbol=symbol,
        tvl=f"{random.uniform(40, 60):.1f}B",
        gas_price=random.randint(15, 50),
        staking_rate=round(random.uniform(3, 8), 2),
        protocols=protocols
    )

def generate_market_overview() -> MarketOverview:
    """Generate mock market overview data"""
    return MarketOverview(
        total_market_cap=f"{random.uniform(1.5, 2.2):.2f}T",
        dominance={"BTC": round(random.uniform(40, 45), 1), "ETH": round(random.uniform(17, 22), 1)},
        fear_greed_index=random.randint(20, 80),
        top_movers=[
            {"symbol": "SOL", "change": round(random.uniform(-20, 20), 1)},
            {"symbol": "AVAX", "change": round(random.uniform(-20, 20), 1)},
            {"symbol": "MATIC", "change": round(random.uniform(-20, 20), 1)},
            {"symbol": "ADA", "change": round(random.uniform(-20, 20), 1)},
        ]
    )

def generate_chart_data(symbol: str, timeframe: str = "24h") -> List[Dict]:
    """Generate mock chart data"""
    base_price = {"BTC": 43000, "ETH": 2800}.get(symbol, 100)
    points = 24 if timeframe == "24h" else 168
    
    data = []
    current_price = base_price
    
    for i in range(points):
        variation = random.uniform(-0.02, 0.02)
        current_price *= (1 + variation)
        
        timestamp = datetime.now() - timedelta(hours=points-i)
        
        data.append({
            "timestamp": timestamp.isoformat(),
            "price": round(current_price, 2),
            "volume": random.uniform(100000, 5000000)
        })
    
    return data

# AI Agent functions
async def process_crypto_query(message: str) -> Dict:
    """Process a crypto-related query and return appropriate function calls"""
    message_lower = message.lower()
    
    function_calls = []
    
    # Determine what functions to call based on the message
    if any(term in message_lower for term in ["bitcoin", "btc"]):
        price_data = generate_price_data("BTC")
        chart_data = generate_chart_data("BTC")
        function_calls.append({
            "type": "price_chart",
            "data": {
                "symbol": "BTC",
                "price": price_data.price,
                "change": price_data.change_24h,
                "volume": price_data.volume_24h,
                "chart_data": chart_data
            }
        })
    
    if any(term in message_lower for term in ["ethereum", "eth"]):
        defi_data = generate_defi_metrics("ETH")
        function_calls.append({
            "type": "defi_metrics",
            "data": {
                "symbol": "ETH",
                "tvl": defi_data.tvl,
                "gasPrice": defi_data.gas_price,
                "stakingRate": defi_data.staking_rate,
                "protocols": defi_data.protocols
            }
        })
    
    if any(term in message_lower for term in ["market", "overview", "general"]):
        market_data = generate_market_overview()
        function_calls.append({
            "type": "market_overview",
            "data": {
                "totalCap": market_data.total_market_cap,
                "dominance": market_data.dominance,
                "fearGreed": market_data.fear_greed_index,
                "topMovers": market_data.top_movers
            }
        })
    
    # Generate AI response
    if "bitcoin" in message_lower or "btc" in message_lower:
        ai_response = "I'm analyzing Bitcoin data for you. Let me pull the latest price charts and market information."
    elif "ethereum" in message_lower or "eth" in message_lower:
        ai_response = "Fetching Ethereum analytics and on-chain metrics. I'll show you the current trends and DeFi data."
    elif "market" in message_lower:
        ai_response = "Getting real-time market data across all major cryptocurrencies. I'll display the top movers and market sentiment."
    else:
        ai_response = "I'm processing your request and gathering relevant crypto data. The information will appear on the right panel."
    
    return {
        "ai_response": ai_response,
        "function_calls": function_calls
    }

# API Routes
@app.get("/")
async def root():
    return {"message": "Crypto Agent API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/crypto/{symbol}")
async def get_crypto_price(symbol: str):
    """Get current price data for a cryptocurrency"""
    try:
        price_data = generate_price_data(symbol.upper())
        return price_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

@app.get("/api/defi/{symbol}")
async def get_defi_metrics(symbol: str):
    """Get DeFi metrics for a cryptocurrency"""
    try:
        defi_data = generate_defi_metrics(symbol.upper())
        return defi_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"DeFi data for {symbol} not found")

@app.get("/api/market/overview")
async def get_market_overview():
    """Get market overview data"""
    return generate_market_overview()

@app.get("/api/chart/{symbol}")
async def get_chart_data(symbol: str, timeframe: str = "24h"):
    """Get chart data for a cryptocurrency"""
    try:
        chart_data = generate_chart_data(symbol.upper(), timeframe)
        return {"symbol": symbol.upper(), "timeframe": timeframe, "data": chart_data}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Chart data for {symbol} not found")

@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """Process a chat message and return AI response with function calls"""
    try:
        result = await process_crypto_query(message.message)
        return {
            "timestamp": datetime.now(),
            "user_message": message.message,
            "ai_response": result["ai_response"],
            "function_calls": result["function_calls"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message
            result = await process_crypto_query(message_data["message"])
            
            # Send AI response
            response = {
                "type": "ai_response",
                "data": {
                    "message": result["ai_response"],
                    "timestamp": datetime.now().isoformat()
                }
            }
            await manager.send_personal_message(json.dumps(response), websocket)
            
            # Send function calls with delay for better UX
            for i, func_call in enumerate(result["function_calls"]):
                await asyncio.sleep(1 + i * 0.5)  # Stagger function calls
                func_response = {
                    "type": "function_call",
                    "data": {
                        "id": f"{datetime.now().timestamp()}_{i}",
                        **func_call
                    }
                }
                await manager.send_personal_message(json.dumps(func_response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Background task for real-time price updates
async def broadcast_price_updates():
    """Broadcast real-time price updates to all connected clients"""
    while True:
        try:
            # Generate price updates for major cryptos
            symbols = ["BTC", "ETH", "SOL", "AVAX"]
            
            for symbol in symbols:
                price_data = generate_price_data(symbol)
                update = {
                    "type": "price_update",
                    "data": {
                        "symbol": symbol,
                        "price": price_data.price,
                        "change": price_data.change_24h,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await manager.broadcast(json.dumps(update))
                
            await asyncio.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            print(f"Error in price updates: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the server starts"""
    asyncio.create_task(broadcast_price_updates())

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )