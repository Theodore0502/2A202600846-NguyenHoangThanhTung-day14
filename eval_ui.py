import sys
import time
import asyncio
import json
from pathlib import Path
import streamlit as st
import os

# Setup working directory and paths
ROOT_PATH = Path(__file__).parent.resolve()
DAY09_PATH = ROOT_PATH / "2A202600846-NguyenHoangThanhTung-Day09"

# Xoá đường dẫn thư mục gốc khỏi sys.path để tránh Python import nhầm file app.py của thư mục gốc!
root_dir = str(ROOT_PATH)
sys.path = [p for p in sys.path if p != root_dir and p != ""]

if str(DAY09_PATH / "src") not in sys.path:
    sys.path.insert(0, str(DAY09_PATH / "src"))

os.chdir(DAY09_PATH)

if "app" in sys.modules:
    del sys.modules["app"]

try:
    # pyrefly: ignore [missing-import]
    from app.graph import ShoppingAssistant
except ImportError as e:
    st.error(f"Failed to import ShoppingAssistant: {e}")
    st.write(f"Sys Path: {sys.path}")
    st.stop()

os.chdir(ROOT_PATH)
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

try:
    from engine.day09_judge import Day09Judge
except ImportError as e:
    st.error(f"Failed to import Day09Judge: {e}")
    st.stop()

os.chdir(DAY09_PATH)

st.set_page_config(page_title="Day 09 Evaluation UI", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
/* Header CSS */
.main-header { margin-bottom: 1.5rem; }
.main-header h2 { margin-bottom: 0.2rem; font-size: 1.8rem; font-weight: 700; color: #111; }
.main-header p { color: #666; font-size: 0.95rem; }

/* Workflow */
.workflow-container {
    display: flex; flex-direction: row; align-items: center; justify-content: space-between;
    background: #fcfcfc; padding: 20px; border-radius: 12px; border: 1px solid #eaeaea; margin-bottom: 1.5rem;
}
.parallel-nodes { display: flex; flex-direction: column; gap: 12px; }
.flow-arrow { color: #bbb; font-size: 1.2rem; }

/* Card CSS */
.worker-card {
    background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 12px; padding: 15px 20px;
    transition: all 0.3s ease; display: flex; flex-direction: column; align-items: center; justify-content: center;
    box-shadow: 0 3px 6px rgba(0,0,0,0.06); min-width: 150px;
}
.card-title { font-size: 1rem; font-weight: 700; color: #333; margin-bottom: 5px; white-space: nowrap; }
.card-desc { font-size: 0.8rem; color: #777; text-align: center; line-height: 1.2; }

/* Glow Animations */
@keyframes pulse-sup-compact { 0% { box-shadow: 0 0 0 0 rgba(0, 170, 255, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(0, 170, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 170, 255, 0); } }
.glow-supervisor { border-color: #00aaff !important; background-color: #e6f7ff !important; color: #005580 !important; animation: pulse-sup-compact 1.5s infinite; }

@keyframes pulse-pol-compact { 0% { box-shadow: 0 0 0 0 rgba(255, 153, 0, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(255, 153, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 153, 0, 0); } }
.glow-policy { border-color: #ff9900 !important; background-color: #fff4e6 !important; color: #804d00 !important; animation: pulse-pol-compact 1.5s infinite; }

@keyframes pulse-dat-compact { 0% { box-shadow: 0 0 0 0 rgba(0, 204, 102, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(0, 204, 102, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 204, 102, 0); } }
.glow-data { border-color: #00cc66 !important; background-color: #e6fff2 !important; color: #006633 !important; animation: pulse-dat-compact 1.5s infinite; }

@keyframes pulse-res-compact { 0% { box-shadow: 0 0 0 0 rgba(153, 51, 255, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(153, 51, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(153, 51, 255, 0); } }
.glow-response { border-color: #9933ff !important; background-color: #f2e6ff !important; color: #4d0099 !important; animation: pulse-res-compact 1.5s infinite; }

/* Judge Card */
.judge-card { border: 2px solid #5cb85c; background-color: #f9fff9; border-radius: 8px; padding: 1rem; margin-top: 1rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_assistant():
    return ShoppingAssistant()

@st.cache_resource
def get_judge():
    return Day09Judge()

# Dataset Loader
dataset_path = DAY09_PATH / "data" / "test.json"
test_cases = []
if dataset_path.exists():
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

case_options = ["Tự nhập câu hỏi..."] + [f"[{c['id']}] {c['question'][:50]}..." for c in test_cases]

# Form states
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""
if "contains_input" not in st.session_state:
    st.session_state.contains_input = ""
if "status_input" not in st.session_state:
    st.session_state.status_input = "ok"
    
def on_case_change():
    sel = st.session_state.case_selector
    if sel == "Tự nhập câu hỏi...":
        st.session_state.prompt_input = ""
        st.session_state.contains_input = ""
        st.session_state.status_input = "ok"
        return
    case_id = sel.split("]")[0][1:]
    for c in test_cases:
        if c["id"] == case_id:
            st.session_state.prompt_input = c.get("question", "")
            st.session_state.contains_input = ", ".join(c.get("expected_contains", []))
            st.session_state.status_input = c.get("expected_status", "ok")
            break

def render_debug_trace(trace_list):
    if not trace_list:
        return
        
    tab1, tab2 = st.tabs(["✨ Visual Trace", "📦 Raw JSON State"])
    with tab1:
        for item in trace_list:
            node = item.get("node")
            if node == "supervisor":
                st.markdown("#### 👨‍💼 Supervisor Agent")
                if item.get("action") == "fallback_used":
                    st.error("⚠️ LLM lỗi format, tự động nhảy vào Fallback Route")
                else:
                    route = item.get("output", {})
                    st.write(f"- **Policy:** `{'✅' if route.get('needs_policy') else '❌'}`")
                    st.write(f"- **Data:** `{'✅' if route.get('needs_data') else '❌'}`")
            elif node == "policy_worker":
                st.markdown("#### 📖 Policy Worker")
                st.info(f"**Tóm tắt:**\n{item.get('output', {}).get('summary', '')}")
            elif node == "data_worker":
                st.markdown("#### 🗄️ Data Worker")
                tool_calls = item.get("tool_calls", [])
                for tc in tool_calls:
                    st.markdown(f"**🛠️ Gọi Tool:** `{tc.get('tool')}`")
                st.success(f"**Tóm tắt:**\n{item.get('output', {}).get('summary', '')}")
            elif node == "response_worker":
                st.markdown("#### 🗣️ Response Worker")
            st.markdown("---")
    with tab2:
        st.json(trace_list)
        
def get_workflow_html(active_nodes=None):
    if active_nodes is None: active_nodes = []
    sup_cls = "glow-supervisor" if "supervisor" in active_nodes else ""
    pol_cls = "glow-policy" if "worker_1_policy" in active_nodes else ""
    dat_cls = "glow-data" if "worker_2_data" in active_nodes else ""
    res_cls = "glow-response" if "worker_3_response" in active_nodes else ""
    return f"""
    <div class="workflow-container">
        <div class="worker-card {sup_cls}"><div class="card-title">👨‍💼 Supervisor</div></div>
        <div class="flow-arrow">➜</div>
        <div class="parallel-nodes">
            <div class="worker-card {pol_cls}"><div class="card-title">📖 Policy Worker</div></div>
            <div class="worker-card {dat_cls}"><div class="card-title">🗄️ Data Worker</div></div>
        </div>
        <div class="flow-arrow">➜</div>
        <div class="worker-card {res_cls}"><div class="card-title">🗣️ Response</div></div>
    </div>
    """

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("""
    <div class="main-header">
        <h2>⚖️ Manual Eval & Debug Trace</h2>
        <p>Hệ thống tự động chấm điểm Shopping Agent thông qua LLM Judge</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Cấu hình Model")
    is_arena = st.toggle("⚔️ Bật chế độ Đấu trường (Arena Mode)", value=False)
    
    if is_arena:
        st.info("Chế độ Arena sẽ chạy tuần tự 2 Model để đánh giá khách quan.")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("**🛡️ Model A**")
            provider_a = st.selectbox("Provider A", ["ollama", "openai", "gemini", "openrouter"], index=0, key="prov_a")
            model_a = st.text_input("Tên Model A", value="qwen2.5:7b", key="mod_a")
        with col_m2:
            st.markdown("**⚔️ Model B**")
            provider_b = st.selectbox("Provider B", ["ollama", "openai", "gemini", "openrouter"], index=0, key="prov_b")
            model_b = st.text_input("Tên Model B", value="qwen2.5:3b", key="mod_b")
    else:
        col_prov, col_mod = st.columns(2)
        with col_prov:
            provider_a = st.selectbox("LLM Provider", ["ollama", "openai", "gemini", "openrouter"], index=0)
        with col_mod:
            model_a = st.text_input("LLM Model", value="qwen2.5:7b")
        provider_b, model_b = None, None

    st.markdown("### 📝 Thiết lập bài Test")
    st.selectbox("Load từ Test Dataset:", case_options, key="case_selector", on_change=on_case_change)
    
    with st.form("eval_form"):
        user_prompt = st.text_area("Câu hỏi từ khách hàng:", key="prompt_input")
        st.markdown("Tiêu chí chấm điểm (Nếu có)")
        expected_contains_input = st.text_input("Expected Contains (cách nhau bởi dấu phẩy):", key="contains_input")
        
        status_opts = ["ok", "clarification_needed", "not_found", "out_of_scope"]
        idx = status_opts.index(st.session_state.status_input) if st.session_state.status_input in status_opts else 0
        
        col1, col2 = st.columns(2)
        with col1:
            expected_status = st.selectbox("Expected Route Status:", status_opts, index=idx)
        with col2:
            use_fallback = st.toggle("Cho phép Fallback Parser", value=True)
            
        submitted = st.form_submit_button("Chạy Đánh Giá", type="primary", use_container_width=True)

with col_right:
    st.markdown("### 📊 Kết quả thực thi")
    results_container = st.container(height=650, border=False)

    def run_eval_for_model(provider, model_name, container, prefix=""):
        os.environ["LLM_PROVIDER"] = provider
        os.environ["LLM_MODEL"] = model_name
        get_assistant.clear()
        
        try:
            assistant = get_assistant()
            judge = get_judge()
        except Exception as e:
            container.error(f"Lỗi khởi tạo mô hình {model_name}: {e}")
            return
            
        status_text = container.empty()
        status_text.markdown(f"⏳ **{prefix}{model_name}** đang suy nghĩ...")
        workflow_ph = container.empty()
        workflow_ph.markdown(get_workflow_html(["supervisor"]), unsafe_allow_html=True)
        
        final_answer = ""
        full_trace = []
        actual_status = "unknown"
        pending_workers = []
        
        try:
            for event in assistant.graph.stream(
                {"question": user_prompt, "trace": [], "use_fallback": use_fallback}, 
                stream_mode="updates"
            ):
                for node_name, node_data in event.items():
                    if "trace" in node_data:
                        full_trace.extend(node_data["trace"])
                        
                if "supervisor" in event:
                    route = event["supervisor"].get("route", {})
                    actual_status = route.get("status", "unknown")
                    if route.get("needs_policy"): pending_workers.append("worker_1_policy")
                    if route.get("needs_data"): pending_workers.append("worker_2_data")
                    workflow_ph.markdown(get_workflow_html(pending_workers if pending_workers else ["worker_3_response"]), unsafe_allow_html=True)
                elif "worker_1_policy" in event:
                    if "worker_1_policy" in pending_workers: pending_workers.remove("worker_1_policy")
                    workflow_ph.markdown(get_workflow_html(pending_workers if pending_workers else ["worker_3_response"]), unsafe_allow_html=True)
                elif "worker_2_data" in event:
                    if "worker_2_data" in pending_workers: pending_workers.remove("worker_2_data")
                    workflow_ph.markdown(get_workflow_html(pending_workers if pending_workers else ["worker_3_response"]), unsafe_allow_html=True)
                    
                if "worker_3_response" in event:
                    final_answer = event["worker_3_response"].get("final_answer", "Không tìm thấy.")
                    
            status_text.empty()
            workflow_ph.empty()
            container.markdown(final_answer)
            
            with container.expander("🛠️ Xem Trace chi tiết"):
                render_debug_trace(full_trace)
            
            # --- EVALUATION ---
            container.markdown("---")
            container.subheader("🧑‍⚖️ LLM Judge Evaluation")
            
            contains_list = [c.strip() for c in expected_contains_input.split(",")] if expected_contains_input.strip() else []
            
            with container.spinner("Giám khảo đang chấm bài..."):
                judge_res = asyncio.run(judge.evaluate_multi_judge_contains(user_prompt, final_answer, contains_list))
                
            score = judge_res["final_score"]
            status_match = actual_status == expected_status
            if not status_match:
                score = min(score, 2.0)
                
            container.markdown(f"""
            <div class="judge-card">
                <h3>Điểm số: {score} / 5.0</h3>
                <p><b>Status Route:</b> Thực tế <code>{actual_status}</code> (Kỳ vọng: <code>{expected_status}</code>)</p>
                <hr/>
                <p><b>🧑‍⚖️ Giám khảo Khắt khe (Strict):</b> {judge_res['reasoning']['judge_strict']} (Điểm: {judge_res['individual_scores']['judge_strict']})</p>
                <p><b>🧑‍⚖️ Giám khảo Ngữ nghĩa (Semantic):</b> {judge_res['reasoning']['judge_semantic']} (Điểm: {judge_res['individual_scores']['judge_semantic']})</p>
                <p><b>Độ đồng thuận:</b> {judge_res['agreement_rate']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            status_text.empty()
            workflow_ph.empty()
            container.error(f"Đã xảy ra lỗi: {e}")


    if submitted and user_prompt:
        with results_container:
            st.chat_message("user").write(user_prompt)
            
            if not is_arena:
                with st.chat_message("assistant"):
                    run_eval_for_model(provider_a, model_a, st.container(), prefix="")
            else:
                col_res_a, col_res_b = st.columns(2)
                with col_res_a:
                    st.markdown(f"### 🛡️ Model A: `{model_a}`")
                    run_eval_for_model(provider_a, model_a, st.container(), prefix="Model A ")
                with col_res_b:
                    st.markdown(f"### ⚔️ Model B: `{model_b}`")
                    run_eval_for_model(provider_b, model_b, st.container(), prefix="Model B ")
