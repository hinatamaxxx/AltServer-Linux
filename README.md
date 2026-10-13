# AltServer-Linux

日本語 | [English](README.en.md)

自宅の Debian サーバーで AltServer を動かし、iPhone の AltStore から Wi-Fi 経由でアプリをリフレッシュするためのセットアップ一式です。Windows や Mac を常時起動しておく必要はありません。

[NyaMisty/AltServer-Linux](https://github.com/NyaMisty/AltServer-Linux) をもとにした**非公式のプレビュー版**です。AltStore の開発チームが提供するものではありません。

## できること

- iPhone の AltStore から、Debian 上の AltServer を使ってアプリをリフレッシュする
- AltServer・iPhone との通信・Apple 認証用データ（Anisette）を systemd で常駐させ、止まったら自動で復旧する
- サービスの状態確認や復旧操作を、ブラウザーの管理画面から行う（任意）

## 必要なもの

| 必要なもの | 用途 |
| --- | --- |
| Debian 12 または 13（amd64、systemd）とインターネット接続 | AltServer を常駐させるサーバー |
| iPhone 1台と USB ケーブル | 最初のペアリング（「信頼」）に使います。以降は Wi-Fi で更新します |
| Windows PC（Windows 版 AltServer と iCloud が動作するもの） | 最初に1回だけ、Apple の iCloud ライブラリを書き出すのに使います |
| iPhone とサーバーが同じ LAN にあること | Wi-Fi 更新では、iPhone が LAN 内でサーバーを探して接続します |

amd64 以外の CPU や Docker Desktop は対象外です。Apple ID とパスワードは、セットアップでは入力しません。AltStore でサインインするときに使います。

## 導入手順

### 1. サーバーの準備

```sh
git clone https://github.com/hinatamaxxx/AltServer-Linux.git
cd AltServer-Linux
sudo sh install.sh --prepare
```

必要なパッケージ、AltServer、netmuxd を導入し、Anisette 用のコンテナイメージをビルドします。この段階では iPhone は不要で、AltServer もまだ起動しません。[リリース](https://github.com/hinatamaxxx/AltServer-Linux/releases)の `AltServer-Linux-amd64-setup.tar.gz` を展開して、同じコマンドを実行してもかまいません。

### 2. Apple の iCloud ライブラリの取り込み

Apple への認証には、Windows 版 iCloud のライブラリを Wine で動かして作るデータを使います。Apple のファイルは再配布できないため、このリポジトリには含めていません。

Windows PC で、このリポジトリの `scripts\windows\export-apple-runtime.ps1` を実行します。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export-apple-runtime.ps1
```

作成された `apple-runtime.tar.gz` をサーバーにコピーし、取り込みます。

```sh
sudo sh install.sh --import-apple-runtime apple-runtime.tar.gz
```

取り込み時に、ライブラリの版をハッシュで確認します。Apple ID やパスワードは含まれません。

### 3. iPhone の接続と有効化

iPhone を1台だけ USB で接続し、iPhone に表示される「このコンピュータを信頼しますか？」で「信頼」を選びます。そのうえで有効化します。

```sh
sudo sh install.sh --configure
sudo /usr/local/sbin/altserver-native-healthcheck
```

ペアリング情報がないと言われた場合は、iPhone のロックを解除して `idevicepair pair` を実行し、「信頼」を選んでから `--configure` をやり直してください。

### 4. AltStore でのサインインとリフレッシュ

iPhone を USB から外し、サーバーと同じ Wi-Fi につないだ状態で、AltStore からリフレッシュします。

初めてのサインインでは、2要素認証のコード入力欄が出ずに `-22411` で失敗することがあります。Apple がサーバーを新しい端末として扱い、AltStore が対応していない方式の確認を求めるためです（[AltStore#1737](https://github.com/altstoreio/AltStore/issues/1737)）。その場合は次の手順で一度だけサーバーを信頼させてください。

1. iPhone の「設定」→ 自分の名前 →「サインインとセキュリティ」→「2ファクタ認証」→「確認コードを受け取る」でコードを表示します。
2. サーバーで `sudo altserver-apple-trust` を実行し、Apple ID・パスワード・表示されたコードを入力します。
3. `Success` と表示されたら、AltStore でもう一度リフレッシュします。

入力したパスワードとコードは保存しません。

## 困ったとき

| 症状 | 対処 |
| --- | --- |
| `AltServer could not be found`（エラー 1200） | iPhone の Wi-Fi をオフにしてからオンに戻し、もう一度リフレッシュします。iPhone とサーバーが同じ LAN にあるかも確認してください |
| `-22411` で失敗し、コード入力欄が出ない | 上の「4. AltStore でのサインインとリフレッシュ」の手順で `altserver-apple-trust` を実行します |
| `-80045`（This action cannot be completed at this time） | v0.3.x 以前の Android 系 Anisette が Apple に拒否されています。v0.4.0 へ移行してください（[移行手順](docs/setup.md)） |
| サービスの状態を知りたい | `sudo /usr/local/sbin/altserver-native-healthcheck` を実行します。`healthy` なら正常、iPhone が近くにないときの `waiting_for_device` は通常の待機状態です |

自動確認は、前回の確認が終わってから15秒後に行います。3回続けて失敗したときだけサービスを再起動し、再起動の間隔は5分以上あけます。`healthy` はサーバーと通信の確認結果で、アプリ更新の成功までは保証しません。自動確認が Apple にログインしたり、アプリを更新したりすることはありません。

## Web 管理画面（任意）

サービスの状態、iPhone との接続、診断ログ、復旧操作を、ブラウザーから日本語・英語で確認できます。サーバーとアクセスする PC の両方で Tailscale を使い、HTTPS とパスキーでログインします。

```sh
sudo sh scripts/install-web-ui.sh --tailscale
```

AltServer の有効化後に実行してください。Tailscale を使わない LAN 内公開や、インターネットへの公開はサポートしていません。詳しくは [Web 管理画面](docs/web-ui.md) を参照してください。

## 仕組み

| サービス | 役割 |
| --- | --- |
| `altserver-native.service` | AltServer 本体。LAN に Bonjour で存在を知らせ、AltStore からの要求を処理します |
| `altserver-native-netmuxd.service` | Wi-Fi 上の iPhone との通信（公式 netmuxd） |
| `altserver-icloud-local.service` | Apple 認証用データ（Anisette）を作る Docker コンテナ。Windows 版 iCloud のライブラリを Wine で動かします |
| `iphone-mobdev-address.service` ほか | 設定した iPhone を見つけて netmuxd に登録します |
| `altserver-native-healthcheck.timer` | 定期確認と自動復旧 |

設定は `/etc/altserver-native.env`（権限 0600）に保存します。Apple が信頼した端末情報は `/var/lib/altserver-native/icloud-local` にあります。このディレクトリを消すと、Apple から新しい端末として扱われ、もう一度 `altserver-apple-trust` が必要になります。

## 更新・移行

インストーラーは、既存の環境を見つけると何も変更せずに停止します。v0.3.x からの移行は手動で行います。手順は[セットアップ・移行](docs/setup.md)を参照してください。

## 注意事項

- プレビュー版です。既存の Debian サーバーと iOS 27 の iPhone でリフレッシュできることを確認していますが、新規導入の一連の流れ、ホスト再起動後の動作、長時間の稼働は未検証です。詳細は[検証記録](docs/verification.md)にあります。
- Apple の認証情報、ペアリング情報、端末識別子、ログ、Anisette や Wine の状態、Apple のライブラリはコミットしないでください。
- 本体は [AGPL-3.0](LICENSE)、取り込んだ復旧スクリプトは [MIT](LICENSE.autorecover) です。依存ソフトウェアにはそれぞれのライセンスが適用されます。

## 開発者向け

ソースからビルドする場合は、次のコマンドを実行します。通常の導入にはビルド環境は不要です。

```sh
git clone --recursive https://github.com/hinatamaxxx/AltServer-Linux.git
cd AltServer-Linux
docker build -f docker/Dockerfile.build --target export --output type=local,dest=dist .
```

- [変更履歴](docs/changelog.md)・各版のリリースノート（`docs/release-*.md`）
- [取り込み元と URL](docs/provenance.md)・[リンク一覧 HTML](docs/sources.html)
- [公式実装の調査](docs/upstream-review.md)・[フォーク調査](docs/fork-review.md)・[保守手順](docs/maintenance.md)
- [上流の README](docs/upstream-readme.md)（参考用）

公式 AltServer のコードは [Windows 版](https://github.com/rileytestut/AltServer-Windows)と [macOS 版（AltStore 内）](https://github.com/altstoreio/AltStore/tree/classic/AltServer)で確認できます。

これまでの作業には、Codex の GPT-6 Astra（High、以前の復旧機能は Low）を使い、日英の校正には Gemini 3.8 Flash（High）を使いました。v0.4.0 の Wine 版 Anisette、信頼登録ツール、この README の書き直しには、Claude Code の Claude Opus 5.5 を使っています。AI を使ったことは、実機での互換性を保証するものではありません。
