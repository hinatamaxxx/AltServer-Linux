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
- [Ben-Diehlci / PR #138](https://github.com/NyaMisty/AltServer-Linux/pull/138): Web UI と別のサービス構成への移行は対象外です。GSA 接続修正は採用内容と重複します。v0.1.2 では、このフォークの Bonjour 引数・型定義の修正を部分的に取り込みました（下記参照）。
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
- [Ben-Diehlci / PR #138](https://github.com/NyaMisty/AltServer-Linux/pull/138): switching to its web UI and service stack remains outside this update. Its GSA fix overlaps with the adopted change. v0.1.2 selectively adopts its Bonjour argument/type corrections, as described below.
- [Rogue911 / PR #136](https://github.com/NyaMisty/AltServer-Linux/pull/136) repairs the corecrypto build environment. We use a verified builder image pinned by digest and do not rebuild that environment here.
- We also compared authentication, dependency, ARM64 and build changes in [datspike](https://github.com/datspike/AltServer-Linux), [carck](https://github.com/carck/AltServer-Linux) and [BartSiwek](https://github.com/BartSiwek/AltServer-Linux). Duplicate fixes and broader changes beyond the amd64 distribution were not imported wholesale.
- [Curve](https://github.com/Curve/AltServer-Linux) provides CMake support. We retain the current build system.

### Validation scope

CI links the same ldid object as AltServer into a test CLI and signs a synthetic ARM64 Mach-O and app bundle with a disposable self-signed identity. It checks the CMS cryptographic signature, full 20-byte SHA-1 and 32-byte SHA-256 agility hashes, a designated requirement and generated CodeResources. Test keys are generated and deleted in a temporary directory and are not distributed.

The generated GSA factory is checked against a local HTTP/1.1 server for separate TCP connections and an enabled TLS-validation setting. These checks do not validate Apple's live service or iOS acceptance of the signature. See [verification](verification.md).

## v0.1.2: 関連実装からの追加取り込み

- **Bonjour の引数と型定義**: [Ben-Diehlci の dnssd_loader.cpp](https://github.com/Ben-Diehlci/altserver-linux/blob/04d98547c4e60dee9d8715002ec7878b1eeddcf7/libraries/dnssd_loader/dnssd_loader.cpp)（AGPL-3.0）を参考に調整。`DNSServiceRef` を `c_void_p` で保持し、API の引数型を明示します。文字列は生成コードではなく argv で渡し、TXT の全バイトを符号なしの16進数で保持します。NULL と空文字列も区別します。
- **登録結果の受け取り**: 子プロセスが生存しているだけで成功とみなす方式は採用せず、専用パイプで登録 API の戻り値を受け取る処理を実装しました。Python 起動失敗・登録エラー・5秒以内に応答しない場合はエラーを返し、失敗した子プロセスを回収します。成功は「API が登録要求を受理した」ことだけを示し、LAN 上で発見可能であることは保証しません。Avahi 再起動後の広告復旧は今回の変更に含みません。
- **JSON 要求の長さ制限**: 独立した Rust 実装 [AltKeeper の read_frame](https://github.com/BartolomeoRusso9/altkeeper/blob/48f8059b18ef96b9eff9b3d6b07935f0c59f7345/src/altserver.rs)（MIT）の4 MiB上限と受信前検証を参考に、C++ で実装しました。長さヘッダーは4バイトの little-endian として読み、不足・ゼロ・負数相当・上限超過を本文受信前に拒否します。IPA 本体は別の転送で、この上限の対象外です。Rust の実装全体や独自 VPN/DNS 機能は取り込んでいません。
- **追加比較**: [dreth/Altserver-docker の起動処理](https://github.com/dreth/Altserver-docker/blob/5d9794577c5fe736b04ab67eab08d6e012e012c7/scripts/docker-entrypoint.sh)と [althea の導入・ペアリング処理](https://github.com/vyvir/althea/blob/215d8aaa748fe9bb0d18446ceaee242e40683719/main.py)も確認しました。既存のセットアップと機能が重なり、起動時のバイナリ再取得や GUI への移行は採用していません。

Bonjour は本番 C++ ブリッジと Python ヘルパーを模擬共有ライブラリに接続して5ケースを試験します。引用符・改行・日本語、0x80以上のバイト・NUL、NULL/空文字列、登録失敗、Python 不在、応答停止を対象とします。JSON はビルド時に生成した本番 `ReceiveRequest` を模擬転送に接続し、不正長で本文読み出しを呼ばないことと、2バイト・4 MiB の要求を処理できることを確認します。

## v0.1.2: Additional related implementations

- **Bonjour arguments and types**: adapt the approach in [Ben-Diehlci's dnssd_loader.cpp](https://github.com/Ben-Diehlci/altserver-linux/blob/04d98547c4e60dee9d8715002ec7878b1eeddcf7/libraries/dnssd_loader/dnssd_loader.cpp) (AGPL-3.0). Store `DNSServiceRef` as `c_void_p`, declare API argument types, pass strings through argv rather than generated code, and preserve all TXT bytes with unsigned hexadecimal encoding. NULL and empty strings remain distinct.
- **Registration result**: instead of treating a surviving child process as success, our implementation receives the registration API result through a dedicated pipe. Python launch failure, API errors and no response within five seconds return an error; failed children are reaped. Success means only that the API accepted the registration request, not that the service is discoverable on the LAN. Recovery of advertisements after an Avahi restart is outside this change.
- **JSON frame bounds**: use the 4 MiB cap and validation-before-read approach in the independent Rust implementation [AltKeeper's read_frame](https://github.com/BartolomeoRusso9/altkeeper/blob/48f8059b18ef96b9eff9b3d6b07935f0c59f7345/src/altserver.rs) (MIT), implemented here in C++. Decode an exact four-byte little-endian header and reject short, zero, signed-negative and oversized lengths before reading the body. IPA payloads use a separate transfer and are not subject to this cap. The broader Rust implementation and its VPN/DNS features are not imported.
- **Also reviewed**: [dreth/Altserver-docker startup](https://github.com/dreth/Altserver-docker/blob/5d9794577c5fe736b04ab67eab08d6e012e012c7/scripts/docker-entrypoint.sh) and [althea setup/pairing](https://github.com/vyvir/althea/blob/215d8aaa748fe9bb0d18446ceaee242e40683719/main.py). These overlap with our setup; fetching binaries on every startup and moving to a GUI were not adopted.

Five Bonjour tests connect the production C++ bridge and Python helper to a fake shared library. They cover quotes, newlines, Japanese text, high-bit bytes and NUL, NULL versus empty strings, registration failure, missing Python and a hung API call. JSON tests compile the generated production `ReceiveRequest` against a fake transport, checking that invalid lengths never trigger a body read and that two-byte and 4 MiB requests succeed.
