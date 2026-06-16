import streamlit as st
import asyncio
import os
from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge

# Streamlit config
st.set_page_config(page_title="LLM Arena Real-time", layout="wide")
st.title("🤖 LLM Arena: Model A vs Model B")
st.caption("Powered by Local Models / APIs")

# Initialize session state for messages and tools
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_a" not in st.session_state:
    st.session_state.agent_a = MainAgent(version="optimized", config_prefix="AGENT_A")

if "agent_b" not in st.session_state:
    st.session_state.agent_b = MainAgent(version="optimized", config_prefix="AGENT_B")

if "judge" not in st.session_state:
    st.session_state.judge = LLMJudge(model="online-consensus")

model_a_name = os.environ.get("AGENT_A_MODEL", "Model A")
model_b_name = os.environ.get("AGENT_B_MODEL", "Model B")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "eval_result_a" in msg and "eval_result_b" in msg:
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"🛡️ {model_a_name}")
                st.markdown(msg["answer_a"])
                with st.expander("📊 Evaluation Metrics"):
                    st.json(msg["eval_result_a"])
            with col2:
                st.subheader(f"⚔️ {model_b_name}")
                st.markdown(msg["answer_b"])
                with st.expander("📊 Evaluation Metrics"):
                    st.json(msg["eval_result_b"])

# Handle new user input
prompt = st.chat_input("Ask a question based on the dataset...")

if prompt:
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Agent response and Evaluation
    with st.chat_message("assistant"):
        with st.status("⚙️ Processing Arena Battle...", expanded=True) as status:
            # Lookup ground truth
            ground_truth = "Unknown ground truth"
            for item in st.session_state.agent_a.knowledge_base:
                if prompt.lower().strip() in item["question"].lower() or item["question"].lower() in prompt.lower().strip():
                    ground_truth = item.get("expected_answer", "")
                    break
            
            st.write("🔍 Models are generating answers...")
            # We run sequentially to avoid OOM on local GPU, but could be gathered if API
            async def run_arena():
                res_a = await st.session_state.agent_a.query(prompt)
                res_b = await st.session_state.agent_b.query(prompt)
                return res_a, res_b
            
            agent_result_a, agent_result_b = asyncio.run(run_arena())
            answer_a = agent_result_a.get("answer", "")
            answer_b = agent_result_b.get("answer", "")
            
            st.write("⚖️ Multi-Judge is evaluating answers...")
            async def eval_arena():
                e_a = await st.session_state.judge.evaluate_multi_judge(prompt, answer_a, ground_truth)
                e_b = await st.session_state.judge.evaluate_multi_judge(prompt, answer_b, ground_truth)
                return e_a, e_b
            
            eval_a, eval_b = asyncio.run(eval_arena())
            
            status.update(label="Battle Complete!", state="complete", expanded=False)
            
        st.write("### 🏆 Arena Results")
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"**Model A:** {model_a_name}")
            st.markdown(answer_a)
            st.metric("Score", eval_a.get("final_score", 0))
            with st.expander("View Reasoning"):
                st.write("**Strict:**", eval_a['individual_scores']['judge_strict_gpt_style'])
                st.info(eval_a['reasoning']['judge_strict_gpt_style'])
                st.write("**Semantic:**", eval_a['individual_scores']['judge_semantic_claude_style'])
                st.info(eval_a['reasoning']['judge_semantic_claude_style'])
                
        with col2:
            st.info(f"**Model B:** {model_b_name}")
            st.markdown(answer_b)
            st.metric("Score", eval_b.get("final_score", 0))
            with st.expander("View Reasoning"):
                st.write("**Strict:**", eval_b['individual_scores']['judge_strict_gpt_style'])
                st.info(eval_b['reasoning']['judge_strict_gpt_style'])
                st.write("**Semantic:**", eval_b['individual_scores']['judge_semantic_claude_style'])
                st.info(eval_b['reasoning']['judge_semantic_claude_style'])

    # 3. Save assistant message
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Arena battle concluded. See results below.",
        "answer_a": answer_a,
        "answer_b": answer_b,
        "eval_result_a": eval_a,
        "eval_result_b": eval_b
    })
