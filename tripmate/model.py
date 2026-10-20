"""입력 접근·검증 (TD6 model). 모든 말단 값은 {value, source, kind} (D-2). value=null 은 미정."""
import re

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
RANGE_KEYS = {("travel", k) for k in ("station_M", "M_R", "R_P", "P_O", "O_C")} | \
             {("travel_window", k) for k in ("subway_extra", "bus", "taxi")}
TIME_KEYS = {("meta", "now"), ("meta", "arrival"), ("meta", "departure"),
             ("deadlines", "C_entry"), ("deadlines", "O_indoor"), ("deadlines", "M_window_start"),
             ("deadlines", "M_window_end"), ("deadlines", "M_free_cancel"), ("deadlines", "R_time"),
             ("travel_window", "window_start"), ("travel_window", "window_end"),
             ("user_times", "dep_M"), ("user_times", "dep_R"), ("user_times", "dep_P"), ("user_times", "dep_O")} | \
            {("plan", k) for k in "MRPOC"}
INT_KEYS = {("deadlines", "M_max_stay"), ("deadlines", "R_grace"), ("durations", "M_stay"), ("durations", "R_meal"),
            ("durations", "P_stay"), ("durations", "O_stay"), ("prefs", "budget"), ("prefs", "taxi_max"),
            ("prefs", "rain_outdoor_max"), ("user_times", "taxi_uses"), ("meta", "party")}
MODES = ("subway", "bus", "taxi")


class InputError(Exception):
    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = errors


def t2m(s):
    m = TIME_RE.match(str(s).strip())
    return int(m.group(1)) * 60 + int(m.group(2))


def m2t(m):
    m = int(m)
    return f"{m // 60:02d}:{m % 60:02d}"


class Input:
    """검증된 입력. get() 은 (값 또는 None, source) 를 돌려준다."""

    def __init__(self, data):
        if not isinstance(data, dict):
            raise InputError(["입력 최상위는 JSON 객체여야 합니다."])
        self.d = data
        self.errors = []
        self._validate()
        if self.errors:
            raise InputError(self.errors)

    def node(self, group, key):
        g = self.d.get(group)
        if isinstance(g, dict):
            return g.get(key)
        return None

    def raw(self, group, key):
        n = self.node(group, key)
        if isinstance(n, dict):
            return n.get("value")
        return None

    def src(self, group, key):
        n = self.node(group, key)
        return n.get("source", "?") if isinstance(n, dict) else "?"

    def time(self, group, key):
        v = self.raw(group, key)
        return None if v is None else t2m(v)

    def rng(self, group, key):
        v = self.raw(group, key)
        return None if v is None else (int(v[0]), int(v[1]))

    def num(self, group, key):
        v = self.raw(group, key)
        return None if v is None else int(v)

    def _validate(self):
        for (g, k) in sorted(TIME_KEYS | RANGE_KEYS | INT_KEYS):
            n = self.node(g, k)
            label = f"{g}.{k}"
            if n is None:
                continue  # 없는 항목은 미정과 같게 처리
            if not isinstance(n, dict) or "value" not in n:
                self.errors.append(f"{label}: {{value, source, kind}} 형식이 아닙니다.")
                continue
            for f in ("source", "kind"):
                if not n.get(f):
                    self.errors.append(f"{label}: {f} 가 비어 있습니다 (D-2).")
            v = n["value"]
            if v is None:
                continue
            if (g, k) in TIME_KEYS and not TIME_RE.match(str(v).strip()):
                self.errors.append(f"{label}: 시각 형식 오류 '{v}' (HH:MM, 예 09:20).")
            elif (g, k) in RANGE_KEYS:
                if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)):
                    self.errors.append(f"{label}: [최소, 최대] 숫자 2개여야 합니다. 받은 값: {v}")
                elif v[0] > v[1]:
                    self.errors.append(f"{label}: 최소({v[0]})가 최대({v[1]})보다 큽니다.")
                elif v[0] < 0:
                    self.errors.append(f"{label}: 음수 소요시간({v[0]})은 허용되지 않습니다.")
            elif (g, k) in INT_KEYS and (isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0):
                self.errors.append(f"{label}: 0 이상의 숫자여야 합니다. 받은 값: {v}")
        mode = self.raw("user_times", "P_O_mode")
        if mode is not None and mode not in MODES:
            self.errors.append(f"user_times.P_O_mode: {', '.join(MODES)} 중 하나여야 합니다. 받은 값: {mode}")
        ws, we = self.raw("travel_window", "window_start"), self.raw("travel_window", "window_end")
        if ws and we and TIME_RE.match(str(ws)) and TIME_RE.match(str(we)) and t2m(ws) >= t2m(we):
            self.errors.append(f"travel_window: 시작({ws})이 끝({we})보다 같거나 늦습니다.")
