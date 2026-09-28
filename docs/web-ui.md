# Web UI / 管理画面

## 日本語

ブラウザーでサービスの状態、設定済みiPhoneの接続、診断ログを確認できます。接続診断、既存の自動復旧処理の手動実行、サービスごとの再起動に対応します。アプリのリフレッシュは引き続きiPhoneのAltStore Classicから行います。

AltServer設定済みで、サーバーと利用端末がTailscaleに接続している場合、次を実行します。

```sh
sudo sh scripts/install-web-ui.sh --tailscale
```

表示されたHTTPS URLを開き、「パスキーを登録する」を押してFace ID・Touch ID・Windows Helloなどの案内に従います。初回登録はサーバー所有者のTailscaleアカウントからの接続だけに許可されます。次回から「パスキーでログイン」で利用でき、管理用アクセスキーの入力は不要です。本人確認方法は端末・ブラウザー・パスキープロバイダーによって異なります。

TailscaleでHTTPSが未設定の場合、表示される設定URLでHTTPSを有効にしてから再実行してください。Funnelは不要です。サイトはTailscale内で利用し、HTTPS証明書の発行によりサーバーのDNS名が公開証明書ログに記録されます。既存の443番ポートが別アプリに使われている場合、設定を上書きせず停止します。タグ付きノードの初回登録はサポートしていません。

認証検証にはpy_webauthnを使います。インストーラーは専用のPython仮想環境に依存パッケージを導入します。秘密鍵や生体情報をサーバーへ送信せず、公開鍵などの登録情報を `/var/lib/altserver-webui/passkeys.json` に権限0600で保存します。初回登録完了後の追加登録は現在サポートしていません。端末間でのパスキー共有はプロバイダーの同期機能によります。

パスキーを失った場合、SSHで管理画面を停止し、登録ファイルをバックアップとして移動してから再起動すると、所有者だけが再登録できます。通常のアップデートではこのファイルを保持してください。

```sh
sudo systemctl stop altserver-webui
sudo mv /var/lib/altserver-webui/passkeys.json /var/lib/altserver-webui/passkeys.backup.json
sudo systemctl start altserver-webui
```

`--tailscale` を付けずに初めて導入する場合は、従来のループバック・アクセスキー方式になります。HTTPS設定済みの環境を更新する場合、同オプションを省いても設定と登録済みパスキーを保持します。HTTPSモードでは旧アクセスキーによるログインを無効化します。

- 状態は画面を表示している間、約10秒ごとに更新します。通信失敗時は最後の取得結果と警告を表示します。
- 「復旧処理」は既存のヘルスチェックを起動します。既存の失敗回数・待機時間の判定に従うため、毎回強制再起動する操作ではありません。
- 再起動・復旧の前に確認画面を表示します。実行中のアプリ更新が中断される場合があります。
- 診断ログには画面からの操作記録と、AltServerログ末尾32 KiBから集計した固定カテゴリの件数を表示します。生ログ、Apple認証ヘッダー、端末IDは転送しません。件数はアプリ更新の成功を証明しません。
- 画面からの操作記録はメモリー上に最大120件保持し、画面サービスの再起動で消えます。セッションの有効期間は8時間です。
- この管理画面はroot権限で決められた診断・systemd操作だけを実行します。パスキーはサーバー管理用として扱ってください。任意コマンドの実行機能はありません。

停止・無効化: `sudo systemctl disable --now altserver-webui`。AltServer本体のサービスは継続します。管理画面のアップデートは同じインストールコマンドの再実行で行えます。既存のキーと待受設定を保持し、画面サービスだけを再起動します。

見た目だけ試す場合は `python3 web/server.py --demo` を実行し、ループバックURLでキー `demo` を使います。表示データと操作結果はすべて架空です。

## English

The optional console shows service status, the configured iPhone connection and diagnostic logs. It supports connection checks, manually running the existing recovery check, and restarting individual services. Continue refreshing apps from AltStore Classic on your iPhone.

On a configured AltServer host, with both server and client connected to Tailscale, run:

```sh
sudo sh scripts/install-web-ui.sh --tailscale
```

Open the displayed HTTPS URL, choose **Register a passkey**, and follow your device’s Face ID, Touch ID, Windows Hello or other authenticator prompts. Initial enrollment is restricted to connections from the server owner’s Tailscale account. Subsequent visits use **Sign in with a passkey**, with no administration access key to enter. Available verification methods depend on the device, browser and passkey provider.

If Tailscale HTTPS is not enabled, use the setup URL printed by the command to enable HTTPS, then rerun. Funnel is unnecessary. Access stays within the tailnet; certificate issuance records the server’s DNS name in public certificate transparency logs. An existing app on port 443 is not overwritten. Initial enrollment on tagged nodes is unsupported.

Verification uses py_webauthn, installed into a dedicated Python virtual environment. Private keys and biometric data are not sent to the server. Public credential data is stored in `/var/lib/altserver-webui/passkeys.json` with mode 0600. Additional enrollment after the first passkey is currently unsupported; availability on other devices depends on your provider’s passkey synchronization.

If the passkey is lost, use SSH to stop the console, move its registration file to a backup, and restart it. Only the owner can enroll again. Preserve this file during normal updates.

```sh
sudo systemctl stop altserver-webui
sudo mv /var/lib/altserver-webui/passkeys.json /var/lib/altserver-webui/passkeys.backup.json
sudo systemctl start altserver-webui
```

A fresh installation without `--tailscale` uses the legacy loopback/access-key mode. Updating an existing HTTPS installation preserves its configuration and passkey even when the flag is omitted. HTTPS mode disables access-key login.

- Status updates approximately every 10 seconds while the page is visible. Connection failures leave the last result visible with a warning.
- Recovery starts the existing health check and respects its failure thresholds and cooldowns; it does not force a restart every time.
- Recovery and restart actions show a confirmation dialog and may interrupt an app refresh in progress.
- Logs show console actions and fixed-category counts from the last 32 KiB of AltServer output. Raw logs, Apple authentication headers and device identifiers are not transmitted. Counts do not prove that an app refresh succeeded.
- Up to 120 console events are held in memory and reset when the console service restarts. Login sessions expire after eight hours.
- The console runs as root for predefined diagnostic and systemd operations. Treat the passkey as an administration credential. It cannot run arbitrary commands.

Disable it with `sudo systemctl disable --now altserver-webui`; AltServer services continue running. Rerun the installer to update the console while preserving its key and listening configuration; only the console service restarts.

For a visual preview, run `python3 web/server.py --demo`, open the loopback URL, and use the key `demo`. All data and operation results in demo mode are synthetic.

## References / 参考

The status-check organization of [Ben-Diehlci/altserver-linux](https://github.com/Ben-Diehlci/altserver-linux) and the authenticated controls in [AltKeeper](https://github.com/BartolomeoRusso9/altkeeper) informed the design. This console is a new implementation; their web code was not copied. The fork's existing AltServer and recovery services remain its runtime foundation.

状態診断の構成はBen-Diehlci/altserver-linux、認証付き操作はAltKeeperを参考にしました。Webコードの転載ではなく、このフォークの既存サービスに合わせた新規実装です。

Reviewed commits / 参照コミット: Ben-Diehlci `04d98547c4e60dee9d8715002ec7878b1eeddcf7`; AltKeeper `48f8059b18ef96b9eff9b3d6b07935f0c59f7345`.
