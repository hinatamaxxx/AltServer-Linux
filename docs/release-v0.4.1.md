# v0.4.1 — Stability fixes / 安定性の修正

## 日本語

v0.4.0 の不具合を2件修正しました。

- Anisette のコンテナに `--init` を付けました。Wine が残す終了済みプロセスが回収されずに溜まり、約77分ごとにプロセス数の上限に達して Anisette の要求が `503` で失敗していました。
- ヘルスチェックが、設定時に記録した LAN の IPv4 アドレスではなく、サーバーが今持っているアドレスと Bonjour の告知を照合するようにしました。DHCP でアドレスが変わると、AltServer が5分おきに再起動され続けていました。

v0.4.0 から更新する場合は、`sudo sh scripts/install-helper-scripts.sh` を実行してから `sudo systemctl restart altserver-icloud-local.service` を実行してください。Apple が信頼した端末情報（Wine の状態）はそのまま使えます。

## English

Fixes two v0.4.0 bugs.

- The Anisette container now runs with `--init`. Exited processes left by Wine were never reaped, so the container hit its process limit about every 77 minutes and Anisette requests failed with `503`.
- The health check now matches the Bonjour announcement against the addresses the server currently holds, not the LAN IPv4 address recorded at setup. After a DHCP address change, AltServer was restarted every five minutes.

To update from v0.4.0, run `sudo sh scripts/install-helper-scripts.sh`, then `sudo systemctl restart altserver-icloud-local.service`. The device identity Apple trusts (Wine state) is kept.
