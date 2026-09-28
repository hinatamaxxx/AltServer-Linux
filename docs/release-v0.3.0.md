# v0.3.0 — Web UI preview / 管理画面プレビュー

## 日本語

サービス状態・iPhone接続・診断ログを確認できる、日本語／英語のWeb UIを追加しました。接続診断、既存の復旧処理の手動実行、個別サービスの再起動ができます。

AltServer設定済みの環境では、ソースまたは展開したセットアップフォルダーで `sudo sh scripts/install-web-ui.sh` を実行すると追加できます。初期設定はループバック接続・アクセスキー認証です。リモート接続にはTailscaleまたはSSHポート転送を使います。[利用方法](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.3.0/docs/web-ui.md)

アプリの更新は引き続きiPhoneから行います。ログは操作記録と固定カテゴリの集計のみで、生の認証情報や端末IDは画面に送信しません。既存の署名・ペアリング・Anisette設定は変更しません。

## English

Adds an optional Japanese/English web console for service status, iPhone connectivity and diagnostic logs. Run connection checks, trigger the existing recovery check, or restart individual services.

On a configured AltServer host, run `sudo sh scripts/install-web-ui.sh` from the source checkout or extracted setup folder. It defaults to loopback access with access-key authentication. Use Tailscale or SSH forwarding for remote access. [Usage](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.3.0/docs/web-ui.md)

Continue refreshing apps from your iPhone. The console exposes action records and fixed-category counts, without transmitting raw authentication data or device identifiers. Installing it preserves existing signing, pairing and Anisette settings.
