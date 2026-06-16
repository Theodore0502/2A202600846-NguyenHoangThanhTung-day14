import sys
import time
from pathlib import Path
import streamlit as st

# Ensure src is in path so we can import app
src_path = Path(__file__).parent.resolve()
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from app.graph import ShoppingAssistant

# 1. Config trang dạng Wide
st.set_page_config(page_title="AI Thổ Địa Mua Sắm", page_icon="🤖", layout="wide")

# 2. Custom CSS cho nền trắng, viền xám và hiệu ứng phát sáng Realtime (Compact)
st.markdown("""
<style>
/* CSS cho Header */
.main-header {
    margin-bottom: 1.5rem;
}
.main-header h2 {
    margin-bottom: 0.2rem;
    font-size: 1.8rem;
    font-weight: 700;
    color: #111;
}
.main-header p {
    color: #666;
    font-size: 0.95rem;
}

/* Workflow Container */
.workflow-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    background: #fcfcfc;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #eaeaea;
    margin-bottom: 1.5rem;
}

.parallel-nodes {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.flow-arrow {
    color: #bbb;
    font-size: 1.2rem;
}

/* Detailed Worker Card */
.worker-card {
    background-color: #ffffff;
    border: 1px solid #dcdcdc;
    border-radius: 12px;
    padding: 15px 20px;
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 3px 6px rgba(0,0,0,0.06);
    min-width: 150px;
}
.card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #333;
    margin-bottom: 5px;
    white-space: nowrap;
}
.card-desc {
    font-size: 0.8rem;
    color: #777;
    text-align: center;
    line-height: 1.2;
}

/* Hiệu ứng Glowing cho từng Worker */
@keyframes pulse-sup-compact {
    0% { box-shadow: 0 0 0 0 rgba(0, 170, 255, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(0, 170, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 170, 255, 0); }
}
.glow-supervisor {
    border-color: #00aaff !important;
    background-color: #e6f7ff !important;
    color: #005580 !important;
    animation: pulse-sup-compact 1.5s infinite;
}

@keyframes pulse-pol-compact {
    0% { box-shadow: 0 0 0 0 rgba(255, 153, 0, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(255, 153, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 153, 0, 0); }
}
.glow-policy {
    border-color: #ff9900 !important;
    background-color: #fff4e6 !important;
    color: #804d00 !important;
    animation: pulse-pol-compact 1.5s infinite;
}

@keyframes pulse-dat-compact {
    0% { box-shadow: 0 0 0 0 rgba(0, 204, 102, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(0, 204, 102, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 204, 102, 0); }
}
.glow-data {
    border-color: #00cc66 !important;
    background-color: #e6fff2 !important;
    color: #006633 !important;
    animation: pulse-dat-compact 1.5s infinite;
}

@keyframes pulse-res-compact {
    0% { box-shadow: 0 0 0 0 rgba(153, 51, 255, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(153, 51, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(153, 51, 255, 0); }
}
.glow-response {
    border-color: #9933ff !important;
    background-color: #f2e6ff !important;
    color: #4d0099 !important;
    animation: pulse-res-compact 1.5s infinite;
}

/* Nút bấm mẫu rộng full 100% */
.stButton > button {
    width: 100%;
    margin-bottom: 5px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# Khởi tạo mô hình
@st.cache_resource
def get_assistant():
    return ShoppingAssistant()

try:
    assistant = get_assistant()
except Exception as e:
    st.error(f"Lỗi khởi tạo hệ thống: {e}")
    st.stop()

# STATE INITIALIZATION
if "messages" not in st.session_state:
    st.session_state.messages = []
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""
if "last_active_nodes" not in st.session_state:
    st.session_state.last_active_nodes = []

# Hàm Render Debug Trace Thông Minh
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
                    st.code(item.get("raw_llm_output", ""), language="json")
                else:
                    route = item.get("output", {})
                    st.write(f"- **Cần tra Policy:** `{'✅ Có' if route.get('needs_policy') else '❌ Không'}`")
                    st.write(f"- **Cần tra Data:** `{'✅ Có' if route.get('needs_data') else '❌ Không'}`")
                    if route.get("clarification_question"):
                        st.write(f"- **Hỏi thêm user:** `{route.get('clarification_question')}`")
            
            elif node == "policy_worker":
                st.markdown("#### 📖 Policy Worker")
                chunks = item.get("retrieved_chunks", [])
                st.write(f"Đã lấy {len(chunks)} chunk tài liệu từ VectorDB.")
                for i, chunk in enumerate(chunks):
                    with st.expander(f"📄 Tài liệu {i+1}: {chunk.get('citation', 'N/A')}"):
                        st.write(chunk.get("content", ""))
                st.info(f"**Tóm tắt:**\n{item.get('output', {}).get('summary', '')}")
                
            elif node == "data_worker":
                st.markdown("#### 🗄️ Data Worker")
                tool_calls = item.get("tool_calls", [])
                if not tool_calls:
                    st.write("*(Không có Tool nào được gọi)*")
                else:
                    for tc in tool_calls:
                        st.markdown(f"**🛠️ Gọi Tool:** `{tc.get('tool')}`")
                        st.write("**📥 Input Args:**")
                        st.code(tc.get("args"), language="json")
                        with st.expander("📤 Xem JSON Data trả về"):
                            st.json(tc.get("result", {}))
                st.success(f"**Tóm tắt:**\n{item.get('output', {}).get('summary', '')}")
                
            elif node == "response_worker":
                st.markdown("#### 🗣️ Response Worker")
                st.write("**Raw Final Output:**")
                st.text(item.get("output", ""))
                
            st.markdown("---")
            
    with tab2:
        st.json(trace_list)

# 4. LAYOUT 2 CỘT (50% : 50%)
col_left, col_right = st.columns([1, 1], gap="large")

# --- CỘT TRÁI: HEADER, WORKFLOW & TIỆN ÍCH ---
with col_left:
    # Header nhỏ gọn ở góc trên trái
    st.markdown("""
    <div class="main-header">
        <h2>🤖 AI Thổ Địa Mua Sắm</h2>
        <p>Trải nghiệm Multi-Agent hỗ trợ trả lời mọi thắc mắc từ Chính sách cửa hàng đến Đơn hàng cá nhân</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🌐 Luồng xử lý (Real-time)")
    
    # Placeholder cho luồng Workflow dạng Flowchart nằm ngang
    workflow_ph = st.empty()
    
    def draw_nodes(active_nodes=None):
        if active_nodes is None:
            active_nodes = []
            
        sup_cls = "glow-supervisor" if "supervisor" in active_nodes else ""
        pol_cls = "glow-policy" if "worker_1_policy" in active_nodes else ""
        dat_cls = "glow-data" if "worker_2_data" in active_nodes else ""
        res_cls = "glow-response" if "worker_3_response" in active_nodes else ""
        
        html = f"""
        <div class="workflow-container">
            <div class="worker-card {sup_cls}">
                <div class="card-title">👨‍💼 Supervisor</div>
                <div class="card-desc">Điều phối & Phân luồng</div>
            </div>
            <div class="flow-arrow">➜</div>
            <div class="parallel-nodes">
                <div class="worker-card {pol_cls}">
                    <div class="card-title">📖 Policy Worker</div>
                    <div class="card-desc">Tìm kiếm RAG (Chính sách)</div>
                </div>
                <div class="worker-card {dat_cls}">
                    <div class="card-title">🗄️ Data Worker</div>
                    <div class="card-desc">Tra cứu Database (Tool)</div>
                </div>
            </div>
            <div class="flow-arrow">➜</div>
            <div class="worker-card {res_cls}">
                <div class="card-title">🗣️ Response</div>
                <div class="card-desc">Tổng hợp Kết quả cuối</div>
            </div>
        </div>
        """
        workflow_ph.markdown(html, unsafe_allow_html=True)

    # Mặc định vẽ các hộp tĩnh ban đầu (Giữ nguyên trạng thái của câu hỏi trước)
    draw_nodes(st.session_state.last_active_nodes)
    
    st.markdown("---")
    
    # Chia phần dưới cột trái thành 2 nửa cho gọn
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.markdown("#### ⚡ Tiện ích")
        use_fallback = st.toggle("Dùng Fallback", value=True, help="Nếu tắt, hệ báo lỗi nếu JSON parse fail.")
        show_debug = st.toggle("🐛 Bật Debug", value=True, help="Hiển thị hộp thoại Trace cực kỳ chi tiết dưới mỗi tin nhắn để Debug.")
        
        if st.button("🔄 Làm mới trò chuyện", type="primary"):
            st.session_state.messages = []
            st.session_state.prompt_input = ""
            st.rerun()
            
    with sub_col2:
        st.markdown("#### 💡 Câu hỏi mẫu")
        sample_questions_file = Path("data/sample_questions.txt")
        if sample_questions_file.exists():
            with open(sample_questions_file, "r", encoding="utf-8") as f:
                sample_questions = [line.strip() for line in f if line.strip()]
        else:
            sample_questions = []
            
        with st.container(height=250, border=True):
            for q in sample_questions:
                if st.button(q):
                    st.session_state.prompt_input = q

# --- CỘT PHẢI: KHUNG CHAT (50% Màn hình) ---
with col_right:
    # Khung chứa chat message
    chat_container = st.container(height=650, border=False)
    
    with chat_container:
        if len(st.session_state.messages) == 0:
            st.info("👋 Xin chào! Hãy đặt câu hỏi hoặc chọn một câu hỏi mẫu ở bên trái để bắt đầu.")
            
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                display_content = message["content"]
                
                # Làm sạch tin nhắn nếu TẮT debug
                if message["role"] == "assistant" and not show_debug:
                    if display_content.startswith("Status:"):
                        if "Question:" in display_content:
                            display_content = display_content.split("Question:", 1)[-1].strip()
                        elif "Message:" in display_content:
                            display_content = display_content.split("Message:", 1)[-1].strip()
                            
                    if "Answer:" in display_content:
                        display_content = display_content.replace("Answer:", "").strip()
                    if "Evidence:" in display_content:
                        display_content = display_content.split("Evidence:")[0].strip()
                        
                st.markdown(display_content)
                
                if message["role"] == "assistant" and "trace" in message and show_debug:
                    with st.expander("🛠️ Xem Trace chi tiết (Debug Mode)"):
                        render_debug_trace(message["trace"])
    
    # Khung input tin nhắn
    chat_val = st.chat_input("Nhập câu hỏi của bạn...")

# Xử lý input (từ nút hoặc từ thanh chat)
user_prompt = st.session_state.prompt_input if st.session_state.prompt_input else chat_val

if user_prompt:
    st.session_state.prompt_input = "" # Reset
    
    # Hiển thị tin nhắn người dùng lập tức
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_prompt)
            
    # Hiển thị đang xử lý và chạy Stream
    with chat_container:
        with st.chat_message("assistant"):
            status_text = st.empty()
            status_text.markdown("⏳ Đang suy nghĩ...")
            
            # 1. Bật sáng Supervisor đầu tiên
            draw_nodes(["supervisor"])
            
            # 2. Bắt đầu streaming từ LangGraph
            final_answer = "Không có câu trả lời."
            pending_workers = []
            full_trace = []
            used_nodes = {"supervisor"}
            
            try:
                for event in assistant.graph.stream(
                    {"question": user_prompt, "trace": [], "use_fallback": use_fallback}, 
                    stream_mode="updates"
                ):
                    # Thu thập trace từ bất kỳ node nào vừa chạy xong
                    for node_name, node_data in event.items():
                        used_nodes.add(node_name)
                        if "trace" in node_data:
                            full_trace.extend(node_data["trace"])
                            
                    if "supervisor" in event:
                        route = event["supervisor"].get("route", {})
                        if route.get("needs_policy"):
                            pending_workers.append("worker_1_policy")
                        if route.get("needs_data"):
                            pending_workers.append("worker_2_data")
                            
                        if pending_workers:
                            draw_nodes(pending_workers)
                        else:
                            draw_nodes(["worker_3_response"])
                            
                    elif "worker_1_policy" in event:
                        if "worker_1_policy" in pending_workers:
                            pending_workers.remove("worker_1_policy")
                        if not pending_workers:
                            draw_nodes(["worker_3_response"])
                        else:
                            draw_nodes(pending_workers)
                            
                    elif "worker_2_data" in event:
                        if "worker_2_data" in pending_workers:
                            pending_workers.remove("worker_2_data")
                        if not pending_workers:
                            draw_nodes(["worker_3_response"])
                        else:
                            draw_nodes(pending_workers)
                            
                    if "worker_3_response" in event:
                        final_answer = event["worker_3_response"].get("final_answer", "Không tìm thấy câu trả lời.")
                        
                # 3. Khi kết thúc toàn bộ graph
                status_text.empty()
                
                # Format final answer trước khi in ra (giống hệt logic ở trên)
                display_answer = final_answer
                if not show_debug:
                    if display_answer.startswith("Status:"):
                        if "Question:" in display_answer:
                            display_answer = display_answer.split("Question:", 1)[-1].strip()
                        elif "Message:" in display_answer:
                            display_answer = display_answer.split("Message:", 1)[-1].strip()
                            
                    if "Answer:" in display_answer:
                        display_answer = display_answer.replace("Answer:", "").strip()
                    if "Evidence:" in display_answer:
                        display_answer = display_answer.split("Evidence:")[0].strip()
                        
                st.markdown(display_answer)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_answer, # Vẫn lưu bản full thô vào lịch sử
                    "trace": full_trace
                })
                
                # Lưu lại toàn bộ các node đã dùng trong câu hỏi này để giữ sáng
                st.session_state.last_active_nodes = list(used_nodes)
                st.rerun() # Refresh layout
                
            except Exception as e:
                status_text.empty()
                st.error(f"Đã xảy ra lỗi: {e}")
                st.session_state.last_active_nodes = []
                draw_nodes([])
