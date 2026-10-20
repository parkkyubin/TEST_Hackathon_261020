"""LLM 폴백 점검 (R11, R12). .env 는 열지 않는다. 키 값은 출력하지 않는다.
LLM-0: 실제 연결(.env + 셸 LLM_MODEL) / LLM-1: 키 없음 / LLM-2: 잘못된 키 / LLM-3: 잘못된 주소 / LLM-4: 모델 미설정"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tripmate import llm_client
from tripmate.pipeline import run
data = json.load(open("sample_input.json", encoding="utf-8"))
case = sys.argv[1]
if case != "LLM-0":
    llm_client._load_env = lambda: None  # .env 를 쓰지 않는 조건을 만든다
    for k in ("ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "LLM_MODEL"):
        os.environ.pop(k, None)
    if case in ("LLM-2", "LLM-3"):
        os.environ["LLM_MODEL"] = "claude-sonnet-5-5"
        os.environ["ANTHROPIC_API_KEY"] = "invalid-test-key"
        os.environ["ANTHROPIC_BASE_URL"] = "https://api.anthropic.com" if case == "LLM-2" else "http://127.0.0.1:9"
    if case == "LLM-4":
        os.environ["ANTHROPIC_API_KEY"] = "x"; os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:9"
r = run(data, use_llm=True)
print(json.dumps({"case": case, "ok": r["ok"], "blocks": [len(r[k]) for k in ("conclusion", "why", "unknown", "human_next")],
                  "llm_status": r["llm"]["status"], "detail": r["llm"]["detail"][:120], "text_len": len(r["llm"]["text"]),
                  "text": r["llm"]["text"][:400]}, ensure_ascii=False))
