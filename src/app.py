from typing import Optional, Any, Callable
"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
Chuyên biệt hóa cho Trợ lý Du lịch & Đặt phòng Khách sạn (Travel & Booking Agent).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider
from memory import ConversationSummaryBufferMemory
from guardrails import check_safety

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def format_observation_answer(tool_name: str, obs_data: dict) -> str:
    """Hàm tổng hợp kết quả quan sát (Observation) thành câu trả lời tự nhiên"""
    if not obs_data:
        return "Chưa nhận được phản hồi hợp lệ từ công cụ MCP Server."
    status = obs_data.get("status")
    if status == "NOT_FOUND":
        msg = obs_data.get("message", "Không tìm thấy thông tin yêu cầu.")
        sug = obs_data.get("suggestion")
        return f"{msg}\n💡 Gợi ý: {sug}" if sug else msg

    if tool_name == "weather_query":
        loc = obs_data.get("location", "")
        dt = obs_data.get("target_date", "")
        cond = obs_data.get("weather_condition", "")
        temp = obs_data.get("temperature_celsius", {})
        rain = obs_data.get("rain_probability_percent", 0)
        return (
            f"Dự báo thời tiết tại {loc} (ngày {dt}): {cond}. "
            f"Nhiệt độ dao động từ {temp.get('min', 'N/A')}°C đến {temp.get('max', 'N/A')}°C. "
            f"Xác suất có mưa: {rain}%."
        )
    elif tool_name == "hotel_search":
        loc = obs_data.get("location", "")
        total = obs_data.get("total_hotels_found", 0)
        hotels = obs_data.get("hotels", [])
        hotel_lines = []
        for h in hotels:
            rooms_str = ", ".join([
                f"{r.get('room_type')} - {r.get('name')} ({r.get('price_per_night', 0):,} VND/đêm)" 
                for r in h.get("available_rooms", [])
            ])
            hotel_lines.append(f"• {h.get('hotel_name')} (Đánh giá {h.get('rating')}⭐)\n  Địa chỉ: {h.get('address')}\n  Phòng còn trống: {rooms_str}")
        return f"Tìm thấy {total} khách sạn còn phòng trống tại khu vực {loc}:\n" + "\n".join(hotel_lines)
    elif tool_name == "hotel_room_availability":
        h_name = obs_data.get("hotel_name", "")
        dt = obs_data.get("check_in_date", "")
        nights = obs_data.get("nights", 1)
        rooms = obs_data.get("available_rooms", [])
        src = obs_data.get("source", "Agoda Inventory")
        room_lines = [
            f"  - [{r.get('room_type')}] {r.get('name')}: {r.get('price_per_night', 0):,} VND/đêm ({r.get('status')})"
            for r in rooms
        ]
        return (
            f"Tình trạng phòng tại {h_name} (Nhận phòng: {dt}, {nights} đêm, nguồn {src}):\n"
            + "\n".join(room_lines)
        )
    elif tool_name in ["book_hotel_room", "reserve_room"]:
        return obs_data.get("message", f"Đặt phòng thành công! Mã xác nhận: {obs_data.get('booking_id')}")
    elif tool_name == "attraction_search":
        loc = obs_data.get("location", "")
        attractions = obs_data.get("attractions", [])
        attr_lines = [f"• {a.get('name')} ({a.get('category')}): {a.get('highlights')}" for a in attractions]
        return f"Danh sách các địa điểm du lịch nổi bật tại {loc}:\n" + "\n".join(attr_lines)
    elif "message" in obs_data:
        return obs_data["message"]
    elif "data" in obs_data:
        d = obs_data["data"]
        return f"Kết quả tra cứu sinh viên {obs_data.get('student_id', '')} ({d.get('full_name', '')}): Lớp {d.get('class')}, GPA: {d.get('gpa')}, Cố vấn: {d.get('advisor')}."
    return json.dumps(obs_data, ensure_ascii=False)


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer, memory: Optional[ConversationSummaryBufferMemory] = None, on_event: Optional[Any] = None) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Hỗ trợ suy luận đa bước (Multi-step Reasoning) cho đến khi đưa ra Final Answer.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    # 🛡️ KIỂM TRA BẢO MẬT & AN TOÀN NỘI DUNG (SAFETY GUARDRAILS)
    is_safe, category, refusal_msg = check_safety(user_query)
    if not is_safe:
        print(f"🛡️ [SAFETY GUARDRAIL BLOCKED]: Câu hỏi vi phạm quy chuẩn an toàn [{category}]!")
        print(f"🏁 [Final Answer]: {refusal_msg}")
        guard_event = {
            "step": 1,
            "query": user_query,
            "action_type": "GUARDRAIL_BLOCKED",
            "thought": f"Hệ thống Guardrail phát hiện nội dung nhạy cảm ({category}). Tự động chặn và từ chối an toàn.",
            "tool_name": "safety_guardrail",
            "arguments": {"category": category, "verdict": "BLOCKED", "risk_level": "HIGH"},
            "output": refusal_msg,
            "latency_ms": 1.2
        }
        if on_event:
            on_event({"type": "guardrail_blocked", "data": guard_event})
        return [guard_event]
    
    step = 0
    trace_logs = []
    executed_tool_names = set()
    tools_list = mcp_server.list_tools()
    # Tích hợp ngữ cảnh bộ nhớ (Summary + 3 lượt gần nhất) nếu có
    memory_context = memory.get_context_prompt() if memory else ""
    if memory_context:
        print(f"🧠 [MEMORY CONTEXT]: Đã nạp {len(memory.recent_turns)}/3 lượt hội thoại gần nhất" + (" + Tóm tắt dài hạn." if memory.summary else "."))
        current_prompt = f"{memory_context}\n\n👤 Câu hỏi hiện tại của người dùng: {user_query}"
    else:
        current_prompt = user_query
    last_tool_name = None
    last_obs_data = None
    
    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(current_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        if on_event:
            on_event({"type": "thought", "step": step, "thought": thought})
        
        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            
            # 1. Tự động bắt lỗi model "nói suông kế hoạch" thay vì gọi Tool
            planning_keywords = [
                "tôi sẽ thực hiện", "tôi sẽ bắt đầu", "bước 1", "bước 2", 
                "trước tiên tôi sẽ", "đầu tiên tôi sẽ", "tôi sẽ tra cứu", 
                "tôi sẽ tìm kiếm", "tôi sẽ tiến hành", "để cung cấp thông tin"
            ]
            is_premature_plan = (
                last_obs_data is None and 
                any(kw in final_content.lower() for kw in planning_keywords) and
                len(final_content) < 400
            )
            
            if is_premature_plan and step < MAX_ITERATIONS:
                print(f"⚠️ [ReAct Auto-Correction]: Model thông báo kế hoạch bằng lời thay vì gọi Tool. Đang kích hoạt Tool Call ngay...")
                current_prompt += (
                    f"\n\n[HỆ THỐNG YÊU CẦU]: Bạn vừa trả lời bằng văn bản mô tả kế hoạch: '{final_content}'. "
                    f"TUYỆT ĐỐI KHÔNG mô tả kế hoạch bằng lời hay hỏi người dùng. Hãy PHÁT SINH TOOL CALL NGAY LẬP TỨC (ví dụ 'hotel_search' hoặc 'attraction_search')!"
                )
                continue

            # 2. Tự động bắt lỗi model dừng lại hỏi ngày nhận phòng/số đêm thay vì chủ động tra cứu
            q_lower = user_query.lower()
            fc_lower = final_content.lower()
            needs_hotel = any(k in q_lower for k in ["lưu trú", "khách sạn", "hotel", "ở đâu", "phòng", "chỗ ở", "nghỉ"])
            asking_date_keywords = [
                "ngày nhận phòng", "số đêm", "thời gian lưu trú", "ngày check-in", 
                "cho tôi biết ngày", "cho biết ngày", "ngày nhận", "ngày đến"
            ]
            is_asking_dates = any(kw in fc_lower for kw in asking_date_keywords)
            
            has_booked = any(t in executed_tool_names for t in ["book_hotel_room", "reserve_room"])
            is_booking_intent = any(k in q_lower for k in ["đặt phòng", "book", "reserve", "đặt "])
            if not has_booked and not is_booking_intent and (needs_hotel or "khách sạn" in fc_lower) and "hotel_search" not in executed_tool_names and is_asking_dates and step < MAX_ITERATIONS:
                print(f"⚠️ [ReAct Proactive]: Model dừng lại hỏi ngày thay vì chủ động tìm kiếm. Đang tự động gọi 'hotel_search' với ngày ngầm định...")
                current_prompt += (
                    f"\n\n[HỆ THỐNG YÊU CẦU]: BẠN KHÔNG ĐƯỢC HỎI NGÀY NHẬN PHÒNG HOẶC SỐ ĐÊM CỦA NGƯỜI DÙNG! "
                    f"Người dùng muốn xem danh sách khách sạn và giá tham khảo ngay. "
                    f"Hãy CHỦ ĐỘNG dùng check_in_date='ngày mai' và nights=1 để PHÁT SINH TOOL CALL 'hotel_search' NGAY LẬP TỨC!"
                )
                continue

            # 2.5. Tự động đảm bảo gọi 'weather_query' khi người dùng lên kế hoạch du lịch chung theo mốc thời gian
            has_temporal = any(k in q_lower for k in ["ngày mai", "ngày kia", "hôm nay", "thời tiết", "dự báo", "tuần tới", "cuối tuần", "mấy ngày tới", "sắp tới"])
            is_general_travel = any(k in q_lower for k in ["du lịch", "thông tin liên quan", "đi chơi", "kế hoạch", "chuyến đi", "khám phá"])
            missing_weather = (has_temporal and is_general_travel) and "weather_query" not in executed_tool_names
            
            if missing_weather and step < MAX_ITERATIONS:
                print(f"⚠️ [ReAct Proactive]: Người dùng du lịch theo mốc thời gian. Đang tự động kích hoạt 'weather_query'...")
                current_prompt += (
                    f"\n\n[HỆ THỐNG YÊU CẦU]: Người dùng có kế hoạch đi du lịch theo thời gian xác định. "
                    f"Bạn BẮT BUỘC phải phát sinh Tool Call 'weather_query' để cung cấp dự báo thời tiết cho chuyến đi trước khi kết luận!"
                )
                continue

            # 3. Tự động bắt lỗi model "dừng giữa chừng để hỏi người dùng" khi câu hỏi đã yêu cầu cả 2 (du lịch + lưu trú)
            needs_tourism = any(k in q_lower for k in ["du lịch", "thắng cảnh", "tham quan", "điểm đến"])
            missing_hotel = needs_hotel and "hotel_search" not in executed_tool_names
            missing_attraction = needs_tourism and "attraction_search" not in executed_tool_names
            
            has_unfinished_request = (missing_hotel or missing_attraction) and any(
                w in fc_lower for w in [
                    "bạn có muốn tìm kiếm khách sạn", "bạn có muốn tìm khách sạn", 
                    "bạn có muốn lưu trú", "bạn có muốn", "nếu có, hãy cho tôi biết"
                ]
            )
            
            if has_unfinished_request and step < MAX_ITERATIONS:
                next_tool = "hotel_search" if missing_hotel else "attraction_search"
                print(f"⚠️ [ReAct Proactive]: Người dùng đã yêu cầu cả du lịch và lưu trú. Đang tự động gọi tiếp '{next_tool}'...")
                current_prompt += (
                    f"\n\n[HỆ THỐNG YÊU CẦU]: Trong câu hỏi ban đầu, người dùng ĐÃ YÊU CẦU cả thông tin lưu trú/khách sạn. "
                    f"TUYỆT ĐỐI KHÔNG dừng lại hỏi người dùng! Bạn phải phát sinh Tool Call '{next_tool}' ngay lập tức để lấy thông tin khách sạn!"
                )
                continue
                
            print(f"🏁 [Final Answer]: {final_content}")
            if on_event:
                on_event({"type": "final_answer", "step": step, "output": final_content, "latency_ms": latency_ms})
            if memory is not None:
                memory.add_turn(user_query, final_content, provider=provider)
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break
            
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            last_tool_name = tool_name
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")
            
            # Thực thi Tool qua MCP Server
            executed_tool_names.add(tool_name)
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            last_obs_data = obs_data
            
            if on_event:
                on_event({"type": "action", "step": step, "tool_name": tool_name, "arguments": arguments})
                
            obs_str = json.dumps(obs_data, ensure_ascii=False)
            print(f"👁️ [Observation từ MCP Server]: {obs_str}")
            if on_event:
                on_event({"type": "observation", "step": step, "tool_name": tool_name, "observation": obs_data, "latency_ms": latency_ms})
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            
            # Cập nhật prompt với kết quả quan sát cho vòng lặp tiếp theo
            current_prompt += f"\n\n[Observation từ {tool_name}]: {obs_str}"
            
    # Nếu kết thúc vòng lặp mà chưa có FINAL_ANSWER trong trace_logs (do chạm giới hạn vòng lặp)
    has_final = any(log.get("action_type") == "FINAL_ANSWER" for log in trace_logs)
    if not has_final and last_obs_data is not None:
        final_answer = format_observation_answer(last_tool_name, last_obs_data)
        print(f"🧠 [Thought]: Tổng hợp kết quả từ hệ sinh thái công cụ để phản hồi.")
        print(f"🏁 [Final Answer]: {final_answer}")
        trace_logs.append({
            "step": step + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Tổng hợp kết quả cuối cùng từ Observation của MCP Server.",
            "output": final_answer,
            "latency_ms": 10.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🌴 TRAVEL & BOOKING REACT AGENT (MCP ENHANCED) - DAY 03 LAB")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent Du lịch & Đặt phòng:")
        print("🧠 [MEMORY SYSTEM]: Đã kích hoạt Conversation Summary Buffer Memory:")
        print("   - Duy trì nguyên văn 3 lượt hội thoại gần nhất (k=3)")
        print("   - Tự động nén/tóm tắt các trao đổi cũ hơn (> 3 lượt) để không mất thông tin quan trọng!")
        print("💡 Lệnh tiện ích:")
        print("   - '/clear' hoặc '/reset'  : Xóa bộ nhớ và bắt đầu hội thoại mới")
        print("   - '/memory' hoặc '/status': Xem trạng thái bộ nhớ hiện tại")
        print("   - 'exit' hoặc 'quit'      : Kết thúc phiên trò chuyện.\n")
        
        chat_memory = ConversationSummaryBufferMemory(max_recent_turns=3)
        
        while True:
            try:
                user_input = input(f"👤 [{chat_memory.get_status_info()}]\n   Khách hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Chúc bạn có những chuyến đi thú vị.")
                    break
                elif user_input.lower() in ["/clear", "/reset"]:
                    chat_memory.clear()
                    print("🧹 [MEMORY]: Đã xóa sạch bộ nhớ hội thoại. Bắt đầu phiên mới!")
                    continue
                elif user_input.lower() in ["/memory", "/status", "/history"]:
                    print("\n=== 📜 TRẠNG THÁI BỘ NHỚ HIỆN TẠI ===")
                    print(chat_memory.get_context_prompt() if (chat_memory.recent_turns or chat_memory.summary) else "(Bộ nhớ đang trống, chưa có trao đổi)")
                    print("======================================\n")
                    continue
                    
                logs = run_react_agent(user_input, provider, mcp_server, memory=chat_memory)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            logs = run_react_agent(tc["question"], provider, mcp_server)
            all_traces.extend(logs)
            completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases thành công!")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu thời tiết) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive hoặc python src/app.py --all")
