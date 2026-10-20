"""LLM 호출부 — 이 모듈 하나로 격리 (R11, R12, D-8, TD4).
.env 의 ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY, LLM_MODEL 을 쓴다. 키 값은 어디에도 출력하지 않는다 (D-7).
LLM 은 구조화 결과의 요약만 만든다. 판정·수치 변경 금지 → 결과에 없는 시각·수치가 나오거나 린트 위반이면 폐기 (§3.4).
"""
import json
import os
import re

from . import lint

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SYSTEM = (
    "너는 여행 일정 도우미의 요약 작성기다. 주어진 JSON(규칙 엔진 결과)만 근거로 한국어 3~5문장 요약을 쓴다. "
    "판정(SAFE/AT_RISK/FAIL/UNKNOWN), 시각, 수치, 순서를 바꾸거나 새 수치를 만들지 않는다. 이동수단을 추천하지 않는다. "
    "예보·추정은 확정처럼 쓰지 않는다('반드시 비', '폐쇄됐다', '정확히 N분' 금지). 각 문장 끝에 근거 출처 ID를 [D02] 형식으로 붙인다."
)


def _load_env():
    try:
        from dotenv import load_dotenv
        # .env 가 개발 도구가 셸에 남긴 ANTHROPIC_* 값보다 우선 (G-03: 별개 계정)
        load_dotenv(os.path.join(ROOT, ".env"), override=True)
    except ImportError:
        pass


def _numbers(text):
    return set(re.findall(r"\d{1,2}:\d{2}", text)) | set(re.findall(r"(?<![\d:])\d+(?![\d:])", text))


def summarize(payload, timeout=20.0):
    _load_env()
    base, key, model = (os.environ.get(k, "").strip() for k in ("ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "LLM_MODEL"))
    res = {"status": "LLM 미연결", "text": "", "detail": ""}
    missing = [n for n, v in (("ANTHROPIC_BASE_URL", base), ("ANTHROPIC_API_KEY", key), ("LLM_MODEL", model)) if not v]
    if missing:
        res["detail"] = "환경변수 미설정: " + ", ".join(missing)
        return res
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key, base_url=base, timeout=timeout, max_retries=0)
        body = json.dumps(payload, ensure_ascii=False)
        msg = client.messages.create(model=model, max_tokens=600, system=SYSTEM,
                                     messages=[{"role": "user", "content": body}])
        text = "".join(getattr(b, "text", "") for b in msg.content).strip()
    except Exception as e:  # 키 오류·주소 오류·타임아웃 → 폴백 (R12)
        res["detail"] = f"{type(e).__name__}: " + str(e).replace(key, "***")[:200]
        return res
    if not text:
        res["detail"] = "빈 응답"
        return res
    hits = lint.check(text)
    if hits:
        res.update(status="LLM 요약 폐기(확정 표현)", detail="; ".join(h["match"] for h in hits))
        return res
    allowed = _numbers(json.dumps(payload, ensure_ascii=False))
    extra = sorted(n for n in _numbers(text) if n not in allowed)
    if extra:
        res.update(status="LLM 요약 폐기(결과에 없는 수치)", detail=", ".join(extra[:10]))
        return res
    res.update(status="LLM 연결됨", text=text)
    return res
