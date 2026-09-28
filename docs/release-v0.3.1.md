# v0.3.1 — Passkey sign-in / パスキーログイン

## 日本語

管理画面のサポート対象はTailscale経由のHTTPS＋パスキーです。アクセスするPCへの独自CA証明書の追加は不要です。TailscaleなしでのLAN公開・一般公開はサポートしません。AltStoreのWi-Fi更新の要件は変わりません。

Web管理画面に初回パスキー登録とパスキーログインを追加しました。`sudo sh scripts/install-web-ui.sh --tailscale` でHTTPSを設定し、表示されたURLから登録します。管理用アクセスキーの入力は不要です。初回登録はサーバー所有者のTailscaleアカウントに限定します。

登録情報はサーバーに保存し、再起動やアップデート後も保持します。秘密鍵と生体情報は送信しません。追加パスキー登録は現時点では未対応です。[利用方法・紛失時の復旧](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.3.1/docs/web-ui.md)

実環境でHTTPSの初回登録画面と、利用者の登録後のログイン状態を確認しました。認証署名、Origin/RP ID、本人確認の必須化、期限切れ・再利用要求の拒否は模擬認証器によるテストで検証します。

## English

The supported console configuration is HTTPS over Tailscale with passkeys. No custom CA certificate installation is required on the accessing PC. Direct LAN access without Tailscale and public internet exposure are unsupported. AltStore Wi-Fi refresh requirements are unchanged.

Adds first-time passkey enrollment and passkey sign-in to the web console. Run `sudo sh scripts/install-web-ui.sh --tailscale` to configure HTTPS, then enroll at the displayed URL. No administration access key needs to be entered. Initial enrollment is restricted to the server owner’s Tailscale account.

Registration data persists across restarts and updates. Private keys and biometric data are not transmitted. Additional passkey enrollment is not yet supported. [Usage and lost-passkey recovery](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.3.1/docs/web-ui.md)

Live checks confirmed the HTTPS enrollment screen and the signed-in state after user enrollment. Synthetic-authenticator tests cover signatures, Origin/RP ID, mandatory user verification, and rejection of expired or replayed requests.
