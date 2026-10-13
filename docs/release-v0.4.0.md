# v0.4.0 — Wine Anisette / Wine 版 Anisette

## 日本語

Android 系 Anisette（anisette-v3-server）は、最新版でも Apple に拒否される（`-80045`）ようになりました。そのため廃止し、Windows 版 iCloud のライブラリを Docker 上の Wine で動かすローカル Anisette（`altserver-icloud-local.service`、`127.0.0.1:6972`）に置き換えました。コンテナは `anisette/icloud-wine` から手元でビルドし、イメージ ID で固定します。

Apple のライブラリは再配布できないため、本リポジトリには含みません。Windows 版 AltServer と iCloud が動作する PC で `scripts/windows/export-apple-runtime.ps1` を実行し、`sudo sh install.sh --import-apple-runtime apple-runtime.tar.gz` で取り込みます。`iCloud_main.dll` と `CoreADI.dll` は SHA-256 で検証します。

初回のサインインで、AltStore がコード入力欄を出さずに `-22411` で失敗することがあります。その場合は iPhone の設定アプリで確認コードを表示し、`sudo altserver-apple-trust` で入力してください。パスワードとコードは保存しません。

v0.3.x からの移行は手動です。[セットアップ・移行](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.4.0/docs/setup.md)を参照してください。既存の Debian サーバーで、Wine 版 Anisette と信頼登録の後に iOS 27.0.1 の AltStore からリフレッシュできることを確認しました。新規導入とホスト再起動後の動作は未検証です。

## English

The Android-based Anisette (anisette-v3-server), including its latest image, is now rejected by Apple with `-80045`. It is replaced by local Anisette from Apple's Windows iCloud libraries running under Wine in Docker (`altserver-icloud-local.service`, `127.0.0.1:6972`). The container is built locally from `anisette/icloud-wine` and pinned by image ID.

Apple's libraries cannot be redistributed and are not included. On a PC where AltServer for Windows and iCloud work, run `scripts/windows/export-apple-runtime.ps1`, then import the archive with `sudo sh install.sh --import-apple-runtime apple-runtime.tar.gz`. `iCloud_main.dll` and `CoreADI.dll` are verified by SHA-256.

The first sign-in may fail in AltStore with `-22411` and no code field. Show a verification code in the iPhone's Settings app and enter it with `sudo altserver-apple-trust`. The password and code are never stored.

Migration from v0.3.x is manual; see [setup and migration](https://github.com/hinatamaxxx/AltServer-Linux/blob/v0.4.0/docs/setup.md). On the existing Debian server, AltStore on iOS 27.0.1 refreshed successfully after Wine Anisette and trust were set up. Clean installation and behavior after a host reboot are unverified.
