from model.llm import LocalLLM
from utils.prompt import build_agent_prompt

class AgentPlanner:
    def __init__(self, llm: LocalLLM):
        self.llm = llm

    def plan_next_step(self, history: list, context: str, user_query: str, steps: list):
        prompt = build_agent_prompt(history, context, user_query, steps)
        response_json = self.llm.generate_json(prompt)
        
        if response_json.get("action") not in {"calculator", "context_search", "document_search", "final_answer"}:
            response_json["action"] = "final_answer"
        return response_json