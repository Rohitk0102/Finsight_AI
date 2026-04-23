import os
import httpx
import json
from typing import AsyncGenerator
from loguru import logger

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class LLMService:
    # Use high-performance models available on OpenRouter
    MODELS = [
        "google/gemini-flash-1.5",
        "mistralai/mistral-7b-instruct",
        "meta-llama/llama-3-8b-instruct",
        "gryphe/mythomax-l2-13b"
    ]

    @staticmethod
    async def stream_response(prompt: str) -> AsyncGenerator[str, None]:
        if not OPENROUTER_API_KEY:
            yield "OPENROUTER_API_KEY not configured. Finsight AI requires a valid OpenRouter API key to generate responses."
            return

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://finsight-ai.com", # Required by OpenRouter
            "X-Title": "Finsight AI",
            "Content-Type": "application/json"
        }
        
        payload_base = {
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "temperature": 0.4,
            "max_tokens": 2048,
        }

        # Try models in sequence
        for model_name in LLMService.MODELS:
            url = "https://openrouter.ai/api/v1/chat/completions"
            logger.info(f"Attempting LLM generation with OpenRouter model: {model_name}...")
            
            current_payload = {**payload_base, "model": model_name}

            try:
                # 10s connect timeout, 60s total timeout
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
                    async with client.stream("POST", url, headers=headers, json=current_payload) as response:
                        if response.status_code == 429:
                            logger.warning(f"Rate limit (429) hit for {model_name}. Falling back...")
                            continue 
                        
                        if response.status_code != 200:
                            error_body = await response.aread()
                            logger.error(f"OpenRouter API error ({response.status_code}) for {model_name}: {error_body.decode()}")
                            continue

                        # Success! Stream the response
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                
                                try:
                                    chunk = json.loads(data_str)
                                    if "choices" in chunk and len(chunk["choices"]) > 0:
                                        delta = chunk["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
                        return 

            except Exception as e:
                logger.error(f"LLM attempt with {model_name} failed: {e}")
                if model_name == LLMService.MODELS[-1]: 
                    yield f"\n[Error: Connection to Finsight AI backend failed. {str(e)}]"
        
        yield "\n[Error: All configured OpenRouter models are currently unavailable.]"

llm_service = LLMService()
