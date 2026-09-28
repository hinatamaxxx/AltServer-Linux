# Web UI / 管理画面

## 日本語

ブラウザーでサービスの状態、設定済みiPhoneの接続、診断ログを確認できます。接続診断、既存の自動復旧処理の手動実行、サービスごとの再起動に対応します。アプリのリフレッシュは引き続きiPhoneのAltStore Classicから行います。

AltServerの設定後、ソースまたは展開したセットアップフォルダーで実行します。Python標準ライブラリのみを使用し、Node.jsは不要です。

```sh
sudo sh scripts/install-web-ui.sh
sudo cat /var/lib/altserver-webui/access-key
```

初期URLは `http://127.0.0.1:8787` です。表示したアクセスキーでログインします。キーはApple IDのパスワードとは別のものです。キーを公開したり、URLに含めたりしないでください。

別のPCやiPhoneからは、Tailscaleを接続したうえで `/etc/altserver-webui.env` の `WEBUI_LISTEN` をサーバー自身のTailscale IPv4アドレスに変更し、`sudo systemctl restart altserver-webui` を実行します。そのIPアドレスのポート8787をブラウザーで開きます。サーバーの再起動時にTailscaleのアドレスがまだ使えない場合、画面サービスは5秒後に再試行します。

ループバックで待ち受けたままSSHポート転送で利用することもできます。この画面自体はHTTPです。リモート利用ではTailscaleまたはSSHの暗号化経路を使ってください。インターネットへのポート公開やHTTPSリバースプロキシはサポートしていません。

- 状態は画面を表示している間、約10秒ごとに更新します。通信失敗時は最後の取得結果と警告を表示します。
- 「復旧処理」は既存のヘルスチェックを起動します。既存の失敗回数・待機時間の判定に従うため、毎回強制再起動する操作ではありません。
- 再起動・復旧の前に確認画面を表示します。実行中のアプリ更新が中断される場合があります。
- 診断ログには画面からの操作記録と、AltServerログ末尾32 KiBから集計した固定カテゴリの件数を表示します。生ログ、Apple認証ヘッダー、端末IDは転送しません。件数はアプリ更新の成功を証明しません。
- 画面からの操作記録はメモリー上に最大120件保持し、画面サービスの再起動で消えます。セッションの有効期間は8時間です。
- この管理画面はroot権限で決められた診断・systemd操作だけを実行します。アクセスキーはサーバー管理用として扱ってください。任意コマンドの実行機能はありません。

停止・無効化: `sudo systemctl disable --now altserver-webui`。AltServer本体のサービスは継続します。管理画面のアップデートは同じインストールコマンドの再実行で行えます。既存のキーと待受設定を保持し、画面サービスだけを再起動します。

見た目だけ試す場合は `python3 web/server.py --demo` を実行し、ループバックURLでキー `demo` を使います。表示データと操作結果はすべて架空です。

## English

The optional console shows service status, the configured iPhone connection and diagnostic logs. It supports connection checks, manually running the existing recovery check, and restarting individual services. Continue refreshing apps from AltStore Classic on your iPhone.

After configuring AltServer, run these commands from the source checkout or extracted setup folder. Only the Python standard library is required; Node.js is not needed.

```sh
sudo sh scripts/install-web-ui.sh
sudo cat /var/lib/altserver-webui/access-key
```

Open `http://127.0.0.1:8787` and sign in with the displayed access key. This is separate from your Apple ID password. Keep it private and do not place it in a URL.

For another PC or iPhone, connect Tailscale, set `WEBUI_LISTEN` in `/etc/altserver-webui.env` to the server's own Tailscale IPv4 address, and run `sudo systemctl restart altserver-webui`. Open that IP address on port 8787. If the Tailscale address is unavailable during boot, the console service retries after five seconds.

Alternatively, keep the loopback binding and use SSH port forwarding. The console itself uses HTTP; remote access requires an encrypted Tailscale or SSH connection. Public port forwarding and HTTPS reverse proxies are not supported.

- Status updates approximately every 10 seconds while the page is visible. Connection failures leave the last result visible with a warning.
- Recovery starts the existing health check and respects its failure thresholds and cooldowns; it does not force a restart every time.
- Recovery and restart actions show a confirmation dialog and may interrupt an app refresh in progress.
- Logs show console actions and fixed-category counts from the last 32 KiB of AltServer output. Raw logs, Apple authentication headers and device identifiers are not transmitted. Counts do not prove that an app refresh succeeded.
- Up to 120 console events are held in memory and reset when the console service restarts. Login sessions expire after eight hours.
- The console runs as root for predefined diagnostic and systemd operations. Treat its access key as an administration credential. It cannot run arbitrary commands.

Disable it with `sudo systemctl disable --now altserver-webui`; AltServer services continue running. Rerun the installer to update the console while preserving its key and listening configuration; only the console service restarts.

For a visual preview, run `python3 web/server.py --demo`, open the loopback URL, and use the key `demo`. All data and operation results in demo mode are synthetic.

## References / 参考

The status-check organization of [Ben-Diehlci/altserver-linux](https://github.com/Ben-Diehlci/altserver-linux) and the authenticated controls in [AltKeeper](https://github.com/BartolomeoRusso9/altkeeper) informed the design. This console is a new implementation; their web code was not copied. The fork's existing AltServer and recovery services remain its runtime foundation.

状態診断の構成はBen-Diehlci/altserver-linux、認証付き操作はAltKeeperを参考にしました。Webコードの転載ではなく、このフォークの既存サービスに合わせた新規実装です。

Reviewed commits / 参照コミット: Ben-Diehlci `04d98547c4e60dee9d8715002ec7878b1eeddcf7`; AltKeeper `48f8059b18ef96b9eff9b3d6b07935f0c59f7345`.
