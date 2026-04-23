import json
from typing import List, Dict, Any

def build_prompt(message: str, history: List[Dict[str, Any]], ticker_data: List[Dict[str, Any]], system_prompt: str) -> str:
    """
    Builds a Mistral-Instruct formatted prompt string.
    """
    # Format Market Data
    market_data_str = ""
    if ticker_data:
        market_data_str = "Market Data:\n"
        for data in ticker_data:
            # Minimal compact JSON representation for the LLM
            compact_data = {
                k: v for k, v in data.items() 
                if v is not None and k not in ["symbol", "source"]
            }
            market_data_str += f"{data.get('symbol')}: {json.dumps(compact_data)}\n"
            
    # Mistral-Instruct v0.2 prompt format:
    # <s>[INST] <<SYS>>
    # {system_prompt}
    # <</SYS>>
    # {chat_history}
    # {user_message} [/INST]
    
    sys_section = f"<<SYS>>\n{system_prompt}\n{market_data_str}\n<</SYS>>\n"
    
    # Format chat history
    history_str = ""
    # Only keep the last 10 messages for context window efficiency
    recent_history = history[-10:] if len(history) > 10 else history
    
    for msg in recent_history:
        role = msg.get("role")
        content = msg.get("content")
        if role == "user":
            history_str += f"User: {content}\n"
        else:
            history_str += f"Assistant: {content}\n"
            
    prompt = f"<s>[INST] {sys_section}\n{history_str}\nUser: {message} [/INST]"
    return prompt
