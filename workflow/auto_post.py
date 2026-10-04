#!/usr/bin/env python3
"""
自動投稿スクリプト（生成→検証→修正ループ→投稿）

フロー:
  1. 投稿文を生成（WebSearch付きClaude）
  2. 全ての事実主張を検証（WebSearchで裏取り）
  3. 問題があれば修正し再検証（最大3回）
  4. 検証パスのみ投稿、失敗なら中断

Usage:
    python3 workflow/auto_post.py morning
    python3 workflow/auto_post.py noon
    python3 workflow/auto_post.py evening
"""

import json
import os
import random
import re
import sys
import subprocess
import tempfile
import time
import tweepy
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
SLOT_LABELS = {"morning": "朝", "noon": "昼", "evening": "晩"}
ROOT_DIR = Path(__file__).parent.parent
INSIGHTS_PATH = ROOT_DIR / "workflow" / "insights.md"
POSTED_LOG = ROOT_DIR / "workflow" / "posted_log.jsonl"
MAX_VERIFY_ATTEMPTS = 3

# ──────────────────────────────────────────
# プロンプト定義
# ──────────────────────────────────────────

GENERATE_PROMPT = """\
あなたはFX・ゴールド・株価指数を扱うトレーダーの「はじめ」本人として、今日の{slot_label}のX（旧Twitter）投稿を1本書きます。

【最重要】この投稿はAIが書いたと気づかれてはいけない。
トレーダー本人が今この瞬間に感じたこと・気づいたことをそのまま書いたような「人間らしい文章」にすること。

---

## STEP 1: 今の相場をWebSearchで確認する

{theme_rule}

ビットコイン・仮想通貨は扱わない（はじめさん本人がビットコインの投稿をしていて、内容がぶつかるため）。
過去分析インサイトにビットコインの話が出てきても、それは参考データとしてだけ読み、テーマには選ばない。

確認したら:
- **数値を使う場合は必ず2つ以上の独立したソースで裏取りする**
- 裏取りできなかった情報・数値は絶対に使わない
- 方向感は「〜を試しそうだ」「〜に向かう可能性がある」の形で書いてよいが、「〜になる」「確実」のような断定はしない

---

## STEP 2: 投稿文を書く

### ❶ 人間らしさの絶対ルール（最優先）

**やること:**
- 「けど」「なんか」「謎に」「なんで」「どうせ」「正直」などの口語を自然に使う
- 語尾は言い切る。「っぽい」「かも」「気がする」のような軽く見える語尾は使わない
  - 値動きの理由や今の状況の説明は言い切る（✗「金利がつかない弱みが勝ったっぽい」→ ○「金利がつかない弱みが勝った」）
  - この先の見通しは「〜そうだ」「〜と見ている」で書く（✗「分かれ目になりそう」→ ○「分かれ目になりそうだ」）
  - ただし「〜になる」「〜は確実」のように将来の値動きを断定はしない
- 驚きや感情が伝わる表現を入れる（「大丈夫か？」「急に強くなった」「やけに」など）
- 「昨日」「今朝」「さっき」「今週」など時間的文脈を自然に入れる
{emoji_rule}

**絶対にやらないこと:**
- 箇条書き（◽️・■）や見出し構造は使わない
- 「〜が重要です」「〜を意識しましょう」「参考になれば」などの解説調は使わない
- 3点セット（「①②③」「まず〜次に〜最後に」）は使わない
- 「ではまた」などの定型締めは使わない
- AI特有の丁寧語（「〜となります」「〜をご確認ください」）は絶対に使わない
- 投稿を「まとめ」で締めない

### ❷ 文体の細かいルール

- 一人称: 「僕」
- 文末: 句点「。」を付けない（体言止め・タメ口調で締める）
- 文章スタイル: 空行で段落を区切る
- 文字数: 100〜160文字
- 行数: 4〜6行（空行含む）

### ❸ 内容のルール

- 価格や価格の水準は数字で一切書かない。「160円」「156円台」「3,500ドル」のようなキリのいい節目も書かない
  → 「200日線」「直近高値」「節目」「大台」「三尊のネックライン」「MACDのデッドクロス」などの言葉で表す
  （初心者向け基礎の「仮にドル円150円で1万通貨なら」のような仮の計算例だけは例外）
- チャートの節目・構造（三尊・ネックライン・週足・ピンバー・MACD等）への言及は高評価につながる
- RSIは使わない。オシレーター系を使う場合はMACDに統一する
- アフィリエイト案件（Vantage Trading、FXGT等）には触れない（触れると景品表示法・ステマ規制上の開示表記が必要になるため）
- 「僕も最初は〜だった」「昔〜して損した」のような、はじめさん本人の過去の体験は、失敗談の投稿で登録済みエピソードを使う場合を除いて書かない（本人に無い体験を作ると事実でない投稿になるため）
- 「なぜそうなったか」の自分なりの解釈を入れる
- 方向感（「上を試しそうだ」「下に向かう可能性がある」）はOK。「〜になる」「確実」の断定はNG

### ❹ トレーダーとしての見せ方（重要）

はじめさんは「常に相場環境を見て、自分のルール・ノウハウ通りに淡々とトレードしている」プロ。
感情や不安で動くトレーダーに見える書き方はしない。

- 判断の理由は「感情」ではなく「相場環境・ルール」で書く
  - NG: 「怖いから」「不安だから」「自信がない」「迷ってる」「読み切れてない」
  - OK: 「飛び乗るのは危険だから」「リスクが高いから」「ルール外だから」「環境認識的にまだ早い」
- 価格分析の投稿（値動き・まとめ・ファンダメンタル・来週の注目イベント）では、「僕はここから入りたい」「確認してからエントリーしたい」のような自分のエントリー時期・入る条件は書かない
  - 締めは相場の見方か、どこが分かれ目か・どこに注目するかで終える
  - OK: 「落ちない値動きは強い」「来週はこの指標が分かれ目になりそうだ」「ここを抜けるかどうかで景色が変わる」
- どの投稿でも、トレードそのものをやめる方向の締めはしない
  - NG: 「今日は様子見」「トレードは控える」「見送る」「休む」

### ❺ スロット別の自然なトーン

- 朝（9時ごろ投稿）: 「昨夜のNY時間の動きと、今日どこに注目するか」を語る雰囲気
- 昼: 「午前の動きを見て感じたこと」を会話するような雰囲気
- 晩（18時ごろ投稿）: 「今日の東京時間の振り返りと、今夜の欧州・NY時間に向けてどこを見るか」を語る雰囲気

---

### 文体の参考例

はじめさんの高反応だった投稿の口調を、ドル円・ナスダック・ゴールドに当てはめた参考例（実際の投稿ではない）。
口調と構成の参考として使い、文面はそのまま使わない。

例1:
ドル円

CPIで方向は出ず『行って来い』の値動き

『ここから一気に円安か？』
と飛び乗った人はヤラれた

高値圏はサッと抜けないと危険

例2:
ゴールド

やけに弱くなったけど大丈夫か？

日足の短期線を割ってきたから、ここで買いに飛び乗るのはリスクが高い
下で止まれるかどうかが分かれ目になりそうだ

例3:
ナスダック

三尊のネックラインを割ったと見せかけて謎に落ちなかった🚀
FOMCの初動の下落でも崩れなかった

落ちない値動きは強い

→ 共通点: 1行目にテーマ名、短い文、口語、疑問・驚き、「謎に」「やけに」などの感覚的な言葉、チャート用語、相場の見方で締める

---

今日: {date}（{slot_label}）
"""

WEEKDAY_THEME = """平日の投稿は、下の【初心者向けの基礎】か【失敗談】が基本。相場の値動きの投稿は、急騰・急落と言える大きな値動きがあった時だけにする。

まずWebSearchで、ナスダック・ゴールド・ドル円（メイン）と日経平均（サブ）に大きな値動きがあったかを確認する。
目安: 直近24時間でドル円が1円以上、ゴールドやナスダックが2%以上、日経平均が3%以上動いた。または指標発表・要人発言などで短時間に急変した。
値動きの幅は2つ以上のソースで確認し、日中の高値・安値ベースか終値ベースかを投稿の中で混ぜない。
目安に届いているか微妙なときは、大きな値動きなしとして扱う。

大きな値動きがあった場合: その銘柄の値動きについて投稿する（1行目はテーマ名）。日経平均はメイン3銘柄と合わせて触れるか、日経平均だけが大きく動いた時に取り上げる。
大きな値動きがなかった場合: 値動きの話はせず、次の内容で投稿する。どちらにしたかの説明は書かない。

{evergreen}"""

BASICS_THEME = """【初心者向けの基礎】
ロット計算、証拠金、レバレッジ、スワップ、pips、損切り幅の決め方など、FXを始めたばかりの人が保存したくなる内容を1つに絞る。
- 教科書っぽい解説調ではなく、はじめさんが後輩に教えるような口調で書く。計算例は改行で見やすく並べてよい（◽️や■は使わない）
- 数字の例は「仮にドル円150円で1万通貨なら」のように仮の数字だと分かる書き方にし、計算は必ず合っていること
- 国内口座と海外口座で条件が違うもの（レバレッジの上限、1ロットの通貨量など）は、どちらの話かを書く
- 業者名は出さない
- 1行目は「証拠金」「ロット計算」のようなラベルにせず、続きを読みたくなる一文にする（例: 「必要証拠金ぴったりで入るのが、一番危ない入り方」。文面はそのまま使わない）。2行目以降でその答えが分かる流れにする。煽りすぎや、事実と合わない言い切りはしない
- 120〜200文字まで可
- 締めは「これを知ってから入るだけで全然違う」のように、正しくトレードしたくなる前向きな一言にする"""

STORY_THEME = """【失敗談・人間味のある話】
「昔これで大損した」「この失敗があって今のルールを作った」系の話にする。
最後は、今はルール通りにトレードしているから大丈夫、という前向きな形で締める（❹の人物像を崩さない）。120〜200文字まで可。
1行目はラベルにせず、続きを読みたくなる一文にする（例: 「損切りを1回ずらしたのが、退場の始まりだった」。文面はそのまま使わない）
{episodes}"""

EPISODES_PATH = ROOT_DIR / "workflow" / "episodes.md"


def load_episodes() -> list[str]:
    if not EPISODES_PATH.exists():
        return []
    return [l[2:].strip() for l in EPISODES_PATH.read_text(encoding="utf-8").splitlines()
            if l.startswith("- ") and l[2:].strip()]


def episodes_rule() -> str:
    episodes = load_episodes()
    if episodes:
        listed = "\n".join(f"- {e}" for e in episodes)
        return ("失敗談は、次のはじめさん本人の実際のエピソードから1つ選んで書く。"
                "ここに書かれていない出来事・金額・時期は足さない（事実でない体験談は信用を失うため）:\n" + listed)
    return ("はじめさん本人の実際の失敗エピソードはまだ登録されていない。"
            "本人の体験として出来事・金額・時期を作ると事実でない話になるので、"
            "「これで退場する人は本当に多い」のように、よくある失敗パターン（損切りを動かす、ナンピンを繰り返す、"
            "指標発表で飛び乗る、負けを取り返そうとロットを上げる等）として書く。「僕も昔〜した」のような本人の体験としては書かない")

WEEKEND_COMMON = """
今日は{day_label}（日本時間）で市場は休場。「午前の動き」「今夜のNY時間」など平日の言い方はしない。
対象はドル円・ナスダック・ゴールド（1つでも、まとめてでもよい）。土日の投稿は120〜200文字まで長くしてよい。
土日の投稿は1行目に「ドル円」「ゴールド」などのテーマ名を置かず、いきなり本文から書き始める（参考例の1行目のテーマ名は平日用）。
締めは❹のとおり、自分のエントリー時期は書かず、来週どこが分かれ目か・どこに注目するかで終える。"""

FUNDAMENTAL_THEME = """この投稿はファンダメンタルズの話にする。
金融政策（FRB・日銀の金利見通し）、インフレ・雇用などの経済指標、米国債利回り、ドルの強弱など、値動きの背景にある材料を1つに絞り、
「なぜそれが相場に効くのか」「来週以降どこを見ておくか」をはじめさんの見方として書く。チャートの細かい話より、背景と見通しが中心。

ファンダメンタル投稿の口調の参考（実際の投稿ではない。文面は使わない）:
ドル円は結局ずっと金利差の話に戻ってくる

アメリカの利下げ観測が後退してる限り、円を買う理由はなかなか出てこない

次の指標で流れが変わるかどうか、そこだけは見ておきたい""" + WEEKEND_COMMON

FALLBACK_NOTE = """

ただし、語れる材料が薄くて投稿として良い内容にならない場合は、この形はやめてファンダメンタルズの投稿にする。
その場合は、金融政策以外の切り口（資金の流れ・需給・地政学・季節性など）を選ぶ（今日のもう1本のファンダメンタル投稿と話が重ならないようにするため）。
どちらにしたかの説明は書かず、投稿本文だけを出す。"""

RECAP_THEME = """この投稿は「今週のまとめ」にする。
今週のドル円・ナスダック・ゴールドの値動きをWebSearchで確認し、一番語れる流れ（FOMCやCPIなどの指標を受けてどう動いたか、週足でどう締めたか等）を1つに絞って、はじめさんの振り返りとして書く。""" + FALLBACK_NOTE + WEEKEND_COMMON

PREVIEW_THEME = """この投稿は「来週の注目イベント」の話にする。
来週の経済指標・イベント（FOMC、雇用統計、CPI、日銀会合、要人発言など）をWebSearchで確認し、ドル円・ナスダック・ゴールドに一番効きそうなものを1つに絞って、
なぜ大事か・結果次第で相場の見方がどう変わりそうかを、はじめさんの見方として書く。
イベントの日時を書く場合は日本時間で書き、2つ以上のソースで確認する。""" + FALLBACK_NOTE + WEEKEND_COMMON

# (曜日, スロット) → テーマ。土曜朝は今週のまとめ、日曜夜は来週の注目イベント、残りはファンダメンタル
WEEKEND_THEMES = {
    (5, "morning"): RECAP_THEME,
    (5, "evening"): FUNDAMENTAL_THEME,
    (6, "morning"): FUNDAMENTAL_THEME,
    (6, "evening"): PREVIEW_THEME,
}


def theme_rule_for(date_str: str, slot: str) -> str:
    weekday = datetime.strptime(date_str, "%Y-%m-%d").weekday()
    if weekday < 5:
        # 大きな値動きがない日は、朝は初心者向けの基礎、夜は失敗談
        if slot == "evening":
            evergreen = STORY_THEME.format(episodes=episodes_rule())
        else:
            evergreen = BASICS_THEME
        return WEEKDAY_THEME.format(evergreen=evergreen)
    theme = WEEKEND_THEMES.get((weekday, slot), FUNDAMENTAL_THEME)
    return theme.format(day_label="土曜" if weekday == 5 else "日曜")


OUTPUT_RULE = """

---

## 出力形式（厳守）

投稿本文だけを <post> と </post> の間に書くこと。<post> は1回だけ使う。

<post> の中に入れてはいけないもの:
- 「修正後の投稿文:」「投稿文:」などのラベル・見出し
- 区切り線（---）
- URL・リンク
- 検証メモ・出典・注釈・※・説明

<post> の中身はそのままXに投稿される。はじめさん本人が書いた本文以外は一文字も入れないこと。
"""

VERIFY_PROMPT = """\
以下の投稿文に含まれる「事実主張」を検証してください。

---
投稿文:
{draft}
---

## 検証手順

1. 投稿文から「事実主張」をすべて列挙する
   - 事実主張 = 価格・変動率・日時・指標結果・発言の引用など、正誤が存在する情報
   - 「〜そうだ」「と見ている」「と思う」など意見・予測・感想や、値動きの理由についてのはじめさんの解釈は対象外
   - チャートパターンへの言及（「三尊を形成中」等）は、現在の相場状況と照らして確認する
   - 「仮に〜なら」の計算例は、仮の数字自体は対象外。計算結果が正しいかと、制度の数字（国内のレバレッジ上限25倍、1ロットの通貨量など）が正しいかを確認する
   - はじめさん本人の過去の体験として書かれた部分はWebで確認できないので対象外（一般論として書かれた失敗パターンも対象外）

2. WebSearchで各主張を独立した2つ以上のソースで裏取りする
   - 数値は複数ソースで一致することを確認する
   - 1つしか見つからない情報は「要確認」とする

3. 結果を以下のフォーマットで出力する:

## 検証結果

| 主張 | 判定 | 根拠 |
|---|---|---|
| （主張内容） | ✅ 確認済み | （ソース名・内容） |
| （主張内容） | ❌ 誤り | （正しい情報） |
| （主張内容） | ⚠️ 要確認 | （確認できなかった理由） |

## 総合判定
- 全項目✅: PASS
- ❌または⚠️が1件でもある: FAIL（理由を明記）

## スタイルチェック
- 断定的な価格予測が含まれていないか
- 「〜になる」「〜は確実」などの断定表現がないか
- 投資推奨（「買い推奨」「売れ」、具体的な価格での売買指示、利益の保証）が含まれていないか
  - ※「押し目を待ってからエントリー」「ブレイクを確認してから入る」など、手法・ルールとしての待ち方の話は投資推奨に当たらないので問題なし
"""

FIX_PROMPT = """\
以下の投稿文を、検証ログの指摘に従って修正してください。

---
現在の投稿文:
{draft}

---
検証ログ:
{verify_log}
---

## 修正ルール

- ❌（誤り）と⚠️（要確認）の項目のみ修正する
- 修正方法:
  - 数値が間違っている → 正しい数値に直す（または数値を使わない表現に変える）
  - 確認できない情報 → その部分を削除するか、チャートパターン的な表現に置き換える
  - 断定的すぎる表現 → 「〜そうだ」「〜の可能性がある」の形にする（「かも」「っぽい」は使わない）

- ✅（確認済み）の部分は変えない
- 文体・人間らしさ・長さを維持する
"""


# ──────────────────────────────────────────
# Claude CLI 呼び出し
# ──────────────────────────────────────────

def call_claude(prompt: str, timeout: int = 300, model: str | None = None) -> str:
    """model 指定で失敗した場合は RuntimeError（呼び出し側で既定モデルに切り替える）"""
    cmd = ["claude", "--print", "--dangerously-skip-permissions"]
    if model:
        cmd += ["--model", model]
    # リポジトリの CLAUDE.md（予約投稿時代の手順書）を読み込ませないよう、空のフォルダで実行する
    with tempfile.TemporaryDirectory() as workdir:
        result = subprocess.run(
            cmd + ["-"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            cwd=workdir,
        )
    if result.returncode != 0:
        print(f"ERROR: claude CLI failed (model={model or 'default'})\n{result.stderr}", file=sys.stderr)
        if model:
            raise RuntimeError(result.stderr)
        sys.exit(result.returncode)
    return result.stdout.strip()


MAX_POST_CHARS = 250

# 相場の価格水準（160円方向、156円台、3,500ドル付近、20,000ポイント など）。損益額などの金額は対象外
PRICE_LEVEL = (
    r"(\d{2,3}(\.\d+)?円|\d[\d,]*(\.\d+)?(ドル|ポイント|pt))"
    r"(台|方向|手前|付近|ちょうど|まで|前後|近辺|割れ|突破|回復|到達|超え|を(上|下|割|超|抜|試|回|付)|で(止|跳|反|押|頭|底)|から|へ|に(到|迫|接|届|乗|戻|タッチ)|が(壁|節目|目の前|視野|意識))"
)

FORBIDDEN_PATTERNS = [
    (r"https?://|www\.|\.com|\.jp", "URL"),
    (r"^\s*[-=_*―─]{3,}\s*$", "区切り線"),
    (r"^\s*#", "見出し"),
    (r"```|\*\*|<|>|\[|\]", "マークダウン/タグ"),
    (r"^[^\n]{0,20}[:：]\s*$", "ラベル行"),
    (r"投稿文|修正(後|前|版|案|した)|訂正|改訂|検証|確認済|未確認|要確認|メモ|出典|ソース|参照|注[:：]|※|補足|以下(の|省略|略)|下書き|ドラフト|案[0-9０-９]|バージョン|文字数", "メタ文言"),
    (r"怖|不安(だ|で|に)|自信がな|迷って|読み切れ|様子見(し|する|かな|で)|(トレード|エントリー|取引|売買)(は|を|も)?(控え|見送|休)|今日は(休|やめ)|休もう|やめとく|やめておく", "弱気・トレードを控える表現"),
    (r"っぽい|かも|気がする", "軽く見える語尾（っぽい・かも・気がする）"),
    (r"そう[\s\U0001F300-\U0001FAFF\u2600-\u27BF\u203C\uFE0F]*$", "「〜そう」で終わる行（「〜そうだ」にする）"),
    (r"(入り|エントリーし|拾い|乗り|買い|売り|仕掛け|狙い)たい|入ろう|入るつもり|(入る|乗る|エントリーする)予定|から(入る|乗る|エントリーする|拾う)\s*$", "自分のエントリー時期（価格分析の投稿には書かない）"),
    (r"ビットコイン|仮想通貨|暗号資産|イーサリアム|リップル|アルトコイン|ビトコ", "ビットコイン・仮想通貨（本人の投稿と重なるため扱わない）"),
]

# 投稿に出てきてよい英字（これ以外の英単語が入っていたらAIの説明文とみなす）
ALLOWED_ASCII_WORDS = {
    "MACD", "FOMC", "CPI", "PCE", "PPI", "FRB", "FED", "ECB", "BOJ",
    "ETF", "FX", "USD", "JPY", "EUR", "GBP", "XAU", "GDP", "NY", "ATH", "NFP", "ISM",
    "NASDAQ", "VIX", "S", "P",
    "QT", "QE", "YCC", "BOE", "OPEC", "WTI", "IMF",
    "PIPS", "PIP", "LOT",
    "TOPIX", "SOX", "AI", "PMI", "ADP", "JOLTS", "GAFAM", "EV", "US", "EU", "UK",
}


BASICS_LABELS = {"証拠金", "必要証拠金", "ロット計算", "ロット", "スワップ", "レバレッジ", "pips", "損切り", "損切り幅",
                 "維持率", "ロスカット", "資金管理", "ナンピン", "FXの基礎", "基礎", "失敗談"}

THEME_TITLES = {"ドル円", "ゴールド", "ナスダック", "日経平均", "日経", "金", "為替", "ドル", "米国株", "日本株", "S&P500", "FX", "ユーロドル", "ポンド円"}


def find_problems(post: str, weekend: bool | None = None) -> list[str]:
    if not post.strip():
        return ["本文が空"]
    problems = []
    lines = post.split("\n")
    if weekend is None:
        weekend = datetime.now(JST).weekday() >= 5
    if weekend and lines[0].strip() in THEME_TITLES:
        problems.append(f"土日は1行目にテーマ名を書かない: {lines[0].strip()}")
    if lines[0].strip() in BASICS_LABELS:
        problems.append(f"1行目がラベルだけ（続きを読みたくなる一文にする）: {lines[0].strip()}")
    for pattern, label in FORBIDDEN_PATTERNS:
        for line in lines:
            if re.search(pattern, line):
                problems.append(f"{label}: {line.strip()}")
    if re.search(r"[⚠❌]", post):
        problems.append("⚠️・❌ は事実確認の判定記号と紛らわしいので使わない")
    if len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿‼]", post)) > 2:
        problems.append("絵文字が多すぎる（2個まで）")
    for line in lines:
        if "仮に" not in line and re.search(PRICE_LEVEL, line):
            problems.append(f"価格の数字（書かないルール）: {line.strip()}")
    for word in re.findall(r"[A-Za-z]+", post):
        if word.upper() not in ALLOWED_ASCII_WORDS:
            problems.append(f"想定外の英単語: {word}")
    seen = set()
    for line in (l.strip() for l in lines):
        if len(line) >= 4 and line in seen:
            problems.append(f"同じ行の重複（2案混入の疑い）: {line}")
        seen.add(line)
    if len(post) > MAX_POST_CHARS:
        problems.append(f"長すぎる（{len(post)}文字）")
    return problems


REVIEW_PROMPT = """\
次の文章は、この後そのまま1文字も変えずにXへ投稿されます。

<post>
{post}
</post>

トレーダー本人が書いたXの投稿本文として、そのまま出して問題ないかだけを判定してください。
次のどれかが1つでもあればNGです:
- 投稿本文以外のもの（ラベル、見出し、区切り線、説明、メモ、注釈、出典、URL、AIからの一言）
- 修正前と修正後など、2つ以上の案が混ざっている
- 同じ内容の繰り返し
- 途中で切れている、または文として壊れている

判定するのは上の4点だけ。文体・内容の良し悪しや事実関係は別の工程で確認済みなので、ここでは判定しない。
平日の値動きの投稿は1行目に「ゴールド」「ドル円」のような短いテーマ名を置く書き方で、これは本文の一部なのでNGにしない。

1行目に OK または NG とだけ書き、NGの場合は2行目に理由を書いてください。
"""


def passes_review(post: str) -> tuple[bool, str]:
    result = call_claude(REVIEW_PROMPT.format(post=post))
    first = result.strip().split("\n")[0].strip()
    return first == "OK", result


def extract_post(raw: str) -> str | None:
    matches = re.findall(r"<post>(.*?)</post>", raw, re.DOTALL)
    if len(matches) != 1:
        return None
    return matches[0].strip()


def draft_with_claude(prompt: str) -> str:
    """<post>タグ内の本文だけを取り出し、機械チェック＋別AIの目視チェックを通す。3回ダメなら投稿中止"""
    feedback = ""
    for attempt in range(1, 4):
        raw = call_claude(prompt + OUTPUT_RULE + feedback)
        post = extract_post(raw)
        problems = find_problems(post) if post is not None else ["<post>タグが1つではない"]
        if not problems:
            ok, review = passes_review(post)
            if ok:
                return post
            problems = [f"レビューNG: {review}"]
        print(f"\n[FORMAT NG {attempt}/3] {problems}\n--- raw ---\n{raw}\n{'-'*40}")
        feedback = (
            "\n\n---\n\n## 前回の下書きは次の理由で使えなかった。この点を直して書き直す\n"
            + (f"<前回の下書き>\n{post}\n</前回の下書き>\n" if post else "")
            + "\n".join(f"- {p}" for p in problems)
            + "\n（英字の略語が原因の場合は、カタカナや日本語の言い方に置き換える）"
        )
    print("❌ 本文以外の混入を解消できなかったため投稿を中止します", file=sys.stderr)
    sys.exit(1)


EMOJI_PALETTE = {
    "急騰・強い": "🚀 📈 🔥 💪",
    "急落・弱い": "📉 🥶 😱 💦",
    "驚き": "😳 👀 ‼️",
    "注目・分かれ目": "👀 📌 🎯",
    "首をかしげる": "🤔 🧐",
    "失敗談・苦い思い出": "😇 💸 🫠 😅 😭",
    "基礎・学び": "💡 📝 ✅ 🔰",
    "前向き": "💪 👍 ✨ 🙌",
    "週末": "☕ 🗓️",
}


def emoji_rule_for(date_str: str, slot: str) -> str:
    # 日付とスロットで決まる乱数（作り直しても同じ回は同じ方針になる）
    rng = random.Random(f"{date_str}-{slot}")
    if rng.random() < 0.2:
        return "- 今回の投稿は絵文字を使わない（毎回入っていると機械的に見えるため）"
    all_emoji = " ".join(EMOJI_PALETTE.values()).split()
    hints = " ".join(rng.sample([e for e in all_emoji if e != "🤔"], 3))
    table = "\n".join(f"    - {k}: {v}" for k, v in EMOJI_PALETTE.items())
    return (
        "- 絵文字は内容に合うものを0〜2個。同じ絵文字ばかりだと機械的に見えるので、場面に合わせて使い分ける\n"
        "  - 🤔は本当に首をかしげる場面だけにし、多用しない\n"
        f"  - 今回は {hints} あたりが候補（内容に合わなければ使わなくてよい）\n"
        "  - 場面ごとの使い分け:\n" + table
    )


def build_generate_prompt(date_str: str, slot: str) -> str:
    slot_label = SLOT_LABELS[slot]
    base = GENERATE_PROMPT.format(
        date=date_str, slot=slot, slot_label=slot_label,
        theme_rule=theme_rule_for(date_str, slot),
        emoji_rule=emoji_rule_for(date_str, slot),
    )
    if INSIGHTS_PATH.exists():
        insights = INSIGHTS_PATH.read_text(encoding="utf-8")
        base += (
            "\n\n---\n\n## 先週の反応分析からの改善方針（毎週日曜に更新。上のルールと食い違う場合は上のルールを優先）\n\n"
            + insights
        )
    return base


def is_verified(verify_log: str) -> bool:
    """検証ログにFAILまたは❌/⚠️があればFalse"""
    if "FAIL" in verify_log:
        return False
    lines = verify_log.split("\n")
    for line in lines:
        if re.search(r"^[\|\s]*[❌⚠️]", line):
            return False
    return True


# ──────────────────────────────────────────
# Opus 5.5 との壁打ち
# ──────────────────────────────────────────

CRITIC_MODEL = os.environ.get("CRITIC_MODEL", "claude-opus-5-5")
MAX_SPAR_ROUNDS = 2

CRITIQUE_PROMPT = """\
あなたは、FX・ゴールド・株価指数を扱うトレーダー「はじめ」さんのX投稿を、投稿前に一緒に磨く相談相手です。
はじめさんはFXのアフィリエイト収入で生計を立てていて、誤った情報や信用を落とす投稿は致命的です。
下書きを書いた担当者は、次の指示を受けて書いています。

<指示>
{rules}
</指示>

<下書き>
{draft}
</下書き>

X上のトレーダーやFX初心者の読者の目線で、この下書きをより良くするための率直な指摘をしてください。見る観点:
- 事実の正確さと、誤解を招く書き方がないか。事実が怪しいと思ったらWebSearchで確認する
- 指示（テーマ・文体・人物像・締め方・禁止事項）に沿っているか
- 読んだ人が反応・保存・拡散したくなる中身と切り口になっているか
- 人が書いた自然な投稿に見えるか

直すべき点がなければ、1行目に OK とだけ書いて終える。
直すべき点があれば、1行目に「指摘あり」と書き、その下に指摘を重要な順に書く（なぜそう直すべきかも添える）。
改善案の文面を示す場合、新しい事実を足すなら、2つ以上のソースで確認できたものだけにし、確認したソースを添える。
価格や価格の水準は数字で書かない（キリのいい節目も含む）というルールがあるので、改善案にも価格の数字は入れない。
"""

REVISE_PROMPT = """\
{rules}

---

## 相談相手からの指摘を踏まえて書き直す

あなたが書いた下書き:
<下書き>
{draft}
</下書き>

相談相手（別のAI）からの指摘:
<指摘>
{critique}
</指摘>

指摘を1つずつ検討し、納得できるものは取り入れ、納得できないもの（上の指示に反する、事実が確認できない等）は取り入れずに書き直す。
指摘の中の新しい事実を使う場合は、自分でもWebSearchで2つ以上のソースから確認できたものだけを使う。
"""


def critique(rules: str, draft: str) -> str:
    prompt = CRITIQUE_PROMPT.format(rules=rules, draft=draft)
    try:
        return call_claude(prompt, timeout=600, model=CRITIC_MODEL)
    except (RuntimeError, subprocess.TimeoutExpired):
        print(f"::warning::{CRITIC_MODEL} を使えなかったため、既定のモデルで壁打ちしました")
        return call_claude(prompt, timeout=600)


def spar(rules: str, draft: str) -> str:
    for round_no in range(1, MAX_SPAR_ROUNDS + 1):
        print(f"\n[壁打ち {round_no}/{MAX_SPAR_ROUNDS}] {CRITIC_MODEL} に相談中...")
        feedback = critique(rules, draft)
        print(f"\n--- 指摘 ---\n{feedback}\n{'-'*40}")
        if feedback.strip().split("\n")[0].strip() == "OK":
            print("\n壁打ち完了（指摘なし）")
            return draft
        draft = draft_with_claude(REVISE_PROMPT.format(rules=rules, draft=draft, critique=feedback))
        print(f"\n--- 書き直し ({len(draft)}文字) ---\n{draft}\n{'-'*40}")
    return draft


# ──────────────────────────────────────────
# メインフロー
# ──────────────────────────────────────────

def generate_and_verify(date_str: str, slot: str) -> str:
    slot_label = SLOT_LABELS[slot]

    print(f"\n[STEP 1] 投稿生成中 ({slot_label})...")
    rules = build_generate_prompt(date_str, slot)
    draft = draft_with_claude(rules)
    print(f"\n--- 初回生成 ({len(draft)}文字) ---\n{draft}\n{'-'*40}")

    draft = spar(rules, draft)

    for attempt in range(1, MAX_VERIFY_ATTEMPTS + 1):
        print(f"\n[STEP 2] 検証中（{attempt}/{MAX_VERIFY_ATTEMPTS}回目）...")
        verify_log = call_claude(VERIFY_PROMPT.format(draft=draft))
        print(f"\n--- 検証ログ ---\n{verify_log}\n{'-'*40}")

        if is_verified(verify_log):
            print(f"\n✅ 検証パス（{attempt}回目で完了）")
            return draft

        print(f"\n⚠️ 検証で問題を検出（attempt {attempt}）")

        if attempt < MAX_VERIFY_ATTEMPTS:
            print(f"\n[STEP 3] 修正中...")
            draft = draft_with_claude(FIX_PROMPT.format(draft=draft, verify_log=verify_log))
            print(f"\n--- 修正後 ({len(draft)}文字) ---\n{draft}\n{'-'*40}")

    # 3回試して通らなかった
    print(f"\n❌ {MAX_VERIFY_ATTEMPTS}回の検証ループで問題が解消されませんでした", file=sys.stderr)
    print("投稿をブロックします。検証ログを確認してください:", file=sys.stderr)
    print(verify_log, file=sys.stderr)
    sys.exit(1)


def post_to_x(text: str) -> str:
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    try:
        response = client.create_tweet(text=text)
        return str(response.data["id"])
    except tweepy.errors.Unauthorized as e:
        resp_text = e.response.text if hasattr(e, "response") else str(e)
        print(f"401 Unauthorized: {resp_text}", file=sys.stderr)
        raise
    except tweepy.errors.Forbidden as e:
        resp_text = e.response.text if hasattr(e, "response") else str(e)
        print(f"403 Forbidden: {resp_text}", file=sys.stderr)
        raise


def main():
    slot = sys.argv[1] if len(sys.argv) > 1 else "morning"
    if slot not in SLOT_LABELS:
        print(f"ERROR: slot must be morning/noon/evening, got: {slot}", file=sys.stderr)
        sys.exit(1)

    date_str = datetime.now(JST).strftime("%Y-%m-%d")

    # 生成→検証→修正ループ（問題があれば自動でブロック）
    verified_text = generate_and_verify(date_str, slot)

    problems = find_problems(verified_text)
    if problems:
        print(f"❌ 投稿直前チェックNGのため中止: {problems}", file=sys.stderr)
        sys.exit(1)
    print(f"\n--- 投稿する本文 ---\n{verified_text}\n{'-'*40}")

    if not os.environ.get("TWITTER_API_KEY"):
        print("\nTWITTER_API_KEY未設定のため投稿をスキップ（ドライラン）")
        return

    post_at = os.environ.get("POST_AT")
    if post_at:
        wait = int(post_at) - time.time()
        target = datetime.fromtimestamp(int(post_at), JST).strftime("%H:%M")
        if wait > 0:
            print(f"\n{target} JST まで {int(wait)} 秒待ってから投稿します")
            time.sleep(wait)

    print("\n[STEP 4] X に投稿中...")
    tweet_id = post_to_x(verified_text)
    print(f"\n✅ 投稿完了: https://x.com/hajime_cp/status/{tweet_id}")
    with open(POSTED_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": tweet_id, "posted_at": datetime.now(JST).isoformat(timespec="seconds"),
                            "slot": slot, "text": verified_text}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
