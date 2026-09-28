# フォーク調査 / Fork review — 2026-09-28

## 日本語

上流のフォーク一覧、関連 PR、候補の差分を確認し、既存の復旧構成に適用できる修正を選びました。他プロジェクトの実機成功報告は、本フォークの実機検証として扱いません。

### 取り込んだ修正

| 出典 | 適用内容 |
| --- | --- |
| [Rogue911 / 上流 PR #135](https://github.com/NyaMisty/AltServer-Linux/pull/135)、[jaakkopalvaila/ng](https://github.com/jaakkopalvaila/AltServer-Linux/tree/620f5871e494717c35c2c42f3911cd3a38e23c76) | `X-MMe-Client-Info` の `com.apple.dt.Xcode` をすべて `com.apple.akd` に置換。既存の入力検証を保ち、ヘッダー値をログに出さず、繰り返し出現する場合もテスト。 |
| [jaakkopalvaila/AltServer-Windows dae9501](https://github.com/jaakkopalvaila/AltServer-Windows/commit/dae9501abad10a4f008cc8a73138310679decd81) | ldid 更新、Linux のバンドルパスと新しい Progress API への対応、GSA の要求ごとに HTTP クライアントを作成する修正、認証 User-Agent の更新。サブモジュールをこのコミットに固定。 |
| [公式 AltServer-Windows 62a7a2b](https://github.com/rileytestut/AltServer-Windows/commit/62a7a2be90c08e5e4773e6bbba5484e3704e19fd)、[AltSign PR #52](https://github.com/rileytestut/AltSign/pull/52) | ldid と GSA 接続修正の一次資料。採用した ldid.cpp / ldid.hpp の Git blob は公式コミットと一致。 |

取り込み先に残っていた `set_validate_certificates(false)` は、Linux 向けソース変換時に `true` に変更しました。将来のサブモジュール更新で該当箇所が変わった場合は、ビルドを停止して再確認を求めます。ソース変換スクリプトの変更も Make の依存関係に含めました。

### 今回は採用しなかった変更

- jaakkopalvaila の libimobiledevice アドレス修正: 既存の loopback アダプターで同じ Linux/BSD 形式差を処理しています。端末のコピー長の扱いも別途検証が必要なため、現行のアダプターを維持しました。
- [Ben-Diehlci / PR #138](https://github.com/NyaMisty/AltServer-Linux/pull/138): Web 設定 UI、無線復旧、Docker スタック等を確認。GSA 接続修正は採用内容と重複します。Web UI と別のサービス構成への移行は今回の対象に含めません。
- [Rogue911 / PR #136](https://github.com/NyaMisty/AltServer-Linux/pull/136): corecrypto ビルド環境の修正。現在のビルドは検証済みのイメージをダイジェスト固定で使用しており、この環境を再構築しないため未採用。
- [datspike](https://github.com/datspike/AltServer-Linux)、[carck](https://github.com/carck/AltServer-Linux)、[BartSiwek](https://github.com/BartSiwek/AltServer-Linux): 認証、依存ライブラリ、ARM64、ビルド変更の差分も比較。重複修正や、今回の amd64 配布対象を超える変更はまとめて取り込んでいません。
- [Curve](https://github.com/Curve/AltServer-Linux): CMake 化。現在のビルド方式の全面置換は行いません。

### 検証範囲

CI は AltServer と同じ ldid オブジェクトをテスト用 CLI にリンクし、架空の ARM64 Mach-O と一時的な自己署名証明書で、単体バイナリ・アプリバンドルを署名します。CMS の暗号学的検証、SHA-1 の20バイトと SHA-256 の32バイトの完全なハッシュ、designated requirement、CodeResources の生成を確認します。テスト用鍵は一時ディレクトリ内で生成・破棄し、配布しません。

生成済み GSA クライアント関数は、ローカル HTTP/1.1 サーバーを使って別々の TCP 接続になることと、TLS 検証の設定が有効であることを確認します。Apple の実サービスや iOS の署名受理を検証するテストではありません。詳細は[検証記録](verification.md)を参照してください。

## English

We reviewed the upstream fork list, related PRs and candidate diffs, then selected fixes that fit the existing recovery setup. Device success reports from other projects are not treated as device validation of this fork.

### Adopted changes

- [Rogue911 / upstream PR #135](https://github.com/NyaMisty/AltServer-Linux/pull/135) and [jaakkopalvaila/ng](https://github.com/jaakkopalvaila/AltServer-Linux/tree/620f5871e494717c35c2c42f3911cd3a38e23c76): replace every `com.apple.dt.Xcode` occurrence in `X-MMe-Client-Info` with `com.apple.akd`. Existing input validation remains; header values are not logged, and repeated occurrences are tested.
- Pin `upstream_repo` to [jaakkopalvaila/AltServer-Windows dae9501](https://github.com/jaakkopalvaila/AltServer-Windows/commit/dae9501abad10a4f008cc8a73138310679decd81): updated ldid, Linux bundle paths, the new Progress API, a fresh HTTP client per GSA request and an updated authentication User-Agent.
- The ldid.cpp / ldid.hpp Git blobs match [official AltServer-Windows commit 62a7a2b](https://github.com/rileytestut/AltServer-Windows/commit/62a7a2be90c08e5e4773e6bbba5484e3704e19fd). [AltSign PR #52](https://github.com/rileytestut/AltSign/pull/52) is the primary reference for separate GSA connections.

Our Linux source rewriter changes the inherited `set_validate_certificates(false)` calls to `true` and fails the build if a later submodule update changes the expected locations. Make dependencies now include the rewriter scripts.

### Changes not adopted

- The jaakkopalvaila libimobiledevice address patch overlaps with our loopback adapter. Its address copy-length handling needs separate validation, so the existing adapter remains.
- [Ben-Diehlci / PR #138](https://github.com/NyaMisty/AltServer-Linux/pull/138) adds web setup, wireless recovery and Docker deployment. Its GSA fix overlaps with the adopted change; switching to its UI and service stack is outside this update.
- [Rogue911 / PR #136](https://github.com/NyaMisty/AltServer-Linux/pull/136) repairs the corecrypto build environment. We use a verified builder image pinned by digest and do not rebuild that environment here.
- We also compared authentication, dependency, ARM64 and build changes in [datspike](https://github.com/datspike/AltServer-Linux), [carck](https://github.com/carck/AltServer-Linux) and [BartSiwek](https://github.com/BartSiwek/AltServer-Linux). Duplicate fixes and broader changes beyond the amd64 distribution were not imported wholesale.
- [Curve](https://github.com/Curve/AltServer-Linux) provides CMake support. We retain the current build system.

### Validation scope

CI links the same ldid object as AltServer into a test CLI and signs a synthetic ARM64 Mach-O and app bundle with a disposable self-signed identity. It checks the CMS cryptographic signature, full 20-byte SHA-1 and 32-byte SHA-256 agility hashes, a designated requirement and generated CodeResources. Test keys are generated and deleted in a temporary directory and are not distributed.

The generated GSA factory is checked against a local HTTP/1.1 server for separate TCP connections and an enabled TLS-validation setting. These checks do not validate Apple's live service or iOS acceptance of the signature. See [verification](verification.md).
