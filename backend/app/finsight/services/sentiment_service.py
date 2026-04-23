import os
import httpx
import json
from typing import Dict, List
from loguru import logger

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class SentimentService:
    @staticmethod
    async def get_sentiment(headlines: List[str]) -> Dict[str, float]:
        """
        Analyzes sentiment of multiple headlines using OpenRouter (Gemini Flash 1.5).
        """
        if not headlines or not OPENROUTER_API_KEY:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        combined_headlines = "\n".join([f"- {h}" for h in headlines])
        
        prompt = f"""
        Analyze the overall financial sentiment of these stock market headlines.
        Headlines:
        {combined_headlines}
        
        Provide your response in raw JSON format with three keys: 'positive', 'negative', and 'neutral'. 
        Each value must be a float between 0.0 and 1.0 representing the confidence/weight.
        Return ONLY the JSON.
        """

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://finsight-ai.com",
            "X-Title": "Finsight AI",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(url, headers=headers, json={
                    "model": "google/gemini-flash-1.5",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                })
                
                if response.status_code == 200:
                    data = response.json()
                    sentiment_text = data["choices"][0]["message"]["content"]
                    scores = json.loads(sentiment_text)
                    
                    # Normalizing/Validating keys
                    result = {
                        "positive": float(scores.get("positive", 0.0)),
                        "negative": float(scores.get("negative", 0.0)),
                        "neutral": float(scores.get("neutral", 0.0))
                    }
                    return result
                return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
        except Exception as e:
            logger.error(f"OpenRouter sentiment analysis failed: {e}")
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

sentiment_service = SentimentService()
