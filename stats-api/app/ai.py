"""Giải thích kết quả bằng Claude, dựa trên bộ skill trong skills-hs/.

- Chỉ gửi BẢNG KẾT QUẢ đã tính (JSON), không bao giờ gửi dữ liệu thô của học sinh.
- Chỉ nạp skill liên quan đến phép phân tích để giữ chi phí thấp.
- Phần skill (system prompt) không đổi giữa các lượt nên được cache.
"""
import json
import os
from pathlib import Path

import anthropic

from .utils import LoiPhanTich

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills-hs"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("CLAUDE_EFFORT", "medium")

SKILL_MAP = {
    "mo-ta": ["thong-ke-mo-ta"],
    "tan-suat": ["tan-suat"],
    "trung-binh": ["trung-binh-do-lech-chuan"],
    "t-test": ["t-test"],
    "anova": ["anova"],
    "thang-do": ["cham-diem-thang-do"],
    "nhieu-lua-chon": ["nhieu-lua-chon"],
    "bang-cheo": ["bang-cheo"],
    "tuong-quan": ["tuong-quan"],
}

DO_DAI_CAU_HOI_TOI_DA = 2000
SO_LUOT_TOI_DA = 10
KICH_THUOC_KET_QUA_TOI_DA = 60_000  # ký tự JSON

TRA_LOI_KHI_TU_CHOI = ("Xin lỗi, trợ lý chưa trả lời được câu hỏi này. "
                       "Bạn thử hỏi cách khác, hoặc hỏi giáo viên hướng dẫn nhé.")

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def skills_for(result: dict) -> list[str]:
    analysis = result.get("analysis")
    if analysis not in SKILL_MAP:
        raise LoiPhanTich(f"Chưa có skill giải thích cho phép phân tích '{analysis}'.")
    names = list(SKILL_MAP[analysis])
    # Kết quả có dùng điểm thang đo chuẩn thì cần thêm skill chấm điểm thang đo
    if result.get("thang_do") and "cham-diem-thang-do" not in names:
        names.append("cham-diem-thang-do")
    return names


def build_system(skill_names: list[str]) -> str:
    """Ghép _core.md và các skill theo thứ tự cố định để prompt cache khớp giữa các lượt."""
    parts = [(SKILL_DIR / "_core.md").read_text(encoding="utf-8")]
    for name in skill_names:
        parts.append((SKILL_DIR / name / "SKILL.md").read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def build_messages(result: dict, question: str, history: list[dict]) -> list[dict]:
    """Lượt đầu chứa bảng kết quả; các lượt sau là hỏi đáp nối tiếp."""
    question = (question or "").strip()
    if not question:
        raise LoiPhanTich("Bạn chưa nhập câu hỏi.")
    if len(question) > DO_DAI_CAU_HOI_TOI_DA:
        raise LoiPhanTich(f"Câu hỏi dài quá {DO_DAI_CAU_HOI_TOI_DA} ký tự.")
    history = history or []
    if len(history) > SO_LUOT_TOI_DA * 2:
        raise LoiPhanTich("Cuộc trò chuyện đã quá dài. Hãy bắt đầu lượt hỏi mới.")
    for i, turn in enumerate(history):
        expected = "user" if i % 2 == 0 else "assistant"
        if turn.get("role") != expected or not isinstance(turn.get("content"), str):
            raise LoiPhanTich("Lịch sử trò chuyện không hợp lệ.")

    payload = json.dumps(result, ensure_ascii=False, indent=1)
    if len(payload) > KICH_THUOC_KET_QUA_TOI_DA:
        raise LoiPhanTich("Bảng kết quả quá lớn để giải thích một lần. Hãy chọn ít biến hơn.")
    intro = f"Đây là bảng kết quả phân tích của tôi (định dạng JSON):\n\n{payload}\n\n"

    turns = history + [{"role": "user", "content": question}]
    messages = [{"role": t["role"], "content": t["content"]} for t in turns]
    messages[0]["content"] = intro + "Câu hỏi: " + messages[0]["content"]
    return messages


def explain(result: dict, question: str, history: list[dict] | None = None, client=None) -> dict:
    if not isinstance(result, dict) or "analysis" not in result:
        raise LoiPhanTich("Thiếu bảng kết quả phân tích.")
    # Lời giải thích tự động không cần gửi cho AI
    result = {k: v for k, v in result.items() if k != "giai_thich"}
    skill_names = skills_for(result)
    system = build_system(skill_names)
    messages = build_messages(result, question, history or [])
    client = client or get_client()

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": EFFORT},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    )

    if response.stop_reason == "refusal":
        text = TRA_LOI_KHI_TU_CHOI
    else:
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if response.stop_reason == "max_tokens":
            text += "\n\n(Câu trả lời bị cắt vì quá dài. Bạn hãy hỏi cụ thể hơn.)"
    usage = response.usage
    return {
        "tra_loi": text,
        "skill_da_dung": skill_names,
        "model": response.model,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", None),
        },
    }
