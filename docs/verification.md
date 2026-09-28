# 検証記録 / Verification

v0.1.3 の CI では Python 34件、ネイティブ通信9ケース、BSD コピー長512通りを試験します。アダプター試験を削除し、旧バージョンの準備状態を拒否する試験1件を追加しました。C++、署名、GSA、要求受信、CLI 6ケース、amd64 ビルド、Debian 13 での展開済みインストーラ試験も実行します。インストーラ試験はアダプターが配布・有効化されないことと、直接接続のポート設定も確認します。通信試験は模擬サーバー、サービス起動は記録用の模擬処理です。実機の iPhone 更新・Apple ログイン・ホスト再起動後の復旧は未検証です。[方式と出典](fork-review.md)を参照してください。

For v0.1.3, CI runs 34 Python tests, nine native communication cases and 512 BSD copy-length assertions. Adapter tests are removed and one cross-version preparation guard test is added. C++, signing, GSA, request handling, six CLI cases, the amd64 build and an extracted-installer test on Debian 13 also run. The installer test checks that the adapter is neither distributed nor enabled and verifies the direct-connection port settings. Communication uses synthetic servers; service activation is recorded by a stub. Physical iPhone refresh, live Apple sign-in and full-host reboot recovery remain unverified. See [methods and sources](fork-review.md).

v0.1.2 では Bonjour ブリッジの5ケースを加え、Python テストは39件になります。生成済みの要求受信処理に対し、JSON 長さの境界値と不正長の拒否も試験します。[追加調査](fork-review.md)に詳細を記載しています。実際の LAN 上の Bonjour 探索と Avahi 再起動後の広告復旧は未検証です。

v0.1.2 adds five Bonjour bridge cases, bringing the Python total to 39, and tests JSON length boundaries and rejection in the generated request handler. See the [additional review](fork-review.md). Actual Bonjour discovery on a LAN and advertisement recovery after an Avahi restart remain unverified.

v0.1.1 の CI には、署名の暗号学的検証と完全なハッシュの確認、GSA の TCP 接続分離と TLS 検証設定の確認を追加しています。使用するのは架空のアプリ、一時的なテスト証明書、ローカルサーバーです。[フォーク調査](fork-review.md)に方法と限界を記載しています。当時の Python テストは34件で、CLI は6ケースです。

For v0.1.1, CI additionally checks cryptographic signatures, full agility hashes, separate GSA TCP connections and the TLS-validation setting, using a synthetic app, disposable test identity and local server. The [fork review](fork-review.md) describes methods and limits. That version had 34 Python regressions and six CLI cases.

## 日本語

このプレビューでは、iPhone を使わずに実施できる検証を対象とします。Python の通信・復旧・移行・設定テスト、C++ の UTC / routing info テスト、ソースからの amd64 ビルド、生成された実行ファイルの CLI テストを CI で実行します。

v0.1.0 で完了した検証（履歴）:

- Python 回帰テスト34件。アダプター・復旧・移行・設定・中断後の再開を確認。
- C++ の UTC / routing info テストと、本番の `WiredConnection.cpp` に模擬通信を接続した転送テスト。
- 本フォーク全体の amd64 ソースビルドと、生成した実行ファイルによる CLI テスト6ケース。
- 配布アーカイブを展開し、Debian 13 コンテナで実際のパッケージ導入、バイナリ取得・チェックサム確認、Docker イメージ取得、設定生成、systemd unit の構文検査。
- Git 管理対象ファイルの簡易プライバシースキャン（検出0件）。網羅的な秘密情報検査ではありません。

インストーラ試験の `systemctl` 操作は記録用の代替処理です。端末情報も架空の値を使用しています。サービスを実際に起動した試験、実ペアリングの試験、クリーンな実機への導入試験ではありません。

iPhone での署名・インストール・更新、実機への新規セットアップ、USB 再接続、ホスト再起動後の復旧、長時間稼働は未検証です。過去の netmuxd 再登録成功例は旧バイナリの結果であり、この版の成功として扱いません。既存サーバーの稼働設定と認証状態は保持しています。

## English

This preview focuses on checks that need no iPhone. CI runs Python protocol, recovery, migration and configuration tests; C++ UTC/routing-info tests; an amd64 build from source; and CLI tests against the resulting executable.

Checks completed for v0.1.0 (historical):

- 34 Python regression tests covering the adapter, recovery, migration, configuration and setup resumption.
- C++ UTC/routing-info tests and transfer tests compiling the production `WiredConnection.cpp` against a fake transport.
- A full amd64 source build and six CLI cases against the resulting executable.
- Extraction of the setup archive in a Debian 13 container, with real package installation, binary downloads/checksums, Docker image download, configuration generation and systemd unit syntax validation.
- A heuristic scan of Git-tracked files, with zero findings. This is not an exhaustive secret audit.

The installer test records `systemctl` calls instead of executing them and uses synthetic device values. It does not verify actual service activation, real pairing or installation on a clean physical host.

Signing, installation and refresh on an iPhone, a clean physical-host setup, USB reconnection, full-host reboot recovery and long-duration operation remain unverified. Earlier netmuxd re-registration successes used the old binary and are not treated as validation of this version. The existing server's runtime configuration and authentication state are preserved.
