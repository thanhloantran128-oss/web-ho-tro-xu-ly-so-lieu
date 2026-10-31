from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import ai
from app.main import app
from app.utils import LoiPhanTich

TTEST = {"analysis": "t-test", "type": "independent", "groups": [{"label": "Nam", "n": 87, "mean": 2.89}]}


class FakeClient:
    """Giả lập Claude: ghi lại tham số gọi và trả về câu trả lời cố định."""

    def __init__(self, stop_reason="end_turn", text="Giải thích…"):
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self._stop, self._text = stop_reason, text

    def _create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(
            stop_reason=self._stop, model=kw["model"],
            content=[SimpleNamespace(type="text", text=self._text)],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5,
                                  cache_read_input_tokens=0, cache_creation_input_tokens=10))


def test_loads_core_and_matching_skill_with_cache():
    fake = FakeClient()
    out = ai.explain(TTEST, "Kết quả này nghĩa là gì?", client=fake)
    call = fake.calls[0]
    system = call["system"][0]
    assert system["cache_control"] == {"type": "ephemeral"}
    assert "Nguyên tắc chung" in system["text"] and "Kiểm định t" in system["text"]
    assert "ANOVA" not in system["text"].split("---")[0]  # skill ANOVA không bị nạp
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert out["skill_da_dung"] == ["t-test"]


def test_scale_results_add_scale_skill():
    assert ai.skills_for({**TTEST, "thang_do": [{"ma": "PSS-10"}]}) == ["t-test", "cham-diem-thang-do"]
    assert ai.skills_for({"analysis": "thang-do"}) == ["cham-diem-thang-do"]


def test_system_prompt_is_identical_across_turns():
    assert ai.build_system(["t-test"]) == ai.build_system(["t-test"])


def test_results_only_in_first_turn():
    history = [{"role": "user", "content": "Câu 1"}, {"role": "assistant", "content": "Đáp 1"}]
    msgs = ai.build_messages(TTEST, "Câu 2", history)
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]
    assert '"analysis": "t-test"' in msgs[0]["content"] and msgs[0]["content"].endswith("Câu 1")
    assert msgs[2]["content"] == "Câu 2"


def test_invalid_history_and_empty_question_rejected():
    with pytest.raises(LoiPhanTich):
        ai.build_messages(TTEST, "  ", [])
    with pytest.raises(LoiPhanTich):
        ai.build_messages(TTEST, "Hỏi", [{"role": "assistant", "content": "x"}])


def test_refusal_returns_friendly_message():
    out = ai.explain(TTEST, "Hỏi", client=FakeClient(stop_reason="refusal", text=""))
    assert out["tra_loi"] == ai.TRA_LOI_KHI_TU_CHOI


def test_unknown_analysis_rejected():
    with pytest.raises(LoiPhanTich):
        ai.explain({"analysis": "hoi-quy"}, "Hỏi", client=FakeClient())


def test_endpoint_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = TestClient(app).post("/giai-thich", json={"ket_qua": TTEST, "cau_hoi": "Hỏi"})
    assert r.status_code == 503
