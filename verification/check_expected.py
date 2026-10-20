"""DESIGN.md §7 E1~E3 + V1~V8 + 이상 입력 자동 대조. 실행: python verification/check_expected.py
(구현 세션 작성 — 임시 권한: 부여자 사용자 / 범위 verification/ 이번 검증·재검증 / 사유 구현 세션이 검증 수행)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = lambda n: json.load(open(os.path.join(HERE, "actual", n + ".json"), encoding="utf-8"))
results = []


def chk(cid, desc, cond, actual=""):
    results.append((cid, desc, "Pass" if cond else "Fail", str(actual)[:160]))


def m2t(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def J(res, jid):
    return next((j for j in res["judgments"] if j["id"] == jid), None)


def cmp(res, mode, key="compare"):
    c = next(c for c in res[key] if c["mode"] == mode)
    return [(m2t(r["from"]), m2t(r["to"]), r["status"]) for r in c["intervals"]]


def alltext(res):
    out = []
    for k in ("conclusion", "why", "unknown", "human_next", "actions"):
        out += [i["text"] for i in res[k]]
    out += [k["title"] + k["value"] for k in res["kpi"]]
    return "\n".join(out)


def status_at(iv, t):
    for a, b, s in iv:
        if a <= t <= b:
            return s
    return None


e1, e2, e3 = A("E1"), A("E2"), A("E3")
# ---------- E1 ----------
j = J(e1, "J-M-ENTRY")
chk("E1-1", "M 도착 09:45~09:55, 입장창 SAFE", j["status"] == "SAFE" and j["data"]["arr"] == [585, 595], (j["status"], j["data"]["arr"]))
d = J(e1, "J-R-LASTDEP")["data"]
chk("E1-2", "M 최종 출발 12:35/12:40, 13:15 기준 12:50/12:55",
    d["on_time"] == [755, 760] and d["grace"] == [770, 775], (d["on_time"], d["grace"]))
d = J(e1, "J-O-LASTDEP")
chk("E1-3", "O 최종 출발 18:10(최대)/18:20(최소), Hard, D02·D03",
    d["data"]["max_basis"] == 1090 and d["data"]["min_basis"] == 1100 and d["label"] == "Hard"
    and {"D02", "D03"} <= set(d["sources"]), (m2t(d["data"]["max_basis"]), m2t(d["data"]["min_basis"]), d["sources"]))
iv = cmp(e1, "subway")
exp = {"16:45": "SAFE", "16:46": "AT_RISK", "16:59": "AT_RISK", "17:00": "SAFE", "17:15": "SAFE",
       "17:16": "AT_RISK", "17:30": "AT_RISK", "17:31": "FAIL"}
chk("E1-4", "지하철 구간: ≤16:45 SAFE, ~17:00 AT_RISK, 17:00~17:15 SAFE, ~17:30 AT_RISK, 이후 FAIL",
    all(status_at(iv, t) == s for t, s in exp.items()), iv)
bus, taxi = cmp(e1, "bus"), cmp(e1, "taxi")
chk("E1-5", "버스·택시: 점검 겹침 출발 SAFE, 17:00 이후 UNKNOWN",
    status_at(bus, "16:30") == "SAFE" and status_at(taxi, "16:30") == "SAFE"
    and status_at(bus, "17:00") == "UNKNOWN" and status_at(taxi, "17:10") == "UNKNOWN", (bus, taxi))
txt = alltext(e1)
hids = [h["text"][:3] for h in e1["human_next"]]
chk("E1-6", "수단 추천 없음 + H03·H04 판단 정보",
    not re.search(r"추천합니다|권장|을 타세요|를 이용하세요", txt) and "H03" in hids and "H04" in hids
    and "50~75분" in next(h["text"] for h in e1["human_next"] if h["text"].startswith("H03")), hids)
ref_sub, ref_bus, ref_taxi = cmp(e1, "subway", "compare_ref"), cmp(e1, "bus", "compare_ref"), cmp(e1, "taxi", "compare_ref")
chk("E1-7", "참고 B(O 17:00): 지하철 ≤15:45 SAFE / ~16:10 AT_RISK, 버스 ≤16:10 SAFE, 택시 ≤16:25 SAFE",
    status_at(ref_sub, "15:45") == "SAFE" and status_at(ref_sub, "15:46") == "AT_RISK" and status_at(ref_sub, "16:10") == "AT_RISK"
    and status_at(ref_sub, "16:11") == "FAIL" and status_at(ref_bus, "16:10") == "SAFE" and status_at(ref_bus, "16:11") != "SAFE"
    and status_at(ref_taxi, "16:25") == "SAFE" and status_at(ref_taxi, "16:26") != "SAFE", (ref_sub, ref_bus, ref_taxi))
h02 = next((h["text"] for h in e1["human_next"] if h["text"].startswith("H02")), "")
chk("E1-8", "날씨는 예보로 표시, P 판정 없음, H02·H08 표시",
    "80%" in h02 and "예보" in h02 and "판정하지 않음" in h02 and "H08" in hids, h02)
chk("E1-9", "Human next 최상단 H01 (남은 10분)", e1["human_next"][0]["text"].startswith("H01") and "남은 10분" in e1["human_next"][0]["text"],
    e1["human_next"][0]["text"][:60])
ut = "\n".join(u["text"] for u in e1["unknown"])
chk("E1-10", "Unknown에 U01·U03·체류시간, 예산 판정 없음", "U01" in ut and "U03" in ut and "체류시간" in ut and "예산 충족" in ut, ut[:150])
chk("E1-11", "금지 표현 0건", not e1["lint"] and not re.search(r"반드시\s*\S{0,6}\s*비|폐쇄\s*됐|정확히\s*\d+\s*분", txt), e1["lint"])

# ---------- E2 ----------
j = J(e2, "J-M-ENTRY")
chk("E2-1", "M 도착 11:05~11:15 → FAIL(Hard)", j["status"] == "FAIL" and j["data"]["arr"] == [665, 675] and j["label"] == "Hard", (j["status"], j["data"]["arr"]))
ctext = "\n".join(c["text"] for c in e2["conclusion"])
h01 = e2["human_next"][0]["text"]
chk("E2-2", "결론에 M FAIL, 취소 권고 없음, 사실(전액 환불)+H01만",
    "FAIL" in ctext and "미술관" in ctext and not re.search(r"취소하(세요|십시오|는 것이 좋)|취소를 권", alltext(e2))
    and "전액 환불" in h01 and h01.startswith("H01"), ctext[:120])
chk("E2-3", "서울역→식당 직행 소요 UNKNOWN", any("서울역→식당" in u["text"] for u in e2["unknown"]), [u["text"][:30] for u in e2["unknown"]])
chk("E2-4", "C·O 관련 결과(E1-3~E1-5) E1과 동일",
    J(e2, "J-O-LASTDEP")["data"] == J(e1, "J-O-LASTDEP")["data"] and e2["compare"] == e1["compare"], "")
chk("E2-5", "결과가 E1과 다르게 생성(고정 문구 아님)", e2["conclusion"] != e1["conclusion"] and e2["badge"] != e1["badge"], (e1["badge"], e2["badge"]))

# ---------- E3 ----------
ref = {r["place"]: r for r in e3["reference"]}
rdep, parr = ref.get("식당 R 출발"), ref.get("한강공원 P")
chk("E3-1", "참고 B: R 출발 14:30, P 도착 14:55~15:05, [USER] 라벨",
    rdep and rdep["calc"] == ["dep", 870, 870] and rdep["user"] and parr["calc"] == ["arr", 895, 905] and parr["user"], (rdep, parr))
chk("E3-2", "Hard 판정 E1과 동일", e3["judgments"] == e1["judgments"] and e3["compare"] == e1["compare"], "")
ut3 = "\n".join(u["text"] for u in e3["unknown"])
chk("E3-3", "공원·전망대 체류시간 UNKNOWN 유지 (R_meal은 제외)", "P_stay" in ut3 and "O_stay" in ut3 and "R_meal" not in ut3, ut3[:120])
keys = [a["key"] for a in e3["actions"]]
chk("E3-4", "행동 우선순위 시각순 + Hard/Soft 라벨 유지", keys == sorted(keys) and any("[Soft]" in a["text"] for a in e3["actions"])
    and any("[Hard]" in a["text"] for a in e3["actions"]), [a["text"][:12] for a in e3["actions"]])
chk("E3-5", "날씨·수단·예산 판정 없음 유지", "판정하지 않음" in "\n".join(h["text"] for h in e3["human_next"]) and "예산 충족" in ut3, "")

# ---------- V1~V8 (docs/REQUIREMENTS.md §4 — 방향 확인) ----------
v = {n: A(n) for n in ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8")}
h02 = lambda r: next(h["text"] for h in r["human_next"] if h["text"].startswith("H02"))
chk("V1", "강수 20%/3m/s → 예보 값 반영(P 판정은 HB2 미정으로 없음)", "20%" in h02(v["V1"]) and "3m/s" in h02(v["V1"]), h02(v["V1"])[:70])
chk("V2", "강수 95%/14m/s → 예보 값 반영, 데크 확인 H05 유지", "95%" in h02(v["V2"]) and any(h["text"].startswith("H05") for h in v["V2"]["human_next"]), h02(v["V2"])[:70])
iv3 = cmp(v["V3"], "subway")
chk("V3", "점검 +60분 → 지하철 90~105분, 겹침 구간 SAFE 종료 앞당겨짐, 버스·택시 비교 유지",
    any(r["range"] == [90, 105] for r in next(c for c in v["V3"]["compare"] if c["mode"] == "subway")["intervals"])
    and status_at(iv3, "16:15") == "SAFE" and status_at(iv3, "16:16") != "SAFE", iv3)
d4 = J(v["V4"], "J-O-LASTDEP")["data"]
chk("V4", "공연 마감 18:00 → 전망대 최종 출발 17:30/17:40", (d4["max_basis"], d4["min_basis"]) == (1050, 1060), (m2t(d4["max_basis"]), m2t(d4["min_basis"])))
iv5 = cmp(v["V5"], "subway")
chk("V5", "전망대 마감 17:00 → P 출발 구간 재계산 (16:10 이후 SAFE 없음)", status_at(iv5, "15:45") == "SAFE" and status_at(iv5, "16:11") == "FAIL", iv5)
h04 = next(h["text"] for h in v["V6"]["human_next"] if h["text"].startswith("H04"))
chk("V6", "예산 2만 원 → H04에 반영, 요금 미정이라 판정 없음", "20000원" in h04 and "판정 안 함" in h04, h04[:80])
j7 = J(v["V7"], "J-M-ENTRY")
chk("V7", "도착 10:30 → M 도착 10:55~11:05 AT_RISK + 결론 경고", j7["status"] == "AT_RISK"
    and any("AT_RISK" in c["text"] for c in v["V7"]["conclusion"]), (j7["status"], j7["data"]["arr"]))
d8 = J(v["V8"], "J-R-LASTDEP")["data"]
chk("V8", "지각 허용 0분 → 좌석 보장 기준 출발 12:35/12:40", d8["grace"] == [755, 760], d8["grace"])

# ---------- 이상 입력 ----------
def err(n):
    r = A(n)
    return (not r.get("ok")) and r.get("errors")
for n, frag in (("X_badtime", "시각 형식"), ("X_minmax", "최소(30)가 최대(20)"), ("X_badmode", "P_O_mode"), ("X_neg", "음수")):
    e = err(n)
    chk(n, f"오류 메시지에 '{frag}' 포함, 크래시 없음", bool(e) and any(frag in x for x in e), e)
xn = open(os.path.join(HERE, "actual", "X_notjson.json"), encoding="utf-8").read()
chk("X_notjson", "JSON 아님 → 형식 오류 메시지", "JSON 형식 오류" in xn, xn[:80])
r = A("X_null_C")
chk("X_null_C", "공연 마감 null → UNKNOWN, 결론은 계산 안 했음을 표시", r["ok"] and J(r, "J-O-LASTDEP")["status"] == "UNKNOWN"
    and "계산하지 않았습니다" in r["conclusion"][0]["text"], r["conclusion"][0]["text"][:60])
r = A("X_missingkey")
# 4회차 기대 수정: E-1(B3 연쇄) 반영 후에는 전망대 마감이 없어도 공연 연쇄 한도로 비교표를 만든다
chk("X_missingkey", "전망대 마감 항목 삭제 → 죽지 않고 공연 연쇄 한도(18:10/18:20)로 비교", r["ok"] and len(r["compare"]) == 3
    and r["compare"][0]["binding"]["binding"] == "공연 연쇄" and r["compare"][0]["deadline"] == 1090, r["compare"][0]["binding"]["text"] if r["compare"] else None)
r = A("X_window")
iv = cmp(r, "subway")
chk("X_window", "점검 16:00~18:00 → 겹침 구간 이동 (15:14 출발 SAFE 평상시, 17:00 출발 점검 범위)",
    status_at(iv, "15:14") == "SAFE" and any(x[2] == "FAIL" for x in iv), iv)
r = A("X_hugedelay")
iv = cmp(r, "subway")
chk("X_hugedelay", "매우 큰 지연(+300~600분) → 겹침 구간 FAIL, 크래시 없음", r["ok"] and status_at(iv, "16:00") == "FAIL", iv[:3])
r = A("X_userdep")
st = {j["id"]: j["status"] for j in r["judgments"]}
chk("X_userdep", "USER 출발 시각 입력 시에만 상태 판정 (R AT_RISK→H07, O 도착, C 도착, 택시 Soft)",
    st.get("J-R-ARRIVE") in ("AT_RISK", "FAIL") and "J-O-ARRIVE" in st and st.get("J-C-ARRIVE") == "AT_RISK"
    and st.get("J-TAXI") == "AT_RISK" and any(h["text"].startswith("H07") for h in r["human_next"]), st)
for n in ("E1", "E2", "E3", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"):
    r = A(n)
    miss = [i["text"][:30] for k in ("conclusion", "why", "unknown", "human_next", "actions") for i in r[k] if not i["sources"]]
    miss += [k["title"] for k in r["kpi"] if not k["sources"]]
    chk(f"SRC-{n}", "모든 문장에 출처 ID", not miss, miss)
    chk(f"LINT-{n}", "금지 표현 0건", not r["lint"], r["lint"])

# ---------- 독립 검증보고(검증보고.md) 중대 오류 회귀 ----------
v4 = cmp(A("V4"), "subway")
chk("REG-E1", "E-1 공연 18:00 → P 출발 SAFE는 16:15까지, 17:00~17:10 AT_RISK, 17:11 이후 FAIL (공연 연쇄 반영)",
    status_at(v4, "16:15") == "SAFE" and status_at(v4, "16:16") == "AT_RISK" and status_at(v4, "17:05") == "AT_RISK"
    and status_at(v4, "17:11") == "FAIL" and all(not (s == "SAFE" and b >= "17:00") for a, b, s in v4), v4)
ov4 = cmp(A("O_V4_C1800"), "subway")
chk("REG-E1b", "E-1 oracle 입력(V4_C1800)에서도 17:00 이후 SAFE 없음", not any(s == "SAFE" and b >= "17:00" for a, b, s in ov4), ov4)
chk("REG-E1c", "E-1 기본 입력은 구속 조건이 전망대 실내 입장(결과 불변)", e1["compare"][0]["binding"]["binding"] == "전망대 실내 입장"
    and A("V4")["compare"][0]["binding"]["binding"] == "공연 연쇄", (e1["compare"][0]["binding"]["text"], A("V4")["compare"][0]["binding"]["text"]))
xn = A("X_null_C")
chk("REG-E2", "E-2 공연 마감 null → 배지 UNKNOWN (SAFE 아님)", xn["badge"] == "UNKNOWN" and "판정 불가 1건" in xn["badge_note"], (xn["badge"], xn["badge_note"]))
chk("REG-E2b", "E-2 기본 입력 배지에 판정 건수·미판정 건수 표시", e1["badge"] == "SAFE" and "Hard 판정 1건 기준" in e1["badge_note"] and "미판정 2건" in e1["badge_note"], e1["badge_note"])
o3 = A("O_ORC3a1_durations")
chk("REG-I5", "I-5 입력된 P 체류시간이 '미사용' 안내로 표시", any("P_stay=180분" in u["text"] and "판정에 쓰지 않음" in u["text"] for u in o3["unknown"]),
    [u["text"][:40] for u in o3["unknown"]])
jr = J(e1, "J-R-LASTDEP"); jm = J(e1, "J-M-STAY")
chk("REG-I8", "I-8 판정 상세의 최소/최대 칸 채움", bool(jr["min_basis"]) and bool(jr["max_basis"]) and bool(jm["min_basis"]), (jr["min_basis"], jm["max_basis"]))
o2 = A("O_ORC3a2_usertimes")
st2 = {j["id"]: (j["status"], j.get("data", {}).get("arr")) for j in o2["judgments"]}
chk("ORC-3a2", "oracle: C AT_RISK 18:35~18:45, O AT_RISK", st2["J-C-ARRIVE"] == ("AT_RISK", [1115, 1125]) and st2["J-O-ARRIVE"][0] == "AT_RISK", st2)
oo2 = A("O_ORC2_arrival1040")
chk("ORC-2", "oracle: 도착 10:40 → M FAIL, 배지 FAIL, C 판정 E1과 동일", J(oo2, "J-M-ENTRY")["status"] == "FAIL" and oo2["badge"] == "FAIL"
    and J(oo2, "J-O-LASTDEP")["data"] == J(e1, "J-O-LASTDEP")["data"], oo2["badge"])

w = max(len(r[0]) for r in results)
fails = [r for r in results if r[2] == "Fail"]
for r in results:
    print(f"{r[0]:<{w}} {r[2]:<4} {r[1]} | {r[3]}")
print(f"\n합계 {len(results)} / Pass {len(results) - len(fails)} / Fail {len(fails)}")
sys.exit(1 if fails else 0)
