# v0.2.1 — Preview / プレビュー

## 日本語

iOS 18以降で、AltStore Classicからインストール済みアプリをリフレッシュした後に、開発元の信頼を再設定する必要が生じる問題への修正候補です。アプリを再インストールせず署名プロファイルだけを更新する処理にも、信頼を維持するための対策を追加しました。

新しいプロファイルを先にインストールし、成功後に不要になった非アクティブなプロファイルを整理します。iOS 17以前の処理順序は維持しています。すでに信頼が失われている場合は、設定から一度信頼し直してから検証してください。

v0.2.0を使ったiOS 27.0 / AltStore Classic 2.3の実機検証では、証明書が変わっていないにもかかわらず、更新時に既存の4件のプロファイルをすべて削除してから再登録し、信頼切れが再発することを確認しました。この修正候補を適用した実機での結果は、まだ確認できていません。

参考: [公式AltServer-WindowsのiOS 18向け修正](https://github.com/rileytestut/AltServer-Windows/commit/5da5175c20ba945250bb75bc1b82ab884eab6c6a)。今回の変更は、その考え方を通常のリフレッシュ処理へ拡張する、このフォーク独自の修正です。

## English

This preview contains a candidate fix for repeated developer-trust prompts after refreshing installed apps through AltStore Classic on iOS 18 or later. It extends trust preservation to profile-only refreshes, which do not reinstall the app.

New profiles are installed before inactive profiles are cleaned up. The operation order for iOS 17 and earlier is unchanged. If trust has already been lost, trust the developer once in Settings before testing.

On a real device running iOS 27.0 and AltStore Classic 2.3 with v0.2.0, we observed all four existing profiles being removed before their replacements were installed, followed by another trust prompt, while the signing certificates remained unchanged. This candidate fix has not yet been verified on a real device.

Reference: [the official AltServer-Windows iOS 18 fix](https://github.com/rileytestut/AltServer-Windows/commit/5da5175c20ba945250bb75bc1b82ab884eab6c6a). This fork extends that approach to the regular refresh path; this extension is not an upstream change.
