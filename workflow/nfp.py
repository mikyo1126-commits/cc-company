#!/usr/bin/env python3
"""
米雇用統計の速報（発表から1〜3分）と、結果を受けた見通しの投稿

  python3 workflow/nfp.py check   # 今が発表日の待機時間内かを判定（GitHub Actions 用）
  python3 workflow/nfp.py run     # 予想を調べて発表まで待ち、速報 → 見通しの順に投稿
  python3 workflow/nfp.py test    # 公式データの最新の結果で速報の文面を表示するだけ（投稿しない）

速報の文面はコードで作る（発表の瞬間にAIは文章を書かない）。
数字は米労働省（BLS）の公式データAPIから読み、対象月が今回の月に更新されるまで投稿しない。
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).parent.parent
SCHEDULE_PATH = ROOT_DIR / "workflow" / "nfp_schedule.json"
NY = ZoneInfo("America/New_York")
JST = ZoneInfo("Asia/Tokyo")
BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
PAYROLLS = "CES0000000001"     # 非農業部門雇用者数（季節調整済み・千人）
UNEMPLOYMENT = "LNS14000000"   # 失業率（季節調整済み・%）

WAIT_BEFORE = timedelta(hours=4, minutes=30)   # 発表のこれだけ前から待機してよい（ジョブの上限6時間に収める）
LATE_LIMIT = timedelta(minutes=10)             # これより遅れて起動したら速報にならないので何もしない
POLL_FAST = (timedelta(minutes=10), 3)         # 発表から10分間は3秒おき
POLL_GIVE_UP = timedelta(minutes=60)           # 1時間たっても更新されなければ諦める（発表延期など）
FOLLOWUP_DELAY = timedelta(minutes=8)          # 見通し投稿は、ニュースと値動きが出そろうまで少し待ってから作る


# ──────────────────────────────────────────
# 発表日
# ──────────────────────────────────────────

def load_schedule() -> list[dict]:
    return json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))


def release_time(entry: dict) -> datetime:
    y, m, d = map(int, entry["release"].split("-"))
    return datetime(y, m, d, 8, 30, tzinfo=NY)


def current_release(now: datetime) -> dict | None:
    for entry in load_schedule():
        at = release_time(entry)
        if at - WAIT_BEFORE <= now <= at + LATE_LIMIT:
            return entry
    return None


# ──────────────────────────────────────────
# 公式データ（BLS API）
# ──────────────────────────────────────────

def fetch_bls(key: str, year: int) -> dict[str, list[dict]]:
    import requests
    resp = requests.post(BLS_URL, json={
        "seriesid": [PAYROLLS, UNEMPLOYMENT], "registrationkey": key,
        "startyear": str(year - 1), "endyear": str(year),
    }, timeout=10)
    body = resp.json()
    if body.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS API: {body.get('status')} {body.get('message')}")
    return {s["seriesID"]: s["data"] for s in body["Results"]["series"]}


def month_key(year_month: str) -> tuple[str, str]:
    y, m = year_month.split("-")
    return y, f"M{int(m):02d}"


def previous_month(year_month: str) -> str:
    y, m = map(int, year_month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def value_for(data: list[dict], year_month: str) -> str | None:
    y, p = month_key(year_month)
    for row in data:
        if row["year"] == y and row["period"] == p:
            return row["value"]
    return None


def read_result(series: dict[str, list[dict]], ref_month: str) -> dict | None:
    """対象月のデータが出ていれば結果を返す。まだ先月までなら None（古い数字を出さない）"""
    payrolls_now = value_for(series[PAYROLLS], ref_month)
    payrolls_prev = value_for(series[PAYROLLS], previous_month(ref_month))
    rate_now = value_for(series[UNEMPLOYMENT], ref_month)
    if payrolls_now is None or payrolls_prev is None or rate_now is None:
        return None
    # 雇用者数の増減は、今回の発表に含まれる前月（改定後）との差。米労働省の発表の数字と同じ計算
    return {
        "payrolls_change_k": int(round(float(payrolls_now))) - int(round(float(payrolls_prev))),
        "unemployment": round(float(rate_now), 1),
    }


# ──────────────────────────────────────────
# 文面
# ──────────────────────────────────────────

def man(k: int, sign: bool = True) -> str:
    """千人単位を「+14.3万人」の形に（端数は丸めない）"""
    s = f"{abs(k) / 10:.1f}万人"
    if not sign:
        return s
    return ("+" if k > 0 else "−" if k < 0 else "±") + s


def compare_payrolls(result_k: int, forecast_k: int) -> str:
    d = result_k - forecast_k
    if d == 0:
        return "→ 予想どおり"
    return f"→ 予想を{man(d, sign=False)}{'上回った' if d > 0 else '下回った'}"


def compare_rate(result: float, forecast: float) -> str:
    d = round(result - forecast, 1)
    if d == 0:
        return "→ 予想どおり"
    return f"→ 予想を{abs(d):.1f}ポイント{'上回った' if d > 0 else '下回った'}"


def flash_text(ref_month: str, result: dict, forecast: dict | None) -> str:
    month_label = f"{int(ref_month.split('-')[1])}月分"
    lines = [f"【速報】米雇用統計（{month_label}）", "", "■ 雇用者数", f"結果：{man(result['payrolls_change_k'])}"]
    if forecast:
        lines += [f"予想：{man(forecast['payrolls_k'])}", compare_payrolls(result["payrolls_change_k"], forecast["payrolls_k"])]
    lines += ["", "■ 失業率", f"結果：{result['unemployment']:.1f}%"]
    if forecast:
        lines += [f"予想：{forecast['unemployment']:.1f}%", compare_rate(result["unemployment"], forecast["unemployment"])]
    return "\n".join(lines)


# ──────────────────────────────────────────
# 予想（発表前に調べておく）
# ──────────────────────────────────────────

FORECAST_PROMPT = """\
米雇用統計（{ref_label}分、発表は日本時間 {release_jst}）の市場予想を、WebSearchで調べてください。

- 調べるのは「非農業部門雇用者数の前月比の予想」と「失業率の予想」の2つ
- 2つ以上の独立した情報源（通信社・金融メディア・経済指標カレンダーなど）で確認する
- 情報源の間で値が違う場合は、多くの情報源が載せている値を使う。どうしても1つに決められなければ、その項目は null にする
- 雇用者数は千人単位の整数で書く（例: 予想が+5.5万人＝55,000人なら 55）。失業率は%の数字（例: 4.4）

最後に次の形だけを出力する:
<json>{{"payrolls_k": 55, "unemployment": 4.4, "sources": ["情報源1", "情報源2"]}}</json>
"""


def get_forecast(ref_month: str, release_at: datetime) -> dict | None:
    sys.path.insert(0, str(Path(__file__).parent))
    import auto_post as ap
    seconds_left = (release_at - datetime.now(NY)).total_seconds() - 90
    if seconds_left < 60:
        print("::warning::発表までに予想を調べる時間がないため、予想なしで速報を出す")
        return None
    prompt = FORECAST_PROMPT.format(
        ref_label=f"{ref_month.split('-')[0]}年{int(ref_month.split('-')[1])}月",
        release_jst=release_at.astimezone(JST).strftime("%m/%d %H:%M"),
    )
    try:
        raw = ap.call_claude(prompt, timeout=int(min(600, seconds_left)))
        m = re.search(r"<json>(.*?)</json>", raw, re.DOTALL)
        data = json.loads(m.group(1)) if m else {}
    except Exception as e:  # 予想が取れなくても速報は出す
        print(f"::warning::予想を取得できなかった: {e}")
        return None
    payrolls, rate = data.get("payrolls_k"), data.get("unemployment")
    if not (isinstance(payrolls, int) and -1000 <= payrolls <= 1000 and isinstance(rate, (int, float)) and 2 <= rate <= 15):
        print(f"::warning::予想の値が不正なので使わない: {data}")
        return None
    print(f"予想: 雇用者数 {man(payrolls)} / 失業率 {rate}%（{', '.join(data.get('sources', []))}）")
    return {"payrolls_k": payrolls, "unemployment": round(float(rate), 1)}


# ──────────────────────────────────────────
# 実行
# ──────────────────────────────────────────

def wait_until(at: datetime) -> None:
    seconds = (at - datetime.now(NY)).total_seconds()
    if seconds > 0:
        print(f"{at.astimezone(JST):%H:%M:%S} JST まで {int(seconds)} 秒待機")
        time.sleep(seconds)


def poll_result(key: str, entry: dict) -> dict | None:
    release_at = release_time(entry)
    ref_month = entry["reference_month"]
    while datetime.now(NY) < release_at + POLL_GIVE_UP:
        try:
            result = read_result(fetch_bls(key, int(ref_month[:4])), ref_month)
            if result:
                return result
        except Exception as e:
            print(f"公式データの取得に失敗（再試行）: {e}")
        fast = datetime.now(NY) < release_at + POLL_FAST[0]
        time.sleep(POLL_FAST[1] if fast else 20)
    return None


def post(text: str, slot: str) -> None:
    import auto_post as ap
    if not os.environ.get("TWITTER_API_KEY"):
        print(f"\n（ドライラン）投稿する本文:\n{text}")
        return
    tweet_id = ap.post_to_x(text)
    print(f"✅ 投稿完了: https://x.com/hajime_cp/status/{tweet_id}")
    ap.record_post(tweet_id, slot, text)


def run() -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    import auto_post as ap
    entry = current_release(datetime.now(NY))
    if not entry:
        print("今は雇用統計の発表日の待機時間ではない")
        return
    key = os.environ["BLS_API_KEY"]
    release_at, ref_month = release_time(entry), entry["reference_month"]
    print(f"発表: {release_at.astimezone(JST):%Y-%m-%d %H:%M} JST（{ref_month} 分）")

    forecast = get_forecast(ref_month, release_at)
    wait_until(release_at - timedelta(seconds=3))
    result = poll_result(key, entry)
    if not result:
        print("::warning::発表から1時間たっても公式データが今回の月に更新されなかったため、投稿しない（発表延期の可能性）")
        sys.exit(1)
    print(f"結果: {result}（発表から {int((datetime.now(NY) - release_at).total_seconds())} 秒）")
    post(flash_text(ref_month, result, forecast), "nfp_flash")
    Path(".nfp-posted").write_text("posted")  # 速報を出したことをワークフローに伝える（重複防止の記録用）

    ap.NFP_CONTEXT.update({
        "month_label": f"{int(ref_month.split('-')[1])}月",
        "payrolls": man(result["payrolls_change_k"]),
        "payrolls_fc": man(forecast["payrolls_k"]) if forecast else "不明",
        "rate": f"{result['unemployment']:.1f}%",
        "rate_fc": f"{forecast['unemployment']:.1f}%" if forecast else "不明",
    })
    wait_until(release_at + FOLLOWUP_DELAY)
    ap.RUN_CONTEXT["slot"] = "nfp_followup"
    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    text = ap.generate_and_verify(date_str, "nfp_followup")
    problems = ap.find_problems(text)
    if problems:
        print(f"::warning::見通し投稿は投稿前チェックで止めた: {problems}")
        sys.exit(1)
    post(text, "nfp_followup")


def test() -> None:
    """公式データの今の最新月で文面を作って表示する（投稿しない）"""
    key = os.environ["BLS_API_KEY"]
    now = datetime.now(NY)
    series = fetch_bls(key, now.year)
    latest = series[PAYROLLS][0]
    ref_month = f"{latest['year']}-{int(latest['period'][1:]):02d}"
    result = read_result(series, ref_month)
    print(f"公式データの最新月: {ref_month}  結果: {result}")
    print("\n--- 速報の文面（予想は仮の値）---")
    print(flash_text(ref_month, result, {"payrolls_k": result["payrolls_change_k"] - 20, "unemployment": result["unemployment"]}))
    upcoming = [e for e in load_schedule() if release_time(e) > now]
    print(f"\n次回の発表: {upcoming[0]['release'] if upcoming else '予定表に未登録（workflow/nfp_schedule.json に追加が必要）'}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "check":
        entry = current_release(datetime.now(NY))
        print(f"go={'true' if entry else 'false'}")
        if entry:
            print(f"release={entry['release']}")
    elif mode == "run":
        run()
    elif mode == "test":
        test()
