"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
Hỗ trợ giao thức MCP JSON-RPC 2.0 cho Travel & Booking Agent và Academic Agent.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPAcademicServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol (MCP)
    """
    def __init__(self, server_name: str = "travel-booking-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        [TASK 2.1] HỌC VIÊN HOÀN THIỆN HÀM THỰC THI TOOL TRÊN MCP SERVER
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC 2.0
        """
        # 1. Gọi hàm dispatch_tool_call(tool_name, arguments) để lấy kết quả từ Tool Router
        raw_result_str = dispatch_tool_call(tool_name, arguments)
        
        # 2. Chuyển đổi chuỗi JSON kết quả thành Python Dictionary
        try:
            content = json.loads(raw_result_str)
        except Exception:
            content = {"status": "RAW_TEXT", "output": raw_result_str}
            
        # 3. Đóng gói phản hồi và trả về Dict theo đúng chuẩn giao thức MCP JSON-RPC 2.0
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (travel-booking-mcp-server)")
    print("==========================================================")
    
    server = MCPAcademicServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")
    
    # In danh sách các công cụ được công bố
    for idx, t in enumerate(tools, 1):
        print(f"   {idx}. {t.get('name')}: {t.get('description')}")
    print()

    # Kiểm tra trạng thái TODO 1.2 (Tool Schema)
    sched_tool = next((t for t in tools if t.get("name") == "schedule_appointment"), None)
    if sched_tool and not sched_tool.get("parameters", {}).get("properties"):
        print("⏳ [TODO 1.2]: Tool 'schedule_appointment' chưa được định nghĩa properties trong 'src/tools.py'.")
    else:
        print("✅ [TODO 1.2]: Tool 'schedule_appointment' đã có schema đầy đủ.")

    # Kiểm tra trạng thái TODO 2.1 (call_tool)
    print("\n--- 🧪 TEST DISPATCH TOOL QUA GIAO THỨC MCP JSON-RPC 2.0 ---")
    
    # Test 1: weather_query
    test_weather = server.call_tool("weather_query", {"location": "Hải Phòng", "date": "ngày mai"})
    print(f"✅ [MCP Result - weather_query]:")
    print(f"   {json.dumps(test_weather, ensure_ascii=False, indent=2)}")
    
    # Test 2: hotel_search
    test_hotel = server.call_tool("hotel_search", {"location": "Hạ Long", "nights": 2})
    print(f"\n✅ [MCP Result - hotel_search]:")
    print(f"   {json.dumps(test_hotel, ensure_ascii=False, indent=2)}")

    # Test 3: book_hotel_room
    test_booking = server.call_tool("book_hotel_room", {
        "hotel_name": "Vinpearl Resort & Spa Ha Long",
        "room_type": "A102",
        "check_in_date": "ngày mai",
        "nights": 2
    })
    print(f"\n✅ [MCP Result - book_hotel_room]:")
    print(f"   {json.dumps(test_booking, ensure_ascii=False, indent=2)}")
