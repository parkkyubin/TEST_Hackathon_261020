"""확정 금지 표현 린트 (R8, D-4). 패턴은 D08 예시와 그 동형에서만 도출한다 (DESIGN §3.4).
D08: "오후에는 반드시 비가 온다", "전망대 야외 데크가 폐쇄됐다", "교통 지연이 정확히 30분이다".
"""
import re

BANNED = [
    (re.compile(r"반드시\s*\S{0,6}\s*(비|온다|내린)"), "D08: 강수 단정 ('반드시 비')"),
    (re.compile(r"폐쇄\s*(됐|되었|된다|되었습니다|됐습니다)"), "D08: 데크 폐쇄 단정 ('폐쇄됐다')"),
    (re.compile(r"정확히\s*\d+\s*분"), "D08: 지연 단정 ('정확히 N분')"),
]


def check(text):
    hits = []
    for rx, why in BANNED:
        for m in rx.finditer(text or ""):
            hits.append({"match": m.group(0), "reason": why})
    return hits


def check_all(texts):
    out = []
    for t in texts:
        h = check(t)
        if h:
            out.append({"text": t, "hits": h})
    return out
