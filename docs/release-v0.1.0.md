# v0.1.0 — Preview / プレビュー

## 日本語

本家 AltServer-Linux のフォークとして、本体修正と従来の自動復旧機能を統合しました。UTC 時刻処理、64ビット routing info、Anisette 応答値のデバッグ出力、CLI 引数・終了コード、通信のゼロバイト転送を修正しています。

Debian amd64 向けセットアップは、Docker を含む依存環境とバイナリをまとめて準備できます。`sudo sh install.sh --prepare` は iPhone 不要です。USB ペアリング後に `--configure` で有効化します。既存環境の自動移行は行いません。

`AltServer-Linux-amd64-setup.tar.gz` はセットアップ一式、`AltServer-x86_64` は単体バイナリ、`SHA256SUMS` はチェックサムです。依存パッケージの取得にインターネットが必要です。iPhone 実機での更新とホスト再起動は未検証のプレビューです。

## English

This fork combines fixes in AltServer-Linux with the existing recovery tools. Fixes cover UTC timestamps, 64-bit routing info, removal of Anisette response debug output, CLI arguments and exit codes, and zero-progress transfers.

The Debian amd64 setup prepares dependencies, including Docker, and the binaries together. `sudo sh install.sh --prepare` needs no iPhone. Activate with `--configure` after USB pairing. Existing installations are not automatically migrated.

`AltServer-Linux-amd64-setup.tar.gz` contains the setup bundle; `AltServer-x86_64` is the standalone binary; `SHA256SUMS` lists checksums. Dependency downloads require internet access. This is a preview: iPhone refresh and full-host reboot remain unverified.
