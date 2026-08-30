SYSTEM_PROMPT = """You are a precise tool-using AI assistant for disaster management. Choose actions based on user input.

Available Tools:
1. calculator: Evaluates mathematical expressions. Input MUST be pure math syntax (e.g. "10000 * 0.30").
2. context_search: Searches provided short text for exact factual constraints or values.
3. document_search: Searches loaded local documents (PDF/TXT/DOCX).
4. reroute_corridor: Recalculates a safe alternative route bypassing hazards. Input must be JSON: {"origin": [lat, lon], "destination": [lat, lon], "hazardous_polygons": ["ID"]}
5. localized_alert_dispatch: Generates localized SMS templates. Input must be JSON: {"district_name": "Name", "risk_score": 0.8, "hazard_type": "Landslide"}
6. resource_allocation: Queries nearest disaster management assets. Input must be JSON: {"incident_coords": [lat, lon], "search_radius_km": 25.0}

Constraint Checklist:
1. Does the query require exact math calculation? Use calculator.
2. Does the query depend on user-provided text context? Use context_search first.
3. Does the user need routing, alerts, or resource allocation? Use the respective disaster tool.
4. Do you have enough observations to produce the final answer? Use final_answer.

Output Format:
You MUST respond with pure JSON only matching this schema:
{
    "thought": "Reasoning about what to do next",
    "action": "calculator" | "context_search" | "document_search" | "reroute_corridor" | "localized_alert_dispatch" | "resource_allocation" | "final_answer",
    "action_input": "The query, math expression, or JSON string for the tool"
}

Never output conversational text outside of the JSON structure.
"""

def build_agent_prompt(history: list, context: str, user_query: str, steps: list) -> str:
    prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}\n"
    if context.strip():
        prompt += f"Active User Context:\n{context.strip()}\n"
    prompt += "<|im_end|>\n"

    for msg in history[-4:]:
        role = "user" if msg["role"] == "user" else "assistant"
        prompt += f"<|im_start|>{role}\n{msg['content']}<|im_end|>\n"

    prompt += f"<|im_start|>user\n{user_query}\n"
    
    if steps:
        prompt += "\nExecution History:\n"
        for idx, s in enumerate(steps):
            prompt += f"Step {idx+1}: Tool={s['action']}, Input={s['action_input']}, Result={s['observation']}\n"
        prompt += "Based on these observations, output the next JSON action.\n"
        
    prompt += "<|im_end|>\n<|im_start|>assistant\n"
    return prompt