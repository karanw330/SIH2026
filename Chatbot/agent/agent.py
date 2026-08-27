from model.llm import LocalLLM
from agent.planner import AgentPlanner
from agent.memory import ConversationMemory
from tools.calculator import CalculatorTool
from tools.context_search import ContextSearchTool
from tools.document_search import DocumentSearchTool

class AgentController:
    def __init__(self, model_path: str = "models/qwen2.5-0.5b-instruct-q4_k_m.gguf", max_iterations: int = 5):
        self.llm = LocalLLM(model_path=model_path)
        self.planner = AgentPlanner(self.llm)
        self.memory = ConversationMemory()
        self.max_iterations = max_iterations
        
        self.calculator = CalculatorTool()
        self.context_search = ContextSearchTool()
        self.document_search = DocumentSearchTool()

    def run(self, user_query: str, context: str = "", doc_text: str = ""):
        steps = []
        iterations = 0
        yield {"status": "start", "message": "Analyzing request..."}
        
        while iterations < self.max_iterations:
            iterations += 1
            plan = self.planner.plan_next_step(self.memory.get_history(), context, user_query, steps)
            
            action = plan.get("action")
            action_input = str(plan.get("action_input", ""))
            
            if action == "final_answer":
                yield {"status": "complete", "action": "Final Answer", "result": action_input}
                self.memory.add_message("user", user_query)
                self.memory.add_message("assistant", action_input)
                return

            yield {"status": "tool_start", "action": action, "input": action_input}

            if action == "calculator":
                observation = self.calculator.execute(action_input)
            elif action == "context_search":
                observation = self.context_search.execute(action_input, context)
            elif action == "document_search":
                observation = self.document_search.execute(action_input, doc_text)
            else:
                observation = f"Unsupported tool: {action}"

            steps.append({"action": action, "action_input": action_input, "observation": observation})
            yield {"status": "tool_done", "action": action, "observation": observation}

        yield {"status": "complete", "action": "Limit Reached", "result": "Iteration cap reached."}