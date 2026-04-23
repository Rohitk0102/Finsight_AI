from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import json
import asyncio
from datetime import datetime

from app.finsight.schemas.chat_schemas import ChatRequest, ChatResponse, MarketData
from app.finsight.services.session_service import session_service
from app.finsight.services.market_service import market_service
from app.finsight.services.intent_service import intent_service
from app.finsight.services.llm_service import llm_service
from app.finsight.utils.ticker_extractor import extract_tickers
from app.finsight.utils.prompt_builder import build_prompt

router = APIRouter()

SYSTEM_PROMPT = """You are Finsight AI, a highly intelligent and conversational financial assistant, similar in personality to Gemini.
Today's date is {date}.

Guidelines:
1. Tone: Friendly, professional, and helpful. Speak naturally.
2. Formatting: Use standard Markdown for clear structure. Bold key numbers and stock symbols. Use bullet points or numbered lists for complex data.
3. Market Data: Naturally integrate the provided Market Data into your answers. If a ticker is mentioned, provide its current price and change percentage.
4. Symbols: Use ▲ for gains and ▼ for losses when discussing price movements.
5. Accuracy: Always cite the figures provided in the context.
6. Safety & Advice: Provide data-driven insights and 'what analysts suggest,' but never give direct personal financial advice or 'buy/sell' commands.
7. Redirect: If asked about non-financial topics, politely transition back to how you can help with financial intelligence or market analysis."""

@router.get("/sessions")
async def get_sessions(user_id: str = "anonymous"):
    return await session_service.get_user_sessions(user_id)

@router.get("/history/{session_id}")
async def get_history(session_id: str, user_id: str = "anonymous"):
    return await session_service.get_history(session_id, user_id)

@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    data = await market_service.get_ticker_data(symbol)
    if not data:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return data

@router.websocket("/ws/{session_id}")
async def finsight_websocket(websocket: WebSocket, session_id: str, user_id: str = "anonymous"):
    await websocket.accept()
    logger.info(f"WebSocket connected for session {session_id}")
    
    try:
        while True:
            # Wait for user message
            data = await websocket.receive_text()
            try:
                request_data = json.loads(data)
                user_message = request_data.get("message", "")
            except json.JSONDecodeError:
                user_message = data
                
            if not user_message:
                continue

            timestamp = datetime.utcnow().isoformat()
            
            # Extract tickers
            tickers = await extract_tickers(user_message)
            logger.info(f"Extracted tickers: {tickers}")
            
            # Fetch Market Data in parallel
            ticker_tasks = [market_service.get_ticker_data(t) for t in tickers]
            market_data_results = await asyncio.gather(*ticker_tasks, return_exceptions=True)
            market_data_list = [d for d in market_data_results if isinstance(d, dict) and d]
                    
            # Get history
            history = await session_service.get_history(session_id, user_id)
            
            # Append User Message to session
            await session_service.append_message(session_id, user_id, "user", user_message, timestamp)
            
            # Build prompt
            prompt = build_prompt(user_message, history, market_data_list, SYSTEM_PROMPT.format(date=datetime.now().strftime("%Y-%m-%d")))
            
            # Stream response
            full_response = ""
            async for token in llm_service.stream_response(prompt):
                if token:
                    full_response += token
                    await websocket.send_json({"type": "token", "token": token})
            
            # Save Assistant response to session
            await session_service.append_message(session_id, user_id, "assistant", full_response, datetime.utcnow().isoformat())
            
            # Send done signal with metadata
            await websocket.send_json({
                "type": "done",
                "metadata": {
                    "tickers": tickers,
                    "market_data": market_data_list
                }
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "market_open": market_service.is_market_open()
    }
