import os
import json
from typing import Dict, Any
from llama_cpp import Llama

class LocalLLM:
    _instance = None

    def __new__(cls, model_path: str = "models/qwen2.5-0.5b-instruct-q4_k_m.gguf", n_ctx: int = 2048):
        if cls._instance is None:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}.")
            
            cls._instance = super(LocalLLM, cls).__new__(cls)
            cls._instance.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=4,  # Tuned for Intel i5-1155G7 core performance
                verbose=False
            )
        return cls._instance

    def generate_json(self, prompt: str, temperature: float = 0.1, max_tokens: int = 256) -> Dict[str, Any]:
        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|im_end|>", "```"],
            echo=False
        )
        raw_text = response["choices"][0]["text"].strip()
        
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