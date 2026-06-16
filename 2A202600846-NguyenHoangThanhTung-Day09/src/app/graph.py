from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import Settings
from app.state import ShoppingState
from provider import get_chat_model
from app.data_access import ShoppingDataStore, build_data_tools
from rag.embeddings import SentenceTransformerEmbeddings
from rag.vector_store import ChromaPolicyStore
from app.prompts import SUPERVISOR_PROMPT, POLICY_WORKER_PROMPT, DATA_WORKER_PROMPT, RESPONSE_WORKER_PROMPT

class ShoppingAssistant:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.load()
        self.llm = get_chat_model(self.settings)
        
        data_path = Path("data/order_customer_mock_data.json")
        self.data_store = ShoppingDataStore(data_path)
        self.data_tools = build_data_tools(self.data_store)
        
        embedding_model = SentenceTransformerEmbeddings("sentence-transformers/all-MiniLM-L6-v2")
        persist_dir = Path("data/chroma_db")
        self.policy_store = ChromaPolicyStore(
            persist_directory=persist_dir,
            embedding_model=embedding_model,
        )
        
        self.graph = build_graph(self.llm, self.policy_store, self.data_tools)

    def ask(
        self,
        question: str,
        trace_file: Path | None = None,
        rebuild_index: bool = False,
    ) -> dict[str, Any]:
        if rebuild_index:
            self.policy_store.rebuild(Path("data/policy_mock_vi.md"))
        else:
            self.policy_store.ensure_index(Path("data/policy_mock_vi.md"))
            
        initial_state = {"question": question, "trace": []}
        result = self.graph.invoke(initial_state)
        
        if trace_file:
            with open(trace_file, "w", encoding="utf-8") as f:
                json.dump(result.get("trace", []), f, ensure_ascii=False, indent=2)
                
        return result

    def run_batch(
        self,
        test_file: Path,
        output_dir: Path,
        rebuild_index: bool = False,
    ) -> dict[str, Any]:
        if rebuild_index:
            self.policy_store.rebuild(Path("data/policy_mock_vi.md"))
        else:
            self.policy_store.ensure_index(Path("data/policy_mock_vi.md"))
            
        with open(test_file, "r", encoding="utf-8") as f:
            test_cases = json.load(f)
            
        summary = {"total": len(test_cases), "results": []}
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, case in enumerate(test_cases):
            question = case.get("question")
            if not question:
                continue
                
            trace_file = output_dir / f"trace_{i}.json"
            result = self.ask(question, trace_file=trace_file)
            
            summary["results"].append({
                "question": question,
                "final_answer": result.get("final_answer"),
                "expected_route": case.get("expected_route", "N/A"),
                "actual_route": result.get("route", {})
            })
            
        with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        return summary

def parse_json_from_llm(text: str) -> dict:
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception:
        return {}

def supervisor_node(state: ShoppingState, llm: Any) -> ShoppingState:
    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=state["question"])
    ]
    response = llm.invoke(messages)
    route_data = parse_json_from_llm(response.content)
    
    if not route_data:
        use_fallback = state.get("use_fallback", True)
        if use_fallback:
            route_data = {"status": "ok", "needs_policy": True, "needs_data": False, "clarification_question": None}
            trace_item = {"node": "supervisor", "action": "fallback_used", "raw_llm_output": response.content}
        else:
            raise ValueError(f"LLM không trả về đúng định dạng JSON. Raw output: {response.content}")
    else:
        trace_item = {"node": "supervisor", "output": route_data}
        
    return {"route": route_data, "trace": [trace_item]}

def worker_1_policy_node(state: ShoppingState, llm: Any, policy_store: Any) -> ShoppingState:
    hits = policy_store.search(state["question"], top_k=3)
    
    context = ""
    for hit in hits:
        context += f"Citation: {hit['citation']}\nContent: {hit['content']}\n\n"
        
    prompt = f"{POLICY_WORKER_PROMPT}\n\nQuestion: {state['question']}\n\nRetrieved Context:\n{context}"
    messages = [HumanMessage(content=prompt)]
    
    response = llm.invoke(messages)
    policy_result = parse_json_from_llm(response.content)
    
    if not policy_result:
        policy_result = {"status": "ok", "summary": response.content, "facts": [], "citations": []}
        
    trace_item = {"node": "policy_worker", "retrieved_chunks": hits, "output": policy_result}
    return {"policy_result": policy_result, "trace": [trace_item]}

def worker_2_data_node(state: ShoppingState, llm: Any, data_tools: list) -> ShoppingState:
    llm_with_tools = llm.bind_tools(data_tools)
    messages = [
        SystemMessage(content=DATA_WORKER_PROMPT),
        HumanMessage(content=state["question"])
    ]
    
    tool_calls_trace = []
    
    for _ in range(3):
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        if not response.tool_calls:
            break
            
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            tool_instance = next((t for t in data_tools if t.name == tool_name), None)
            if tool_instance:
                tool_result = tool_instance.invoke(tool_args)
                tool_calls_trace.append({"tool": tool_name, "args": tool_args, "result": tool_result})
                
                # Format to str if dict
                if isinstance(tool_result, dict):
                    tool_result_str = json.dumps(tool_result, ensure_ascii=False)
                else:
                    tool_result_str = str(tool_result)
                    
                # Fix: append a ToolMessage properly instead of a dict
                from langchain_core.messages import ToolMessage
                messages.append(
                    ToolMessage(
                        name=tool_name,
                        content=tool_result_str,
                        tool_call_id=tool_call["id"]
                    )
                )
                
    final_prompt = [
        SystemMessage(content=DATA_WORKER_PROMPT),
        HumanMessage(content=f"Question: {state['question']}\nHistory:\n" + "\n".join([str(m) for m in messages[1:]]))
    ]
    final_response = llm.invoke(final_prompt)
    data_result = parse_json_from_llm(final_response.content)
    
    if not data_result:
        data_result = {"status": "ok", "summary": final_response.content, "facts": [], "missing_fields": [], "not_found_entities": []}
        
    trace_item = {"node": "data_worker", "tool_calls": tool_calls_trace, "output": data_result}
    return {"data_result": data_result, "trace": [trace_item]}

def worker_3_response_node(state: ShoppingState, llm: Any) -> ShoppingState:
    route = state.get("route", {})
    if route.get("status") == "clarification_needed":
        q = route.get("clarification_question", "Xin vui lòng cung cấp thêm thông tin.")
        final_answer = f"Status: clarification_needed\nQuestion: {q}"
        return {"final_answer": final_answer, "trace": [{"node": "response_worker", "output": final_answer}]}
        
    data_res = state.get("data_result", {})
    if data_res.get("status") == "clarification_needed":
        final_answer = f"Status: clarification_needed\nQuestion: Vui lòng cung cấp thêm thông tin (ví dụ: mã đơn hàng hoặc mã khách hàng) để tôi tra cứu nhé."
        return {"final_answer": final_answer, "trace": [{"node": "response_worker", "output": final_answer}]}
        
    if data_res.get("status") == "not_found":
        msg = data_res.get("summary", "Không tìm thấy dữ liệu bạn yêu cầu.")
        final_answer = f"Status: not_found\nMessage: {msg}"
        return {"final_answer": final_answer, "trace": [{"node": "response_worker", "output": final_answer}]}
        
    policy_res = state.get("policy_result", {})
    
    context = ""
    if route.get("needs_policy"):
        context += f"Policy Context:\n{json.dumps(policy_res, ensure_ascii=False)}\n\n"
    if route.get("needs_data"):
        context += f"Data Context:\n{json.dumps(data_res, ensure_ascii=False)}\n\n"
        
    messages = [
        SystemMessage(content=RESPONSE_WORKER_PROMPT),
        HumanMessage(content=f"Question: {state['question']}\n\n{context}")
    ]
    
    response = llm.invoke(messages)
    final_answer = response.content.strip()
    
    trace_item = {"node": "response_worker", "output": final_answer}
    return {"final_answer": final_answer, "trace": [trace_item]}


def build_graph(llm: Any, policy_store: Any, data_tools: list) -> Any:
    workflow = StateGraph(ShoppingState)
    
    def s_node(state: ShoppingState):
        return supervisor_node(state, llm)
    
    def p_node(state: ShoppingState):
        return worker_1_policy_node(state, llm, policy_store)
        
    def d_node(state: ShoppingState):
        return worker_2_data_node(state, llm, data_tools)
        
    def r_node(state: ShoppingState):
        return worker_3_response_node(state, llm)
        
    workflow.add_node("supervisor", s_node)
    workflow.add_node("worker_1_policy", p_node)
    workflow.add_node("worker_2_data", d_node)
    workflow.add_node("worker_3_response", r_node)
    
    workflow.add_edge(START, "supervisor")
    
    def route_supervisor(state: ShoppingState):
        r = state.get("route", {})
        if r.get("status") == "clarification_needed":
            return ["worker_3_response"]
            
        nodes = []
        if r.get("needs_policy"):
            nodes.append("worker_1_policy")
        if r.get("needs_data"):
            nodes.append("worker_2_data")
            
        if not nodes:
            return ["worker_3_response"]
        return nodes
        
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        ["worker_1_policy", "worker_2_data", "worker_3_response"]
    )
    
    workflow.add_edge("worker_1_policy", "worker_3_response")
    workflow.add_edge("worker_2_data", "worker_3_response")
    workflow.add_edge("worker_3_response", END)
    
    return workflow.compile()
