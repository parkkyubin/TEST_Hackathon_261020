"""입력 → 판단 → 결론 → WHY → Human next (+LLM 요약, 린트). UI·CLI 가 같은 함수를 쓴다 (결과 일치)."""
from .model import Input, InputError, m2t
from . import engine, conclude, lint, llm_client


def _texts(res):
    for k in ("conclusion", "why", "unknown", "human_next", "actions"):
        for i in res[k]:
            yield i["text"]
    for k in res["kpi"]:
        yield k["title"] + " " + k["value"]


def run(data, use_llm=True):
    try:
        inp = Input(data)
    except InputError as e:
        return {"ok": False, "errors": e.errors}
    try:
        ev = engine.evaluate(inp)
        res = conclude.build(inp, ev)
    except Exception as e:  # 예상 못 한 입력 조합 — 죽지 않고 의미 있는 메시지로 (2단계 stress)
        return {"ok": False, "errors": [f"계산 중 오류: {type(e).__name__}: {e}"]}
    res["ok"] = True
    res["lint"] = lint.check_all(list(_texts(res)))
    if res["lint"]:  # 규칙 출력에서 위반이 나오면 해당 문장을 가린다
        bad = {v["text"] for v in res["lint"]}
        for k in ("conclusion", "why", "unknown", "human_next", "actions"):
            res[k] = [i for i in res[k] if i["text"] not in bad]
    if use_llm:
        payload = {k: [{"text": i["text"], "sources": i["sources"]} for i in res[k]]
                   for k in ("conclusion", "why", "unknown", "human_next")}
        payload["kpi"] = res["kpi"]
        res["llm"] = llm_client.summarize(payload)
    else:
        res["llm"] = {"status": "LLM 미사용", "text": "", "detail": "사용자가 LLM 요약을 끔"}
    return res


def fmt_interval(r):
    rng = "자료 없음" if r["range"] is None else f"{r['range'][0]}~{r['range'][1]}분"
    ov = " · 점검 겹침→D06 범위 적용" if r["overlap"] else ""
    why = f" ({r['why']})" if r["why"] else ""
    return f"{m2t(r['from'])}~{m2t(r['to'])} 출발: {r['status']} · {rng}{ov}{why}"


def to_text(res):
    if not res.get("ok"):
        return "입력 오류:\n" + "\n".join(f"- {e}" for e in res["errors"])
    src = lambda i: " [" + "][".join(i["sources"]) + "]"
    L = [f"■ 결론  ({res['badge']} — {res['badge_note']})"] + [f"  {i['text']}{src(i)}" for i in res["conclusion"]]
    L += ["", f"■ KPI  ({res['kpi_note']})"] + [f"  - {k['title']}: {k['value']}{src(k)}" for k in res["kpi"]]
    L += ["", "■ WHY"] + [f"  - {i['text']}{src(i)}" for i in res["why"]]
    L += ["", "■ UNKNOWN (상위 3)"] + [f"  - {i['text']}{src(i)}" for i in res["unknown"][:3]]
    L += ["", "■ HUMAN NEXT (상위 3)"] + [f"  - {i['text']}{src(i)}" for i in res["human_next"][:3]]
    L += ["", "── 상세 ──", "[행동 우선순위 A]"] + [f"  - {i['text']}{src(i)}" for i in res["actions"]]
    L += ["[판정 상세: 최소·최대 소요 기준]"]
    for j in res["judgments"]:
        mb = j.get("min_basis") or {}
        xb = j.get("max_basis") or {}
        f = lambda b: ", ".join(f"{k}={m2t(v)}" for k, v in b.items()) if b else "-"
        L.append(f"  - {j['id']} [{j['label']}] {j['title']}: {j['status']} | 최소 소요 기준 {f(mb)} | 최대 소요 기준 {f(xb)} [{']['.join(j['sources'])}]")
    for title, key in (("[P→O 수단 비교 — 전망대 도착 한도 기준(B3 연쇄), 추천 없음]", "compare"),
                       ("[P→O 수단 비교 — 원안 전망대 도착 시각 기준(참고, Hard 아님)]", "compare_ref")):
        L.append(title)
        if key == "compare" and res[key]:
            b = res[key][0]["binding"]
            L.append(f"  {b['text']} ({b['detail']}) [{']['.join(b['sources'])}]")
        for c in res[key]:
            L.append(f"  {c['label']}:")
            L += [f"    {fmt_interval(r)}" for r in c["intervals"]]
    L.append("[참고 일정표 B]")
    for r in res["reference"]:
        calc = "" if not r["calc"] else f" → {'도착' if r['calc'][0] == 'arr' else '출발'} {m2t(r['calc'][1])}~{m2t(r['calc'][2])}"
        plan = "" if r["plan"] is None else f"원안 {m2t(r['plan'])}"
        tag = " [USER] 사용자 입력 가정" if r.get("user") else ""
        L.append(f"  - {r['place']}: {plan}{calc}{tag} {r.get('note', '')} [{']['.join(r['sources'])}]")
    L += ["[UNKNOWN 전체]"] + [f"  - {i['text']}{src(i)}" for i in res["unknown"]]
    L += ["[HUMAN NEXT 전체]"] + [f"  - {i['text']}{src(i)}" for i in res["human_next"]]
    llm = res["llm"]
    L += ["", f"[LLM] {llm['status']}" + (f" — {llm['detail']}" if llm.get("detail") else "")]
    if llm.get("text"):
        L.append("  " + llm["text"])
    L.append(f"[확정 표현 린트] 위반 {len(res['lint'])}건")
    return "\n".join(L)
