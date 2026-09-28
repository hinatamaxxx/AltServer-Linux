# セットアップ / Setup

## 日本語

v0.1.3 では AltServer が `127.0.0.1:27015` の公式 netmuxd に直接接続します。互換アダプターは配布・起動しません。旧構成から切り替える場合は、新バイナリ、netmuxd の待受ポート、systemd の依存関係、監視処理をまとめて変更し、旧アダプターを停止・無効化する必要があります。アダプターだけを停止しても移行は完了しません。異なるバージョンで準備した状態の再利用は拒否します。

新規導入は README の `--prepare`、`--configure` の順で行います。準備だけなら iPhone は不要です。設定時に既存の USB ペアリング情報を使用します。セットアップが Apple の認証情報を尋ねることはありません。

通常はホストの LAN IPv4、USB 接続された iPhone の UDID と Wi-Fi MAC を自動検出します。複数端末や複数 NIC がある場合は `ALTSERVER_HOST_IP`、`IPHONE_UDID`、`IPHONE_WIFI_MAC`、必要なら `IPHONE_FALLBACK_IP` をローカルの環境変数として指定できます。入力は形式を検証し、シェル用に引用して権限 0600 の `/etc/altserver-native.env` に保存します。Apple ID やパスワードは指定しません。

`sudo` が環境変数を消す場合は `sudo ALTSERVER_HOST_IP=... IPHONE_UDID=... IPHONE_WIFI_MAC=... sh install.sh --configure` のように直接渡してください。`...` は説明用で、実際の値に置き換えます。

Anisette の状態は `/var/lib/altserver-native/anisette` に保存します。`device.json` と `adi.pb` を含むディレクトリ全体を保持し、不完全な状態は自動で作り直しません。準備時に取得した Docker イメージのダイジェストを保存し、起動時に `latest` を追従しません。

既存環境からの自動移行はこのプレビューの対象外です。インストーラは既存設定やバイナリを検出すると停止します。稼働中の構成を削除して回避しないでください。旧環境の設定、ペアリング情報、Anisette 状態、systemd の追加設定をバックアップし、別の Debian ホストで動作確認してから切り替えてください。今回の作業では既存実機のサービスは置き換えていません。

停止は `sudo systemctl stop altserver-native-healthcheck.timer altserver-native-boot-recover.service altserver-native-healthcheck.service altserver-native.service iphone-mobdev-address.service iphone-mobdev-service.service altserver-native-netmuxd.service altserver-anisette-docker.service` で行います。状態データは残ります。Docker や Avahi を共有する他のアプリには影響を与えません。再開は `sudo systemctl start altserver-native.service altserver-native-healthcheck.timer` で行います。サーバーの依存サービスも起動します。

## English

In v0.1.3, AltServer connects directly to official netmuxd at `127.0.0.1:27015`. The compatibility adapter is no longer distributed or started. Switching from the old setup requires coordinated changes to the binary, netmuxd listening port, systemd dependencies and health checks, plus stopping and disabling the old adapter. Stopping only the adapter does not complete migration. Setup rejects state prepared by a different version.

For a new installation, run `--prepare`, then `--configure` as shown in the README. Preparation needs no phone. Configuration uses an existing USB pairing record. Setup never asks for Apple credentials.

The host LAN IPv4 and the USB-connected phone's UDID and Wi-Fi MAC are normally detected automatically. For multiple devices or interfaces, set `ALTSERVER_HOST_IP`, `IPHONE_UDID`, `IPHONE_WIFI_MAC` and optionally `IPHONE_FALLBACK_IP` as local environment variables. Values are validated, shell-quoted and stored in `/etc/altserver-native.env` with mode 0600. Do not supply an Apple ID or password.

Pass variables directly to `sudo`, for example `sudo ALTSERVER_HOST_IP=... IPHONE_UDID=... IPHONE_WIFI_MAC=... sh install.sh --configure`, to avoid its environment reset. Replace the illustrative `...` placeholders with local values.

Anisette state lives in `/var/lib/altserver-native/anisette`. The full directory, including `device.json` and `adi.pb`, persists. Incomplete state is not silently regenerated. Setup records the downloaded Docker image's digest, so subsequent starts do not follow `latest`.

Automatic migration of an existing installation is outside this preview's scope. Setup stops if it finds existing configuration or binaries. Do not delete a working installation to bypass this check. Back up configuration, pairing records, Anisette state and systemd overrides, validate on a separate Debian host, then plan the switch. The existing physical server's services were not replaced during this work.

To stop, run `sudo systemctl stop altserver-native-healthcheck.timer altserver-native-boot-recover.service altserver-native-healthcheck.service altserver-native.service iphone-mobdev-address.service iphone-mobdev-service.service altserver-native-netmuxd.service altserver-anisette-docker.service`. State is retained. Other applications sharing Docker or Avahi are unaffected. Resume with `sudo systemctl start altserver-native.service altserver-native-healthcheck.timer`; server dependencies also start.
