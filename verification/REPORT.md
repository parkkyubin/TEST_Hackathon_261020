# 검증 보고서 (verification/REPORT.md)

- 작성: ③ 검증 세션 (담당: `verification/` 폴더만, CR1)
- 기대결과 작성: 2026-10-20 13:18 착수 → 13:20 저장 완료 (구현 코드·실행 결과 열람 전, §0-B 독립성)
- 본 보고 작성 시점: 2026-10-20 13:20

## 0. 결론 요약

**모든 실행 테스트가 미실행이다(S9).** 13:20 기준 작업 폴더에 `README.md`, 소스 코드, `sample_input.json`이 없고 git 저장소도 없음(`fatal: not a git repository`). `docs/` 폴더만 생성되는 중이다(② 세션 진행 중으로 보임). README의 실행 방법이 없어 S8 절차("README 순서대로만 실행")를 시작할 수 없다.

## 1. 사용한 시험 자료

| 자료 | 위치 | 상태 |
|---|---|---|
| 기본 입력 TC0 (D01~D08) | `expected/TC0.md` | 기대결과 작성, 실행 **미실행** |
| 변형 입력 TC1~TC8 (V1~V8) | `expected/TC1.md`~`TC8.md` | 기대결과 작성, 실행 **미실행** |
| 경계값 C/O/R 직전·직후 | `expected/BV_boundary.md` | 판정 기준 작성, 구체 수치는 TC0 실제 출력 확인 후 결정 → **미실행** |
| LLM 키 없음/잘못된 키/주소 오류 | `expected/LLM_fallback.md` | 기대결과 작성, 실행 **미실행** |
| 저장소·README 공통 점검 X1~X11 | `expected/COMMON_checks.md` | **미실행** |
| 판정 원칙·금지 표현 목록 | `expected/00_공통기준.md` | — |

입력 형식 문서가 없어 변경값은 자료 항목(D0x) 의미로만 기술했다. 실제 입력 필드 매핑은 실행 시 `actual/`에 기록 예정.

## 2. 기대 결과 (요약 — 상세는 expected/)

| 케이스 | 핵심 기대 | Hard 판정 포인트 |
|---|---|---|
| TC0 | M·R·C 유지, P 축소/대체(또는 선택지), P→O 지하철 50~75분 반영, O 실내 유지 | CH1 C ≤18:40, CH4 O ≤18:00, CH3 R ≤13:15, H01(09:30) |
| TC1 (비 20%/3m/s) | P 유지 쪽(TC0보다 길거나 같음), D06 교통 경고는 유지 | CH1·CH4 |
| TC2 (95%/14m/s) | P ≤30분/대체/생략, 데크 폐쇄 "가능" 강조, H05·H08 | 유지 강도 TC1 ≥ TC0 ≥ TC2 |
| TC3 (+60분) | 지하철 90~105분 반영, 택시/버스 권고, H04 | CH1·CH4 재계산 |
| TC4 (C 18:00) | 오후 대폭 축소, O 생략 가능, 18:00 USER 표시 | C ≤18:00 |
| TC5 (O 17:00) | O 도착 ≤17:00 불가 시 제외 | CH4 |
| TC6 (예산 2만) | 택시 비추천/경고, 요금 미정이면 Unknown+H04 | CH1 > CS1 |
| TC7 (도착 10:30) | M 도착 10:55~11:05 → 입장 위험 경고 | CH2 (min/max 걸침 → 위험 표시) |
| TC8 (지각 0분) | R 한도 13:00 표시, 버퍼 감소 | CH3 |
| BV | max ≤ 마감 충족(정각 포함), 초과 시 조정/경고, min/max 걸침은 위험 | J3, J4 |
| LLM | 키 없음/오류에도 O1~O4 출력 + "LLM 미연결", 키 미노출 | R12, D-7 |

## 3. 실제 결과 / Pass·Fail

| 케이스 | 실제 결과 | 판정 |
|---|---|---|
| TC0~TC8 | 없음 | **미실행** — 실행 대상 프로그램·README 부재 |
| BV-C1~C4, BV-O1~O2, BV-R1~R2 | 없음 | **미실행** — 같은 이유 + TC0 실제 출력 필요 |
| LLM-0~LLM-3 | 없음 | **미실행** — 같은 이유 |
| X1 README 4항목 | README 없음 | **Fail(현재 시점)** — 13:20 기준 |
| X2 README 실행 | — | **미실행** |
| X3, X7~X11 | — | **미실행** |
| X4·X5 `git ls-files` / 키 검색 | git 저장소 없음 | **미실행** — 저장소 생성 후 재점검 |
| X6 `.env.example` 안내 | — | **미실행** |

`verification/actual/`은 비어 있다(실행 결과 없음).

## 4. 확인된 오류 (재현 방법 포함)

| ID | 내용 | 재현 | 심각도 |
|---|---|---|---|
| ERR-01 | `README.md` 없음 → 실행 경로 없음 (S4, S8) | `ls <작업 폴더>` (13:20) | Hard (진행 중일 수 있음) |
| ERR-02 | 실행 코드·입력 파일(`sample_input.json` 등) 없음 → R1~R12 검증 불가 | 같음 | Hard (진행 중일 수 있음) |
| ERR-03 | git 저장소 미초기화 → S1, S7a(`.env` 미추적) 점검 불가 | `git status` → `not a git repository` | Hard (제출 전 필요, 생성은 사용자 승인 사항 HC1) |

※ 위 항목은 결함 확정이 아니라 **13:20 시점 상태**다. 구현 완료 후 재검증한다.

## 5. 미실행 항목과 이유

- TC0~TC8, BV 전 항목, LLM-0~3, X2~X11: 실행할 프로그램과 README가 없음.
- BV 구체 입력 수치: 체류시간 기본값(HB4 미정)에 따라 도착 시각이 달라져 TC0 실제 출력이 필요함.
- LLM-0(정상 키): `.env`가 없음. 검증 세션은 키 파일을 열거나 복사하지 않는다(HC3은 사용자/② 담당).

## 6. 구현 세션(②)에 전달할 수정 요청 (우선순위순)

1. **[Hard] README.md 작성** — S4 4항목 + 정확한 설치·실행 명령(S8) + 입력 변경 방법(R6) + `.env.example`→`.env` 설정 안내(S7b). 완료되면 ③에 알려 재검증.
2. **[Hard] 실행 코드 + 기본 입력 파일** — 입력값마다 출처(source)·성격(kind) 필드(D-2), 출력 O1~O4, Hard/Soft 라벨, 출처 ID.
3. **[Hard] Hard 시간 판정**: 이동시간 `min~max` 병기, min ≤ 마감 < max는 "위험"으로 표시(R8). 마감 "까지"는 포함(≤) 처리. HB3 결정 전엔 기준을 설정값으로 분리.
4. **[Hard] D06 점검 지연은 P→O 15~17시 출발에 적용**(지하철 50~75분), 날씨 입력과 독립.
5. **[Hard] E10 금지 표현 린트**를 규칙 엔진·LLM 출력 모두에 적용.
6. **[Soft/R12] LLM 폴백**: 키 없음·잘못된 키·주소 오류 시 크래시·키 노출 없이 "LLM 미연결" 표시.
7. **[CR3] 미정값(HB2 임계값, HB4 체류·요금)**: 임의 수치로 확정하지 말고 입력 파라미터 + ASM 표시.
8. **[S7a] 저장소 생성 시** `.gitignore`에 `.env`, 값 없는 `.env.example`만 커밋 (저장소 생성·push는 사용자 승인, HC1).

## 7. 재검증 계획

README와 코드가 생기면, README 명령만 사용해 TC0 → TC1~TC8 → BV → LLM-1/2 → X1~X11 순서로 실행한다. 결과는 `actual/`에 저장하고 이 문서를 갱신한다.

---

# 구현 세션 검증 (DESIGN v0.3 기준)

- 임시 권한: 부여자 사용자 / 범위 `verification/` 이번 검증·재검증 / 사유 구현 세션이 검증까지 수행 (CR1). 위 ③ 세션 원문(§0~§6)은 수정하지 않고 보존.
- 대상 코드: `tripmate/`(model·engine·conclude·kpi·lint·llm_client·pipeline·__main__), `app.py`(Streamlit), `sample_input.json`
- 환경: Windows 11, Python 3.15.0, streamlit 1.66.0, anthropic 1.15.0, python-dotenv 1.2.4
- 도구: 입력 `verification/inputs/*.json`(21개), CLI 결과 `verification/actual/*.json`, 자동 대조 `verification/check_expected.py`, LLM 점검 `verification/check_llm.py`, UI는 브라우저(localhost:8501)에서 조작

## A. 재검증 회차

| 회차 | 일시 | 범위 | 결과 | 오류·수정 |
|---|---|---|---|---|
| 1 | 2026-10-20 14:00 | CLI 61건(E1~E3, V1~V8, 이상 입력, 출처, 린트), LLM 5건, UI(폼·업로드·리셋) | CLI 61/61 Pass, LLM 5/5 Pass, UI **2건 Fail** | ERR-11, ERR-12 (아래) |
| 2 | 2026-10-20 14:02~14:05 | 1~4 전체 처음부터 (CLI 61건, LLM 5건, UI 전 항목, 서버 재시작 후) | **전부 Pass** (CLI 61/61, LLM 5/5, UI 9/9) | — |
| 3 | 2026-10-20 14:10~14:12 | README 작성 후 현재 코드로 CLI 61건·LLM 폴백 4건 재실행 + S8(README 명령을 새 셸·작업 폴더 사본에서 실행) | **전부 Pass** (CLI 61/61, LLM-1~4 4/4, S8 4/4) | — |

### 오류와 수정 이력
| ID | 회차 | 내용 | 원인 | 수정 |
|---|---|---|---|---|
| ERR-11 | 1 | "샘플로 초기화" 후에도 업로더에 이전 파일명이 남음 → 다음 실행에 이전 업로드가 다시 섞일 위험 | 초기화 시 업로더 위젯 키를 같은 값(0)으로 되돌림 | `app.py` 초기화 시 위젯 키를 증가시켜 새 업로더 생성 |
| ERR-12 | 1 | `plan.P`가 없는 입력에서 H08(P 진입 전)이 HUMAN NEXT 최상단(가장 임박)으로 표시 | 정렬 키 기본값이 0 | `tripmate/conclude.py` 정렬 키 기본값을 하루 끝(24:00)으로 |
| (참고) | 1 | 수정 후 UI가 옛 모듈로 동작 | Streamlit 실행 중에는 import한 모듈이 다시 로드되지 않음 | 서버 재시작 후 2회차 수행 |
| (참고) | 구현 중 | 마크다운이 `~` 두 개를 취소선으로 처리해 "15:00~17:00"이 깨짐, shadcn `metric_card`가 이 환경에서 렌더되지 않음 | Streamlit 마크다운 규칙 / 컴포넌트 iframe 미표시 | `~` 이스케이프, KPI는 같은 형태 HTML 카드로 대체(TD2 폴백) |

## B. 요구사항 대조표 (1) — 문제 원본

대조 기준: 과제 요건(최소 기능·제출물·실행 가능성)과 D01~D08. 항목 ID는 docs/REQUIREMENTS.md §4·§5. 2회차 기준.

| ID | 요건 | 판정 | 증거 |
|---|---|---|---|
| R1 | 입력: 파일/폼/CLI | 충족 | `app.py:79` 업로드, `app.py:100` 폼, `tripmate/__main__.py` `--input` · UI 업로드·폼 테스트 Pass |
| R2 | 규칙·계산으로 결과 도출 | 충족 | `tripmate/engine.py:12` status_of, `:32` p_o_range, E1-1~E1-7 Pass |
| R3 | O1~O4 출력 | 부분 충족 | O1=행동 우선순위 A + 참고 일정표 B(AP5), O2=WHY, O3=UNKNOWN·판정 상세(최소/최대), O4=HUMAN NEXT. **장소별 "유지/변경/대체" 라벨은 없음** — 설계(DESIGN §0 P0·P1, AP4 추천 없음)상 일정 변경 추천을 하지 않기 때문 |
| R4 | Hard/Soft 라벨 | 충족 | 행동 우선순위 `[Hard]`/`[Soft]`, 판정 상세 label · E3-4 Pass |
| R5 | 항목별 출처 ID | 충족 | SRC-E1~V8 11건 Pass (모든 문장·KPI에 출처) |
| R6 | 소스 수정 없이 변경·재실행 | 충족 | V1~V8, X_* 입력 파일만 바꿔 실행, UI 폼 변경 → FAIL 반영 |
| R7 | 하드코딩 금지 | 충족 | `tripmate/conclude.py:8` 템플릿 T, E2-5(E1과 결과 다름), V4·X_window 결과 변화 |
| R8 | 확정 표현 금지 | 충족 | `tripmate/lint.py:6`, LINT-E1~V8 11건 0건, LLM 출력도 린트(`llm_client.py`) |
| R9 | Unknown/Human check 구분 | 충족 | UNKNOWN 블록(U01·U03·U09·U10·HB2·HB4), HUMAN NEXT(H01~H08) · E1-10 Pass |
| R10 | 핵심 흐름 처음~끝 | 충족 | 입력→판정→결론→WHY→Human next, UI·CLI 모두 다섯 블록 (UI 9/9) |
| R11 | LLM 연결 | 충족(조건부) | LLM-0 "LLM 연결됨"(응답 615자, 린트·수치 검사 통과). 단 `.env`에 `LLM_MODEL`이 없어 **셸 변수 `LLM_MODEL`로 실행**했다 — `.env`에 모델 변수 추가 필요(사용자) |
| R12 | LLM 장애 시 폴백 | 충족 | LLM-1 키 없음, LLM-2 잘못된 키(401), LLM-3 주소 오류, LLM-4 모델 미설정 → 모두 블록 정상 + "LLM 미연결" |
| R13 | README에 설계 판단 | 충족 | `README.md` ④ "주요 설계 판단" 표 |
| S1 | GitHub 공개 저장소 | 미충족 | 저장소 생성·push는 사용자 승인 대기 (HC1) |
| S2, S2a, S3 | 링크 메일 발송·동결 | 해당없음 | 사용자 수행 |
| S4 | README 4항목 | 충족 | `README.md` ①문제 정의 ②실행·사용 방법 ③검증 결과 ④구현 범위 |
| S5 | 작동 방식·설계 판단 | 충족 | `README.md` ④ 주요 설계 판단·파일 구성 |
| S8 | README 명령 그대로 동작 | 충족 | 3회차: 새 셸(셸의 ANTHROPIC_*·LLM_MODEL 제거)·사본 폴더에서 `python -m pip install -r requirements.txt`(exit 0) → `cp .env.example .env` → `python -m tripmate --input sample_input.json --format text`(exit 0, 다섯 블록, "LLM 미연결") → `--format json`(exit 0, ok=True) → `python -m streamlit run app.py`(다섯 블록, 예외 0) |
| S10 | 코드·README 일치 | 충족 | 3회차 대조: 의존성 3개 = requirements.txt, CLI 옵션 `--input`/`--format`/`--no-llm`·오류 시 exit 2 = `tripmate/__main__.py`, 환경변수 3개 = `.env.example`·`llm_client.py`, 파일 구성 표 = 실제 파일 |
| S6 | sample input | 충족 | `sample_input.json` (DESIGN §4 값, 모든 값 {value, source, kind}) |
| S7, S7a | 키 미포함, `.env` 미추적 | 충족 | `.gitignore:1` `.env`, `git ls-files`에 `.env` 없음 (14:05 확인), `.env.example` 값 비움 |
| S7b | README 설정 안내(값 미기재) | 충족 | `README.md` ② "2. LLM 설정" — 변수명만, 값 없음 |
| S9 | 미실행을 실행으로 쓰지 않음 | 충족 | 본 보고는 실제 실행 결과만 기재, 미실행 항목은 §F |
| S11 | 미완성·한계 README 기재 | 충족 | `README.md` ④ 미완성/알려진 한계·미정 항목 |

## C. (2) 샘플 실행 — UI·CLI 일치

| 검사 | 기대 | 실제 | 판정 |
|---|---|---|---|
| CLI `python -m tripmate --format text` | 다섯 블록 출력 | 결론(SAFE)·KPI 3·WHY 3·UNKNOWN 상위 3·HUMAN NEXT 상위 3 (`actual/E1_cli.txt`) | Pass |
| UI 첫 화면 | 다섯 블록만, 상세 접기 | 다섯 블록 표시, 상세 expander 8개 모두 닫힘 | Pass |
| UI 결론 = CLI 결론 | 같은 문장 | 두 결론 문자열 동일 ("…18:10(최대 소요 기준)~18:20(최소 소요 기준)… 09:30 전 미술관 유지/취소 결정") | Pass |

## D. (3) Stress test

| 입력 | 기대 | 실제 | 판정 |
|---|---|---|---|
| V1 강수 20%·3m/s | 예보 값 반영 | H02에 20%·3m/s, P 판정 없음(HB2) | Pass* |
| V2 강수 95%·14m/s | 예보 값 반영, 데크 확인 | H02 95%·14m/s, H05 유지 | Pass* |
| V3 점검 추가 +60분 | 지하철 소요 증가·구간 재계산 | 지하철 90~105분, SAFE 끝 16:15로 앞당겨짐, 버스·택시 비교 유지 | Pass* |
| V4 공연 마감 18:00 | 전망대 최종 출발 재계산 | 17:30/17:40 | Pass |
| V5 전망대 마감 17:00 | P 출발 구간 재계산 | 16:11 이후 FAIL | Pass |
| V6 예산 2만 원 | H04 반영 | H04 "20000원", 요금 미정이라 판정 안 함 | Pass* |
| V7 도착 10:30 | M 입장창 판정 | 10:55~11:05 → AT_RISK, 결론에 경고 | Pass |
| V8 지각 허용 0분 | R 기준 변화 | 좌석 보장 기준 출발 12:35/12:40 | Pass |
| X_null_C 공연 마감 null | 죽지 않음, UNKNOWN | UNKNOWN, "계산하지 않았습니다" 결론 | Pass |
| X_badtime "9시20분" | 의미 있는 오류 | "meta.arrival: 시각 형식 오류 '9시20분' (HH:MM, 예 09:20)." (CLI·UI 동일) | Pass |
| X_minmax O_C [30,20] | 의미 있는 오류 | "travel.O_C: 최소(30)가 최대(20)보다 큽니다." | Pass |
| X_neg M_R [-5,10] | 의미 있는 오류 | "음수 소요시간(-5)은 허용되지 않습니다." | Pass |
| X_badmode P_O_mode=plane | 의미 있는 오류 | "subway, bus, taxi 중 하나여야 합니다" | Pass |
| X_notjson 깨진 JSON | 의미 있는 오류 | "입력 JSON 형식 오류: …" (exit 2) | Pass |
| X_missingkey O_indoor 삭제 | 죽지 않음 | 비교표 없이 정상 출력 | Pass |
| X_window 점검 16:00~18:00 | 겹침 구간 이동 | 15:15까지 평상시 SAFE, 겹침 구간 재계산 | Pass |
| X_hugedelay +300~600분 | 죽지 않음 | 겹침 구간 FAIL | Pass |
| X_userdep USER 출발 시각 입력 | 입력 구간만 상태 판정 | R AT_RISK→H07, O 도착·C 도착 판정, 택시 2회 > 1회 Soft | Pass |
| LLM-1~4 키 없음·잘못된 키·주소 오류·모델 미설정 | 폴백 + 상태 표시, 키 미노출 | 모두 "LLM 미연결" + 사유, 블록 정상 | Pass |
| UI 상태: 폼 변경 → 업로드 → 초기화 | 이전 입력·결과 섞이지 않음 | 폼 10:40→FAIL, 업로드 시 FAIL 사라지고 폼 값 교체, 초기화 시 파일·결과·폼 모두 샘플로 | Pass (2회차) |

\* docs/REQUIREMENTS.md §4의 기대 방향 중 **판정이 필요한 부분**(V1 "P 유지 쪽", V2 "P 축소/실내 대체", V3 "O 생략 또는 P 축소", V4 "O 생략 가능", V6 "택시 비추천")은 구현하지 않았다. DESIGN v0.3 범위(P0·P1만, AP4 추천 없음, HB2 임계값 미정)와 충돌하기 때문이다. expected는 고치지 않고 사용자에게 보고한다.

## E. (4) 독립 expected 3건 (DESIGN §7) — CLI JSON 대조

| 검사 | 판정 | 실제 (요약) |
|---|---|---|
| E1-1 M 도착 09:45~09:55 SAFE | Pass | SAFE, [09:45, 09:55] |
| E1-2 M 최종 출발 12:35/12:40, 12:50/12:55 | Pass | 동일 |
| E1-3 O 최종 출발 18:10/18:20, Hard, D02·D03 | Pass | 동일 |
| E1-4 지하철 구간표 | Pass | ~16:45 SAFE / 16:46~16:59 AT_RISK / 17:00~17:15 SAFE / 17:16~17:30 AT_RISK / 17:31~ FAIL |
| E1-5 버스·택시 겹침 SAFE, 17:00 이후 UNKNOWN | Pass | 버스 14:11~16:59 SAFE, 택시 14:26~16:59 SAFE, 그 밖 UNKNOWN(U10) |
| E1-6 추천 없음, H03·H04 정보 | Pass | 추천 문구 없음, H03에 수단별 소요·최종 출발 |
| E1-7 참고 B (O 17:00) | Pass | 지하철 ≤15:45 SAFE·~16:10 AT_RISK, 버스 ≤16:10, 택시 ≤16:25 SAFE |
| E1-8 날씨 예보 표시, P 판정 없음, H02·H08 | Pass | 동일 |
| E1-9 최상단 H01 (남은 10분) | Pass | 동일 |
| E1-10 U01·U03·체류시간, 예산 판정 없음 | Pass | 동일 |
| E1-11 금지 표현 0건 | Pass | 0건 |
| E2-1 M 11:05~11:15 FAIL(Hard) | Pass | 동일 |
| E2-2 결론 FAIL, 취소 권고 없음, 사실+H01 | Pass | 결론 2번째 줄 FAIL, H01에 "09:30까지 취소 시 전액 환불" 사실만 |
| E2-3 서울역→R 직행 UNKNOWN | Pass | UNKNOWN 목록에 표시 |
| E2-4 C·O 결과 E1과 동일 | Pass | judgments·비교표 동일 |
| E2-5 E1과 다른 결과 | Pass | 배지 SAFE→FAIL |
| E3-1 R 출발 14:30, P 14:55~15:05, [USER] | Pass | 동일 |
| E3-2 Hard 판정 E1과 동일 | Pass | 동일 |
| E3-3 P·O 체류 UNKNOWN 유지 | Pass | 동일 |
| E3-4 시각순, Hard/Soft 라벨 | Pass | 동일 |
| E3-5 날씨·수단·예산 판정 없음 | Pass | 동일 |

## F. 미실행 항목과 사유

| 항목 | 사유 |
|---|---|
| ③ 세션 `expected/TC0~TC8`, `BV_boundary`, `COMMON_checks` 개별 대조 | v0.3 이전(docs/REQUIREMENTS.md만 기준) 작성. 이번 지시 범위는 DESIGN §7 E1~E3 + REQUIREMENTS §4 V1~V8 + 이상 입력 |
| LLM-0을 `.env`만으로 실행 | `.env`에 `LLM_MODEL` 없음. `.env`를 열지 않는 조건이라 셸 변수로만 확인 |
| 다른 PC·새 가상환경에서의 설치 | 이 PC에서만 실행 (S8은 같은 PC의 새 셸·사본 폴더) |

---

# 구현 세션 재검증 — 독립 검증보고(`검증보고.md`) 반영 (2026-10-20 14:21~14:28)

- 임시 권한: 부여자 사용자 / 범위 `verification/` 이번 검증·재검증 / 사유 구현 세션이 검증 수행 (CR1). ③의 `검증보고.md`, `expected/*`, `actual/oracle/*`는 수정하지 않았다. oracle 입력 4개를 `inputs/O_*.json`으로 복사해 재실행했다.

## G. 대상 SHA (최종 5회차 실행 대상 = 작업 트리, 미커밋)

| 항목 | 값 |
|---|---|
| git HEAD | `9ee484c38f8e01ca149712da964cc0daeeb4feef` (구버전. 검증 대상은 아래 작업 트리이며 커밋은 사용자 승인 대기 — 검증보고 I-6) |
| sha256 앞 12자리 | README.md `366ad0bf732d` · app.py `fac458507a51` · sample_input.json `7f16f350942b` · requirements.txt `e3a1e952d388` · .env.example `0dac128dbb96` · .gitignore `5e3f17ec4dc6` · __main__.py `0f724390f30c` · model.py `c05063fc02d4` · engine.py `3ada550e358d` · conclude.py `d915d26915ea` · kpi.py `dbdd4907ba07` · lint.py `1556dc1c67e8` · llm_client.py `142c1b4eccc6` · pipeline.py `adfbf50543cf` |
| 검증보고 시점 대비 변경 | engine.py(`29dd027546f7`→), conclude.py(`9cd6e1329c8b`→), kpi.py, pipeline.py, app.py, requirements.txt, README.md. model·lint·llm_client·__main__·sample_input 불변 |

## H. 검증보고 지적 사항 처리

| ID | 판정 | 원인 | 수정 | 재검증 |
|---|---|---|---|---|
| E-1 P 출발 SAFE 구간에 공연 연쇄 미반영 | 결함 인정 (DESIGN B3 연쇄 누락) | P→O 구간표 기준을 전망대 실내 입장(18:00)만 사용 | `engine.o_deadline()`: 전망대 도착 한도 = min(실내 입장, 공연 − O→C), 최대·최소 소요 기준 각각, 구속 조건·출처 표시. J-O-ARRIVE에도 적용 | REG-E1: V4에서 SAFE ~16:15, 16:16~16:50 AT_RISK, 17:00~17:10 AT_RISK, 17:11~ FAIL, 17:00 이후 SAFE 없음 Pass · REG-E1b oracle `V4_C1800` Pass · REG-E1c 기본 입력은 구속 조건 "전망대 실내 입장"이라 E1 결과 불변 Pass |
| E-2 미판정·판정 불가인데 배지 SAFE | 결함 인정 | 판정된 Hard만으로 SAFE 결정 | 배지 = FAIL > UNKNOWN > AT_RISK > SAFE, 판정 불가 Hard 있으면 UNKNOWN, `badge_note`에 "Hard 판정 n건 기준 · 판정 불가 · 미판정 m건(사유)" 표시 (CLI·JSON·UI 동일) | REG-E2: C_entry null → UNKNOWN Pass · REG-E2b 기본 입력 SAFE + "판정 1건 기준 · 미판정 2건" Pass · UI 업로드(null)에서 UNKNOWN Pass |
| E-3 초기화 후 폼 값 잔존 | 결함 인정 (2회차 UI 점검은 업로드 후 초기화 절차라 놓침) | 업로드 없이 초기화하면 폼 위젯 키가 같아 브라우저가 값을 유지 | 폼 위젯 키에 초기화 nonce 포함 | 검증보고 절차 그대로: 공연 18:00 실행 → 초기화 → 폼 18:40, 재실행 결과 18:40 Pass |
| I-4 U09 표기 | 반영 | — | WHY·KPI2에 U09 출처, "1분이라도 겹치면 범위 전체" 문구 | 출처 검사 Pass |
| I-5 P_stay 입력 무시 안내 없음 | 반영 | — | UNKNOWN에 "입력됨 — 순방향 전파(P0-C) 범위 밖이라 판정에 쓰지 않음" | REG-I5 Pass |
| I-6 HEAD ≠ 검증 대상 | 미처리 | 커밋 금지 지시 | 사용자 승인 대기 | — |
| I-7 버전 미고정 | 반영 | — | requirements.txt `==` 고정 | S8 설치 Pass |
| I-8 판정 상세 빈칸 | 반영 | — | J-R-LASTDEP·J-M-STAY 최소/최대 칸 채움 | REG-I8 Pass |
| I-9 now < arrival 문구 | 미처리 | 결함 아님(검증보고 판단) | — | — |
| ORC-3a1 연쇄 미계산 | 설계 범위 | HB1 P0-C 배제 | 안내만 추가(I-5) | — |

## I. 회차 (계속)

| 회차 | 일시 | 범위 | 결과 | 오류·수정 |
|---|---|---|---|---|
| 4 | 14:21~14:26 | E-1·E-2·E-3·I-4·5·7·8 수정 후 CLI 70건(회귀 9건 추가), LLM 폴백 4, 실제 LLM, UI(검증보고 E-3 절차, 폼·업로드·초기화·오류 입력·null 배지) | CLI 1차 69/70 → **X_missingkey Fail** | 원인: 구현 세션 자체 기대값이 E-1 이전 동작(전망대 마감 없으면 비교표 없음)을 가정. B3 연쇄상 공연 한도로 비교표를 만드는 것이 맞아 기대값을 수정("공연 연쇄 18:10/18:20 기준 비교") → 70/70 |
| 5 (최종) | 14:27~14:28 | 1)~4) 전체 처음부터: CLI 70건, LLM 폴백 4, 실제 LLM, S8(새 셸·사본) | **전부 Pass**: CLI 70/70 (`actual/check_round5.txt`), LLM-1~4 "LLM 미연결" + 블록 정상, LLM-0 "LLM 연결됨"(650자, 린트·수치 검사 통과), S8 pip·text·json exit 0 | — |
| UI (4회차 코드 = 최종 코드) | 14:23~14:26 | 다섯 블록, 결론 UI=CLI, 폼 변경 FAIL 반영, 업로드 교체(null → UNKNOWN), 초기화(파일·폼·결과), 25:99 오류 메시지, 예외 0 | **전부 Pass** | 캡처: `screenshots/ui_01_original.jpg`(원본, LLM 연결됨), `screenshots/ui_02_stress_V4_C1800.jpg`(공연 18:00 → 전망대 17:30/17:40, KPI SAFE 13:00~16:15) |

## J. LLM 연결 테스트 (R11)

| 케이스 | 조건 | 결과 |
|---|---|---|
| LLM-0 | `.env`의 `ANTHROPIC_BASE_URL`·`ANTHROPIC_API_KEY` + 모델 ID `LLM_MODEL=claude-sonnet-5-5`(셸 변수 — 제공 `.env`에 모델 변수 없음, RU4) | 원본·V4 모두 "LLM 연결됨". V4 요약에 "17:30/17:40", "13:00~16:15" 등 엔진 결과 수치만 사용 → 수치 검사·린트 통과 |
| UI | 미리보기 서버에 `LLM_MODEL`만 환경변수로 전달 | 화면 "LLM 연결됨" (캡처 2장) |
| LLM-1~4 | 키 없음 / 잘못된 키(401) / 접속 불가 주소 / 모델 미설정 | 모두 "LLM 미연결" + 사유, 다섯 블록 정상, 키 문자열 출력 0건 |

## K. 기대 vs 설계 차이 (사용자 판단 대기, expected 미수정)

- docs/REQUIREMENTS.md §4 V1·V2·V3·V4·V6의 "P 유지/축소, O 생략, 택시 비추천" 판정: DESIGN v0.3 범위(P0·P1, AP4, HB2) 밖이라 미구현. 값 반영·재계산만 Pass.
- ③ `expected/TC0~TC8`: v0.3 이전 기준이라 개별 대조 미실행.

## L. 설계명세(DESIGN.md) 갱신 요청 — ① 세션 소유라 미수정

| 위치 | 현재 | 실제 구현 | 요청 → **처리: 사용자 임시 권한(세션 내 모든 파일, 최종 수정)으로 DESIGN v0.4에 반영** |
|---|---|---|---|
| §2 TD2·TD5 | streamlit-shadcn-ui 사용·의존성 | 렌더 불가로 미사용, 의존성 제외 | TD2·TD5 갱신 |
| §3.2 T4 | 수단별 "P 최종 출발" 기준 미명시 | 기준 = min(O 실내 입장, C − O→C) (B3) | 기준 마감 명시 |
| §5.1 | 상단 배지 규칙 없음 | FAIL > UNKNOWN > AT_RISK > SAFE + 판정/미판정 건수 | 배지 규칙 추가 |
| §2 TD5 | 버전 미고정 | `==` 고정 | 반영 |

## M. 미실행

- 다른 PC·OS 설치 (같은 PC 새 셸·사본으로만 S8)
- ③ expected TC0~TC8 개별 대조 (K 참고)

## N. 최종 수정 (사용자 임시 권한: 부여자 사용자 / 범위 세션 내 모든 파일 / 사유 최종 수정, CR1)

| 항목 | 내용 | 결과 |
|---|---|---|
| DESIGN.md v0.4 | L절 요청 4건(TD2·TD5·T4·§5.1 배지) 반영 | 구현·README와 일치 |
| `.env` | 내용을 열지 않고 `LLM_MODEL=claude-sonnet-5-5` 한 줄만 덧붙임 | LLM-0(셸 변수 없이 `.env`만): "LLM 연결됨", 665자 (`actual/LLM-0_envonly.json`) · `git ls-files`에 `.env` 없음 |
| UI | 미리보기 서버에서 `LLM_MODEL` 환경변수 제거 후 `.env`만으로 실행 | 아래 결과 |
| UI 결과 | 셸 변수 없이 `.env`만으로 실행 (14:30) | 상단 "LLM 연결됨", 다섯 블록, 예외 0 — Pass |
| 최종 SHA 추가 | docs/DESIGN.md `e1c95fc3d556` · README.md `366ad0bf732d` · .claude/launch.json(로컬 미리보기, 미커밋 대상) | 코드 파일 SHA는 G절과 동일(5회차 이후 코드 변경 없음) |

## O. 제출 전 점검 (14:36)

| 항목 | 결과 |
|---|---|
| 비밀값 (S7) | API 키·접속 주소 문자열: `.env` 외 파일 0건. `.env`·`.claude/` git 무시 확인 |
| 개인 정보 | 개인 계정 정보가 든 원천 자료 파일을 저장소 밖으로 이동. PC 사용자명이 든 경로를 가림 |
| 원천 자료 | 원천 자료 원문 파일을 저장소 밖으로 이동, `.gitignore`에 `*.docx`·`*.pdf` 추가 |
| 회귀 | 이동·문서 수정 후 `check_expected.py` 70/70 Pass, CLI 기본 실행 정상 (코드 변경 없음) |
| SHA (갱신) | README.md `d8f280c86483` · docs/REQUIREMENTS.md(정제본, 기존 기준 문서 대체) · REPORT.md는 본 표 작성 직후 값 |
