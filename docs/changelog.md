# 変更履歴 / Changelog

旧 README の「主な修正」を移したものです。各版の詳細は `docs/release-*.md` を参照してください。

Moved from the former README. See `docs/release-*.md` for per-release notes.

## 日本語

- v0.4.0: Apple に拒否される Android 系 Anisette を廃止し、Windows 版 iCloud ライブラリを Wine で動かすローカル Anisette に置き換えました。Apple のライブラリはハッシュで検証して取り込みます。AltStore で2要素認証の入力欄が出ない場合の信頼登録ツール `altserver-apple-trust` を追加しました。
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

## English

- v0.4.0: Replace the Android-based Anisette, which Apple rejects, with local Anisette from Apple's Windows iCloud libraries running under Wine. Apple's libraries are imported with hash verification. Add `altserver-apple-trust` for AltStore sign-ins that show no two-factor code field.
- v0.2.0: Move the C++ base and device libraries to official repositories. Adopt authentication code from the official Windows 1.7.5 development source, with fixes for 2FA HTTP errors, authentication logging and unknown error codes. Address compatibility is handled at the input boundary. `VERSION` is the shared version source, exposed by `--version`. See the new [maintenance guide](docs/maintenance.md).
- v0.1.3: Remove the compatibility adapter and adopt jaakkopalvaila's libimobiledevice patch, so AltServer handles Linux/BSD IPv4 and IPv6 addresses directly. Address copy lengths are additionally bounded. This does not imply that the patch has been merged into official upstream.
- v0.1.2: Fix the Bonjour helper's 64-bit types and text/binary argument handling, and report registration API failures to the parent process. Following AltKeeper's approach, reject invalid JSON request lengths before reading the body and cap JSON frames at 4 MiB. This limit does not apply to IPA payloads.
- v0.1.1: Integrate Apple ID client-header and GSA connection fixes reported by other forks, plus the same ldid source as AltServer for Windows 1.7.4, to address signing errors on newer iOS versions. See the [fork review](docs/fork-review.md) for sources and selection decisions. Live Apple sign-in and operation on a physical iPhone remain unverified.
- Enable GSA TLS certificate validation, removing the inherited verification bypass.
- Parse Anisette timestamps as UTC regardless of the host timezone; validate dates and 64-bit routing info.
- Remove Anisette response values from debug output and set a 15-second HTTP request timeout.
- Fix `-h` / `--help`, missing install arguments, `-a` falling through to `-p`, unreadable IPA files and failure exit codes.
- Detect zero-byte transfers or invalid transfer sizes over USB instead of looping indefinitely.
- Preserve Anisette identity and provisioning state across container replacement.
- Connect AltServer directly to official netmuxd at `127.0.0.1:27015`; re-register the configured phone through its official API.
- Monitor and recover netmuxd directly. Check services even while the phone is away.

Recovery acts after three consecutive failures and uses a five-minute restart cooldown. Checks run 15 seconds after the preceding check finishes. `healthy` is a server/protocol result, not proof of a successful app refresh. `waiting_for_device` is expected while the phone is away. Automatic checks do not sign in to Apple or refresh apps.
