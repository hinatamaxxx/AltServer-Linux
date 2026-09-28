# v0.1.2 — Preview / プレビュー

## 日本語

関連実装を追加調査し、Bonjour と要求受信の処理を改善しました。

- Ben-Diehlci の実装を参考に、Bonjour ヘルパーの64ビット型、引用符を含む文字列、バイナリ TXT の受け渡しを修正。
- 登録 API の戻り値を親プロセスへ返し、Python 起動失敗・登録エラー・応答停止を成功扱いしないように変更。
- AltKeeper を参考に、JSON 要求の長さを本文受信前に検証し、4 MiB までに制限。IPA 本体の上限ではありません。

[採用元と検証方法](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.2/docs/fork-review.md)を記録しています。39件の Python テスト、C++ 回帰テスト、署名・GSA・要求受信の検証、amd64 ビルド、CLI、Debian 13 セットアップ試験の通過後に配布物を公開します。セットアップ試験のサービス起動は模擬処理です。

iPhone 実機での導入・更新、Apple への実ログイン、LAN 上の Bonjour 探索、Avahi 再起動後の広告復旧は未検証です。導入方法と対象環境は README を参照してください。

## English

Further review of related implementations led to improvements in Bonjour and request handling.

- Following Ben-Diehlci's implementation, fix the Bonjour helper's 64-bit types, quoted text arguments and binary TXT handling.
- Return the registration API result to the parent process; Python launch failure, API errors and a hung registration no longer count as success.
- Following AltKeeper's approach, validate JSON request lengths before reading the body and cap them at 4 MiB. This is not an IPA payload limit.

[Sources and validation methods](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.1.2/docs/fork-review.md) are documented. Assets are published after 39 Python tests, C++ regressions, signing/GSA/request tests, the amd64 build, CLI tests and the Debian 13 setup test pass. Service activation in the setup test is simulated.

Physical iPhone installation/refresh, live Apple sign-in, Bonjour discovery on the LAN and advertisement recovery after an Avahi restart remain unverified. See the README for installation and supported environments.

Codex: GPT-6 Astra, High reasoning / High（高）。Japanese and English proofreading / 日英校正: Gemini 3.8 Flash, High reasoning / High（高）。
