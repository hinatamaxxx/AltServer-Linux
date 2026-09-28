# v0.1.3 — Preview / プレビュー

## 日本語

追加の互換アダプターを削除し、AltServer 内の libimobiledevice で netmuxd のアドレス形式を直接処理する構成に変更しました。

- jaakkopalvaila の Linux/BSD IPv4・IPv6 対応を取り込み、アドレスのコピー長を補強。公式上流へのマージを意味するものではありません。
- 公式 netmuxd v0.4.3 にポート27015で直接接続。アダプターのスクリプト、サービス、監視処理を削除。
- 古いバイナリと新しい設定が混在しないよう、異なるバージョンで準備したセットアップの再利用を拒否。

[出典と検証方法](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.3/docs/fork-review.md)を記録しています。34件の Python テスト、ネイティブ通信9ケースとコピー長512通り、既存の C++・署名・GSA・要求受信・CLI 試験、amd64 ビルド、展開済みアーカイブによる Debian 13 セットアップ試験の通過後に公開します。セットアップ試験のサービス起動は模擬処理です。

iPhone 実機での導入・更新と Apple への実ログインは未検証です。既存の運用サーバーには適用していません。旧構成のアダプターだけを停止せず、[移行上の注意](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.3/docs/setup.md)を確認してください。

## English

Remove the additional compatibility adapter and handle netmuxd addresses directly in AltServer's libimobiledevice.

- Adopt jaakkopalvaila's Linux/BSD IPv4 and IPv6 support with an additional copy-length correction. This does not imply that the patch has been merged into official upstream.
- Connect directly to official netmuxd v0.4.3 on port 27015. Remove the adapter script, service and monitoring.
- Reject setup state prepared by a different version to prevent mixing old binaries with new configuration.

[Sources and validation methods](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.3/docs/fork-review.md) are documented. Publication follows 34 Python tests, nine native communication cases and 512 copy-length assertions, existing C++/signing/GSA/request/CLI tests, the amd64 build and a Debian 13 setup test using the extracted archive. Service activation in the setup test is simulated.

Physical iPhone installation/refresh and live Apple sign-in remain unverified. This update has not been automatically deployed to the existing physical server. Do not stop only the old adapter; see the [migration notes](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.3/docs/setup.md).

Codex: GPT-6 Astra, High reasoning / High（高）。Japanese and English proofreading / 日英校正: Gemini 3.8 Flash, High reasoning / High（高）。
