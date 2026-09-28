# 検証記録 / Verification

## 日本語

このプレビューでは、iPhone を使わずに実施できる検証を対象とします。Python の通信・復旧・移行・設定テスト、C++ の UTC / routing info テスト、ソースからの amd64 ビルド、生成された実行ファイルの CLI テストを CI で実行します。

2026-09-28 に完了した検証:

- Python 回帰テスト34件。アダプター・復旧・移行・設定・中断後の再開を確認。
- C++ の UTC / routing info テストと、本番の `WiredConnection.cpp` に模擬通信を接続した転送テスト。
- 本フォーク全体の amd64 ソースビルドと、生成した実行ファイルによる CLI テスト6ケース。
- 配布アーカイブを展開し、Debian 13 コンテナで実際のパッケージ導入、バイナリ取得・チェックサム確認、Docker イメージ取得、設定生成、systemd unit の構文検査。
- Git 管理対象ファイルの簡易プライバシースキャン（検出0件）。網羅的な秘密情報検査ではありません。

インストーラ試験の `systemctl` 操作は記録用の代替処理です。端末情報も架空の値を使用しています。サービスを実際に起動した試験、実ペアリングの試験、クリーンな実機への導入試験ではありません。

iPhone での署名・インストール・更新、実機への新規セットアップ、USB 再接続、ホスト再起動後の復旧、長時間稼働は未検証です。過去の netmuxd 再登録成功例は旧バイナリの結果であり、この版の成功として扱いません。既存サーバーの稼働設定と認証状態は保持しています。

## English

This preview focuses on checks that need no iPhone. CI runs Python protocol, recovery, migration and configuration tests; C++ UTC/routing-info tests; an amd64 build from source; and CLI tests against the resulting executable.

Checks completed on 2026-09-28:

- 34 Python regression tests covering the adapter, recovery, migration, configuration and setup resumption.
- C++ UTC/routing-info tests and transfer tests compiling the production `WiredConnection.cpp` against a fake transport.
- A full amd64 source build and six CLI cases against the resulting executable.
- Extraction of the setup archive in a Debian 13 container, with real package installation, binary downloads/checksums, Docker image download, configuration generation and systemd unit syntax validation.
- A heuristic scan of Git-tracked files, with zero findings. This is not an exhaustive secret audit.

The installer test records `systemctl` calls instead of executing them and uses synthetic device values. It does not verify actual service activation, real pairing or installation on a clean physical host.

Signing, installation and refresh on an iPhone, a clean physical-host setup, USB reconnection, full-host reboot recovery and long-duration operation remain unverified. Earlier netmuxd re-registration successes used the old binary and are not treated as validation of this version. The existing server's runtime configuration and authentication state are preserved.
