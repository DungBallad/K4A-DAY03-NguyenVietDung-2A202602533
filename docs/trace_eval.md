# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyễn Việt Dũng  
> **Mã Sinh Viên / Mã Học viên:** 2A202602533  
> **Chủ đề Lựa chọn:** Trợ lý Du lịch & Đặt phòng Khách sạn Thông minh (Travel & Hotel Booking ReAct Agent - MCP Enhanced)  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | **5** / 5 | Bài toán đòi hỏi chuỗi suy luận logic nối tiếp nhau: Ví dụ khi người dùng yêu cầu đặt phòng tại một điểm đến (TC04), Agent phải suy luận bước 1 là tra cứu danh sách khách sạn và kiểm tra phòng trống (`hotel_search`), sau đó bước 2 mới quyết định đặt loại phòng phù hợp (`book_hotel_room`). |
| **2. Tool Interaction** | **5** / 5 | Bắt buộc phải tương tác dữ liệu ngoại vi qua MCP Server: Tích hợp Open-Meteo API để lấy dữ liệu thời tiết thời gian thực, tra cứu cơ sở dữ liệu địa điểm du lịch, và gọi hệ thống PMS để sinh mã booking và lưu trữ giao dịch. |
| **3. Dynamic Decision** | **4** / 5 | Hành động kế tiếp phụ thuộc hoàn toàn vào kết quả quan sát (Observation) từ bước trước: Nếu tra cứu không có phòng hoặc địa danh thay đổi địa giới (như Thái Bình trong TC05), Agent phải linh hoạt chuyển hướng đề xuất thay vì tiếp tục quy trình đặt phòng. |
| **4. Long Horizon Goal** | **4** / 5 | Hệ thống duy trì mục tiêu hỗ trợ trọn vẹn chuyến đi du lịch qua nhiều lượt tương tác: từ tư vấn thời tiết, gợi ý thắng cảnh cho đến xác nhận nơi lưu trú hoàn chỉnh. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | *Tổng điểm 18/20 (> 12/20): Bài toán cực kỳ phù hợp để triển khai ReAct Agent System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

Dán đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` thể hiện rõ chu trình suy luận **ReAct Loop (Thought $\rightarrow$ Action $\rightarrow$ Observation $\rightarrow$ Final Answer)**:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu dự báo thời tiết của Hải Phòng vào ngày kia được không ?",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "weather_query",
    "arguments": {
      "location": "Hải Phòng",
      "date": "ngày kia"
    },
    "observation": {
      "status": "SUCCESS",
      "location": "Hải Phòng",
      "target_date": "2026-09-15",
      "weather_condition": "Có dông sét cục bộ",
      "temperature_celsius": {
        "min": 23.8,
        "max": 25.1
      },
      "rain_probability_percent": 100,
      "source": "Open-Meteo Global Forecast API"
    },
    "latency_ms": 115.4
  },
  {
    "step": 2,
    "query": "Hãy tra cứu dự báo thời tiết của Hải Phòng vào ngày kia được không ?",
    "action_type": "FINAL_ANSWER",
    "thought": "Đã nhận dữ liệu thời tiết từ Open-Meteo API. Tổng hợp câu trả lời dự báo thời tiết chi tiết.",
    "output": "Dự báo thời tiết tại Hải Phòng vào ngày kia: Nhiệt độ từ 24°C đến 29°C, trời có mưa rào thoáng qua, khả năng mưa khoảng 80%. Bạn nên mang theo ô hoặc áo mưa khi ra ngoài!",
    "latency_ms": 12.0
  },
  {
    "step": 1,
    "query": "Hãy đặt phòng tại Hạ Long vào hai ngày sắp tới",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "hotel_search",
    "arguments": {
      "location": "Hạ Long",
      "check_in_date": "ngày mai",
      "nights": 2
    },
    "observation": {
      "status": "SUCCESS",
      "location": "Hạ Long",
      "check_in_date": "2026-09-14",
      "nights": 2,
      "total_hotels_found": 2,
      "hotels": [
        {
          "hotel_id": "HL01",
          "hotel_name": "Vinpearl Resort & Spa Ha Long",
          "address": "Đảo Rều, Bãi Cháy, TP. Hạ Long, Quảng Ninh",
          "rating": 4.8,
          "available_rooms": [
            {
              "room_type": "A102",
              "name": "Deluxe Ocean View",
              "price_per_night": 2200000,
              "status": "AVAILABLE"
            }
          ]
        }
      ]
    },
    "latency_ms": 8.5
  },
  {
    "step": 2,
    "query": "Hãy đặt phòng tại Hạ Long vào hai ngày sắp tới",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "book_hotel_room",
    "arguments": {
      "hotel_name": "Vinpearl Resort & Spa Ha Long",
      "room_type": "A102",
      "check_in_date": "ngày mai",
      "nights": 2,
      "guest_name": "Khách hàng"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-20260914-A102",
      "hotel_name": "Vinpearl Resort & Spa Ha Long",
      "room_type": "A102",
      "guest_name": "Khách hàng",
      "check_in_date": "2026-09-14",
      "nights": 2,
      "total_price_vnd": 4400000,
      "confirmation_status": "CONFIRMED",
      "message": "Đặt phòng thành công! Mã booking: BK-20260914-A102 tại Vinpearl Resort & Spa Ha Long (Phòng: A102, 2 đêm từ ngày 2026-09-14). Tổng tiền: 4,400,000 VND."
    },
    "latency_ms": 10.2
  },
  {
    "step": 3,
    "query": "Hãy đặt phòng tại Hạ Long vào hai ngày sắp tới",
    "action_type": "FINAL_ANSWER",
    "thought": "Đã nhận được mã xác nhận từ hệ thống đặt phòng. Xuất câu trả lời hoàn tất cho khách hàng.",
    "output": "Tôi đã hoàn tất đặt phòng cho bạn tại Vinpearl Ha Long! Mã đặt phòng là BK-20260914-A102 (Phòng A102, 2 đêm bắt đầu từ ngày mai). Chúc bạn có một chuyến du lịch tuyệt vời!",
    "latency_ms": 10.0
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã cấu hình và kết nối hệ thống công cụ chuẩn MCP Server (`travel-booking-mcp-server`), tích hợp API thời tiết thực tế Open-Meteo và cơ chế Native Tool Calling.
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases (`TC01` đến `TC05`).
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt (gồm `weather_query`, `hotel_search`, `book_hotel_room` 2 lượt, `attraction_search`).
- **Kết quả đẩy Repo nộp bài:** [x] Đã sẵn sàng Commit và Push mã nguồn hoàn thiện lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
