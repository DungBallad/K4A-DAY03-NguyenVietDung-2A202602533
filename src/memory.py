"""
🧠 CONVERSATION SUMMARY BUFFER MEMORY (K=3)
Quản lý bộ nhớ hội thoại thông minh cho ReAct Agent:
- Lưu trữ 3 lượt trao đổi gần nhất nguyên văn (k=3 Buffer Window).
- Tự động tóm tắt các lượt cũ hơn (Conversation Summary) để không bị trôi thông tin dài hạn và không làm phình Token.
"""

from typing import List, Dict, Any, Optional

class ConversationSummaryBufferMemory:
    def __init__(self, max_recent_turns: int = 3):
        self.max_recent_turns = max_recent_turns
        self.recent_turns: List[Dict[str, str]] = []
        self.summary: str = ""

    def add_turn(self, user_query: str, assistant_response: str, provider=None):
        """
        Thêm một lượt trao đổi mới (User - Assistant).
        Nếu vượt quá max_recent_turns (3 lượt), lượt cũ nhất sẽ được nén vào bản tóm tắt (Summary).
        """
        if len(self.recent_turns) >= self.max_recent_turns:
            # Lượt cũ nhất sắp bị đẩy ra khỏi cửa sổ 3 lượt
            oldest_turn = self.recent_turns.pop(0)
            self._update_summary(oldest_turn, provider)

        self.recent_turns.append({
            "user": user_query.strip(),
            "assistant": assistant_response.strip()
        })

    def _update_summary(self, old_turn: Dict[str, str], provider=None):
        """Tóm tắt lượt cũ vào bản Summary tích lũy"""
        old_u = old_turn["user"]
        old_a = old_turn["assistant"][:250].replace("\n", " ")

        summary_prompt = (
            f"Bạn là bộ phận quản lý bộ nhớ của AI Trợ lý Du lịch.\n"
            f"Dưới đây là bản tóm tắt ngữ cảnh trước đó:\n\"{self.summary if self.summary else 'Chưa có'}\"\n\n"
            f"Lượt trao đổi cũ vừa diễn ra:\n"
            f"- Người dùng: {old_u}\n"
            f"- Trợ lý: {old_a}\n\n"
            f"Nhiệm vụ: Hãy cập nhật lại bản tóm tắt ngắn gọn (tối đa 2-3 gạch đầu dòng, dưới 50 từ) "
            f"giữ lại các thông tin cốt lõi quan trọng: địa điểm người dùng muốn đi, sở thích/yêu cầu đặc biệt, ngân sách, số người, hoặc khách sạn/mã đặt phòng đã xác nhận. "
            f"Chỉ trả về nội dung tóm tắt, không giải thích."
        )

        try:
            if provider and hasattr(provider, "generate"):
                new_summary = provider.generate(summary_prompt).strip()
                if new_summary and not new_summary.startswith("[") and len(new_summary) > 5:
                    self.summary = new_summary
                    return
        except Exception:
            pass

        # Fallback tóm tắt cục bộ khi không gọi được LLM
        item = f"• Khách đã quan tâm/trao đổi: '{old_u[:50]}...'"
        if not self.summary:
            self.summary = item
        else:
            self.summary = f"{self.summary}\n{item}"

    def get_context_prompt(self) -> str:
        """Định dạng toàn bộ ngữ cảnh bộ nhớ (Summary + 3 lượt gần nhất) để đưa vào Prompt"""
        if not self.summary and not self.recent_turns:
            return ""

        parts = []
        if self.summary:
            parts.append("--- 📜 TỔNG HỢP THÔNG TIN CÁC TRAO ĐỔI TRƯỚC ĐÓ (Long-term Context) ---")
            parts.append(self.summary.strip())
            parts.append("--------------------------------------------------------------------")

        if self.recent_turns:
            parts.append("--- 💬 CÁC LƯỢT HỘI THOẠI CHI TIẾT GẦN NHẤT (Recent Dialogues) ---")
            for idx, turn in enumerate(self.recent_turns, 1):
                assistant_snippet = turn["assistant"]
                if len(assistant_snippet) > 400:
                    assistant_snippet = assistant_snippet[:380] + "...\n[Đã cung cấp chi tiết ở trên]"
                parts.append(f"[Lượt {idx}]:")
                parts.append(f"  👤 Khách: {turn['user']}")
                parts.append(f"  🤖 Trợ lý: {assistant_snippet}")
            parts.append("-------------------------------------------------------------------")

        return "\n".join(parts)

    def clear(self):
        """Xóa trắng bộ nhớ"""
        self.recent_turns = []
        self.summary = ""

    def get_status_info(self) -> str:
        """Hiển thị trạng thái bộ nhớ cho người dùng"""
        total_recent = len(self.recent_turns)
        summary_lines = len(self.summary.splitlines()) if self.summary else 0
        return f"Bộ nhớ: {total_recent}/3 lượt chi tiết | Tóm tắt dài hạn: {'Có (' + str(summary_lines) + ' dòng)' if self.summary else 'Chưa có'}"
