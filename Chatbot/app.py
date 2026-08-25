import streamlit as st
import os
from agent.agent import AgentController
from tools.document_search import DocumentSearchTool

st.set_page_config(page_title="Local Agentic AI Chatbot", page_icon="🤖", layout="wide")

st.title("LOCAL AGENTIC AI CHATBOT")
st.caption("Quantized Offline Inference with Tool-Based Reasoning")

MODEL_PATH = "models/qwen2.5-0.5b-instruct-q4_k_m.gguf"

@st.cache_resource
def get_agent():
    return AgentController(model_path=MODEL_PATH)

if not os.path.exists(MODEL_PATH):
    st.error(f"Missing model at `{MODEL_PATH}`. Please place the model in the models folder.")
    st.stop()

agent = get_agent()

with st.sidebar:
    st.header("Control Panel")
    if st.button("Clear Conversation", use_container_width=True):
        agent.memory.clear()
        st.success("Memory cleared.")

    st.subheader("Document Loader")
    uploaded_file = st.file_uploader("Upload PDF, TXT, or DOCX", type=["pdf", "txt", "docx"])
    extracted_doc_text = ""
    if uploaded_file is not None:
        extracted_doc_text = DocumentSearchTool().extract_text(uploaded_file.read(), uploaded_file.name.split(".")[-1].lower())
        st.success(f"Extracted {len(extracted_doc_text)} characters.")

context_input = st.text_area("Context / Document Reference:", height=100)
query_input = st.text_input("Question:")

if st.button("Ask Agent", type="primary") and query_input.strip():
    status_box = st.empty()
    final_answer = ""
    
    for event in agent.run(user_query=query_input, context=context_input, doc_text=extracted_doc_text):
        if event["status"] == "start":
            status_box.info(f"**Status:** {event['message']}")
        elif event["status"] == "tool_start":
            status_box.warning(f"**Executing Tool:** `{event['action']}`\n\n**Input:** `{event['input']}`")
        elif event["status"] == "tool_done":
            status_box.success(f"**Completed Tool:** `{event['action']}`\n\n**Observation:** `{event['observation']}`")
        elif event["status"] == "complete":
            final_answer = event["result"]

    st.divider()
    st.markdown(f"### Final Answer:\n{final_answer}")