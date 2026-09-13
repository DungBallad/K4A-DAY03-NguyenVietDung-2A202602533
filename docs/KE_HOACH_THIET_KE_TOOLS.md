# 🧭 KẾ HOẠCH & ĐẶC TẢ THIẾT KẾ CÁC CÔNG CỤ (TOOLS) CHO REACT TRAVEL & BOOKING AGENT
**Dự án:** Trợ lý Du lịch & Đặt phòng Khách sạn Thông minh (Bài Lab 3 - K4A/K4B)  
**Tác giả / Học viên:** Nguyễn Viết Dũng - MSSV: 2A202602533  
**Kiến trúc:** ReAct Agent (Thought $\rightarrow$ Action $\rightarrow$ Observation) + Model Context Protocol (MCP)

---

## 📌 1. TỔNG QUAN HỆ THỐNG & MỤC TIÊU BÀI LAB

Hệ thống được thiết kế theo cấp độ **AI System Cấp 3 (ReAct Agent - MCP Enhanced)**, nâng cấp từ Chatbot đơn thuần sang Agent thông minh có khả năng suy luận đa bước, tra cứu dữ liệu thời gian thực và thực thi tác vụ ghi nhận dữ liệu (Transactional Action).

### 4 Nghiệp vụ Công cụ (Tools) Cốt lõi:
1. **Tra cứu thời tiết (`weather_query`):** Lấy dữ liệu nhiệt độ, tình trạng mưa/nắng tại địa phương và mốc thời gian cụ thể để người dùng lên lịch trình du lịch.
2. **Tra cứu thông tin khách sạn (`hotel_search`):** Tìm kiếm khách sạn theo khu vực, thời gian lưu trú, phân hạng sao, giá tiền và tình trạng phòng trống.
3. **Tra cứu địa điểm du lịch (`attraction_search`):** Gợi ý danh lam thắng cảnh, di tích lịch sử, địa điểm vui chơi giải trí và ẩm thực địa phương.
4. **Đặt phòng (`book_hotel_room`):** Tác vụ thay đổi trạng thái (State-changing Action), kiểm tra tính khả dụng, tạo mã đặt phòng (`booking_id`) và lưu vết giao dịch vào hệ thống PMS.

---

## 🌐 2. KHẢO SÁT & LỰA CHỌN API / NỀN TẢNG (PLATFORM & API EVALUATION)

Để đảm bảo việc triển khai vừa nhanh chóng, vừa ổn định trong môi trường kiểm thử tự động (không gặp lỗi hết hạn ngạch API key hay bắt nhập thẻ tín dụng):

| Nghiệp vụ | Nền tảng / API Đề xuất | Phương thức / Endpoint | Đặc điểm kỹ thuật & Ưu điểm |
| :--- | :--- | :--- | :--- |
| **1. Thời tiết** | **Open-Meteo API**<br>*(open-meteo.com)* | • Geocoding:<br>`https://geocoding-api.open-meteo.com/v1/search?name={city}`<br>• Forecast:<br>`https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min` | • **100% Miễn phí, KHÔNG CẦN API KEY**.<br>• Phủ sóng toàn cầu (Việt Nam: Hải Phòng, Hạ Long, Hà Nội, Đà Nẵng...).<br>• Độ trễ cực thấp (< 100ms).<br>• Có lớp Fallback cục bộ khi offline. |
| **2. Khách sạn** | **In-Memory Hotel Catalog / PMS Engine** *(Hỗ trợ mở rộng OpenStreetMap)* | • In-Memory Service hoặc SQLite database cục bộ.<br>• Tương thích chuẩn dữ liệu OTA (Booking/Agoda). | • Không rào cản xác thực thanh toán.<br>• Quản lý trực tiếp cấu trúc phòng trống (`available_rooms`), bảng giá, hạng phòng.<br>• Cho phép Agent suy luận liên kết bước 2 trong TC04 (Tra cứu $\rightarrow$ Đặt phòng). |
| **3. Địa điểm du lịch** | **Curated Vietnam Tourism Knowledge Base** + **Wikidata API** | • Wikidata SPARQL / REST API (Open)<br>• Structured Tourism Knowledge Base | • Nhanh, chuẩn xác về địa danh Việt Nam.<br>• Dễ dàng kiểm soát các tình huống biên (Edge-case TC05: Tỉnh đã sáp nhập/địa giới thay đổi như Thái Bình / Hưng Yên). |
| **4. Đặt phòng** | **Mock PMS (Property Management System) Engine** | • Transactional State Engine nội bộ qua MCP Server. | • Quản lý vòng đời đặt phòng: Nhận yêu cầu $\rightarrow$ Kiểm tra phòng trống $\rightarrow$ Giữ phòng $\rightarrow$ Trả về `booking_id` duy nhất (`BK-HL-2026-XXXX`).<br>• Đảm bảo tính nhất quán dữ liệu (Idempotency). |

---

## 🛠️ 3. ĐẶC TẢ CHI TIẾT 4 TOOL SCHEMAS (JSON SCHEMA CHUẨN NATIVE)

### 3.1. Tool 1: `weather_query` (Tra cứu thời tiết)
- **Tên công cụ:** `weather_query`
- **Mục đích:** Tra cứu dự báo thời tiết tại khu vực và thời gian xác định.
- **Khai báo JSON Schema:**
```json
{
  "name": "weather_query",
  "description": "Tra cứu thông tin dự báo thời tiết tại một khu vực/thành phố và ngày cụ thể.",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "Tên thành phố hoặc khu vực cần tra cứu thời tiết (ví dụ: 'Hải Phòng', 'Hạ Long', 'Hà Nội')"
      },
      "date": {
        "type": "string",
        "description": "Ngày cần tra cứu (ví dụ: '2026-09-15', 'ngày mai', 'ngày kia'). Nếu để trống sẽ tra cứu ngày hiện tại."
      }
    },
    "required": ["location"]
  }
}
```
- **Mẫu dữ liệu trả về từ MCP Server (Observation Result):**
```json
{
  "status": "SUCCESS",
  "location": "Hải Phòng",
  "date": "2026-09-15",
  "weather": "Nắng nhẹ, mây rải rác",
  "temp_min_c": 26.5,
  "temp_max_c": 32.0,
  "humidity_percent": 75,
  "rain_probability_percent": 15
}
```

---

### 3.2. Tool 2: `hotel_search` (Tra cứu khách sạn)
- **Tên công cụ:** `hotel_search`
- **Mục đích:** Tra cứu danh sách các khách sạn, loại phòng trống và bảng giá theo khu vực.
- **Khai báo JSON Schema:**
```json
{
  "name": "hotel_search",
  "description": "Tra cứu danh sách khách sạn, tình trạng phòng trống và mức giá tại một khu vực.",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "Tên địa phương hoặc khu vực cần tìm khách sạn (ví dụ: 'Hạ Long', 'Hải Phòng')"
      },
      "check_in_date": {
        "type": "string",
        "description": "Ngày dự kiến nhận phòng (ví dụ: '2026-09-14')"
      },
      "nights": {
        "type": "integer",
        "description": "Số đêm lưu trú dự kiến (mặc định: 1)"
      },
      "max_price": {
        "type": "number",
        "description": "Mức giá tối đa cho mỗi đêm bằng VND (tuỳ chọn)"
      }
    },
    "required": ["location"]
  }
}
```
- **Mẫu dữ liệu trả về từ MCP Server (Observation Result):**
```json
{
  "status": "SUCCESS",
  "location": "Hạ Long",
  "total_found": 2,
  "hotels": [
    {
      "hotel_name": "Vinpearl Resort & Spa Ha Long",
      "address": "Đảo Rều, Bãi Cháy, TP. Hạ Long",
      "rating": 4.8,
      "available_rooms": [
        {"room_type": "A102", "name": "Deluxe Ocean View", "price_per_night": 2200000, "available": true},
        {"room_type": "B201", "name": "Executive Suite", "price_per_night": 3500000, "available": true}
      ]
    },
    {
      "hotel_name": "Muong Thanh Luxury Ha Long Centre",
      "address": "Bãi Cháy, TP. Hạ Long",
      "rating": 4.5,
      "available_rooms": [
        {"room_type": "C301", "name": "Superior Double", "price_per_night": 1400000, "available": true}
      ]
    }
  ]
}
```

---

### 3.3. Tool 3: `attraction_search` (Tra cứu địa điểm du lịch)
- **Tên công cụ:** `attraction_search`
- **Mục đích:** Tra cứu thông tin danh lam thắng cảnh, khu vui chơi, văn hóa địa phương và xử lý các trường hợp đặc biệt về địa giới.
- **Khai báo JSON Schema:**
```json
{
  "name": "attraction_search",
  "description": "Tra cứu các địa điểm du lịch, danh lam thắng cảnh và hoạt động giải trí tại một địa phương.",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "Tên tỉnh, thành phố hoặc địa danh du lịch (ví dụ: 'Hạ Long', 'Thái Bình', 'Hải Phòng')"
      },
      "category": {
        "type": "string",
        "description": "Loại hình du lịch (ví dụ: 'biển đảo', 'di tích', 'văn hóa', 'ẩm thực')"
      }
    },
    "required": ["location"]
  }
}
```
- **Mẫu dữ liệu trả về thông thường:**
```json
{
  "status": "SUCCESS",
  "location": "Hạ Long",
  "attractions": [
    {"name": "Vịnh Hạ Long", "type": "Di sản thiên nhiên thế giới", "highlights": "Du thuyền ngắm cảnh, Hang Sửng Sốt, Đảo Ti Tốp"},
    {"name": "Bảo tàng Quảng Ninh", "type": "Văn hóa & Kiến trúc", "highlights": "Kiến trúc than đá độc đáo, trưng bày lịch sử mỏ"},
    {"name": "Sun World Halong Complex", "type": "Giải trí", "highlights": "Cáp treo Nữ Hoàng, Vòng quay Mặt Trời, Công viên Rồng"}
  ]
}
```
- **Mẫu dữ liệu trả về Edge-case (TC05 - Thái Bình):**
```json
{
  "status": "NOT_FOUND",
  "location": "Thái Bình",
  "message": "Không tìm thấy danh mục du lịch độc lập cho Thái Bình trong hệ sinh thái mới. Tỉnh này đã được điều chỉnh địa giới hành chính, hiện tại các thông tin dịch vụ liên quan đã được sáp nhập và quy hoạch chung cùng khu vực Hưng Yên.",
  "suggestion": "Bạn có thể tra cứu thông tin du lịch và lưu trú tại Hưng Yên hoặc Hải Phòng lân cận."
}
```

---

### 3.4. Tool 4: `book_hotel_room` (Đặt phòng)
- **Tên công cụ:** `book_hotel_room`
- **Mục đích:** Khởi tạo yêu cầu đặt phòng, xác nhận giữ chỗ và xuất biên nhận đặt phòng.
- **Khai báo JSON Schema:**
```json
{
  "name": "book_hotel_room",
  "description": "Thực hiện đặt phòng tại một khách sạn cụ thể theo thời gian lưu trú và loại phòng.",
  "parameters": {
    "type": "object",
    "properties": {
      "hotel_name": {
        "type": "string",
        "description": "Tên khách sạn muốn đặt phòng (ví dụ: 'Vinpearl Ha Long' hoặc 'Vinpearl Resort & Spa Ha Long')"
      },
      "room_type": {
        "type": "string",
        "description": "Mã phòng hoặc loại phòng muốn đặt (ví dụ: 'A102', 'Deluxe Ocean View')"
      },
      "check_in_date": {
        "type": "string",
        "description": "Ngày nhận phòng (ví dụ: '2026-09-14' hoặc mốc ngày 'ngày mai')"
      },
      "nights": {
        "type": "integer",
        "description": "Số đêm lưu trú (ví dụ: 2)"
      },
      "guest_name": {
        "type": "string",
        "description": "Họ tên khách lưu trú (mặc định: 'Khách hàng')"
      }
    },
    "required": ["hotel_name", "check_in_date"]
  }
}
```
- **Mẫu dữ liệu phản hồi xác nhận đặt phòng:**
```json
{
  "status": "SUCCESS",
  "booking_id": "BK-HL-20260914-A102",
  "hotel_name": "Vinpearl Resort & Spa Ha Long",
  "room_type": "A102 (Deluxe Ocean View)",
  "guest_name": "Khách hàng",
  "check_in_date": "2026-09-14",
  "nights": 2,
  "total_price_vnd": 4400000,
  "confirmation_status": "CONFIRMED",
  "message": "Đặt phòng thành công! Mã xác nhận: BK-HL-20260914-A102 tại Vinpearl Resort & Spa Ha Long (Phòng A102, 2 đêm từ ngày 2026-09-14)."
}
```

---

## 🔄 4. BẢNG ÁNH XẠ KIỂM THỬ (MAPPING 5 TEST CASES)

Các công cụ trên đáp ứng chính xác 5 test cases trong `config/test_cases.json`:

| Mã Test Case | Loại Test Case | Câu hỏi người dùng | Luồng ReAct Agent & Công cụ sử dụng |
| :---: | :--- | :--- | :--- |
| **TC01** | `direct_query` | "Chào bạn, bạn có thể giới thiệu về tác dụng của bạn được không ?" | Trả lời trực tiếp từ System Prompt, **không gọi Tool** (`action_type: FINAL_ANSWER`). |
| **TC02** | `single_tool_query` | "Hãy tra cứu dự báo thời tiết của Hải Phòng vào ngày kia được không ?" | Gọi **1 công cụ**: `weather_query(location='Hải Phòng', date='ngày kia')`. |
| **TC03** | `appointment_booking` | "Đặt phòng A102 tại khách sạn Vinpearl Ha Long bắt đầu từ ngày mai và ở lại 2 ngày" | Gọi **1 công cụ đặt phòng**: `book_hotel_room(hotel_name='Vinpearl Ha Long', room_type='A102', check_in_date='ngày mai', nights=2)`. |
| **TC04** | `multi_step_reasoning` | "Hãy đặt phòng tại Hạ Long vào hai ngày sắp tới" | **Suy luận 2 bước liên tiếp:**<br>1. Bước 1: `hotel_search(location='Hạ Long', nights=2)` để tra cứu phòng trống.<br>2. Bước 2: `book_hotel_room(...)` dựa trên phòng trống vừa tìm được. |
| **TC05** | `edge_case_handling` | "Hãy tra cứu thông tin du lịch của Thái Bình" | Gọi `attraction_search(location='Thái Bình')` $\rightarrow$ Nhận `NOT_FOUND` và phản hồi lịch sự theo quy hoạch địa giới mới. |

---

## 🏛️ 5. KIẾN TRÚC MÔ-ĐUN TRONG CODEBASE BÀI LAB

```
.
├── config/
│   └── test_cases.json         # Danh sách 5 test cases thực tế đã hoàn thiện
├── docs/
│   ├── CODELAB.md              # Đề bài gốc của môn học
│   ├── KE_HOACH_THIET_KE_TOOLS.md # Bản đặc tả kỹ thuật này
│   ├── trace_eval.md           # Báo cáo đánh giá Agentic Fit & Nghiệm thu
│   └── trace_waterfall.json    # File vết thực thi chi tiết (Thought -> Action -> Observation)
├── src/
│   ├── tools.py                # 4 Tool Schemas chuẩn JSON Schema & Execution Layer
│   ├── mcp_server.py           # Model Context Protocol Server (travel-booking-mcp-server)
│   ├── prompts.py              # System Prompts định hướng ReAct cho Agent du lịch
│   ├── providers.py            # Hỗ trợ Gemini, OpenAI và Fallback Mock
│   └── app.py                  # Vòng lặp ReAct Loop đa bước & Xuất Waterfall Trace Log
└── requirements.txt            # Thư viện: google-genai, openai, requests, python-dotenv...
```

---

## 📋 6. KẾ HOẠCH BÀN GIAO & TIÊU CHÍ NGHIỆM THU

1. **Khởi chạy độc lập MCP Server:**
   ```bash
   python src/mcp_server.py
   ```
   *Kết quả mong đợi:* Hiển thị đủ 4 công cụ đăng ký thành công qua chuẩn giao thức MCP JSON-RPC 2.0.
2. **Chạy nghiệm thu toàn bộ 5 Test Cases:**
   ```bash
   python src/app.py --all
   ```
   *Kết quả mong đợi:* Cả 5 test cases vượt qua hoàn hảo, xuất file `docs/trace_waterfall.json` thể hiện rõ độ trễ (latency) và các bước ReAct.
3. **Thử nghiệm tương tác người dùng (Interactive CLI):**
   ```bash
   python src/app.py --interactive
   ```
   *Kết quả mong đợi:* Cho phép người dùng chat trực tiếp, yêu cầu tra cứu và đặt phòng tự nhiên.
