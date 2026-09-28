# v0.2.0 — 公式ソースへの更新 / Official-source update

## 日本語

公式ソースへ追従し、保守する独自差分を整理したプレビュー版です。

- C++ 基盤を [公式 AltServer-Windows の 1.7.5 開発ソース](https://github.com/rileytestut/AltServer-Windows/tree/bd3d7abc58abf6bd332ed256d15307839e498711)へ変更。公式製品の配布版との同等性を示すものではありません。
- libimobiledevice 1.4.0、libusbmuxd 2.1.1、libplist 2.7.0、libimobiledevice-glue 1.3.2 を公式リポジトリのコミットに固定。
- 2FA の HTTP エラー判定と User-Agent を更新し、認証データ・トークンのデバッグ出力を除去。未知の端末エラーコードで戻り値がなくなる不具合も修正。
- 常駐アダプターは引き続き不要。Linux/BSD アドレスは入力部分で長さを検証・正規化し、公式 libimobiledevice へ渡します。
- 版番号を `VERSION` に統一し、実行ファイルに `--version` を追加。重要なソース変換の対象が変わるとビルドを停止します。

新規導入はセットアップアーカイブを展開し、`sudo sh install.sh --prepare` を実行してください。Docker・Anisette・netmuxd 等を準備します。iPhone の接続・信頼は後から `--configure` で行います。既存環境の上書きや自動移行は行いません。

テストは模擬サーバーと Debian 13 コンテナを使用します。Apple への実ログイン、SMS 到着、iPhone でのインストール・更新、ホスト再起動後の復旧は未検証です。ビルダー自体は従来の Alpine イメージを継続使用しています。[検証記録](https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/verification.md)・[保守手順](https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/maintenance.md)をご覧ください。

実装: Codex GPT-6 Astra / High（このセッションのメタデータ確認済み）。日英校正: Gemini 3.8 Flash / High。AI の利用は実機互換性の検証を意味しません。

## English

A preview that follows official source and simplifies local maintenance.

- Move the C++ base to [official AltServer-Windows 1.7.5 development source](https://github.com/rileytestut/AltServer-Windows/tree/bd3d7abc58abf6bd332ed256d15307839e498711). This does not establish parity with an official product release.
- Pin official commits for libimobiledevice 1.4.0, libusbmuxd 2.1.1, libplist 2.7.0 and libimobiledevice-glue 1.3.2.
- Update 2FA HTTP error handling and User-Agent; remove authentication-data and token debug logging. Fix missing return values for unknown native error codes.
- No persistent adapter is required. Linux/BSD address lengths are validated and normalized at the input boundary before reaching official libimobiledevice.
- Share `VERSION` across the executable, installer and release workflow; add `--version`. Critical source transformations stop the build when upstream targets change.

For a new installation, extract the setup archive and run `sudo sh install.sh --prepare` to prepare Docker, Anisette, netmuxd and other dependencies. Connect and trust an iPhone later, then use `--configure`. Existing setups are not overwritten or automatically migrated.

Tests use synthetic servers and a Debian 13 container. Live Apple sign-in, SMS delivery, iPhone installation/refresh and full-host reboot recovery remain unverified. The builder still uses the existing Alpine image. See [verification](https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/verification.md) and [maintenance](https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/maintenance.md).

Implementation: Codex GPT-6 Astra / High, verified from this session's metadata. Japanese/English proofreading: Gemini 3.8 Flash / High. AI assistance does not establish physical-device compatibility.
