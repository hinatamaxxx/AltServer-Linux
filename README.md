# AltServer-Linux — 自動復旧・簡単セットアップ

日本語 | [English](README.en.md)

[NyaMisty/AltServer-Linux](https://github.com/NyaMisty/AltServer-Linux) のフォークです。本体の不具合修正と、[altserver-linux-native-autorecover](https://github.com/hinatamaxxx/altserver-linux-native-autorecover) の復旧機能をまとめています。

直接のフォーク元は **NyaMisty の非公式 Linux 移植版**です。AltStore チームが提供する公式 Linux 版ではありません。公式 AltServer のコードは [Windows 版](https://github.com/rileytestut/AltServer-Windows)と [macOS 版（AltStore 内）](https://github.com/altstoreio/AltStore/tree/classic/AltServer)で確認できます。

[取り込み元と URL](docs/provenance.md)・[公式実装の調査と取り込み方針](docs/upstream-review.md)を公開しています。新しいタブで開くリンクは、[リンク一覧 HTML](docs/sources.html)をダウンロードしてブラウザーで開くと利用できます。GitHub 上の README では新しいタブを強制できないため、Ctrl+クリック（Mac は Command+クリック）を使ってください。

AltServer、公式 netmuxd v0.4.3、Avahi、usbmuxd、Docker、ローカル Anisette を一括導入します。AltServer と端末探索はホスト上、Anisette は Docker 上で動作し、systemd が起動と監視を担当します。

## 簡単な導入

対象は **Debian 12/13・amd64・systemd 環境**です。amd64 以外の CPU アーキテクチャや Docker Desktop はこのインストーラの対象外です。インターネット接続が必要です。Debian 12 とクリーンな実機への新規導入は未検証です。

```sh
git clone https://github.com/hinatamaxxx/AltServer-Linux.git
cd AltServer-Linux
sudo sh install.sh --prepare
```

**準備には iPhone も Apple アカウントも不要です。AltServer はまだ有効化しません。** 依存環境とチェックサム検証済みバイナリを導入し、取得した Anisette イメージをダイジェストで固定します。引数なしでも準備のみを実行します。

準備完了後、iPhone を1台だけ USB 接続し、ペアリング・「信頼」を完了してから有効化します。

```sh
sudo sh install.sh --configure
sudo /usr/local/sbin/altserver-native-healthcheck
```

ペアリング情報がない場合は、iPhone のロックを解除して `idevicepair pair` を実行し、「信頼」に応答してから再度 `sudo sh install.sh --configure` を実行してください。Wi-Fi 更新には、同一 LAN 上で通信できる iPhone とサーバー、および有効なペアリング情報が必要です。Tailscale は遠隔管理用で、Bonjour 探索や USB の信頼操作を代替しません。

リリースの **AltServer-Linux-amd64-setup.tar.gz** を展開して、同じコマンドを実行する方法もあります。本フォークのバイナリと設定用ファイルを同梱します。Debian パッケージ、netmuxd、Anisette は準備時に取得するため、オフライン用ではありません。

**既存環境があれば変更せず停止します。** [セットアップ・移行](docs/setup.md)を参照してください。

## 主な修正

- v0.2.0: C++ 基盤と端末通信ライブラリの参照先を公式リポジトリへ変更。公式 Windows の 1.7.5 開発ソースに含まれる認証処理を取り込み、2FA の HTTP エラー判定・認証ログ・未知のエラーコード処理を修正しました。アドレス互換処理は入力部分に集約しています。版番号は `VERSION` で一元管理し、`--version` で確認できます。[保守手順](docs/maintenance.md)も追加しました。
- v0.1.3: 互換アダプターを削除し、jaakkopalvaila の libimobiledevice 修正を取り込みました。AltServer が Linux/BSD の IPv4・IPv6 アドレスを直接扱います。コピー長の境界値も補強しています。公式上流へのマージを意味するものではありません。
- v0.1.2: Bonjour ヘルパーの64ビット型・文字列とバイナリの受け渡しを修正し、登録 API の失敗を親プロセスへ返します。AltKeeper を参考に JSON 要求を 4 MiB までに制限し、不正な長さを本文受信前に拒否します。IPA 本体のサイズ制限ではありません。
- v0.1.1: 他フォークで報告された Apple ID 認証ヘッダーと GSA 接続の修正、AltServer for Windows 1.7.4 と同じ ldid ソースを取り込みました。新しい iOS での署名エラーへの対応が目的です。出典と採否は[フォーク調査](docs/fork-review.md)を参照してください。Apple への実ログインと iPhone 実機での動作は未検証です。
- GSA の TLS 証明書検証を有効化し、既存コードにあった検証の無効化を除去。
- Anisette の日時をホストのタイムゾーンに依存せず UTC として解釈。日付と64ビット routing info を検証。
- Anisette 応答値のデバッグ出力を除去。HTTP 要求に15秒の制限を設定。
- `-h` / `--help`、IPA 導入時の引数不足、`-a` から `-p` への処理の流れ込み、読めない IPA、失敗時の終了コードを修正。
- USB 通信のゼロバイト転送や不正サイズを検出し、無限ループを防止。
- Anisette の端末 ID と認証状態をコンテナの置き換え時も保持。
- AltServer は公式 netmuxd に `127.0.0.1:27015` で直接接続し、公式 API で設定済み iPhone を再登録。
- netmuxd を直接監視して復旧。iPhone 不在時もサービスを確認。

復旧は3回連続失敗後に行い、サービス再起動は5分間の間隔を確保します。確認の終了から15秒後に次の確認を開始します。`healthy` はサーバー・プロトコルの確認結果で、アプリ更新の成功を保証するものではありません。iPhone が不在なら `waiting_for_device` が通常の待機状態です。自動確認は Apple へのログインやアプリ更新を行いません。

## 検証・ビルド

本フォークは **プレビュー版**です。この版での iPhone 実機への導入・更新、ホスト再起動後の復旧、長時間稼働は未検証です。以前の実機成功例は旧セットアップの結果です。詳細は[検証記録](docs/verification.md)を参照してください。

```sh
git clone --recursive https://github.com/hinatamaxxx/AltServer-Linux.git
cd AltServer-Linux
docker build -f docker/Dockerfile.build --target export --output type=local,dest=dist .
```

上流の amd64 ビルド環境で本フォークのソースと固定されたサブモジュールをビルドします。通常のインストールにはビルド環境は不要です。[上流の説明](docs/upstream-readme.md)も参考用に残しています。

## 個人情報・ライセンス・AI の利用

Apple の認証情報、ペアリング情報、端末識別子、ログ、Anisette の状態をコミットしないでください。設定ファイルは権限 0600 で保存します。セットアップは Apple の認証情報を要求しません。

本体は [AGPL-3.0](LICENSE)、取り込んだ復旧スクリプトは [MIT](LICENSE.autorecover) を維持します。依存ソフトウェアには各々のライセンスが適用されます。詳細は[取り込み元](docs/provenance.md)を参照してください。

今回の作業は Codex の **GPT-6 Astra・High（高）**を使用し、このセッションのメタデータで確認しています。日英の校正には **Gemini 3.8 Flash・High（高）**を使用しました。以前の復旧機能は旧プロジェクトの記録どおり GPT-6 Astra・Low（低）を使用しています。AI の利用は実機互換性の検証を意味しません。
