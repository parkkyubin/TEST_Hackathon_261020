"""트립메이트 UI (Streamlit, TD1·TD2). 실행: python -m streamlit run app.py
첫 화면은 결론 / KPI / WHY / UNKNOWN / HUMAN NEXT 다섯 블록만, 상세는 모두 접기 (DESIGN §5.1).
"""
import copy
import hashlib
import json
import os

import streamlit as st

from tripmate.model import m2t
from tripmate.pipeline import run, fmt_interval


ROOT = os.path.dirname(os.path.abspath(__file__))
PWC = {"orange": "#D04A02", "tangerine": "#EB8C00", "red": "#E0301E", "dark": "#2D2D2D",
       "grey": "#7D7D7D", "bg": "#F2F2F2", "rose": "#DB536A"}
STATUS_COLOR = {"SAFE": PWC["dark"], "AT_RISK": PWC["tangerine"], "FAIL": PWC["red"],
                "UNKNOWN": PWC["grey"], "INFO": PWC["grey"]}

# 폼에서 바꿀 수 있는 값 — (그룹, 키, 라벨, 종류)
FIELDS = [
    ("meta", "now", "현재 시각", "time"), ("meta", "arrival", "서울역 도착", "time"),
    ("deadlines", "C_entry", "공연 입장 마감", "time"), ("deadlines", "O_indoor", "전망대 실내 입장 마감", "time"),
    ("deadlines", "M_window_end", "미술관 입장 마감", "time"), ("deadlines", "R_grace", "식당 지각 허용(분)", "int"),
    ("travel_window", "window_start", "점검 시작", "time"), ("travel_window", "window_end", "점검 끝", "time"),
    ("travel_window", "subway_extra", "점검 추가시간 [최소,최대]", "range"),
    ("user_times", "dep_M", "미술관 출발 예정(USER)", "time"), ("user_times", "dep_P", "한강공원 출발 예정(USER)", "time"),
    ("user_times", "P_O_mode", "P→O 수단(USER: subway/bus/taxi)", "str"), ("user_times", "dep_O", "전망대 출발 예정(USER)", "time"),
    ("durations", "R_meal", "식사 시간(분, USER)", "int"), ("prefs", "budget", "이동비 예산(원)", "int"),
]

st.set_page_config(page_title="트립메이트", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"""<style>
h1 {{ color:{PWC['orange']}; }}
.blk {{ border-left:4px solid {PWC['orange']}; padding:8px 14px; background:{PWC['bg']}; border-radius:4px; margin-bottom:6px; color:{PWC['dark']}; }}
.badge {{ display:inline-block; padding:1px 10px; border-radius:10px; color:#fff; font-size:13px; margin-right:6px; }}
.src {{ font:11px monospace; color:{PWC['grey']}; }}
.soft {{ outline:1px solid {PWC['rose']}; }}
</style>""", unsafe_allow_html=True)


def load_sample():
    with open(os.path.join(ROOT, "sample_input.json"), encoding="utf-8") as fh:
        return json.load(fh)


def md(text):
    """마크다운 취소선(~~) 오인 방지: 범위 표기 '~' 를 이스케이프."""
    return str(text).replace("~", r"\~")


def hx(text):
    """HTML 블록 안에서는 마크다운 이스케이프 대신 문자 참조로."""
    return str(text).replace("~", "&#126;")


def src_tag(item):
    return f"<span class='src'>[{']['.join(item['sources'])}]</span>"


def badge(status):
    return f"<span class='badge' style='background:{STATUS_COLOR.get(status, PWC['grey'])}'>{status}</span>"


def bullets(items):
    for i in items:
        st.markdown(f"- {md(i['text'])} {src_tag(i)}", unsafe_allow_html=True)


# ---------- 입력 상태 (이전 입력·결과가 섞이지 않게) ----------
ss = st.session_state
ss.setdefault("upload_key", 0)
ss.setdefault("base", load_sample())
ss.setdefault("base_name", "sample_input.json")

with st.sidebar:
    st.header("입력")
    up = st.file_uploader("입력 JSON 업로드", type=["json"], key=f"up{ss.upload_key}")
    if up is not None:
        digest = hashlib.sha1(up.getvalue()).hexdigest()
        if ss.get("upload_digest") != digest:  # 새 파일이면 기준 입력을 교체하고 이전 결과를 지움
            try:
                ss.base = json.loads(up.getvalue().decode("utf-8"))
                ss.base_name = up.name
                ss.upload_digest = digest
                ss.pop("result", None)
                ss.form_ver = ss.get("form_ver", 0) + 1
            except Exception as e:  # noqa: BLE001
                st.error(f"JSON 읽기 오류: {e}")
    if st.button("샘플로 초기화 (입력·결과·폼 리셋)"):
        nxt = ss.upload_key + 1  # 새 위젯 키 → 업로더에 남은 이전 파일도 비움
        for k in list(ss.keys()):
            del ss[k]
        ss.upload_key = nxt
        st.rerun()
    st.caption(f"기준 입력: {ss.base_name}")
    use_llm = st.checkbox("LLM 요약 사용", value=True)

    # E-3: 폼 위젯 키에 초기화 nonce(upload_key)와 업로드 버전을 함께 넣어, 초기화·업로드 때 이전 폼 값이 남지 않게 한다
    fkey = f"{ss.upload_key}.{ss.get('form_ver', 0)}"
    with st.form(f"f{fkey}"):
        st.caption("값을 바꾸면 source=USER 로 기록됩니다. 빈칸 = 미정(null).")
        vals = {}
        for g, k, label, kind in FIELDS:
            node = (ss.base.get(g) or {}).get(k) or {}
            cur = node.get("value")
            shown = "" if cur is None else (json.dumps(cur) if kind == "range" else str(cur))
            vals[(g, k, kind)] = (st.text_input(label, value=shown, key=f"{g}.{k}.{fkey}"), shown)
        submitted = st.form_submit_button("실행")

if submitted:
    data = copy.deepcopy(ss.base)
    for (g, k, kind), (new, old) in vals.items():
        if new.strip() == old:
            continue
        v = None if not new.strip() else new.strip()
        if v is not None and kind == "int":
            try:
                v = int(v)
            except ValueError:
                pass  # 검증 단계에서 의미 있는 오류로 표시
        if v is not None and kind == "range":
            try:
                v = json.loads(v)
            except ValueError:
                pass
        data.setdefault(g, {})[k] = {"value": v, "source": "USER", "kind": "assumption" if g in ("user_times", "durations") else "fixed"}
    ss.result = run(data, use_llm=use_llm)
    ss.result_input = data
elif "result" not in ss:  # 첫 화면·업로드 교체 직후: 기준 입력 그대로 1회 실행
    ss.result_input = copy.deepcopy(ss.base)
    ss.result = run(ss.result_input, use_llm=use_llm)

st.title("트립메이트 — 일정 변경 판단 도우미")
res = ss.get("result")
if not res.get("ok"):
    st.error("입력 오류 — 아래 항목을 고친 뒤 다시 실행하세요.")
    for e in res["errors"]:
        st.markdown(f"- {e}")
    st.stop()

llm = res["llm"]
st.markdown(badge(res["badge"]) + f"<span class='src'>{res['badge_note']}</span><br><span class='src'>{llm['status']}{' — ' + llm['detail'] if llm.get('detail') else ''}</span>",
            unsafe_allow_html=True)

# 1 결론
st.subheader("결론")
for c in res["conclusion"]:
    st.markdown(f"<div class='blk'>{badge(c['status']) if c.get('status') else ''}{hx(c['text'])} {src_tag(c)}</div>",
                unsafe_allow_html=True)

# 2 KPI (제안·미승인)
st.subheader("KPI")
st.caption(res["kpi_note"])
cols = st.columns(len(res["kpi"]))
for col, k in zip(cols, res["kpi"]):
    with col:
        # TD2: streamlit-shadcn-ui metric_card 가 이 환경에서 렌더되지 않아 같은 형태의 HTML 카드로 대체
        st.markdown(f"<div class='blk'><b>{hx(k['title'])}</b><br><span style='font-size:20px'>{hx(k['value'])}</span>"
                    f"<br>{src_tag(k)}</div>", unsafe_allow_html=True)

# 3 WHY
st.subheader("WHY")
bullets(res["why"])

# 4 UNKNOWN
st.subheader("UNKNOWN — 판정하지 않은 것")
bullets(res["unknown"][:3])
if len(res["unknown"]) > 3:
    with st.expander(f"나머지 {len(res['unknown']) - 3}건"):
        bullets(res["unknown"][3:])

# 5 HUMAN NEXT
st.subheader("HUMAN NEXT — 마감 임박순")
bullets(res["human_next"][:3])
if len(res["human_next"]) > 3:
    with st.expander(f"나머지 {len(res['human_next']) - 3}건"):
        bullets(res["human_next"][3:])

st.divider()
with st.expander("행동 우선순위 A (마감 시각순, Hard/Soft 라벨)"):
    bullets(res["actions"])
with st.expander("판정 상세 — 최소 소요 기준 / 최대 소요 기준"):
    for j in res["judgments"]:
        f = lambda b: ", ".join(f"{k} {m2t(v)}" for k, v in b.items()) if b else "-"
        st.markdown(f"{badge(j['status'])} **{j['title']}** [{j['label']}] — 최소 소요 기준: {f(j.get('min_basis'))} · "
                    f"최대 소요 기준: {f(j.get('max_basis'))} {src_tag(j)}", unsafe_allow_html=True)
with st.expander("P→O 이동수단 비교표 (추천 없음 — H03·H04 확인 후 선택)"):
    for title, key in (("전망대 실내 입장 마감 기준", "compare"), ("원안 17:00 도착 기준 (참고, Hard 아님)", "compare_ref")):
        st.markdown(f"**{title}**")
        for c in res[key]:
            st.markdown(f"*{c['label']}*")
            for r in c["intervals"]:
                st.markdown(f"{badge(r['status'])} {md(fmt_interval(r))} <span class='src'>[D03][D06][AP2]</span>", unsafe_allow_html=True)
with st.expander("참고 일정표 B (원안 시각 + USER 입력 가정만)"):
    for r in res["reference"]:
        calc = "" if not r["calc"] else f" → {'도착' if r['calc'][0] == 'arr' else '출발'} {m2t(r['calc'][1])}~{m2t(r['calc'][2])}"
        plan = "" if r["plan"] is None else f"원안 {m2t(r['plan'])}"
        tag = " **[USER] 사용자 입력 가정**" if r.get("user") else ""
        st.markdown(f"- {r['place']}: {plan}{md(calc)}{tag} {r.get('note', '')} {src_tag(r)}", unsafe_allow_html=True)
with st.expander("LLM 요약"):
    st.write(llm["text"] or f"({llm['status']}) 규칙 기반 출력만 표시합니다.")
with st.expander("입력값 (이번 실행)"):
    st.json(ss.result_input)
