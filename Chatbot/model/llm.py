import os
import json
import urllib.request
from typing import Dict, Any

class LocalLLM:
    _instance = None

    def __new__(cls, model_path: str = None, n_ctx: int = 8192):
        if cls._instance is None:
            cls._instance = super(LocalLLM, cls).__new__(cls)
            cls._instance.api_key = os.getenv("GROQ_API_KEY")
            if not cls._instance.api_key:
                print("Warning: GROQ_API_KEY environment variable not set.")
        return cls._instance

    def generate_json(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1024) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "thought": "GROQ_API_KEY is missing.",
                "action": "final_answer",
                "action_input": "Error: GROQ_API_KEY environment variable is not set. Please set it to use the Groq API."
            }

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Wrap the ChatML formatted prompt as a single user message
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(url, headers=headers, data=json.dumps(data).encode("utf-8"))
        
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                body = res.read().decode("utf-8")
                resp_data = json.loads(body)
                raw_text = resp_data["choices"][0]["message"]["content"]
        except Exception as e:
            return {
                "thought": f"API request failed: {e}",
                "action": "final_answer",
                "action_input": f"Groq API Error: {str(e)}"
            }

        raw_text = raw_text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        raw_text = raw_text.strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            start_idx = raw_text.find("{")
            end_idx = raw_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                try:
                    return json.loads(raw_text[start_idx:end_idx+1])
                except json.JSONDecodeError:
                    pass
            return {
                "thought": "Failed to output valid JSON.",
                "action": "final_answer",
                "action_input": raw_text
            }