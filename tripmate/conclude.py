"""결론 조립 (TD6 conclude): 결론 / KPI / WHY / UNKNOWN / HUMAN NEXT + 접기 상세(A, 판정 상세, 비교표, B).
모든 문장은 아래 템플릿 T 에 엔진 값을 바인딩해 만든다 (R7, D-5). 각 문장에 출처 ID를 붙인다 (R5).
"""
from .model import m2t
from .engine import SAFE, AT_RISK, FAIL, UNKNOWN, INFO, MODE_LABEL
from . import kpi as kpi_mod

T = {
    "concl": "공연 입장 마감 {c}(Hard)을 지키려면 전망대에서 {omax}(최대 소요 기준)~{omin}(최소 소요 기준)까지 출발해야 합니다. 가장 임박한 확인: {nd} {ni}.",
    "concl_unknown": "공연 입장 마감 또는 전망대→공연장 소요가 미정이라 최종 출발 시각을 계산하지 않았습니다. 가장 임박한 확인: {nd} {ni}.",
    "concl_fail": "{title}: {status} — 최소 소요 기준 도착 {a0}, 마감 {dl} ({label}).",
    "concl_risk": "{title}: {status} — 도착 범위 {a0}~{a1}가 마감 {dl}에 걸칩니다 ({label}).",
    "why_o": "공연 입장 마감 {c}(확정 조건)에서 전망대→공연장 {lo}~{hi}분(평상시 추정)을 빼면 전망대 최종 출발은 {omax}~{omin}입니다.",
    "why_po": "P→O 지하철은 이동 구간이 점검 시간대 {ws}~{we}와 1분이라도 겹치면 {lo}~{hi}분(점검 안내 범위 전체, U09), 겹치지 않으면 평상시 범위로 계산합니다. {bind} 기준 출발 SAFE 구간: {safe}.",
    "why_m": "미술관 입장 마감 {dl}: 서울역 {arr} 도착 후 {lo}~{hi}분 이동 → 도착 {a0}~{a1}, 상태 {st}.",
    "unk": "{uid} {what} — {why}",
    "hn": "{hid} [{when}] {text}",
    "act": "{t} {label} {text}",
}

STATUS_KO = {SAFE: "SAFE(최대 소요로도 충족)", AT_RISK: "AT_RISK(최소 소요로만 충족)",
             FAIL: "FAIL(최소 소요로도 미충족)", UNKNOWN: "UNKNOWN(판정 불가)", INFO: "정보"}


def it(text, sources, **extra):
    d = {"text": text, "sources": [s for s in dict.fromkeys(sources) if s]}
    d.update(extra)
    return d


def safe_spans(cmp):
    """연속된 SAFE 구간을 합친다 (소요 범위가 달라도 출발 가능 구간으로는 이어짐)."""
    spans = []
    for r in cmp["intervals"]:
        if r["status"] != SAFE:
            continue
        if spans and spans[-1][1] == r["from"] - 1:
            spans[-1][1] = r["to"]
        else:
            spans.append([r["from"], r["to"]])
    return spans


def _safe_txt(cmp):
    s = [f"{m2t(a)}~{m2t(b)}" for a, b in safe_spans(cmp)]
    return ", ".join(s) if s else "없음"


def human_next(inp, ev):
    g = inp.time
    now = ev["now"]
    out = []
    fc = g("deadlines", "M_free_cancel")
    jm = next((j for j in ev["judgments"] if j["id"] == "J-M-ENTRY"), None)
    if fc is not None:
        left = None if now is None else fc - now
        lt = (f"남은 {left}분" if left is not None and left >= 0 else "마감 지남 — 지금 취소하면 환불되지 않음")
        out.append({"id": "H01", "key": fc, "when": f"{m2t(fc)} 전", "short": "미술관 유지/취소 결정",
                    "text": f"미술관 예약 유지/취소 결정 ({lt}). 사실: {m2t(fc)}까지 취소 시 전액 환불, 이후 환불 불가. "
                            f"입장 마감 판정: {jm['status'] if jm else 'UNKNOWN'}",
                    "sources": [inp.src("deadlines", "M_free_cancel"), "H01"] + (jm["sources"] if jm else [])})
    rt, rg = g("deadlines", "R_time"), inp.num("deadlines", "R_grace")
    jr = next((j for j in ev["judgments"] if j["id"] == "J-R-ARRIVE"), None)
    if jr and jr["status"] in (AT_RISK, FAIL):
        out.append({"id": "H07", "key": rt + rg, "when": f"{m2t(rt + rg)} 전", "short": "식당 좌석 확인",
                    "text": f"식당 도착 예상이 {m2t(rt + rg)}(좌석 보장 한도, Soft)를 넘을 수 있음 → 식당에 좌석 확인",
                    "sources": jr["sources"] + ["H07"]})
    wx = [w for w in inp.d.get("weather", []) if isinstance(w, dict)]
    latest = wx[-1] if wx else None
    # P 관련 항목 정렬 키: 원안 P 시각, 없으면 맨 뒤 (임박 항목으로 오인 방지)
    pp = g("plan", "P") if g("plan", "P") is not None else 24 * 60
    if latest:
        win = latest["window"]["value"]
        out.append({"id": "H02", "key": pp, "when": "P 이동 전", "short": "최신 예보 재확인",
                    "text": f"최신 예보 재확인. 현재 {latest['issued']['value']} 발표 예보: {win[0]}~{win[1]} 강수확률 "
                            f"{latest['rain_pct']['value']}%, 풍속 {latest['wind_ms']['value']}m/s (예보이며 변동 가능). "
                            f"비 올 때 연속 야외 {inp.raw('prefs', 'rain_outdoor_max')}분 이상 회피 선호 — P 유지/축소는 판정하지 않음(HB2)",
                    "sources": ["D04", "D07", "H02"]})
    out.append({"id": "H08", "key": pp, "when": "P 진입 전", "short": "P 축소/생략 시 동의",
                "text": "한강공원 축소·생략을 고를 경우 희망자 1명 동의 (공연보다 우선순위 낮음)", "sources": ["D07", "H08"]})
    opts = []
    for c in ev["compare"]:
        rngs = sorted({r["range"] for r in c["intervals"] if r["range"]})
        rtxt = "/".join(f"{a}~{b}분" for a, b in rngs) or "자료 없음"
        lm = "없음" if c["last_dep_max_basis"] is None else m2t(c["last_dep_max_basis"])
        ln = "없음" if c["last_dep_min_basis"] is None else m2t(c["last_dep_min_basis"])
        opts.append(f"{c['label']} {rtxt}, 최종 출발 {lm}(최대)/{ln}(최소)")
    if opts:
        out.append({"id": "H03", "key": pp + 1, "when": "P 출발 전", "short": "P→O 실시간 지연·택시 확인",
                    "text": "P→O 실시간 지연·택시 호출 가능 여부 확인 후 수단 선택 (추천 없음). 판단 정보: " + "; ".join(opts),
                    "sources": ["D03", "D06", "H03"]})
    fares = inp.raw("fares", "taxi_per_ride")
    out.append({"id": "H04", "key": pp + 1, "when": "택시 사용 전", "short": "예산 합의",
                "text": f"이동비 4명 합계 {inp.raw('prefs', 'budget')}원 범위 일행 합의, 택시 {inp.raw('prefs', 'taxi_max')}회 정도. "
                        f"요금 {'미정(U03) — 예산 충족 판정 안 함' if fares is None else str(fares) + '원/회 (USER)'}",
                "sources": ["D07", "H04", "U03"]})
    if inp.raw("facility", "O_deck"):
        out.append({"id": "H05", "key": g("plan", "O") if g("plan", "O") is not None else 24 * 60, "when": "O 도착 시", "short": "데크 운영 현장 확인",
                    "text": f"전망대 야외 데크 운영 여부 현장 확인 (공지: {inp.raw('facility', 'O_deck')})",
                    "sources": [inp.src("facility", "O_deck"), "H05"]})
    out.append({"id": "H06", "key": g("deadlines", "C_entry") if g("deadlines", "C_entry") is not None else 24 * 60, "when": "사전", "short": "21:30 출발 확인",
                "text": f"공연 종료 시각·공연장→서울역 이동시간 확인 ({inp.raw('meta', 'departure')} 출발, 판정 불가 U01)",
                "sources": ["D01", "U01", "H06"]})
    out.sort(key=lambda x: x["key"])
    for h in out:
        h["text_full"] = T["hn"].format(hid=h["id"], when=h["when"], text=h["text"])
    return out


def unknowns(inp, ev):
    U = []
    def add(uid, what, why, srcs):
        U.append(it(T["unk"].format(uid=uid, what=what, why=why), srcs))
    add("U01", "21:30 서울역 출발 가능 여부", "공연 종료 시각·공연장→서울역 소요 자료 없음", ["D01", "D02", "U01"])
    jm = next((j for j in ev["judgments"] if j["id"] == "J-M-ENTRY"), None)
    if jm and jm["status"] == FAIL:
        add("D03", "서울역→식당 직행 소요", "자료에 없는 구간이라 미술관을 건너뛸 때의 일정은 계산하지 않음", ["D03"])
    if any(inp.raw("durations", k) is None for k in ("M_stay", "R_meal", "P_stay", "O_stay")):
        miss = [k for k in ("M_stay", "R_meal", "P_stay", "O_stay") if inp.raw("durations", k) is None]
        add("HB4", "체류시간 " + ", ".join(miss), "자료에 없음, 엔진이 임의 값으로 채우지 않음(사용자 입력 시 참고 일정표에만 반영)", ["A02", "A03", "A04", "HB4"])
    used = [k for k in ("M_stay", "P_stay", "O_stay") if inp.raw("durations", k) is not None]
    if used:
        add("HB1", "입력된 체류시간 " + ", ".join(f"{k}={inp.raw('durations', k)}분" for k in used),
            "입력됨 — 순방향 일정 전파(P0-C)는 승인 범위 밖이라 판정에 쓰지 않음 (식사 시간만 참고 일정표에 반영)", ["USER", "HB1"])
    if inp.raw("fares", "taxi_per_ride") is None or inp.raw("fares", "transit_per_person") is None:
        add("U03", "요금·예산 충족 여부", "요금 미정, 예산 해석 미정(HB6)", ["D07", "U03", "HB6"])
    add("HB2", "날씨 기반 한강공원 유지/축소", "강수·풍속 임계값 미정 — 예보 사실만 표시", ["D04", "HB2"])
    if any(any(r["status"] == UNKNOWN for r in c["intervals"]) for c in ev["compare"]):
        add("U10", "점검 시간대 밖 P→O 버스·택시 소요", "자료(D06)는 점검 시간대 안내만 있음", ["D03", "D06", "U10"])
    add("U09", "점검 지연의 실제 발생 구간", "겹치면 D06 범위 전체 적용(비례 배분 미적용)", ["D06", "U09"])
    if all(inp.raw("user_times", k) is None for k in ("dep_M", "dep_P", "dep_O")):
        add("B5", "구간별 출발 예정 시각", "미입력 — 최종 출발 시각만 제시하고 도착 상태는 판정하지 않음", ["USER"])
    add("U05", "전망대 데크 폐쇄 기준 풍속", "공지에 기준 없음", ["D05", "U05"])
    return U


def actions(inp, ev):
    """A: 행동 우선순위 — 마감 시각순, Hard/Soft 라벨 유지 (AP5, E3-4)."""
    A = []
    g = inp.time
    def add(t, label, text, srcs):
        A.append(it(T["act"].format(t=m2t(t), label=f"[{label}]", text=text), srcs, key=t))
    fc = g("deadlines", "M_free_cancel")
    if fc is not None:
        add(fc, "결정 기한", "미술관 유지/취소 결정 (H01)", [inp.src("deadlines", "M_free_cancel"), "H01"])
    for j in ev["judgments"]:
        d = j["data"]
        if j["id"] == "J-M-ENTRY" and j["status"] != UNKNOWN:
            add(d["deadline"], "Hard", f"미술관 입장 마감 ({m2t(d['window_start'])}부터 입장) — {j['status']}", j["sources"])
        if j["id"] == "J-M-STAY":
            add(d["example_exit"], "Hard", f"미술관 입장 후 {d['max_stay']}분 이내 퇴장 ({m2t(d['example_entry'])} 입장 시)", j["sources"])
        if j["id"] == "J-R-LASTDEP":
            add(d["on_time"][0], "참고", f"식당 {m2t(d['r_time'])} 도착을 위한 미술관 출발 {m2t(d['on_time'][0])}(최대 소요)/{m2t(d['on_time'][1])}(최소 소요)", j["sources"])
            if d["grace"]:
                add(d["grace"][0], "Soft", f"식당 좌석 보장 {m2t(d['grace_end'])}: 미술관 출발 {m2t(d['grace'][0])}(최대 소요)/{m2t(d['grace'][1])}(최소 소요)", j["sources"])
        if j["id"] == "J-O-LASTDEP" and j["status"] != UNKNOWN:
            add(d["max_basis"], "Hard", f"공연 {m2t(d['c_entry'])} 입장을 위한 전망대 출발 {m2t(d['max_basis'])}(최대 소요)/{m2t(d['min_basis'])}(최소 소요)", j["sources"])
    for c in ev["compare"]:
        if c["last_dep_max_basis"] is not None:
            add(c["last_dep_max_basis"], "Hard", f"{c['binding']['text']}을 위한 P 출발 ({c['label']}): SAFE 구간 {_safe_txt(c)}",
                ["D03", "D06"] + c["binding"]["sources"])
    o_ind = g("deadlines", "O_indoor")
    if o_ind is not None:
        add(o_ind, "Hard", "전망대 실내 입장 마감", [inp.src("deadlines", "O_indoor")])
    ce = g("deadlines", "C_entry")
    if ce is not None:
        add(ce, "Hard", "공연 입장 마감 (최우선)", [inp.src("deadlines", "C_entry"), "D01"])
    A.sort(key=lambda x: x["key"])
    return A


def build(inp, ev):
    J = ev["judgments"]
    hn = human_next(inp, ev)
    nxt = hn[0] if hn else {"when": "-", "short": "없음", "sources": []}
    jo = next((j for j in J if j["id"] == "J-O-LASTDEP"), None)
    concl = []
    if jo and jo["status"] != UNKNOWN:
        d = jo["data"]
        concl.append(it(T["concl"].format(c=m2t(d["c_entry"]), omax=m2t(d["max_basis"]), omin=m2t(d["min_basis"]),
                                          nd=nxt["when"], ni=nxt["short"]), jo["sources"] + nxt["sources"]))
    else:
        concl.append(it(T["concl_unknown"].format(nd=nxt["when"], ni=nxt["short"]), (jo["sources"] if jo else []) + nxt["sources"]))
    worst = None
    for j in J:
        if j["status"] in (FAIL, AT_RISK) and j.get("min_basis"):
            mb, xb = j["min_basis"], j["max_basis"]
            tpl = T["concl_fail"] if j["status"] == FAIL else T["concl_risk"]
            concl.append(it(tpl.format(title=j["title"], status=j["status"], a0=m2t(mb["arrive"]), a1=m2t(xb["arrive"]),
                                       dl=m2t(mb["deadline"]), label=j["label"]), j["sources"], status=j["status"]))
            if j["label"] == "Hard" and (worst is None or j["status"] == FAIL):
                worst = j["status"]
    # 전체 상태 (E-2): FAIL > UNKNOWN > AT_RISK > SAFE. Hard 미판정·판정 불가가 있으면 SAFE 로 단정하지 않는다
    hard = [j for j in J if j["label"] == "Hard"]
    judged = [j for j in hard if j["status"] in (SAFE, AT_RISK, FAIL)]
    unknown_h = [j for j in hard if j["status"] == UNKNOWN]
    ids = {j["id"] for j in J}
    unjudged = [t for jid, t in (("J-O-ARRIVE", "전망대 도착(P 출발 시각·수단 미입력)"),
                                 ("J-C-ARRIVE", "공연 도착(전망대 출발 시각 미입력)")) if jid not in ids]
    sts = {j["status"] for j in judged}
    if FAIL in sts:
        badge = FAIL
    elif unknown_h or not judged:
        badge = UNKNOWN
    elif AT_RISK in sts:
        badge = AT_RISK
    else:
        badge = SAFE
    badge_note = f"Hard 판정 {len(judged)}건 기준" + (f" · 판정 불가 {len(unknown_h)}건" if unknown_h else "") +         (f" · 미판정 {len(unjudged)}건: " + ", ".join(unjudged) if unjudged else "")

    why = []
    if jo and jo["status"] != UNKNOWN:
        d = jo["data"]
        why.append(it(T["why_o"].format(c=m2t(d["c_entry"]), lo=d["o_c"][0], hi=d["o_c"][1], omax=m2t(d["max_basis"]),
                                        omin=m2t(d["min_basis"])), jo["sources"]))
    sub = next((c for c in ev["compare"] if c["mode"] == "subway"), None)
    if sub:
        ov = [r for r in sub["intervals"] if r["overlap"] and r["range"]]
        if ov:
            why.append(it(T["why_po"].format(ws=inp.raw("travel_window", "window_start"), we=inp.raw("travel_window", "window_end"),
                                             lo=ov[0]["range"][0], hi=ov[0]["range"][1], bind=sub["binding"]["text"], safe=_safe_txt(sub)),
                          ["D03", "D06", "AP2", "U09"] + sub["binding"]["sources"]))
    jm = next((j for j in J if j["id"] == "J-M-ENTRY" and j["status"] != UNKNOWN), None)
    if jm:
        a = jm["data"]["arr"]
        s_m = inp.rng("travel", "station_M")
        why.append(it(T["why_m"].format(dl=m2t(jm["data"]["deadline"]), arr=inp.raw("meta", "arrival"), lo=s_m[0], hi=s_m[1],
                                        a0=m2t(a[0]), a1=m2t(a[1]), st=jm["status"]), jm["sources"]))

    res = {"conclusion": concl, "badge": badge, "badge_note": badge_note, "why": why[:3], "unknown": unknowns(inp, ev),
           "human_next": [dict(h, text=h["text_full"]) for h in hn], "actions": actions(inp, ev),
           "judgments": J, "compare": ev["compare"], "compare_ref": ev["compare_ref"], "reference": ev["reference"]}
    res["kpi"] = kpi_mod.build(res)
    res["kpi_note"] = kpi_mod.STATUS_NOTE
    return res
