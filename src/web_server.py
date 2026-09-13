"""
🚀 TRAVEL & BOOKING REACT AGENT - MODERN WEB UI & REAL-TIME OBSERVABILITY SERVER
Cung cấp:
- WebSocket (/ws/chat): Truyền luồng suy luận ReAct Loop theo thời gian thực (Real-time Streaming).
- REST API (/api/chat, /api/reset_memory, /api/history_traces).
- Split-Screen UI: Main Chat bên trái, Real-time Waterfall Trace bên phải.
"""

import os
import sys
import json
import time
import asyncio
from typing import Optional, List, Dict, Any

# Đảm bảo import được src/
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from providers import get_llm_provider
from mcp_server import MCPAcademicServer
from memory import ConversationSummaryBufferMemory
from app import run_react_agent, save_waterfall_trace

app = FastAPI(title="Travel & Booking ReAct Agent Web UI")

# Khởi tạo Singletons
provider = get_llm_provider()
mcp_server = MCPAcademicServer()
chat_memory = ConversationSummaryBufferMemory(max_recent_turns=3)

# Mount static folder
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(static_path, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()

# ==============================================================================
# ⚡ REAL-TIME WEBSOCKET ENDPOINT CHO STREAMING TRACE
# ==============================================================================
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    
    try:
        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            user_msg = data.get("message", "").strip()
            
            if not user_msg:
                continue
                
            start_time = time.time()
            event_queue = asyncio.Queue()
            
            def event_callback(event: dict):
                """Bridge luồng sự kiện từ ReAct Agent sang WebSocket Async Queue"""
                loop.call_soon_threadsafe(event_queue.put_nowait, event)
                
            async def run_agent_worker():
                """Chạy ReAct Agent trên worker thread riêng biệt để không block async loop"""
                traces = await asyncio.to_thread(
                    run_react_agent,
                    user_msg,
                    provider,
                    mcp_server,
                    chat_memory,
                    event_callback
                )
                save_waterfall_trace(traces)
                total_latency = round((time.time() - start_time) * 1000, 2)
                
                # Báo hiệu hoàn tất
                await event_queue.put({
                    "type": "complete",
                    "total_latency_ms": total_latency,
                    "memory": {
                        "status_text": chat_memory.get_status_info(),
                        "recent_turns": chat_memory.recent_turns,
                        "summary": chat_memory.summary
                    }
                })

            worker_task = asyncio.create_task(run_agent_worker())
            
            # Đọc và truyền từng sự kiện ngay khi phát sinh tới client
            while True:
                evt = await event_queue.get()
                await websocket.send_json(evt)
                if evt.get("type") in ["complete", "guardrail_blocked"]:
                    break
                    
            await worker_task

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"⚠️ [WebSocket Exception]: {e}")

# ==============================================================================
# REST API CHAT (FALLBACK)
# ==============================================================================
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message.strip()
    if not user_msg:
        return JSONResponse({"error": "Tin nhắn không được để trống"}, status_code=400)
    
    start_time = time.time()
    
    # Thực thi ReAct Agent có gắn bộ nhớ
    traces = run_react_agent(user_msg, provider, mcp_server, memory=chat_memory)
    save_waterfall_trace(traces)
    
    total_latency_ms = round((time.time() - start_time) * 1000, 2)
    
    # Tìm Final Answer hoặc Guardrail Output
    final_reply = "Đã hoàn tất xử lý."
    for t in reversed(traces):
        if t.get("action_type") in ["FINAL_ANSWER", "GUARDRAIL_BLOCKED"]:
            final_reply = t.get("output", "")
            break
            
    return {
        "reply": final_reply,
        "traces": traces,
        "total_latency_ms": total_latency_ms,
        "memory": {
            "status_text": chat_memory.get_status_info(),
            "recent_turns": chat_memory.recent_turns,
            "summary": chat_memory.summary
        }
    }

@app.post("/api/reset_memory")
async def reset_memory():
    chat_memory.clear()
    return {
        "status": "SUCCESS",
        "message": "Đã xóa sạch bộ nhớ hội thoại!",
        "memory": {
            "status_text": chat_memory.get_status_info(),
            "recent_turns": [],
            "summary": ""
        }
    }

@app.get("/api/memory")
async def get_memory():
    return {
        "status_text": chat_memory.get_status_info(),
        "recent_turns": chat_memory.recent_turns,
        "summary": chat_memory.summary
    }

@app.get("/api/history_traces")
async def get_history_traces():
    docs_trace = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "trace_waterfall.json")
    if os.path.exists(docs_trace):
        try:
            with open(docs_trace, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {"status": "SUCCESS", "data": data}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    return {"status": "NOT_FOUND", "data": []}

if __name__ == "__main__":
    print("🌴 Khởi động Travel & Booking ReAct Agent Web UI tại: http://127.0.0.1:8000")
    uvicorn.run("web_server:app", host="127.0.0.1", port=8000, reload=False)
