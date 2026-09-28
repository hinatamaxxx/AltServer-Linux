# v0.2.2 — Preview / プレビュー

## 日本語

新規セットアップで、netmuxdを特定のバージョンに固定せず、導入時点の公式最新リリースを取得するよう変更しました。取得したファイルはGitHubが公開するSHA-256と照合し、採用したバージョン・URL・チェックサムをセットアップの状態ファイルに記録します。

検証に使ったバージョンは[検証記録](https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/verification.md)に記載しています。

## English

New setups now download the latest official netmuxd release available at installation time instead of a fixed version. Setup verifies the download against the SHA-256 digest published by GitHub and records the selected version, URL, and checksum in its state file.

Versions used for testing are listed in the [verification record](https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/verification.md).
