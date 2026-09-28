# 取り込み元 / Provenance

## English

- Upstream: `NyaMisty/AltServer-Linux`, branch `new`, base `7876451`. Git history and AGPL-3.0 are retained. In v0.1.1, `upstream_repo` is repinned to `jaakkopalvaila/AltServer-Windows` at `dae9501abad10a4f008cc8a73138310679decd81`; other submodule commits are unchanged. See [fork review](fork-review.md) for exact sources and local adaptations.
- Recovery code: `hinatamaxxx/altserver-linux-native-autorecover`, commit `d61a5b6`, MIT. Runtime helpers, regression tests and diagnostic tools were imported; the new installer and service defaults integrate official netmuxd v0.4.3.
- `docs/history/` contains predecessor documents. They describe the old helper-only repository and its historical tests, not this fork's current installation procedure. Do not use their trial/upgrade commands for this fork.
- `docs/upstream-readme.md` is an unchanged upstream reference; use the root README for this fork.
- The setup bundle contains this fork's compiled binary. netmuxd and Anisette are fetched from their upstream distributions, not rebuilt or modified here.

## 日本語

- 上流: `NyaMisty/AltServer-Linux`（`new` ブランチ、コミット `7876451`）。本家の Git 履歴と AGPL-3.0 を維持しています。v0.1.1 では `upstream_repo` を `jaakkopalvaila/AltServer-Windows`（コミット `dae9501abad10a4f008cc8a73138310679decd81`）に更新し、他のサブモジュールは維持しています。出典と調整内容は[フォーク調査](fork-review.md)を参照してください。
- 復旧コード: `hinatamaxxx/altserver-linux-native-autorecover`（コミット `d61a5b6`、MIT）。実行用スクリプト、回帰テスト、診断ツールを取り込み、公式 netmuxd v0.4.3 と連携するよう統合しました。
- `docs/history/`: 旧資料です。旧リポジトリの検証記録であり本フォークの導入手順ではありません。旧試験・更新用コマンドは本フォークで使用しないでください。
- `docs/upstream-readme.md`: 上流 README の原文です（参考用）。本フォークの使い方はルート README を参照してください。
- 配布バンドル: 本フォークのビルド済みバイナリを含みます。netmuxd と Anisette は公式配布物を取得し、本リポジトリでは改変・再ビルドしていません。
