import os
import httpx
import json
from loguru import logger

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class IntentService:
    @staticmethod
    async def classify(message: str) -> str:
        """
        Classifies user intent using OpenRouter (Gemini Flash 1.5) for low-latency and high accuracy.
        """
        if not OPENROUTER_API_KEY:
            return "concept_explanation"

        candidate_labels = [
            "stock_lookup",
            "portfolio_analysis",
            "market_summary",
            "news_sentiment",
            "concept_explanation",
            "out_of_scope"
        ]

        prompt = f"""
        Classify the user's financial query into exactly one of these labels: {", ".join(candidate_labels)}.
        Return ONLY the label name in lowercase.
        
        User Query: "{message}"
        Label:"""

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://finsight-ai.com",
            "X-Title": "Finsight AI",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, headers=headers, json={
                    "model": "google/gemini-flash-1.5",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 10
                })
                
                if response.status_code == 200:
                    data = response.json()
                    label = data["choices"][0]["message"]["content"].strip().lower()
                    # Validate label
                    if label in candidate_labels:
                        return label
                return "concept_explanation"
        except Exception as e:
            logger.error(f"OpenRouter intent classification failed: {e}")
            return "concept_explanation"

intent_service = IntentService()
