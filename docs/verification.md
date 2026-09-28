# 検証記録 / Verification

## 日本語

このプレビューでは、iPhone を使わずに実施できる検証を対象とします。Python の通信・復旧・移行・設定テスト、C++ の UTC / routing info テスト、ソースからの amd64 ビルド、生成された実行ファイルの CLI テストを CI で実行します。

iPhone での署名・インストール・更新、実機への新規セットアップ、USB 再接続、ホスト再起動後の復旧、長時間稼働は未検証です。過去の netmuxd 再登録成功例は旧バイナリの結果であり、この版の成功として扱いません。既存サーバーの稼働設定と認証状態は保持しています。

## English

This preview focuses on checks that need no iPhone. CI runs Python protocol, recovery, migration and configuration tests; C++ UTC/routing-info tests; an amd64 build from source; and CLI tests against the resulting executable.

Signing, installation and refresh on an iPhone, a clean physical-host setup, USB reconnection, full-host reboot recovery and long-duration operation remain unverified. Earlier netmuxd re-registration successes used the old binary and are not treated as validation of this version. The existing server's runtime configuration and authentication state are preserved.
