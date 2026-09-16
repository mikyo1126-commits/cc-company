# セットアップガイド — @hajime_cp X運用ワークフロー

---

## ⚠️ 認証方式に関する重要事項

**`ANTHROPIC_API_KEY` は使用しません。**
このワークフローは Claude Max プランの OAuth トークン（`CLAUDE_CODE_OAUTH_TOKEN`）を使用します。
`ANTHROPIC_API_KEY` を GitHub Secrets に登録しても動作しません。

---

## 初回セットアップ手順

### Step 1: OAuth トークンを発行する

ローカルの端末（PC）で以下のコマンドを実行してください:

```bash
claude setup-token
```

ブラウザが開き、Anthropic へのログインと権限承認が求められます。
承認後、ターミナルにトークン文字列が表示されます。

> ⚠️ トークンは一度しか表示されません。必ずコピーして保管してください。

### Step 2: GitHub Secrets にトークンを登録する

1. このリポジトリを開く
2. **Settings** → **Secrets and variables** → **Actions** を開く
3. **New repository secret** をクリック
4. 以下を入力して **Add secret**:

   | 項目 | 値 |
   |------|----|
   | Name | `CLAUDE_CODE_OAUTH_TOKEN` |
   | Secret | Step 1 でコピーしたトークン |

### Step 3: 動作確認

1. **Actions** タブを開く
2. **@hajime_cp 日次X投稿ワークフロー** を選択
3. **Run workflow** → `dry_run: true` にチェック → **Run workflow**
4. ワークフローが完了し、`marketing/content-plan/drafts/YYYY-MM-DD/` にファイルが生成されることを確認する

---

## ワークフローの手動起動方法

時間が空いたときにいつでも手動で起動できます:

1. **Actions** タブ → **@hajime_cp 日次X投稿ワークフロー**
2. **Run workflow** ボタンをクリック
3. オプション:
   - `dry_run: false`（デフォルト）: 下書き生成まで実行
   - `dry_run: true`: 下書き確認のみ（X 予約投稿登録をスキップ）
4. **Run workflow** をクリック

---

## 下書きの確認フロー

ワークフローが完了すると、以下のファイルがリポジトリにコミットされます:

```
marketing/content-plan/drafts/YYYY-MM-DD/
├── search_plan.json          # 検索クエリ計画
├── existing_themes.json      # 既存テーマ一覧（重複防止）
├── raw_trends.md             # 競合分析・市場トレンド収集結果
├── drafts.md                 # 投稿下書き（3〜5本）
├── verification_template.json # 事実検証テンプレート
└── verification_log.md       # 事実検証ログ
```

### 確認手順

1. GitHub のリポジトリページで `drafts.md` を開く
2. 内容を確認する
3. 問題がなければ **そのまま放置** → X 予約投稿登録へ進む
4. 修正したい場合は `drafts.md` を直接編集してコミットする
5. 投稿をスキップしたい場合は該当ブロックを削除する

### X 予約投稿登録

`scripts/x-schedule-post.md` の手順書に従って、Claude in Chrome で予約投稿を登録してください。

---

## OAuthトークンの期限切れ時の対応

トークンが期限切れになると、ワークフローが失敗し GitHub Issue が自動作成されます。

**Issue のタイトル例:** `🔑 [要対応] Claude OAuthトークンの更新が必要です（2026-09-16）`

### 対処手順（5分で完了）

```bash
# 1. ローカルで新しいトークンを発行
claude setup-token

# 2. 表示されたトークンをコピー
```

3. GitHub の Settings → Secrets → `CLAUDE_CODE_OAUTH_TOKEN` を **Update**
4. ワークフローを手動で再実行
5. Issue をクローズ

---

## よくある質問

### Q: ANTHROPIC_API_KEY を持っているが使えないのか?

A: このワークフローは Claude Code CLI (`claude --print`) を使って実行するため、`CLAUDE_CODE_OAUTH_TOKEN` が必要です。`ANTHROPIC_API_KEY` では動作しません。

### Q: 自動スケジュール（毎日05:00 JST）を止めたい

A: `.github/workflows/x-daily-post.yml` の `schedule` セクションをコメントアウトしてください。手動起動のみになります。

### Q: 生成された下書きを全部削除したい

A: `marketing/content-plan/drafts/YYYY-MM-DD/` ディレクトリごと削除してコミットしてください。

### Q: 投稿本数を変えたい

A: `workflow/prompts/03_generate_drafts.md` のタスク説明を編集してください。
