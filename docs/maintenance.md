# 保守手順 / Maintenance

## 日本語

- 直接の上流は [NyaMisty/AltServer-Linux](https://github.com/NyaMisty/AltServer-Linux)。公式 C++ と各ライブラリは `.gitmodules` の URL と Git のサブモジュールコミットで固定します。`git submodule update --init --recursive` は記録済みコミットを取得します。`--remote` による一括更新は行いません。
- 更新は専用ブランチで行い、公式のリリース・開発ブランチ・利用条件を確認します。差分と採否を `docs/upstream-review.md` に記録してください。参照先一覧は `docs/provenance.md` を編集し、`node tools/render-sources.js` で HTML を再生成します。
- Linux 固有の差分は `makefiles/rewrite_altserver_source.py`、`makefiles/AltSign-build/rewrite_altsign_source.py`、`shims/` にあります。重要な変換は対象が変わるとビルドを停止します。エラーを回避するためだけに件数確認を外さず、新しい公式コードと照合してください。
- netmuxd は公式配布物です。`src/NativeNetworkAddress.h` と `rewrite_usbmux_source.py` は受信アドレスの境界処理だけを担当します。公式 libimobiledevice へ同等処理が入ったらローカル差分を減らします。
- 版番号はルートの `VERSION`（`vMAJOR.MINOR.PATCH`）を変更します。実行ファイルの `--version`、セットアップ、リリース処理が共用します。同じ版のコード変更を後から公開済みタグへ上書きしません。
- `python3 -m unittest discover -s tests -v` と CI の全ビルド・通信・署名・展開済みインストーラー試験を通します。`workflow_dispatch` の `publish=false` で検証し、日英資料の校正後に公開します。実機未検証の版はプレビューとして扱います。

ビルダーは直接の上流の Alpine イメージをダイジェスト固定で使用しています。corecrypto・cpprestsdk を含むこのビルド環境自体の刷新は未完了です。依存ライブラリを更新しても、ツールチェーン全体が最新になったとは扱いません。配布先は引き続き Debian 12/13 amd64 で、既存環境の自動上書きは行いません。

## English

- The direct upstream is [NyaMisty/AltServer-Linux](https://github.com/NyaMisty/AltServer-Linux). Official C++ and library sources are pinned by `.gitmodules` URLs and Git submodule commits. `git submodule update --init --recursive` fetches recorded commits; do not bulk-update with `--remote`.
- Use a dedicated update branch. Check official releases, development branches and licensing, then record decisions in `docs/upstream-review.md`. Edit the source directory in `docs/provenance.md` and regenerate HTML with `node tools/render-sources.js`.
- Linux adaptations live in `makefiles/rewrite_altserver_source.py`, `makefiles/AltSign-build/rewrite_altsign_source.py` and `shims/`. Critical transformations stop the build when their targets change. Review new upstream source rather than removing match-count checks just to bypass a failure.
- netmuxd uses the official distribution. `src/NativeNetworkAddress.h` and `rewrite_usbmux_source.py` handle only received-address validation and normalization. Reduce local changes when official libraries provide equivalent handling.
- Set the root `VERSION` file to `vMAJOR.MINOR.PATCH`. The executable's `--version`, setup and release workflow share it. Do not overwrite an already published tag with later code changes.
- Run `python3 -m unittest discover -s tests -v` and the full CI build, communication, signing and extracted-installer checks. Validate with `workflow_dispatch` and `publish=false`, then proofread Japanese and English material before publication. Versions without physical-device validation remain previews.

The builder still uses the direct upstream's Alpine image pinned by digest. Modernizing that environment, including corecrypto and cpprestsdk, remains outstanding. Updated device libraries do not mean the whole toolchain is current. Distribution remains Debian 12/13 amd64; existing installations are not automatically overwritten.
