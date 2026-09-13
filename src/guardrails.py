"""
🛡️ SAFETY & ETHICAL GUARDRAILS SYSTEM
Bộ lọc an toàn và chuẩn mực nội dung cho Trợ lý Du lịch & Đặt phòng.
Bảo vệ hệ thống khỏi:
1. Nội dung khiêu dâm, mại dâm, 18+ (ADULT_NSFW)
2. Bạo lực, vũ khí, chất cấm, ma túy, cờ bạc phạm pháp (ILLEGAL_VIOLENCE)
3. Chính trị nhạy cảm, chống phá, kích động thù hận (POLITICS_HATE)
4. Tấn công vượt rào, tiêm nhiễm Prompt (PROMPT_INJECTION)
"""

import re
from typing import Tuple, Optional

# Danh mục từ khóa và mẫu nhận diện nội dung nhạy cảm
SENSITIVE_PATTERNS = {
    "ADULT_NSFW": [
        r"gái\s*gọi", r"mại\s*dâm", r"gái\s*bán\s*hoa", r"khiêu\s*dâm",
        r"karaoke\s*tay\s*vịn", r"phim\s*heo", r"phim\s*sex", r"chat\s*sex",
        r"gái\s*bao", r"sugar\s*baby", r"sugar\s*daddy", r"mua\s*dâm",
        r"bán\s*dâm", r"massage\s*từ\s*a\s*đến\s*z", r"massage\s*a-z",
        r"gái\s*xinh\s*đi\s*tour", r"tình\s*một\s*đêm", r"one\s*night\s*stand"
    ],
    "ILLEGAL_VIOLENCE": [
        r"ma\s*túy", r"thuốc\s*lắc", r"cần\s*sa", r"heroin", r"hàng\s*trắng",
        r"mua\s*vũ\s*khí", r"mua\s*súng", r"chế\s*tạo\s*bom", r"chế\s*tạo\s*thuốc\s*nổ",
        r"đánh\s*bạc", r"sòng\s*bạc\s*chui", r"buôn\s*lậu", r"rửa\s*tiền",
        r"thuê\s*giang\s*hồ", r"đâm\s*thuê\s*chém\s*mướn", r"tự\s*tử", r"tự\s*hại"
    ],
    "POLITICS_HATE": [
        r"lật\s*đổ\s*chính\s*quyền", r"chống\s*phá\s*nhà\s*nước", r"biểu\s*tình\s*bạo\s*động",
        r"phản\s*động", r"tuyên\s*truyền\s*chống\s*đảng", r"xúc\s*phạm\s*lãnh\s*tụ"
    ],
    "PROMPT_INJECTION": [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"bỏ\s*qua\s*(mọi\s*)?chỉ\s*dẫn\s*trước",
        r"you\s+are\s+now\s+dan",
        r"jailbreak",
        r"system\s*prompt\s*leak"
    ]
}

REFUSAL_MESSAGES = {
    "ADULT_NSFW": (
        "🛡️ **Từ chối yêu cầu**: Là Trợ lý Du lịch & Đặt phòng văn minh, tôi không cung cấp hoặc hỗ trợ các dịch vụ nhạy cảm, "
        "khiêu dâm hoặc không phù hợp với thuần phong mỹ tục. Tôi chỉ hỗ trợ thông tin danh lam thắng cảnh, ẩm thực, "
        "thời tiết và đặt phòng khách sạn lưu trú hợp pháp. Bạn có câu hỏi nào về du lịch lành mạnh không?"
    ),
    "ILLEGAL_VIOLENCE": (
        "🛡️ **Cảnh báo an toàn**: Yêu cầu của bạn có chứa nội dung liên quan đến hành vi vi phạm pháp luật, chất cấm "
        "hoặc bạo lực nguy hiểm. Hệ thống nghiêm cấm xử lý các thông tin này để bảo vệ an toàn cộng đồng."
    ),
    "POLITICS_HATE": (
        "🛡️ **Từ chối yêu cầu**: Là Trợ lý Du lịch & Nghỉ dưỡng, tôi chỉ tập trung vào thông tin hỗ trợ du khách trải nghiệm các điểm đến "
        "văn hóa, danh lam thắng cảnh và chỗ nghỉ, không tham gia thảo luận về các vấn đề chính trị nhạy cảm."
    ),
    "PROMPT_INJECTION": (
        "🛡️ **Cảnh báo bảo mật**: Phát hiện hành vi cố gắng can thiệp hoặc thay đổi cấu hình bảo mật của Tác tử ReAct. "
        "Yêu cầu đã bị chặn bởi hệ thống phòng vệ Guardrails."
    ),
    "DEFAULT": (
        "🛡️ **Từ chối yêu cầu**: Câu hỏi của bạn vi phạm chính sách nội dung an toàn của Trợ lý Du lịch. "
        "Vui lòng chỉ đặt các câu hỏi liên quan đến du lịch, điểm tham quan, ẩm thực, thời tiết và khách sạn lưu trú."
    )
}

def check_safety(query: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Kiểm tra an toàn nội dung của câu hỏi đầu vào.
    Trả về: (is_safe: bool, category: Optional[str], refusal_message: Optional[str])
    """
    if not query:
        return True, None, None
        
    query_lower = query.strip().lower()
    
    for category, patterns in SENSITIVE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, query_lower, re.IGNORECASE):
                refusal = REFUSAL_MESSAGES.get(category, REFUSAL_MESSAGES["DEFAULT"])
                return False, category, refusal
                
    return True, None, None
