# 取り込み元 / Provenance

## フォーク元と参照先 / Parent and source URLs

直接のフォーク元は NyaMisty の非公式 Linux 移植版です。公式 AltServer、他者フォーク、設計上の参考資料を以下で区別します。

The direct parent is NyaMisty's unofficial Linux port; official source, third-party forks and design references are distinguished below.

| 役割 / Role | Repository URL | 使用箇所 / Use |
| --- | --- | --- |
| 直接のフォーク元 / Direct parent | [https://github.com/NyaMisty/AltServer-Linux](https://github.com/NyaMisty/AltServer-Linux) | Linux 基盤・Git 履歴 / Linux base and history |
| 公式 Windows / Official Windows | [https://github.com/rileytestut/AltServer-Windows](https://github.com/rileytestut/AltServer-Windows) | 現在の C++ 基盤 / Current C++ base |
| 公式 macOS / Official macOS | [https://github.com/altstoreio/AltStore](https://github.com/altstoreio/AltStore) | AltServer ディレクトリを調査 / Reviewed the AltServer directory |
| 公式認証ライブラリ / Official authentication library | [https://github.com/rileytestut/AltSign](https://github.com/rileytestut/AltSign) | GSA・2FA の比較 / GSA and 2FA comparison |
| 過去の採用元 / Historical source | [https://github.com/jaakkopalvaila/AltServer-Windows](https://github.com/jaakkopalvaila/AltServer-Windows) | v0.1.x の ldid・GSA。v0.2.0 は公式へ変更 / v0.1.x ldid and GSA; official base in v0.2.0 |
| 過去の採用元 / Historical source | [https://github.com/jaakkopalvaila/libimobiledevice](https://github.com/jaakkopalvaila/libimobiledevice) | v0.1.3 のアドレス互換性。v0.2.0 は公式へ変更 / v0.1.3 address compatibility; official base in v0.2.0 |
| 公式ライブラリ / Official library | [https://github.com/libimobiledevice/libimobiledevice](https://github.com/libimobiledevice/libimobiledevice) | 1.4.0、端末通信 / 1.4.0 device communication |
| 公式ライブラリ / Official library | [https://github.com/libimobiledevice/libusbmuxd](https://github.com/libimobiledevice/libusbmuxd) | 2.1.1、アドレス入力部分のみ調整 / 2.1.1, address input adaptation only |
| 公式ライブラリ / Official library | [https://github.com/libimobiledevice/libplist](https://github.com/libimobiledevice/libplist) | 2.7.0、plist 処理 / 2.7.0 plist processing |
| 公式ライブラリ / Official library | [https://github.com/libimobiledevice/libimobiledevice-glue](https://github.com/libimobiledevice/libimobiledevice-glue) | 1.3.2、共通処理 / 1.3.2 shared utilities |
| 部分的な修正の参考 / Targeted code reference | [https://github.com/Ben-Diehlci/altserver-linux](https://github.com/Ben-Diehlci/altserver-linux) | Bonjour 引数・型 / Bonjour arguments and types |
| 設計の参考 / Design reference | [https://github.com/BartolomeoRusso9/altkeeper](https://github.com/BartolomeoRusso9/altkeeper) | 要求長の検証・実行依存なし / Request-length validation; no runtime dependency |
| 復旧機能の取り込み元 / Imported recovery tools | [https://github.com/hinatamaxxx/altserver-linux-native-autorecover](https://github.com/hinatamaxxx/altserver-linux-native-autorecover) | 監視・復旧スクリプト / Monitoring and recovery scripts |
| 公式配布物 / Upstream distribution | [https://github.com/jkcoxson/netmuxd](https://github.com/jkcoxson/netmuxd) | 改変なし / Unmodified |
| 公式配布物 / Upstream distribution | [https://github.com/Dadoum/anisette-v3-server](https://github.com/Dadoum/anisette-v3-server) | Docker イメージ / Docker image |

固定コミットと変更内容は以下および[フォーク調査](fork-review.md)を、現在の公式実装との比較は[上流調査](upstream-review.md)を参照してください。

Pinned commits and adaptations are documented below and in the [fork review](fork-review.md); see the [official-source review](upstream-review.md) for current comparisons.

[リンク一覧 HTML](sources.html)をダウンロードしてブラウザーで開くと、リンクは新しいタブで開きます。GitHub の Markdown 表示ではリンク先タブを強制できません。

Download and open the [HTML source directory](sources.html) in a browser for new-tab links; GitHub's Markdown rendering does not allow forcing the target tab.

## English

- Current v0.2.0 pins: official Windows `bd3d7abc58abf6bd332ed256d15307839e498711`; libimobiledevice `149f7623c672c1fa73122c7119a12bfc0012f2ac`; libusbmuxd `adf9c22b9010490e4b55eaeb14731991db1c172c`; libplist `cf5897a71ea412ea2aeb1e2f6b5ea74d4fabfd8c`; glue `aef2bf0f5bfe961ad83d224166462d87b1df2b00`. These replace the historical fork references below. Original copyright and license files remain in their submodules.
- Upstream: `NyaMisty/AltServer-Linux`, branch `new`, base `7876451`. Git history and AGPL-3.0 are retained. In v0.1.1, `upstream_repo` is repinned to `jaakkopalvaila/AltServer-Windows` at `dae9501abad10a4f008cc8a73138310679decd81`. In v0.1.3, `libraries/libimobiledevice` is pinned to `jaakkopalvaila/libimobiledevice` at `3ab93704206b11cdf9485db1f49e62d57c1d4dce`, with a local copy-length correction; other submodule commits are unchanged. See [fork review](fork-review.md) for exact sources and local adaptations.
- Recovery code: `hinatamaxxx/altserver-linux-native-autorecover`, commit `d61a5b6`, MIT. Runtime helpers, regression tests and diagnostic tools were imported; the new installer and service defaults integrate official netmuxd v0.4.3.
- `docs/history/` contains predecessor documents. They describe the old helper-only repository and its historical tests, not this fork's current installation procedure. Do not use their trial/upgrade commands for this fork.
- `docs/upstream-readme.md` is an unchanged upstream reference; use the root README for this fork.
- The setup bundle contains this fork's compiled binary. netmuxd and Anisette are fetched from their upstream distributions, not rebuilt or modified here.

## 日本語

- v0.2.0 の固定コミット: 公式 Windows `bd3d7abc58abf6bd332ed256d15307839e498711`、libimobiledevice `149f7623c672c1fa73122c7119a12bfc0012f2ac`、libusbmuxd `adf9c22b9010490e4b55eaeb14731991db1c172c`、libplist `cf5897a71ea412ea2aeb1e2f6b5ea74d4fabfd8c`、glue `aef2bf0f5bfe961ad83d224166462d87b1df2b00`。以下に記載した過去のフォーク参照を置き換えています。各サブモジュールの著作権・ライセンス文書は保持しています。
- 上流: `NyaMisty/AltServer-Linux`（`new` ブランチ、コミット `7876451`）。本家の Git 履歴と AGPL-3.0 を維持しています。v0.1.1 では `upstream_repo` を `jaakkopalvaila/AltServer-Windows`（コミット `dae9501abad10a4f008cc8a73138310679decd81`）に更新しました。v0.1.3 では `libraries/libimobiledevice` を `jaakkopalvaila/libimobiledevice` の `3ab93704206b11cdf9485db1f49e62d57c1d4dce` に固定し、コピー長の修正を加えています。他のサブモジュールは維持しています。出典と調整内容は[フォーク調査](fork-review.md)を参照してください。
- 復旧コード: `hinatamaxxx/altserver-linux-native-autorecover`（コミット `d61a5b6`、MIT）。実行用スクリプト、回帰テスト、診断ツールを取り込み、公式 netmuxd v0.4.3 と連携するよう統合しました。
- `docs/history/`: 旧資料です。旧リポジトリの検証記録であり本フォークの導入手順ではありません。旧試験・更新用コマンドは本フォークで使用しないでください。
- `docs/upstream-readme.md`: 上流 README の原文です（参考用）。本フォークの使い方はルート README を参照してください。
- 配布バンドル: 本フォークのビルド済みバイナリを含みます。netmuxd と Anisette は公式配布物を取得し、本リポジトリでは改変・再ビルドしていません。
