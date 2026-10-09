(() => {
  'use strict';
  const DB_NAME = 'swastya-offline-v118';
  const DB_VERSION = 1;
  const PBKDF2_ITERATIONS = 310000;
  let db = null;
  let cryptoKey = null;
  let csrfToken = '';
  const $ = id => document.getElementById(id);
  const csrfHeaders = () => csrfToken ? {'X-CSRF-Token': csrfToken, 'Content-Type': 'application/json'} : {'Content-Type': 'application/json'};

  function state(id, message, kind = '') {
    const el = $(id); if (!el) return;
    el.textContent = message; el.className = 'state' + (kind ? ' ' + kind : '');
  }
  function uuid() { return (crypto.randomUUID ? crypto.randomUUID() : ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g,c=>(c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16))).replaceAll('-', ''); }
  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const d = req.result;
        if (!d.objectStoreNames.contains('drafts')) d.createObjectStore('drafts', {keyPath:'client_id'});
        if (!d.objectStoreNames.contains('settings')) d.createObjectStore('settings', {keyPath:'key'});
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error || new Error('Could not open local encrypted storage.'));
    });
  }
  function reqPromise(req) { return new Promise((resolve, reject) => { req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(req.error || new Error('Local database operation failed.')); }); }
  async function get(store, key) { return reqPromise(db.transaction(store, 'readonly').objectStore(store).get(key)); }
  async function allDrafts() { return reqPromise(db.transaction('drafts','readonly').objectStore('drafts').getAll()); }
  async function put(store, value) { return reqPromise(db.transaction(store,'readwrite').objectStore(store).put(value)); }
  async function remove(store, key) { return reqPromise(db.transaction(store,'readwrite').objectStore(store).delete(key)); }
  async function clearStore(store) { return reqPromise(db.transaction(store,'readwrite').objectStore(store).clear()); }
  function bytes(value) { return new Uint8Array(value); }
  async function deriveKey(passphrase, salt) {
    const material = await crypto.subtle.importKey('raw', new TextEncoder().encode(passphrase), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2', salt, iterations:PBKDF2_ITERATIONS, hash:'SHA-256'}, material, {name:'AES-GCM', length:256}, false, ['encrypt','decrypt']);
  }
  async function encrypt(value) {
    if (!cryptoKey) throw new Error('Unlock the queue first.');
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const cipher = await crypto.subtle.encrypt({name:'AES-GCM',iv}, cryptoKey, new TextEncoder().encode(JSON.stringify(value)));
    return {iv:Array.from(iv), ciphertext:Array.from(new Uint8Array(cipher))};
  }
  async function decrypt(record) {
    if (!cryptoKey) throw new Error('Unlock the queue first.');
    const plain = await crypto.subtle.decrypt({name:'AES-GCM',iv:bytes(record.iv)}, cryptoKey, bytes(record.ciphertext));
    return JSON.parse(new TextDecoder().decode(plain));
  }
  async function unlock(passphrase) {
    if (!window.crypto?.subtle || !window.indexedDB) throw new Error('This browser does not support encrypted offline storage. Use a current browser over HTTPS or localhost.');
    if (passphrase.length < 12) throw new Error('Use a passphrase of at least 12 characters.');
    let meta = await get('settings','salt');
    if (!meta) {
      const salt = crypto.getRandomValues(new Uint8Array(16));
      await put('settings',{key:'salt',value:Array.from(salt)});
      cryptoKey = await deriveKey(passphrase,salt);
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const verify = await crypto.subtle.encrypt({name:'AES-GCM',iv},cryptoKey,new TextEncoder().encode('swastya-offline-queue-key-check-v1'));
      await put('settings',{key:'verifier',iv:Array.from(iv),ciphertext:Array.from(new Uint8Array(verify))});
    } else {
      cryptoKey = await deriveKey(passphrase,bytes(meta.value));
      const verifier = await get('settings','verifier');
      if (!verifier) { cryptoKey = null; throw new Error('Local queue metadata is incomplete. Delete the local queue and set it up again.'); }
      try {
        const value = await crypto.subtle.decrypt({name:'AES-GCM',iv:bytes(verifier.iv)},cryptoKey,bytes(verifier.ciphertext));
        if (new TextDecoder().decode(value) !== 'swastya-offline-queue-key-check-v1') throw new Error('wrong key');
      } catch (_) { cryptoKey = null; throw new Error('That passphrase did not unlock this local queue. Your drafts were not changed.'); }
    }
    $('saveDraftBtn').disabled=false; $('refreshQueueBtn').disabled=false; $('syncBtn').disabled=!navigator.onLine;
    state('unlockState','Queue unlocked. Draft contents are encrypted at rest; lock the queue when you finish.','good');
    await renderQueue();
  }
  function directIdentifier(text) {
    const tests = [
      ['email',/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i],
      ['Aadhaar-like number',/(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)/],
      ['PAN-like number',/\b[A-Z]{5}\d{4}[A-Z]\b/i],
      ['phone number',/(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)/]
    ];
    for (const [name, pattern] of tests) if (pattern.test(text)) return name;
    return '';
  }
  function readPayload(form) {
    const data = new FormData(form);
    const value = Object.fromEntries(data.entries());
    value.age = value.age === '' ? null : Number(value.age);
    value.consent = data.get('consent') === 'on';
    value.patient_ref = value.patient_ref || ('SYN-' + uuid().slice(0,8).toUpperCase());
    value.address = value.address || 'Configured demonstration facility';
    return value;
  }
  async function saveDraft(ev) {
    ev.preventDefault();
    if (!cryptoKey) return state('draftState','Unlock the local queue before saving.','warn');
    const form = ev.currentTarget;
    if (!form.reportValidity()) return;
    const payload = readPayload(form);
    const combined = [payload.patient_name,payload.patient_ref,payload.address,payload.symptoms].join(' ');
    const identifier = directIdentifier(combined);
    if (identifier) return state('draftState',`Demo safety check detected a possible ${identifier}. Replace it with synthetic/public sample data before saving.`,'error');
    const clientId = uuid();
    try {
      const encrypted = await encrypt(payload);
      await put('drafts',{client_id:clientId, ...encrypted, created_at:new Date().toISOString(), state:'pending', server_case_id:'', error_code:''});
      form.reset();
      state('draftState','Draft encrypted and saved locally. No server or AI request was made.','good');
      await renderQueue();
    } catch (err) { state('draftState',err.message || 'Could not save this encrypted draft.','error'); }
  }
  async function renderQueue() {
    if (!db) return;
    const list = $('queueList');
    if (!cryptoKey) { list.innerHTML='<div class="empty">Unlock your queue to view local draft contents.</div>'; $('queueCount').textContent='Locked'; return; }
    try {
      const records = (await allDrafts()).sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at)));
      const pending = records.filter(r=>r.state==='pending');
      $('queueCount').textContent=`${pending.length} pending · ${records.length} total`;
      if (!records.length) { list.innerHTML='<div class="empty">No offline drafts yet. Create one on the left.</div>'; return; }
      const items=[];
      for (const r of records) {
        let details = null;
        if (r.state === 'pending') { try { details = await decrypt(r); } catch (_) { details={patient_ref:'Encrypted draft', symptoms:''}; } }
        items.push(`<article class="queue-item"><div><b>${r.state==='synced' ? 'Synchronized case' : esc(details?.patient_ref || 'Offline intake')}</b><small>${r.state==='synced' ? `Server case: ${esc(r.server_case_id || 'confirmed')}` : `${esc(details?.patient_name || '')} · ${esc((details?.symptoms || '').slice(0,95))}`}<br>Saved ${esc(new Date(r.created_at).toLocaleString())}${r.error_code ? `<br>Last sync status: ${esc(r.error_code)}` : ''}</small></div><span class="status-tag ${r.state==='synced'?'synced':''}">${r.state==='synced'?'SYNCED':'PENDING'}</span></article>`);
      }
      list.innerHTML=items.join('');
      $('syncBtn').disabled=!navigator.onLine || pending.length===0;
    } catch (err) { state('syncState','Could not read the local queue. Check your passphrase or browser storage.','error'); }
  }
  async function syncNow(automatic = false) {
    if (!cryptoKey) return state('syncState','Unlock the local queue before syncing.','warn');
    if (!navigator.onLine) return state('syncState','You are offline. Drafts remain encrypted on this device.','warn');
    const btn=$('syncBtn'); if(btn)btn.disabled=true;
    state('syncState',automatic?'Connection restored. Attempting safe synchronization…':'Checking the authenticated session and syncing pending drafts…');
    try {
      const sessionResponse = await fetch('/api/offline-session',{headers:{'X-Requested-With':'XMLHttpRequest'},cache:'no-store'});
      let sessionData={}; try{sessionData=await sessionResponse.json()}catch(_){}
      if (!sessionResponse.ok || !sessionData.csrf_token) {
        state('syncState','Sign in with a clinical/reviewer account in the main Swastya Assist app, then return here to synchronize. Drafts remain on this device.','warn');
        return;
      }
      csrfToken=sessionData.csrf_token;
      const records=(await allDrafts()).filter(r=>r.state==='pending');
      if (!records.length) return state('syncState','There are no pending drafts to synchronize.','good');
      const decrypted=[];
      for (const r of records) decrypted.push({client_id:r.client_id,payload:await decrypt(r)});
      const response=await fetch('/api/offline-sync',{method:'POST',headers:csrfHeaders(),body:JSON.stringify({items:decrypted}),cache:'no-store'});
      let result={}; try{result=await response.json()}catch(_){}
      if (!response.ok) throw new Error(result.error || `Sync failed (${response.status}).`);
      const byId=new Map((result.results||[]).map(x=>[x.client_id,x]));
      let completed=0, failed=0;
      for (const old of records) {
        const outcome=byId.get(old.client_id);
        if (outcome && outcome.status==='synced' && outcome.case_id) {
          await put('drafts',{client_id:old.client_id,created_at:old.created_at,state:'synced',server_case_id:outcome.case_id,error_code:''});
          completed++;
        } else {
          await put('drafts',{...old,error_code:outcome?.code || 'SYNC_NOT_CONFIRMED'}); failed++;
        }
      }
      await renderQueue();
      state('syncState',`${completed} draft(s) synchronized. No AI was called; cases require human review.${failed?` ${failed} item(s) remain encrypted because sync was not confirmed.`:''}`, failed?'warn':'good');
    } catch (err) {
      state('syncState',`${err.message || 'Sync failed.'} Nothing unconfirmed was deleted; drafts remain encrypted locally.`,'error');
    } finally {
      if(btn)btn.disabled=!cryptoKey || !navigator.onLine;
    }
  }
  async function lockQueue() {
    cryptoKey=null;
    $('queuePassphrase').value='';
    $('saveDraftBtn').disabled=true; $('refreshQueueBtn').disabled=true; $('syncBtn').disabled=true;
    state('unlockState','Queue locked. Local draft content is not available until unlocked.','');
    state('syncState','Synchronization requires an authenticated clinical account and network access.');
    await renderQueue();
  }
  async function clearQueue() {
    if (!confirm('Delete every local offline draft and sync receipt from this browser? This cannot be undone.')) return;
    try { await clearStore('drafts'); await clearStore('settings'); cryptoKey=null; csrfToken='';
      $('saveDraftBtn').disabled=true; $('refreshQueueBtn').disabled=true; $('syncBtn').disabled=true;
      state('unlockState','Local queue deleted. A new passphrase will set up a fresh queue.','warn');
      state('syncState','All local drafts and receipts were deleted from this browser. Server-synchronized cases are not deleted.','good');
      await renderQueue();
    } catch(err) { state('syncState','Could not clear local storage. Please review browser storage permissions.','error'); }
  }
  function updateNetwork() {
    const badge=$('networkBadge');
    badge.textContent=navigator.onLine?'● Online':'● Offline — local capture only';
    badge.className='pill'+(navigator.onLine?'':' offline');
    $('syncBtn').disabled=!cryptoKey || !navigator.onLine;
    if (navigator.onLine && cryptoKey) syncNow(true);
    else if (!navigator.onLine) state('syncState','Offline. Drafts stay encrypted in this browser; server sync and AI processing are paused.','warn');
  }
  async function init() {
    try {
      db=await openDb();
      state('unlockState','Queue locked. Use your passphrase to open or initialize encrypted storage.');
      await renderQueue();
      await navigator.serviceWorker?.register('/sw.js').catch(()=>{});
    } catch(err) { state('unlockState',err.message || 'Encrypted local storage is unavailable.','error'); }
    $('unlockForm').addEventListener('submit', async ev=>{
      ev.preventDefault(); const pass=$('queuePassphrase').value;
      try { await unlock(pass); $('queuePassphrase').value=''; }
      catch(err) { cryptoKey=null; state('unlockState',err.message || 'Could not unlock the queue.','error'); }
    });
    $('lockBtn').addEventListener('click',lockQueue);
    $('draftForm').addEventListener('submit',saveDraft);
    $('syncBtn').addEventListener('click',()=>syncNow(false));
    $('refreshQueueBtn').addEventListener('click',renderQueue);
    $('clearQueueBtn').addEventListener('click',clearQueue);
    window.addEventListener('online',updateNetwork);
    window.addEventListener('offline',updateNetwork);
    updateNetwork();
  }
  function esc(value) { return String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();
