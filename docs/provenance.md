# 取り込み元 / Provenance

- Upstream: `NyaMisty/AltServer-Linux`, branch `new`, base `7876451`. Git history, AGPL-3.0 and pinned submodule commits are retained.
- Recovery code: `hinatamaxxx/altserver-linux-native-autorecover`, commit `d61a5b6`, MIT. Runtime helpers, regression tests and diagnostic tools were imported; the new installer and service defaults integrate official netmuxd v0.4.3.
- `docs/history/` contains predecessor documents. They describe the old helper-only repository and its historical tests, not this fork's current installation procedure. Do not use their trial/upgrade commands for this fork.
- `docs/upstream-readme.md` is an unchanged upstream reference; use the root README for this fork.
- The setup bundle contains this fork's compiled binary. netmuxd and Anisette are fetched from their upstream distributions, not rebuilt or modified here.

本家の Git 履歴・AGPL-3.0・サブモジュールを維持し、MIT の復旧コードを取り込んでいます。`history` は旧リポジトリの資料で、今回の検証結果や導入手順ではありません。旧試験・更新用コマンドは本フォークで使用しないでください。

- 上流は `NyaMisty/AltServer-Linux` の `new` ブランチ、コミット `7876451` です。
- 復旧コードは `hinatamaxxx/altserver-linux-native-autorecover` の `d61a5b6`（MIT）です。実行用スクリプト、回帰テスト、診断ツールを取り込みました。
- `docs/history/` は旧資料、`docs/upstream-readme.md` は上流 README の原文です。本フォークの使い方はルート README を参照してください。
- バンドルには本フォークのビルド済みバイナリを含めます。netmuxd と Anisette は公式配布物を取得し、本リポジトリでは改変・再ビルドしていません。
