"""규칙 엔진 (TD6 engine): P0 Hard 마감 역산 + P1 P→O 이동수단 비교. 결정적 계산만 한다 (D-1).

상태(AP1): SAFE = 최대 소요로도 충족 / AT_RISK = 최소 소요로만 충족 / FAIL = 최소 소요로도 미충족 /
UNKNOWN = 필요한 값이 null 이거나 자료 없음. 출발 시각이 USER 입력된 구간만 상태 판정(B5).
"""
from .model import m2t

SAFE, AT_RISK, FAIL, UNKNOWN, INFO = "SAFE", "AT_RISK", "FAIL", "UNKNOWN", "INFO"
MODE_LABEL = {"subway": "지하철", "bus": "버스", "taxi": "택시"}


def status_of(arr_min, arr_max, deadline, deadline_min_basis=None):
    """deadline_min_basis: 최소 소요 기준 판정에 쓰는 마감(연쇄 마감이 소요 범위에 따라 달라질 때). 없으면 deadline."""
    dmin = deadline if deadline_min_basis is None else deadline_min_basis
    if arr_max <= deadline:
        return SAFE
    if arr_min <= dmin:
        return AT_RISK
    return FAIL


def _j(jid, label, title, status, sources, min_basis=None, max_basis=None, assumptions=None, data=None):
    return {"id": jid, "label": label, "title": title, "status": status, "min_basis": min_basis,
            "max_basis": max_basis, "sources": list(dict.fromkeys(sources)), "assumptions": assumptions or [],
            "data": data or {}}


def _last_dep(deadline, rng):
    """최종 출발: (최대 소요 기준, 최소 소요 기준) = (마감 − max, 마감 − min) (B2)."""
    return deadline - rng[1], deadline - rng[0]


# ---------------- P1: P→O 수단별 소요 (AP2) ----------------
def p_o_range(inp, mode, d):
    """출발 시각 d 에서의 소요 범위와 점검 겹침(분). 자료 없으면 (None, overlap, reason)."""
    ws, we = inp.time("travel_window", "window_start"), inp.time("travel_window", "window_end")
    base = inp.rng("travel", "P_O")
    if mode == "subway":
        if base is None:
            return None, 0, "travel.P_O 미정"
        ov = 0 if ws is None or we is None else max(0, min(d + base[1], we) - max(d, ws))
        extra = inp.rng("travel_window", "subway_extra")
        if ov >= 1:
            if extra is None:
                return None, ov, "점검 추가시간 미정"
            return (base[0] + extra[0], base[1] + extra[1]), ov, ""
        return base, 0, ""
    r = inp.rng("travel_window", mode)
    if r is None:
        return None, 0, f"{MODE_LABEL[mode]} 소요 미정"
    ov = 0 if ws is None or we is None else max(0, min(d + r[1], we) - max(d, ws))
    if ov >= 1:
        return r, ov, ""
    return None, 0, "U10 점검 시간대 밖 소요 자료 없음"


def mode_intervals(inp, mode, deadline, scan_from, deadline_min_basis=None, binding=None):
    """출발 시각을 1분 단위로 훑어 상태가 같은 구간으로 묶는다 (E1-4 형식).
    deadline = 최대 소요 기준 전망대 도착 한도, deadline_min_basis = 최소 소요 기준 한도 (B3 연쇄)."""
    rows = []
    dmin = deadline if deadline_min_basis is None else deadline_min_basis
    for d in range(scan_from, max(deadline, dmin) + 1):
        rng, ov, why = p_o_range(inp, mode, d)
        st = UNKNOWN if rng is None else status_of(d + rng[0], d + rng[1], deadline, dmin)
        key = (st, rng, ov >= 1, why)
        if rows and rows[-1]["key"] == key:
            rows[-1]["to"] = d
        else:
            rows.append({"key": key, "from": d, "to": d, "status": st, "range": rng, "overlap": ov >= 1, "why": why})
    for r in rows:
        r.pop("key")
    last_safe = max((r["to"] for r in rows if r["status"] == SAFE), default=None)
    last_risk = max((r["to"] for r in rows if r["status"] in (SAFE, AT_RISK)), default=None)
    return {"mode": mode, "label": MODE_LABEL[mode], "deadline": deadline, "deadline_min_basis": dmin,
            "binding": binding or {"text": f"전망대 {m2t(deadline)} 도착", "sources": []}, "intervals": rows,
            "last_dep_max_basis": last_safe, "last_dep_min_basis": last_risk}


def o_deadline(inp):
    """전망대 도착 한도 (B3: C → O 최종 출발 → P 최종 출발). 최대·최소 소요 기준 각각."""
    o_in, c, oc = inp.time("deadlines", "O_indoor"), inp.time("deadlines", "C_entry"), inp.rng("travel", "O_C")
    cands_max, cands_min, parts, srcs = [], [], [], []
    if o_in is not None:
        cands_max.append(o_in); cands_min.append(o_in)
        parts.append(f"전망대 실내 입장 {m2t(o_in)}")
        srcs.append(inp.src("deadlines", "O_indoor"))
    if c is not None and oc is not None:
        cands_max.append(c - oc[1]); cands_min.append(c - oc[0])
        parts.append(f"공연 {m2t(c)} − 전망대→공연장 {oc[0]}~{oc[1]}분 = {m2t(c - oc[1])}(최대 소요)/{m2t(c - oc[0])}(최소 소요), 전망대 체류 미포함")
        srcs += [inp.src("deadlines", "C_entry"), inp.src("travel", "O_C")]
    if not cands_max:
        return None
    dmax, dmin = min(cands_max), min(cands_min)
    bind_max = "공연 연쇄" if c is not None and oc is not None and c - oc[1] < (o_in if o_in is not None else 10 ** 6) else "전망대 실내 입장"
    return {"max_basis": dmax, "min_basis": dmin, "binding": bind_max,
            "text": f"전망대 도착 한도 {m2t(dmax)}(최대 소요 기준)/{m2t(dmin)}(최소 소요 기준) — 구속 조건: {bind_max}",
            "detail": " · ".join(parts), "sources": srcs}


# ---------------- 전체 판정 ----------------
def evaluate(inp):
    J = []
    unknown_reasons = []
    g = inp.time
    arrival, now = g("meta", "arrival"), g("meta", "now")
    c_entry, o_indoor = g("deadlines", "C_entry"), g("deadlines", "O_indoor")
    mws, mwe = g("deadlines", "M_window_start"), g("deadlines", "M_window_end")
    r_time, r_grace = g("deadlines", "R_time"), inp.num("deadlines", "R_grace")
    s_m, m_r, o_c = inp.rng("travel", "station_M"), inp.rng("travel", "M_R"), inp.rng("travel", "O_C")
    src = inp.src

    # B1/CH2 — 미술관 입장창 (서울역 도착 시각에서 출발)
    if None in (arrival, mwe) or s_m is None:
        J.append(_j("J-M-ENTRY", "Hard", "미술관 입장 마감", UNKNOWN, [src("deadlines", "M_window_end"), "D03"],
                    data={"why": "도착 시각·입장 마감·서울역→M 소요 중 미정 값 있음"}))
    else:
        a0, a1 = arrival + s_m[0], arrival + s_m[1]
        J.append(_j("J-M-ENTRY", "Hard", "미술관 입장 마감", status_of(a0, a1, mwe),
                    [src("meta", "arrival"), src("travel", "station_M"), src("deadlines", "M_window_end")],
                    min_basis={"arrive": a0, "deadline": mwe}, max_basis={"arrive": a1, "deadline": mwe},
                    data={"arr": (a0, a1), "window_start": mws, "deadline": mwe}))

    # CH2 — 입장 후 최대 체류 (정보)
    mstay = inp.num("deadlines", "M_max_stay")
    if mstay is not None and mws is not None:
        J.append(_j("J-M-STAY", "Hard", "미술관 퇴장 한도", INFO, [src("deadlines", "M_max_stay")],
                    min_basis={"entry": mws, "exit_limit": mws + mstay}, max_basis={"entry": mws, "exit_limit": mws + mstay},
                    data={"max_stay": mstay, "example_entry": mws, "example_exit": mws + mstay}))

    # R 13:00 / 13:15(Soft, AP3) — 미술관 최종 출발
    if r_time is not None and m_r is not None:
        d_on = _last_dep(r_time, m_r)
        d_grace = _last_dep(r_time + r_grace, m_r) if r_grace is not None else None
        J.append(_j("J-R-LASTDEP", "Soft", "식당 도착을 위한 미술관 최종 출발", INFO,
                    [src("deadlines", "R_time"), src("deadlines", "R_grace"), src("travel", "M_R")],
                    min_basis={"last_dep_13:00": d_on[1]} | ({"last_dep_grace": d_grace[1]} if d_grace else {}),
                    max_basis={"last_dep_13:00": d_on[0]} | ({"last_dep_grace": d_grace[0]} if d_grace else {}),
                    data={"r_time": r_time, "grace_end": None if r_grace is None else r_time + r_grace,
                          "on_time": d_on, "grace": d_grace}))
        dep_m = g("user_times", "dep_M")
        if dep_m is not None and r_grace is not None:
            a0, a1 = dep_m + m_r[0], dep_m + m_r[1]
            J.append(_j("J-R-ARRIVE", "Soft", "식당 13:15 좌석 보장 한도", status_of(a0, a1, r_time + r_grace),
                        [src("user_times", "dep_M"), src("travel", "M_R"), src("deadlines", "R_grace")],
                        min_basis={"arrive": a0, "deadline": r_time + r_grace},
                        max_basis={"arrive": a1, "deadline": r_time + r_grace},
                        assumptions=["dep_M (USER)"], data={"arr": (a0, a1)}))

    # CH1 — 공연 입장: 전망대 최종 출발
    if c_entry is None or o_c is None:
        J.append(_j("J-O-LASTDEP", "Hard", "공연 입장을 위한 전망대 최종 출발", UNKNOWN,
                    [src("deadlines", "C_entry"), src("travel", "O_C")], data={"why": "공연 입장 마감 또는 O→C 소요 미정"}))
    else:
        dmax, dmin = _last_dep(c_entry, o_c)
        J.append(_j("J-O-LASTDEP", "Hard", "공연 입장을 위한 전망대 최종 출발", INFO,
                    [src("deadlines", "C_entry"), src("travel", "O_C")],
                    min_basis={"last_dep": dmin}, max_basis={"last_dep": dmax},
                    data={"c_entry": c_entry, "o_c": o_c, "max_basis": dmax, "min_basis": dmin}))
        dep_o = g("user_times", "dep_O")
        if dep_o is not None:
            a0, a1 = dep_o + o_c[0], dep_o + o_c[1]
            J.append(_j("J-C-ARRIVE", "Hard", "공연 입장 마감", status_of(a0, a1, c_entry),
                        [src("user_times", "dep_O"), src("travel", "O_C"), src("deadlines", "C_entry")],
                        min_basis={"arrive": a0, "deadline": c_entry}, max_basis={"arrive": a1, "deadline": c_entry},
                        assumptions=["dep_O (USER)"], data={"arr": (a0, a1)}))

    # P1 — P→O 수단 비교 (CH4, 추천 없음 AP4)
    scan_from = r_time if r_time is not None else (g("travel_window", "window_start") or 13 * 60) - 120
    compare, compare_ref = [], []
    # B3 연쇄: 전망대 도착 한도 = min(실내 입장 마감, 공연 입장 − O→C 소요). 전망대 체류는 미정이라 0분(미포함)
    o_dl = o_deadline(inp)
    if o_dl:
        compare = [mode_intervals(inp, m, o_dl["max_basis"], scan_from, o_dl["min_basis"], o_dl)
                   for m in ("subway", "bus", "taxi")]
    plan_o = g("plan", "O")
    if plan_o is not None:
        compare_ref = [mode_intervals(inp, m, plan_o, scan_from) for m in ("subway", "bus", "taxi")]
    dep_p, mode = g("user_times", "dep_P"), inp.raw("user_times", "P_O_mode")
    if dep_p is not None and mode and o_dl:
        rng, ov, why = p_o_range(inp, mode, dep_p)
        st = UNKNOWN if rng is None else status_of(dep_p + rng[0], dep_p + rng[1], o_dl["max_basis"], o_dl["min_basis"])
        J.append(_j("J-O-ARRIVE", "Hard", "전망대 도착 한도 (" + o_dl["text"] + ")", st,
                    [src("user_times", "dep_P"), "D03", "D06"] + o_dl["sources"],
                    min_basis=None if rng is None else {"arrive": dep_p + rng[0], "deadline": o_dl["min_basis"]},
                    max_basis=None if rng is None else {"arrive": dep_p + rng[1], "deadline": o_dl["max_basis"]},
                    assumptions=["dep_P, P_O_mode (USER)"], data={"mode": mode, "overlap": ov, "why": why}))

    # Soft — 택시 횟수 (D07)
    tu, tmax = inp.num("user_times", "taxi_uses"), inp.num("prefs", "taxi_max")
    if tu is not None and tmax is not None and tu > tmax:
        J.append(_j("J-TAXI", "Soft", "택시 사용 횟수", AT_RISK, [src("user_times", "taxi_uses"), src("prefs", "taxi_max")],
                    data={"uses": tu, "max": tmax}))

    # 참고 일정표 B (AP5) — 원안 시각 + USER 입력 가정만 사용 (B6)
    ref = reference_schedule(inp)
    return {"judgments": J, "compare": compare, "compare_ref": compare_ref, "reference": ref,
            "now": now, "arrival": arrival}


def reference_schedule(inp):
    g, src = inp.time, inp.src
    rows = []
    arrival = g("meta", "arrival")
    s_m = inp.rng("travel", "station_M")
    rows.append({"place": "서울역 도착", "plan": arrival, "calc": None, "sources": [src("meta", "arrival")], "user": False})
    if arrival is not None and s_m:
        rows.append({"place": "미술관 M", "plan": g("plan", "M"), "calc": ("arr", arrival + s_m[0], arrival + s_m[1]),
                     "sources": [src("plan", "M"), "D03"], "user": False})
    else:
        rows.append({"place": "미술관 M", "plan": g("plan", "M"), "calc": None, "sources": [src("plan", "M")], "user": False})
    rows.append({"place": "식당 R", "plan": g("plan", "R"), "calc": None, "sources": [src("plan", "R"), "D02"], "user": False})
    meal, r_time, r_p = inp.num("durations", "R_meal"), g("deadlines", "R_time"), inp.rng("travel", "R_P")
    if meal is not None and r_time is not None:
        dep = r_time + meal
        rows.append({"place": "식당 R 출발", "plan": None, "calc": ("dep", dep, dep), "sources": ["D02", "USER"],
                     "user": True, "note": "13:00 착석 + 식사 {m}분".format(m=meal)})
        if r_p:
            rows.append({"place": "한강공원 P", "plan": g("plan", "P"), "calc": ("arr", dep + r_p[0], dep + r_p[1]),
                         "sources": [src("plan", "P"), "D03", "USER"], "user": True})
    else:
        rows.append({"place": "식당 R 출발", "plan": None, "calc": None, "sources": ["U02"], "user": False,
                     "note": "식사 시간 미정 (U02, HB4)"})
        rows.append({"place": "한강공원 P", "plan": g("plan", "P"), "calc": None, "sources": [src("plan", "P")], "user": False})
    rows.append({"place": "전망대 O", "plan": g("plan", "O"), "calc": None, "sources": [src("plan", "O")], "user": False,
                 "note": "원안 도착 시각은 Hard 아님 — 아래 '원안 17:00 도착 기준' 비교표 참고"})
    rows.append({"place": "공연장 C", "plan": g("plan", "C"), "calc": None,
                 "sources": [src("plan", "C"), src("deadlines", "C_entry")], "user": False})
    return rows
