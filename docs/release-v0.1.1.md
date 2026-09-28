# v0.1.1 — Preview / プレビュー

## 日本語

他フォークから、Apple ID 認証ヘッダー、GSA 接続、ldid の署名修正を取り込みました。ldid は AltServer for Windows 1.7.4 の公式ソースと一致する版です。GSA の TLS 証明書検証も有効化しました。[出典と採否](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.1/docs/fork-review.md)を記録しています。

CI では既存の回帰・CLI・Debian 13 セットアップ試験に加え、一時証明書と架空のアプリによる署名、完全な SHA-1 / SHA-256 ハッシュ、ローカルサーバーでの GSA 接続分離を検証します。CI 通過後に配布物を公開します。Apple への実ログイン、iPhone での導入・更新は未検証です。

新規導入はセットアップアーカイブを展開し、`sudo sh install.sh --prepare`、ペアリング完了後に `sudo sh install.sh --configure` の順で実行します。Debian 12/13・amd64・systemd が対象です。Debian 12 と実機への新規導入は未検証です。既存環境の自動更新は対象外で、稼働中の設定・認証状態は置き換えていません。

## English

This update adopts Apple ID client-header, GSA connection and ldid signing fixes from other forks. The ldid source matches the official AltServer for Windows 1.7.4 version. GSA TLS certificate validation is now enabled. [Sources and selection decisions](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.1/docs/fork-review.md) are documented.

In addition to existing regression, CLI and Debian 13 setup checks, CI validates signing with a disposable certificate and synthetic app, full SHA-1 and SHA-256 agility hashes and separate GSA connections against a local server. Assets are published after CI passes. Live Apple sign-in and installation/refresh on an iPhone remain unverified.

For a new installation, extract the setup archive, run `sudo sh install.sh --prepare`, then `sudo sh install.sh --configure` after pairing. The installer targets Debian 12/13, amd64 and systemd. Debian 12 and clean physical-host installation remain unverified. Automatic upgrades are outside its scope; the existing server's configuration and authentication state were not replaced.

## AI assistance / AI の利用

Codex: GPT-6 Astra, High reasoning / High（高）。Japanese and English proofreading / 日英校正: Gemini 3.8 Flash, High reasoning / High（高）。
