# v0.2.1 — Preview / プレビュー

## 日本語

netmuxd の動作確認済みバージョンは **v0.4.3** です。セットアップでは、このバージョンの公式配布物を取得します。

iOS 18以降で、AltStore Classicからインストール済みアプリをリフレッシュした後に、開発元の信頼を再設定する必要が生じる問題を修正しました。アプリを再インストールせず署名プロファイルだけを更新する処理にも、信頼を維持するための対策を追加しました。

新しいプロファイルを先にインストールし、成功後に不要になった非アクティブなプロファイルを整理します。iOS 17以前の処理順序は維持しています。すでに信頼が失われている場合は、設定から一度信頼し直してから検証してください。

v0.2.0を使ったiOS 27.0 / AltStore Classic 2.3の実機検証では、証明書が変わっていないにもかかわらず、更新時に既存の4件のプロファイルをすべて削除してから再登録し、信頼切れが再発しました。v0.2.1では、新しい4件を登録した後に古い4件を削除する処理順序をログで確認し、更新したアプリが再度の信頼操作なしで開くことを利用者が確認しました。

生成された本番の更新処理を使った14ケースの回帰テスト、既存のCI検査、Debian 13での展開済みセットアップ検査に合格しています。実機での確認は既存サーバーと1台のiPhoneでの手動更新です。新規導入、ホスト再起動後の復旧、長時間稼働は未検証です。

参考: [公式AltServer-WindowsのiOS 18向け修正](https://github.com/rileytestut/AltServer-Windows/commit/5da5175c20ba945250bb75bc1b82ab884eab6c6a)。今回の変更は、その考え方を通常のリフレッシュ処理へ拡張する、このフォーク独自の修正です。

## English

The tested version of netmuxd is **v0.4.3**. Setup downloads the official distribution of this version.

This preview fixes repeated developer-trust prompts after refreshing installed apps through AltStore Classic on iOS 18 or later. It extends trust preservation to profile-only refreshes, which do not reinstall the app.

New profiles are installed before inactive profiles are cleaned up. The operation order for iOS 17 and earlier is unchanged. If trust has already been lost, trust the developer once in Settings before testing.

On a real device running iOS 27.0 and AltStore Classic 2.3 with v0.2.0, we observed all four existing profiles being removed before their replacements were installed, followed by another trust prompt, while the signing certificates remained unchanged. With v0.2.1, server logs confirmed that all four new profiles were installed before the four old profiles were removed. The user confirmed that the refreshed app opened without another trust action.

All 14 regression cases using the generated production refresh method, existing CI checks, and the extracted-setup test on Debian 13 passed. Hardware verification covers a manual refresh on one iPhone with an existing server. Clean installation, full-host reboot recovery, and long-duration operation remain unverified.

Reference: [the official AltServer-Windows iOS 18 fix](https://github.com/rileytestut/AltServer-Windows/commit/5da5175c20ba945250bb75bc1b82ab884eab6c6a). This fork extends that approach to the regular refresh path; this extension is not an upstream change.
