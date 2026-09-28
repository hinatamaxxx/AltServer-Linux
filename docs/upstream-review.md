# 公式実装の調査と取り込み方針 / Official-source review and adoption policy

確認日 / Checked: 2026-09-28. v0.2.0 の取り込み状況です。実機検証の結果ではありません。

This records source adoption for v0.2.0, not physical-device validation.

## 日本語

### 公式の最新版をどう確認したか

- **直接の上流**: [NyaMisty/AltServer-Linux の new](https://github.com/NyaMisty/AltServer-Linux/tree/78764512b735e7a731ef4ff36aca8d80dbd8d7c8) は現在も `7876451`。本フォークの基点と一致します。これは非公式 Linux 移植版です。
- **公式 Windows**: [1.7.4 ブランチ](https://github.com/rileytestut/AltServer-Windows/tree/f4dba95b66e040540fbf16e2b460dc1517c4d864)と[公式リリースノート](https://faq.altstore.io/release-notes/altserver)を照合しました。リリースノートには 2026-03-24 の 1.7.4 が掲載されています。既定の `master` や古い `develop` だけでは最新の実装を確認できません。
- **公式 Windows の新しい開発ブランチ**: [arm_1.7.5_jayce](https://github.com/rileytestut/AltServer-Windows/tree/bd3d7abc58abf6bd332ed256d15307839e498711) には、2026-09-08 の GSA 接続分離・HTTP 5xx 判定と 1.7.5 への版番号更新があります。上記リリースノートとは別に確認し、正式配布状況はソースだけで断定しません。
- **公式 macOS**: [AltStore の classic ブランチ](https://github.com/altstoreio/AltStore/tree/fafd76ee1a8a19c723146de278660aacce9ded5d/AltServer)には、2026-09-17 の AnisetteKit によるローカル生成と、1.8 へのバージョン更新が含まれます。ソース内の版番号だけで正式配布済みとは判断しません。
- **公式認証ライブラリ**: [AltSign の notarized ブランチ](https://github.com/rileytestut/AltSign/tree/468313b6b718e85cdad1fc2c8ba4ab551db897aa)も確認しました。2026-09-17 の 2FA 関連更新を含み、既定の `master` とは更新状況が異なります。

### 現在との差分と判断

| 公式の実装 | このフォークでの扱い |
| --- | --- |
| Windows 1.7.4 の ldid 更新 | 取り込み済み。`ldid.cpp` と `ldid.hpp` の Git blob は公式 1.7.4 と一致。Linux 用の変換は別途適用されています。 |
| [AltSign PR #52](https://github.com/rileytestut/AltSign/pull/52): GSA 要求ごとの接続分離 | [公式 Windows の対応コミット](https://github.com/rileytestut/AltServer-Windows/commit/5eb3509)を含む C++ 基盤へ更新。要求ごとのクライアント生成と HTTP 5xx の扱いを取り込み、Linux では TLS 証明書検証を有効にします。 |
| [AltSign の 2FA User-Agent 更新](https://github.com/rileytestut/AltSign/commit/468313b6b718e85cdad1fc2c8ba4ab551db897aa)、HTTP エラーの扱い | C++ の通常認証・2FA に共通の User-Agent を適用。2FA のコード要求前・応答解析前に HTTP エラーを判定します。認証データ・トークンのデバッグ出力も除去しました。 |
| Windows の大文字を含む Apple ID 正規化、SMS 2FA、詳細なエラー体系 | 公式 C++ 基盤に含まれる実装を採用。Windows 固有の UI は Linux 向けに調整しています。Apple への実ログイン、SMS 到着、実機動作は未検証です。 |
| macOS の AnisetteKit とライブラリ取得 | Swift/macOS 側の実装として参照。Linux の Docker Anisette をそのまま置き換えず、現在の永続状態を保持します。 |

### 他リポジトリを参考にする方針

他のフォークの修正を選んで取り込む方法は、上流をフォークして改変する開発と両立します。ただし、機能を無条件に集めると上流との差分、依存先、検証負担が増えます。このプロジェクトでは、まず公式の実装と直接の Linux 上流を確認し、不足する Linux 固有の修正だけ他フォークから検討します。

直接のフォーク元、コードの取り込み元、設計だけ参考にした実装を区別します。コードを取り込む際は利用条件と著作権表示を確認・維持し、URL・コミット・目的・ローカル変更・試験を記録します。依存バージョンを固定し、上流に同等修正が入った際は独自差分を減らします。

v0.2.0 では AltServer-Windows と libimobiledevice の参照先を公式リポジトリへ戻しました。libimobiledevice 1.4.0、libusbmuxd 2.1.1、libplist 2.7.0、libimobiledevice-glue 1.3.2 のコミットを固定しています。Linux/BSD アドレスの検証・正規化は libusbmuxd の入力部分だけに置き、公式 libimobiledevice は改変せずビルドします。常駐アダプターは不要です。AltKeeper は要求長の検証方法を参考にしただけで、Rust サーバーや追加の実行依存は導入していません。過去の出典は[フォーク調査](fork-review.md)、更新時の注意点は[保守手順](maintenance.md)を参照してください。

## English

### Checking current official implementations

- **Direct upstream**: [NyaMisty/AltServer-Linux new](https://github.com/NyaMisty/AltServer-Linux/tree/78764512b735e7a731ef4ff36aca8d80dbd8d7c8) remains at `7876451`, this fork's base. It is an unofficial Linux port.
- **Official Windows**: compared the [1.7.4 branch](https://github.com/rileytestut/AltServer-Windows/tree/f4dba95b66e040540fbf16e2b460dc1517c4d864) with the [official release notes](https://faq.altstore.io/release-notes/altserver), which list 1.7.4 dated March 24, 2026. The default `master` and older `develop` branches alone do not show the current implementation.
- **Newer official Windows development branch**: [arm_1.7.5_jayce](https://github.com/rileytestut/AltServer-Windows/tree/bd3d7abc58abf6bd332ed256d15307839e498711) includes GSA connection separation, HTTP 5xx handling and a version bump to 1.7.5 dated September 8, 2026. It was reviewed separately from the release notes; source alone does not establish public release status.
- **Official macOS**: [AltStore's classic branch](https://github.com/altstoreio/AltStore/tree/fafd76ee1a8a19c723146de278660aacce9ded5d/AltServer) includes local AnisetteKit generation dated September 17, 2026 and a version bump to 1.8. A source version number alone does not establish a public release.
- **Official authentication library**: reviewed [AltSign notarized](https://github.com/rileytestut/AltSign/tree/468313b6b718e85cdad1fc2c8ba4ab551db897aa), which includes 2FA updates dated September 17, 2026 and differs from the default `master` branch.

### Comparison and decisions

| Official implementation | Status in this fork |
| --- | --- |
| Windows 1.7.4 ldid update | Already adopted. Git blobs for `ldid.cpp` and `ldid.hpp` match official 1.7.4; Linux transformations are applied separately. |
| [AltSign PR #52](https://github.com/rileytestut/AltSign/pull/52): separate connections per GSA request | The updated C++ base includes the [official Windows commit](https://github.com/rileytestut/AltServer-Windows/commit/5eb3509), with per-request clients and HTTP 5xx handling. TLS certificate validation is enabled on Linux. |
| [AltSign 2FA User-Agent update](https://github.com/rileytestut/AltSign/commit/468313b6b718e85cdad1fc2c8ba4ab551db897aa) and HTTP error handling | A shared User-Agent is applied to C++ authentication and 2FA. HTTP errors are checked before requesting a code or parsing a response. Authentication data and token debug logging are removed. |
| Windows mixed-case Apple ID normalization, SMS 2FA and richer errors | Adopted with the official C++ base, adapting Windows UI for Linux. Live Apple sign-in, SMS delivery and physical-device behavior remain unverified. |
| macOS AnisetteKit and library downloads | Reviewed as a Swift/macOS implementation. It does not directly replace Docker Anisette on Linux; existing persistent state is retained. |

### Policy for other repositories

Selecting fixes from other forks is compatible with maintaining a modified upstream fork. Uncontrolled feature imports, however, increase divergence, dependencies and testing costs. In this project, we review official source and the direct Linux upstream first, then consider other forks for missing Linux-specific fixes.

We distinguish the direct fork parent, imported code and design references. We check and preserve applicable licensing and copyright notices for imported code, and record the URL, commit, purpose, local adaptations and tests. We pin dependencies and reduce local changes when upstream provides equivalent fixes.

In v0.2.0, AltServer-Windows and libimobiledevice point back to official repositories. Commits are pinned for libimobiledevice 1.4.0, libusbmuxd 2.1.1, libplist 2.7.0 and libimobiledevice-glue 1.3.2. Linux/BSD address validation and normalization live only at the libusbmuxd input boundary; official libimobiledevice is built unchanged. No persistent adapter is required. AltKeeper informed request-length validation; its Rust server and additional runtime dependencies were not imported. See the [fork review](fork-review.md) for historical attribution and [maintenance guide](maintenance.md) for update procedures.
