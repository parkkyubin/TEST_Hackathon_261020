"""KPI 슬롯 — DESIGN §5.2 는 '제안(미승인)'. 승인 전까지 이 목록만 바꾸면 교체된다.
각 KPI 는 결과(dict) → {title, value, sources} 를 돌려주는 함수다. 값은 결과에서만 읽는다(하드코딩 금지, R7).
"""
from .model import m2t

APPROVED = False  # 사용자 승인 시 True 로 바꾸고 아래 슬롯을 확정한다
STATUS_NOTE = "KPI 구성: 제안(미승인) — DESIGN §5.2"


def k1_o_last_dep(res):
    j = next((x for x in res["judgments"] if x["id"] == "J-O-LASTDEP"), None)
    if not j or not j["data"].get("c_entry"):
        return {"title": "전망대 최종 출발", "value": "UNKNOWN", "sources": j["sources"] if j else []}
    d = j["data"]
    return {"title": f"전망대 최종 출발 (공연 {m2t(d['c_entry'])} 기준)",
            "value": f"{m2t(d['max_basis'])} (최대 소요) / {m2t(d['min_basis'])} (최소 소요)", "sources": j["sources"]}


def k2_p_last_dep_subway(res):
    sub = next((c for c in res["compare"] if c["mode"] == "subway"), None)
    if not sub:
        return {"title": "P 최종 출발 (지하철)", "value": "UNKNOWN", "sources": ["D02", "D03", "D06"]}
    from .conclude import safe_spans
    safe = [f"{m2t(a)}~{m2t(b)}" for a, b in safe_spans(sub)]
    return {"title": f"P 출발 SAFE 구간 (지하철, 전망대 도착 한도 {m2t(sub['deadline'])} 기준)",
            "value": ", ".join(safe) if safe else "없음",
            "sources": ["D03", "D06", "AP2", "U09"] + sub["binding"]["sources"]}


def k3_checks(res):
    hn = res["human_next"]
    first = hn[0] if hn else None
    return {"title": "확인 필요 항목 / 최근접 마감",
            "value": f"{len(hn)}건 / " + (first["when"] + " " + first["short"] if first else "없음"),
            "sources": list(dict.fromkeys(first["sources"])) if first else []}


SLOTS = [k1_o_last_dep, k2_p_last_dep_subway, k3_checks]


def build(res):
    return [f(res) for f in SLOTS[:3]]
