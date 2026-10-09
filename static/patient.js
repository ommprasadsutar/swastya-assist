(() => {
  const form=document.getElementById('patientTriageForm'); if(!form) return;
  const result=document.getElementById('patientResult'), error=document.getElementById('patientError');
  const csrf=document.querySelector('meta[name="csrf-token"]')?.content||'';
  const key='swastya_patient_draft_v112';
  const fields=['patient_name','age','gender','language','patient_ref','scenario','address','symptoms','report_text'];
  const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const save=()=>{try{const d={ts:Date.now()}; fields.forEach(n=>{const e=form.elements[n]; if(e)d[n]=e.value;}); sessionStorage.setItem(key,JSON.stringify(d));}catch(_){}};
  const restore=()=>{try{const d=JSON.parse(sessionStorage.getItem(key)||'null'); if(!d||Date.now()-(d.ts||0)>86400000)return; fields.forEach(n=>{if(d[n]!=null&&form.elements[n])form.elements[n].value=d[n];});}catch(_){}};
  const clear=()=>{try{sessionStorage.removeItem(key);}catch(_){} fields.forEach(n=>{if(form.elements[n]) form.elements[n].value='';});};
  fields.forEach(n=>form.elements[n]?.addEventListener('input',save));
  form.elements['consent']?.addEventListener('change',save);
  document.getElementById('clearPatientDraft')?.addEventListener('click',()=>{clear(); location.reload();});
  form.addEventListener('submit',async e=>{e.preventDefault(); if(form.dataset.busy==='1')return; form.dataset.busy='1'; const btn=form.querySelector('button[type=submit]'); if(btn){btn.disabled=true;btn.dataset.label=btn.textContent;btn.textContent='Submitting…';} error?.classList.add('hidden'); result?.classList.remove('hidden'); if(result)result.innerHTML='<div class="loading-card"><b>Submitting securely…</b><span>Your information is being prepared for qualified human review.</span></div>';
    const fd=new FormData(form); fd.set('_ai_request_id', (crypto?.randomUUID?crypto.randomUUID().replaceAll('-',''):'pat'+Date.now())); fd.set('csrf_token',csrf);
    try{const r=await fetch('/api/triage',{method:'POST',headers:{'X-Requested-With':'XMLHttpRequest','X-CSRF-Token':csrf},body:fd}); let d={}; try{d=await r.json();}catch(_){} if(!r.ok) throw Object.assign(new Error(d.error||'Submission could not be completed.'),{status:r.status,data:d}); try{sessionStorage.removeItem(key);}catch(_){} if(result)result.innerHTML='<div class="success-banner"><b>Submission received</b><span>Your information has been sent for qualified human review. Clinical AI details are not displayed in the patient portal.</span></div>'; form.reset(); location.hash='submitted'; setTimeout(()=>location.reload(),800);}
    catch(err){if(error){error.textContent=err.status===422?String(err.message||'The information could not be verified.'):err.status===401?'Your session has expired. Please sign in again.':'We could not submit your information right now. Please try again.'; error.classList.remove('hidden');} result?.classList.add('hidden');}
    finally{form.dataset.busy='0';if(btn){btn.disabled=false;btn.textContent=btn.dataset.label||'Submit for human review';}}
  });
  restore();
})();
