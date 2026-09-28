'use strict';
let passkeyRegister = false;
const passkeyText = {
  ja: {title:'パスキーでログイン', first:'初回設定：パスキーを登録',
    help:'Face ID・Touch ID・Windows Helloなどで本人確認してログインします。',
    firstHelp:'このサーバーの所有者として確認できました。この端末のパスキーを登録してください。',
    register:'パスキーを登録する', login:'パスキーでログイン',
    owner:'初回登録は、サーバー所有者のTailscaleアカウントから接続してください。',
    unsupported:'このブラウザーではパスキーを利用できません。HTTPSのURLをSafari・Chrome・Edgeなどで開いてください。',
    failed:'パスキー操作が完了しませんでした。キャンセルした場合は、もう一度ボタンを押してください。',
    wait:'端末の案内に従って本人確認してください…'},
  en: {title:'Sign in with a passkey',first:'First-time setup: register a passkey',
    help:'Use Face ID, Touch ID, Windows Hello or another authenticator to sign in.',
    firstHelp:'You are connected as the server owner. Register a passkey for this console.',
    register:'Register a passkey',login:'Sign in with a passkey',
    owner:'For initial enrollment, connect with the server owner’s Tailscale account.',
    unsupported:'Passkeys are unavailable in this browser. Open the HTTPS URL in Safari, Chrome, Edge or another compatible browser.',
    failed:'The passkey operation did not complete. If you cancelled, press the button to try again.',
    wait:'Follow your device’s instructions to verify your identity…'}
};
function unbase64(value) {
  return Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')), c=>c.charCodeAt(0));
}
function base64(value) {
  return btoa(String.fromCharCode(...new Uint8Array(value))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
}
async function configurePasskeys() {
  const state = await api('/api/auth');
  const panel = document.querySelector('#passkey-panel');
  const legacy = document.querySelector('#legacy-login');
  panel.hidden = !state.passkeys;
  legacy.hidden = state.passkeys;
  if (!state.passkeys) return;
  passkeyRegister = !state.registered;
  const text = passkeyText[lang];
  document.querySelector('#login h1').textContent=text[passkeyRegister?'first':'title'];
  document.querySelector('#login-intro').textContent=text[passkeyRegister?(state.can_register?'firstHelp':'owner'):'help'];
  const button = document.querySelector('#passkey-button');
  button.textContent=text[passkeyRegister?'register':'login'];
  button.disabled=passkeyRegister&&!state.can_register;
  document.querySelector('#passkey-help').textContent=button.disabled?text.owner:'';
  if(!window.isSecureContext || !window.PublicKeyCredential) {
    button.disabled=true;
    document.querySelector('#passkey-help').textContent=text.unsupported;
  }
}
async function usePasskey() {
  const text = passkeyText[lang];
  const button = document.querySelector('#passkey-button');
  const error = document.querySelector('#login-error');
  button.disabled=true;
  error.textContent=text.wait;
  try {
    const path='/api/passkey/'+(passkeyRegister?'register':'login');
    const options=await api(path+'/options',{});
    options.challenge=unbase64(options.challenge);
    if(options.user)options.user.id=unbase64(options.user.id);
    for(const key of ['allowCredentials','excludeCredentials']) {
      if(options[key])options[key]=options[key].map(c=>({...c,id:unbase64(c.id)}));
    }
    const credential=await navigator.credentials[passkeyRegister?'create':'get']({publicKey:options});
    const response={clientDataJSON:base64(credential.response.clientDataJSON)};
    if(passkeyRegister) {
      response.attestationObject=base64(credential.response.attestationObject);
      response.transports=credential.response.getTransports?.()||[];
    } else {
      response.authenticatorData=base64(credential.response.authenticatorData);
      response.signature=base64(credential.response.signature);
      response.userHandle=credential.response.userHandle?base64(credential.response.userHandle):null;
    }
    await api(path+'/verify',{id:credential.id,rawId:base64(credential.rawId),type:credential.type,response});
    error.textContent='';
    await connect();
  } catch {
    error.textContent=text.failed;
  } finally { button.disabled=false; }
}
