const qs = s => document.querySelector(s);
const qsa = s => document.querySelectorAll(s);
const csrfToken = qs('meta[name="csrf-token"]')?.content || '';
const csrfHeaders = csrfToken ? {'X-CSRF-Token': csrfToken, 'X-Requested-With':'XMLHttpRequest'} : {'X-Requested-With':'XMLHttpRequest'};
// ID lookup helper: all $() callers pass element IDs, not CSS selectors.
const $ = id => document.getElementById(id);

function esc(value) {
  return String(value ?? '').replace(/[&<>\'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}
function arr(value) { return Array.isArray(value) ? value : []; }
function setBusy(btn, busy, label) { if (!btn) return; btn.disabled = busy; if (label) btn.dataset.originalLabel ||= btn.innerHTML; btn.innerHTML = busy ? label : (btn.dataset.originalLabel || btn.innerHTML); }
function cloneFormData(source) { const out = new FormData(); for (const [key, value] of source.entries()) out.append(key, value); return out; }
function friendlyError(error, fallback = 'We could not complete that action. Please try again.') {
  const status = Number(error?.status || 0);
  const message = String(error?.message || '');
  const lowered = message.toLowerCase();
  if (status === 401) return 'Your session has expired. Please sign in again.';
  if (status === 403) return 'You do not have permission to perform this action.';
  if (status === 413) return 'That file is too large. Please choose a smaller supported file.';
  if (status === 415) return 'That file type is not supported. Please upload a PNG, JPG/JPEG, or PDF.';
  if (status === 422) return message || 'The information could not be verified. Please check the patient details and uploaded report.';
  if (status === 428) return message || 'Privacy consent is required before sending media to an external AI service.';
  if (status >= 500 || lowered.includes('server returned') || lowered.includes('internal server') || lowered.includes('traceback') || lowered.includes('flask') || lowered.includes('gemini http')) {
    return 'The service is temporarily unavailable. Please try again in a moment or continue with the available manual review workflow.';
  }
  if (lowered.includes('failed to fetch') || lowered.includes('networkerror') || lowered.includes('load failed')) return 'We could not connect right now. Check your connection and try again.';
  return message || fallback;
}
function showClientError(error, fallback) {
  const box=$('clientError'); if (!box) return;
  box.textContent=friendlyError(error,fallback); box.hidden=false; box.classList.remove('hidden');
  window.setTimeout(()=>{ box.hidden=true; box.classList.add('hidden'); },7000);
}
function setupMobileNavigation() {
  const sidebar=$('appSidebar'), toggle=$('mobileNavToggle'), backdrop=$('mobileNavBackdrop');
  if(!sidebar || !toggle || !backdrop) return;
  const setOpen=open=>{ document.body.classList.toggle('nav-open',open); toggle.setAttribute('aria-expanded',String(open)); toggle.setAttribute('aria-label',open?'Close navigation':'Open navigation'); backdrop.hidden=!open; };
  toggle.addEventListener('click',()=>setOpen(!document.body.classList.contains('nav-open')));
  backdrop.addEventListener('click',()=>setOpen(false));
  document.addEventListener('keydown',e=>{if(e.key==='Escape' && document.body.classList.contains('nav-open')){setOpen(false);toggle.focus();}});
  qsa('.nav').forEach(n=>n.addEventListener('click',()=>setOpen(false)));
  window.addEventListener('resize',()=>{if(window.innerWidth>960) setOpen(false);});
  window.__swastyaNavClose=()=>setOpen(false);
}
async function jsonFetch(url, options = {}) {
  const merged = {...options, headers: {...csrfHeaders, ...(options.headers || {})}};
  const response = await fetch(url, merged);
  let data = {};
  try { data = await response.json(); } catch (_) { data = {error: `Server returned ${response.status}`}; }
  if (response.status === 401 && !url.includes('/login')) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.assign('/login?next=' + next);
  }
  if (!response.ok) {
    const err = new Error(data.error || `Request failed (${response.status})`);
    err.data = data;
    err.status = response.status;
    throw err;
  }
  return data;
}

qsa('[data-view]').forEach(btn => btn.addEventListener('click', () => showView(btn.dataset.view)));
function showView(view) {
  const target = qs('#view-' + view); if (!target) return;
  qsa('.view').forEach(x => x.classList.remove('active'));
  target.classList.add('active');
  qsa('.nav').forEach(x => x.classList.toggle('active', x.dataset.view === view));
  if ($('pageTitle')) $('pageTitle').textContent = document.body?.dataset.userRole === 'admin' ? 'Admin Console' : 'Clinical Console';
  if (view === 'dashboard') loadDashboard();
  if (view === 'analytics') loadAnalytics();
  if (view === 'ocr') checkGemini();
  window.scrollTo({top:0, behavior:'smooth'});
}

// Dashboard / queue
async function loadDashboard() {
  try { const box=$('dashboardError'); if(box) box.classList.add('hidden');
    const [a, casesData] = await Promise.all([
      jsonFetch('/api/analytics'),
      jsonFetch('/api/cases?limit=200')
    ]);
    $('kpiOpen').textContent = Math.max(0, a.total - (a.reviewed || 0));
    $('kpiUrgent').textContent = a.urgent ?? 0;
    $('kpiReviewed').textContent = a.reviewed ?? 0;
    $('kpiRate').textContent = `${a.review_rate ?? 0}%`;
    renderCases(casesData, $('riskFilter')?.value || '');
  } catch (e) { console.error(e); const box=$('dashboardError'); if(box){box.textContent=friendlyError(e,'We could not load the review queue.');box.classList.remove('hidden');} }
}
function renderCases(data, filter = '') {
  const container = $('dashboardQueue'); if (!container) return;
  window.__cases = data.cases || [];
  const rows = window.__cases.filter(c => !filter || c.risk === filter);
    let html = '<div class="table-row header"><span>Patient</span><span>Risk</span><span>Status</span><span>Language</span><span>Action</span></div>';
    rows.forEach(c => {
      html += `<div class="table-row"><span><b>${esc(c.patient_name || c.patient_ref)}</b><br><small>${esc(c.patient_ref)} · ${esc((c.created_at || '').slice(0,16).replace('T',' '))}</small></span><span class="risk ${String(c.risk).toLowerCase().replaceAll(' ','-')}">${esc(c.risk)}</span><span>${esc(c.status)}</span><span>${esc(c.language)}</span><button type="button" class="review-btn" data-case-id="${esc(c.id)}">Review →</button></div>`;
    });
  container.innerHTML = html + (rows.length ? '' : '<p class="empty">No encounters match this filter.</p>');
}
async function fetchCases(filter = '') {
  try { renderCases(await jsonFetch('/api/cases?limit=200'), filter); }
  catch (e) { const container=$('dashboardQueue'); if(container) container.innerHTML = `<p class="empty error-text">${esc(friendlyError(e,'We could not load the review queue.'))}</p>`; }
}
$('riskFilter')?.addEventListener('change', e => renderCases({cases: window.__cases || []}, e.target.value));
$('refreshDashboard')?.addEventListener('click', () => loadDashboard());

document.addEventListener('click', e => {
  const btn = e.target.closest('[data-case-id]');
  if (btn) {
    e.preventDefault();
    if (window.__reviewDirty && !confirm('You have unsaved reviewer changes. Open another encounter and discard them?')) return;
    window.__reviewDirty = false;
    loadCase(btn.dataset.caseId);
  }
});

async function loadCase(id) {
  try {
    const c = await jsonFetch('/api/cases/' + encodeURIComponent(id));
    window.__activeCaseId = id;
    $('detail')?.classList.remove('hidden');
    const n = c.ai_note || {};
    const evidenceBase = arr(c.evidence_review).length ? arr(c.evidence_review) : arr(n.evidence).map(x => ({item:x.item || '', source:x.source || 'Not provided', status:'Pending', note:''}));
    const evidence = evidenceBase.map((x, i) => `<div class="evidence-review-item" data-evidence-index="${i}"><div><b>${esc(x.item || '')}</b><small>Source: ${esc(x.source || 'Unknown')}</small></div><div class="evidence-controls"><select class="evidence-status" aria-label="Evidence review status"><option ${x.status==='Pending'?'selected':''}>Pending</option><option ${x.status==='Verified'?'selected':''}>Verified</option><option ${x.status==='Rejected'?'selected':''}>Rejected</option><option ${x.status==='Unclear'?'selected':''}>Unclear</option></select><input class="evidence-note" maxlength="500" value="${esc(x.note || '')}" placeholder="Reviewer note (optional)"></div></div>`).join('') || '<p class="muted">No explicit source mapping returned. Verify the original inputs.</p>';
    const followUps = arr(c.follow_up_answers).length ? arr(c.follow_up_answers) : arr(n.follow_up_questions).map(q => ({question:q, answer:'', source:'Reviewer', verified:false}));
    const reportFields = arr(n.extracted_report_fields).map(x => typeof x === 'object' ? `<li><b>${esc(x.field || x.name || 'Value')}</b>: ${esc(x.value || x.text || '')} <small>${esc(x.source || 'Uploaded report')}</small></li>` : `<li>${esc(x)}</li>`).join('') || '<li>No report fields extracted.</li>';
    const reportLinkLabel = document.body?.dataset.demoOnly === "1" ? "Open privacy-checked report preview ↗" : "Open original report ↗";
    const reportLink = c.report_filename ? `<a class="secondary inline-btn" href="/api/cases/${encodeURIComponent(id)}/report" target="_blank" rel="noopener">${reportLinkLabel}</a>` : '<span class="muted">No uploaded report</span>';
    $('detailBody').innerHTML = `
      <div class="detailGrid">
        <div class="detailBlock">
          <div class="detail-kicker">PATIENT</div><h3>${esc(c.patient_ref)} <span class="source-pill">${esc(c.source || 'Intake')}</span></h3>
          <p><b>Name:</b> ${esc(c.patient_name || '—')} · <b>Age:</b> ${esc(c.age ?? '—')} · <b>Gender:</b> ${esc(c.gender || '—')}</p>
          <p><b>Language:</b> ${esc(c.language || '—')} · <b>Scenario:</b> ${esc(c.scenario || '—')}</p>
          <p><b>Facility/locality:</b> ${esc(c.address || '—')}</p>
          <p><b>Final priority:</b> <span class="risk ${String(c.final_risk || c.risk).toLowerCase().replaceAll(' ','-')}">${esc(c.final_risk || c.risk)}</span> · <b>Automated:</b> ${esc(c.ai_risk || 'Needs review')}</p>
          ${c.risk_override_reason ? `<p><b>Priority change reason:</b> ${esc(c.risk_override_reason)}</p>` : ''}
          <h4>Patient narrative</h4><p class="preline">${esc(c.symptoms || '—')}</p>
          <h4>Report text</h4><p class="preline">${esc(c.report_text || '—')}</p>
          <h4>Uploaded report</h4><p>${esc(c.report_filename || 'No uploaded report')}</p>${reportLink}
        </div>
        <div class="detailBlock">
          <div class="detail-kicker">AI TRIAGE PACKET</div><h3>${esc(n.risk_category || c.risk || 'Needs review')}</h3>
          <p>${esc(n.summary || 'No summary returned.')}</p>
          <h4>Timeline</h4><p>${esc(n.timeline || 'Timeline requires reviewer verification.')}</p>
          <h4>Key details</h4><ul>${arr(n.key_details).map(x => `<li>${esc(typeof x === 'object' ? (x.value || x.text || JSON.stringify(x)) : x)}</li>`).join('') || '<li>None returned.</li>'}</ul>
          <h4>Missing / unclear</h4><ul>${arr(n.missing_information).map(x => `<li>${esc(x)}</li>`).join('') || '<li>None returned.</li>'}</ul>
          <h4>Suggested follow-up questions</h4><ul>${arr(n.follow_up_questions).map(x => `<li>${esc(x)}</li>`).join('') || '<li>None returned.</li>'}</ul>
          <h4>Follow-up answers</h4><div class="followup-list">${followUps.map((x,i) => `<div class="followup-item" data-followup-index="${i}"><b>${esc(x.question || '')}</b><textarea class="followup-answer" maxlength="1200" placeholder="Record patient/clinician answer">${esc(x.answer || '')}</textarea><label class="tiny-check"><input class="followup-verified" type="checkbox" ${x.verified?'checked':''}> Verified</label></div>`).join('') || '<p class="muted">No follow-up questions returned.</p>'}</div>
          <h4>Urgency signals</h4><ul>${arr(n.risk_signals).map(x => `<li><b>${esc(x.label || 'Signal')}</b>: ${esc(x.term || x.detail || '')}</li>`).join('') || '<li>No signal returned.</li>'}</ul>
          <h4>Report extraction</h4><ul>${reportFields}</ul>${n.full_report_extraction ? `<h4>Full report extraction</h4><pre class="preline reviewer-full-extraction">${esc(n.full_report_extraction)}</pre>` : ''}
        </div>
      </div>
      <div class="evidence-panel"><h3>Evidence traceability</h3><p>Every AI statement must be checked against the original patient input or uploaded report.</p><div class="evidence-review-list">${evidence}</div></div>
      <div class="review-decision"><div class="detail-kicker">HUMAN REVIEW</div><h3>Reviewer decision</h3><p class="muted">AI output is advisory. A qualified reviewer confirms, modifies, escalates or requests more information.</p>
        <form class="reviewForm" id="reviewForm"><input type="hidden" name="csrf_token" value="${esc(csrfToken)}">
          <label>Reviewer status<select name="status"><option ${c.status==='Needs review'?'selected':''}>Needs review</option><option ${c.status==='Reviewed'?'selected':''}>Reviewed</option><option ${c.status==='Escalated'?'selected':''}>Escalated</option><option ${c.status==='Needs more information'?'selected':''}>Needs more information</option></select></label>
          <label>Final operational priority<select name="final_risk"><option ${c.final_risk==='Routine review'?'selected':''}>Routine review</option><option ${c.final_risk==='Priority review'?'selected':''}>Priority review</option><option ${c.final_risk==='Urgent review'?'selected':''}>Urgent review</option><option ${c.final_risk==='Needs review'?'selected':''}>Needs review</option><option ${c.final_risk==='Insufficient information'?'selected':''}>Insufficient information</option></select></label>
          <p class="muted"><b>Automated priority:</b> ${esc(c.ai_risk || c.risk || 'Needs review')} · changing it requires a reason.</p>
          <label>Risk-change reason<textarea name="risk_override_reason" maxlength="2000" placeholder="Required only when changing the automated priority.">${esc(c.risk_override_reason || '')}</textarea></label>
          <label>Reviewer note<textarea name="reviewer_note" maxlength="5000" placeholder="Document verification, handoff or administrative next step.">${esc(c.reviewer_note || '')}</textarea></label>
          <label class="consent-check"><input type="checkbox" name="urgent_verified" value="1"> I checked the original patient/report information. Required before saving an <b>Urgent review</b> decision.</label>
          <div class="form-grid"><label>Referral / handoff status<select name="referral_status">${['Not required','Draft','Ready','Sent','Acknowledged','Completed'].map(v=>`<option ${c.referral_status===v?'selected':''}>${v}</option>`).join('')}</select></label><label>Referral destination<input name="referral_destination" maxlength="500" value="${esc(c.referral_destination || '')}" placeholder="Synthetic receiving facility"></label></div>
          <div class="contact-panel"><div><b>Urgent patient contact</b><p class="muted">Optional. For an urgent case, record contact consent and a synthetic/demo number before initiating a call.</p></div><label class="consent-check"><input type="checkbox" name="contact_patient" ${c.contact_consent && c.contact_phone ? 'checked' : ''}> Contact patient/caregiver after this review</label><div class="form-grid"><label>Contact phone<input name="contact_phone" inputmode="tel" autocomplete="tel" maxlength="24" value="${esc(c.contact_phone || '')}" placeholder="+1-555-010-0100"></label><label class="consent-check"><input type="checkbox" name="contact_consent" ${c.contact_consent ? 'checked' : ''}> Contact consent recorded</label></div>${c.contact_phone && c.contact_consent && c.final_risk === 'Urgent review' ? `<button type="button" id="callPatientBtn" class="secondary">Call patient ↗</button><span id="contactState" class="status">${(c.contact_attempts||[]).length ? `${(c.contact_attempts||[]).length} call attempt(s) recorded` : 'No call attempt recorded'}</span>` : ''}</div>
          <div class="review-actions"><button class="primary" type="submit">Save reviewer decision</button><span id="reviewSaveState" class="status">Not saved</span></div>
        </form>
      </div>`;
    const reviewForm = $('reviewForm');
    if (reviewForm) {
      reviewForm.dataset.savedStatus = reviewForm.elements.status.value;
      reviewForm.dataset.savedNote = reviewForm.elements.reviewer_note.value;
      reviewForm.addEventListener('input', () => {
        window.__reviewDirty = true;
        const state = $('reviewSaveState');
        if (state && state.textContent === 'Saved just now') { state.textContent = 'Unsaved changes'; state.className = 'status'; }
      });
      reviewForm.addEventListener('change', () => {
        window.__reviewDirty = true;
        const state = $('reviewSaveState');
        if (state && state.textContent === 'Saved just now') { state.textContent = 'Unsaved changes'; state.className = 'status'; }
      });
      reviewForm.addEventListener('submit', saveReview);
      $('callPatientBtn')?.addEventListener('click', async () => {
        const state = $('contactState');
        try {
          const x = await jsonFetch('/api/cases/' + encodeURIComponent(window.__activeCaseId) + '/contact', {method:'POST'});
          if (!x.ok) throw new Error(x.error || 'Contact could not be initiated.');
          if (state) { state.textContent = 'Call initiated'; state.className = 'status ready'; }
          window.location.href = x.tel_uri;
        } catch (err) {
          if (state) { state.textContent = friendlyError(err, 'Patient contact could not be initiated.'); state.className = 'status error'; }
        }
      });
    }
  } catch (e) { const box=$('dashboardError'); if(box){box.textContent=friendlyError(e);box.classList.remove('hidden');} }
}
async function saveReview(e) {
  e.preventDefault();
  const form = e.currentTarget, btn = form.querySelector('button[type=submit]'), state = $('reviewSaveState');
  if (!window.__activeCaseId) { if (state) { state.textContent='No case selected'; state.className='status error'; } return; }
  setBusy(btn, true, 'Saving…');
  if (state) { state.textContent = 'Saving…'; state.className = 'status'; }
  try {
    const detailRoot = $('detailBody') || document;
    const evidenceReview = [...detailRoot.querySelectorAll('.evidence-review-item')].map(item => ({
      item: item.querySelector('b')?.textContent?.trim() || '',
      source: item.querySelector('small')?.textContent?.replace(/^Source:\s*/i,'').trim() || 'Not provided',
      status: item.querySelector('.evidence-status')?.value || 'Pending',
      note: item.querySelector('.evidence-note')?.value || ''
    }));
    const followUpAnswers = [...detailRoot.querySelectorAll('.followup-item')].map(item => ({
      question: item.querySelector('b')?.textContent?.trim() || '',
      answer: item.querySelector('.followup-answer')?.value || '',
      source: 'Reviewer',
      verified: Boolean(item.querySelector('.followup-verified')?.checked)
    }));
    form.querySelectorAll('input[name="evidence_review"], input[name="follow_up_answers"]').forEach(x => x.remove());
    const evidenceInput = document.createElement('input'); evidenceInput.type='hidden'; evidenceInput.name='evidence_review'; evidenceInput.value=JSON.stringify(evidenceReview); form.appendChild(evidenceInput);
    const followInput = document.createElement('input'); followInput.type='hidden'; followInput.name='follow_up_answers'; followInput.value=JSON.stringify(followUpAnswers); form.appendChild(followInput);
    // Use URL-encoded form data for the reviewer route so Flask parses it
    // deterministically on every local/proxy/server combination. Send the
    // CSRF token in BOTH the form body and request header.
    const fd = new FormData(form);
    const body = new URLSearchParams();
    for (const [key, value] of fd.entries()) body.append(key, String(value));
    const x = await jsonFetch('/api/cases/' + encodeURIComponent(window.__activeCaseId) + '/review', {
      method:'POST',
      headers:{'X-Requested-With':'XMLHttpRequest','Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},
      body
    });
    if (!x.ok) throw new Error(x.error || 'Reviewer decision was not saved.');
    if (state) { state.textContent = 'Saved just now'; state.className = 'status ready'; }
    form.dataset.savedStatus = form.elements.status.value;
    form.dataset.savedNote = form.elements.reviewer_note.value;
    form.dataset.savedRisk = form.elements.final_risk.value;
    form.dataset.savedOverride = form.elements.risk_override_reason.value;
    form.dataset.savedReferralStatus = form.elements.referral_status.value;
    form.dataset.savedReferralDestination = form.elements.referral_destination.value;
    window.__reviewDirty = false;
    await loadDashboard();
    await loadCase(window.__activeCaseId);
  } catch (err) {
    console.error('Reviewer save failed:', err);
    if (state) { state.textContent = friendlyError(err, 'Reviewer decision could not be saved.'); state.className = 'status error'; }
  } finally { setBusy(btn, false); }
}
window.addEventListener('beforeunload', e => {
  if (window.__reviewDirty) { e.preventDefault(); e.returnValue = ''; }
});

$('closeDetailBtn')?.addEventListener('click', () => { if(window.__reviewDirty && !confirm('Discard unsaved reviewer changes?')) return; window.__reviewDirty=false; $('detail')?.classList.add('hidden'); });

$('printPacketBtn')?.addEventListener('click', async () => {
  if (!window.__activeCaseId) return;
  try {
    const x = await jsonFetch('/api/cases/' + encodeURIComponent(window.__activeCaseId) + '/packet');
    const p = x.packet, n = p.ai || {}, w = window.open('', '_blank');
    if (!w) { alert('Allow pop-ups to print the packet.'); return; }
    const list = a => arr(a).map(v => `<li>${esc(typeof v === 'object' ? (v.value || v.text || JSON.stringify(v)) : v)}</li>`).join('') || '<li>None</li>';
    w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Swastya Assist Reviewer Packet</title><link rel="stylesheet" href="/static/packet.css?v=19.0"></head><body><h1>Swastya Assist Reviewer Packet</h1><p class="muted">${esc(p.disclaimer)}</p><div class="box"><h2>Patient</h2><b>${esc(p.patient.reference)}</b><br>${esc(p.patient.name)} · Age ${esc(p.patient.age)} · ${esc(p.patient.gender)}<br>Language: ${esc(p.patient.language)} · Scenario: ${esc(p.patient.scenario)}</div><div class="box"><h2>AI summary</h2><p>${esc(n.summary || '')}</p><h3>Timeline</h3><p>${esc(n.timeline || '')}</p><h3>Key details</h3><ul>${list(n.key_details)}</ul><h3>Missing information</h3><ul>${list(n.missing_information)}</ul><h3>Follow-up questions</h3><ul>${list(n.follow_up_questions)}</ul><h3>Urgency signals</h3><ul>${list((n.risk_signals||[]).map(v => (v.label||'Signal')+': '+(v.term||v.detail||'')))}</ul></div><div class="box"><h2>Human review</h2><p>Status: ${esc(p.status)}</p><p>${esc(p.reviewer_note || 'No reviewer note yet.')}</p></div><div class="safe">AI-generated advisory documentation. Final clinical decisions remain with qualified healthcare personnel.</div></body></html>`);
    w.document.close(); w.focus(); setTimeout(() => w.print(), 350);
  } catch (e) { alert(friendlyError(e, 'The reviewer packet could not be prepared.')); }
});

// Patient intake is handled here so the same API/error/rendering path is used
// by intake and report/OCR workflows.
const triageForm = $('triageForm');
let __lastTriagePayload = null;
let __lastTriageRetryToken = '';
let __triageInFlight = false;
let __triageRequestId = '';
function newAiRequestId(){ return (crypto?.randomUUID ? crypto.randomUUID().replaceAll('-','') : ('req'+Date.now()+Math.random().toString(36).slice(2,12))); }
async function submitTriage(form, out, btn, retry=false) {
  if (__triageInFlight) return;
  const uploadChosen = Boolean(form.querySelector('input[name="report_image"]')?.files?.length);
  if (uploadChosen && !form.elements.external_ai_media_consent?.checked) {
    if (out) { out.classList.remove('hidden'); out.innerHTML = '<div class="error-card"><b>Privacy Gate</b><span>Nothing was sent to Gemini. Review the file, then explicitly opt in under External AI file gate to continue. The original file is not automatically masked.</span></div>'; }
    return;
  }
  __triageInFlight = true;
  setBusy(btn, true, retry ? 'Retrying AI…' : 'Processing…');
  out?.classList.remove('hidden');
  if (out) out.innerHTML = '<div class="loading-card"><b>Processing AI review…</b><span>One failed AI request stops this processing chain. No duplicate API calls are made.</span></div>';
  try {
    if (!retry) { __triageRequestId = newAiRequestId(); __lastTriageRetryToken = ''; }
    const payload = retry && __lastTriagePayload ? cloneFormData(__lastTriagePayload) : new FormData(form);
    payload.set('_ai_request_id', __triageRequestId);
    if (retry) payload.set('_ai_retry_token', __lastTriageRetryToken);
    else { __lastTriagePayload = cloneFormData(payload); }
    const x = await jsonFetch('/api/triage', {method:'POST', headers:{'X-Requested-With':'XMLHttpRequest'}, body:payload});
    renderNote(x.note || {}, x.warning, out);
    __lastTriagePayload = null; __lastTriageRetryToken = ''; form.reset(); triageUpload.clear(); clearTriageDraft();
    if (typeof window.__swastyaResetVoice === 'function') window.__swastyaResetVoice();
    await loadDashboard();
  } catch (err) {
    const canRetry = Boolean(err.data?.retryable && err.data?.retry_token);
    if (canRetry) __lastTriageRetryToken = err.data.retry_token;
    if (out) { const detected = err.data?.code === 'PATIENT_NAME_MISMATCH' && err.data?.report_patient_name ? `<div class="metric"><b>Verification status:</b> NOT VERIFIED</div><div class="metric"><b>Detected report name:</b> ${esc(err.data.report_patient_name)}</div>` : `<div class="metric"><b>Verification status:</b> NOT VERIFIED</div>`; out.innerHTML = `<div class="error-card"><b>Report verification stopped</b>${detected}<span>${esc(friendlyError(err))}</span>${canRetry ? '<button type="button" id="retryTriageBtn" class="secondary compact retry-btn">↻ Retry same patient input</button><small>This is the one allowed retry for this input.</small>' : '<small>No extraction or triage output was exposed. Start a new patient input.</small>'}</div>`; }
    if (canRetry) $('retryTriageBtn')?.addEventListener('click', () => submitTriage(form, out, btn, true), {once:true});
  } finally { __triageInFlight = false; setBusy(btn, false); }
}
const TRIAGE_DRAFT_KEY = 'swastya_intake_draft_v112';
function saveTriageDraft(){ try{ if(!triageForm)return; const d={ts:Date.now()}; ['patient_name','age','gender','language','patient_ref','scenario','address','symptoms','report_text'].forEach(name=>{ const el=triageForm.elements[name]; if(el)d[name]=el.value; }); d.consent=Boolean(triageForm.elements.consent?.checked); sessionStorage.setItem(TRIAGE_DRAFT_KEY,JSON.stringify(d)); }catch(_){} }
function restoreTriageDraft(){ try{const d=JSON.parse(sessionStorage.getItem(TRIAGE_DRAFT_KEY)||'null');if(!d||Date.now()-(d.ts||0)>86400000)return;['patient_name','age','gender','language','patient_ref','scenario','address','symptoms','report_text'].forEach(name=>{if(d[name]!=null&&triageForm?.elements[name])triageForm.elements[name].value=d[name];});if(triageForm?.elements.consent)triageForm.elements.consent.checked=Boolean(d.consent);}catch(_){} }
function clearTriageDraft(){try{sessionStorage.removeItem(TRIAGE_DRAFT_KEY);}catch(_){}}
if(triageForm){ triageForm.addEventListener('input',saveTriageDraft); triageForm.addEventListener('change',saveTriageDraft); triageForm.addEventListener('submit',async e=>{e.preventDefault(); await submitTriage(e.currentTarget, $('result'), e.currentTarget.querySelector('button[type=submit]'));}); }
function iconSvg(name){
  const map={
    report:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6z"/><path d="M15 3v5h5M9 12h6M9 16h6M9 8h2"/></svg>',
    summary:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h14v14H5z"/><path d="M8 9h8M8 12h8M8 15h5"/></svg>',
    calendar:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M16 3v4M8 3v4M3 10h18"/></svg>',
    alert:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4 21 20H3L12 4Z"/><path d="M12 9v5M12 17h.01"/></svg>',
    shield:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 20 6v5c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg>',
    intake:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    check:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 7"/></svg>'
  };
  return map[name] || map.report;
}

function renderNote(n, warning, el = $('result')) {
  if (!el) return;
  el.classList.remove('hidden');
  const manualFallback = n.processing_mode === 'Manual fallback';
  const isOcrResult = el.id === 'ocrResult';
  const ocrSections = arr(n.ocr_sections);
  const ocrUnreadable = arr(n.ocr_unreadable_portions);
  const ocrMeasurements = arr(n.ocr_measurements);
  const reportVerification = n.report_patient_name ? `<div class="ocr-verification-panel"><h3>${isOcrResult ? 'OCR document verification' : 'Uploaded report verification'}</h3><div class="verification-status-ok"><b>VERIFIED</b><span>Healthcare document verified and patient name matched.</span></div></div><div class="ocr-verified-details"><div class="metric"><b>Patient name on report:</b> ${esc(n.report_patient_name)}</div>${isOcrResult ? `<div class="metric"><b>Document type:</b> ${esc(n.ocr_document_type || 'Healthcare document')}</div><div class="metric"><b>Report date:</b> ${esc(n.ocr_report_date || 'Not readable')}</div><div class="metric"><b>OCR quality:</b> ${esc(n.ocr_quality || 'Unknown')}</div><h4>Document sections</h4><ul>${ocrSections.map(x=>`<li>${esc(x)}</li>`).join('')||'<li>No sections confidently detected.</li>'}</ul><h4>Measurements / values read from the document</h4><ul>${ocrMeasurements.map(x=>`<li><b>${esc(x.label || 'Value')}</b>: ${esc(x.value || '')}${x.unit ? ` ${esc(x.unit)}` : ''}${x.reference_range ? ` <small>Reference: ${esc(x.reference_range)}</small>` : ''}${x.section ? ` <small>Section: ${esc(x.section)}</small>` : ''}</li>`).join('')||'<li>No measurements confidently extracted.</li>'}</ul><h4>Unreadable portions</h4><ul>${ocrUnreadable.map(x=>`<li>${esc(x)}</li>`).join('')||'<li>None reported.</li>'}</ul>` : ''}<p class="muted">Verification is complete. The following content is shown only after the healthcare-document and patient-name checks passed. It is not a diagnosis and does not replace qualified clinical review.</p></div>` : '';
  const structuredFields = arr(n.extracted_report_fields).map(x=>`<li><b>${esc(x.field || 'Value')}</b>: ${esc(x.value || '')} <small>${esc(x.source || 'Uploaded report')}</small></li>`).join('');
  const reportSurface = (n.report_patient_name && (isOcrResult || el.id === 'result')) ? `<div class="verified-content-note"><b>Verified document received.</b><span>The original report text and full extraction are kept for the qualified reviewer. This screen shows only the structured reviewer-support summary.</span></div>${structuredFields ? `<div class="result-section"><div class="result-section-head"><span class="result-icon">${iconSvg('report')}</span><div><h3>Verified report fields</h3><small>Structured values from the verified document</small></div></div><ul>${structuredFields}</ul></div>` : ''}` : '';
  const riskSignals = arr(n.risk_signals);
  const signalHtml = riskSignals.map(x=>`<li><span class="signal-dot"></span><div><b>${esc(x.label || 'Signal')}</b><small>${esc(x.term || x.detail || '')}</small></div></li>`).join('') || '<li class="empty-signal">No urgency signal returned.</li>';
  const keyHtml = arr(n.key_details).map(x=>`<li>${esc(typeof x==='object'?(x.value||x.text||JSON.stringify(x)):x)}</li>`).join('')||'<li>None returned.</li>';
  const missingHtml = arr(n.missing_information).map(x=>`<li>${esc(x)}</li>`).join('')||'<li>None returned.</li>';
  const followHtml = arr(n.follow_up_questions).map(x=>`<li>${esc(x)}</li>`).join('')||'<li>None returned.</li>';
  el.innerHTML = `<div class="success-banner"><b>${manualFallback ? 'Case saved for manual review' : 'Triage report generated'}</b><span>${manualFallback ? 'Gemini was unavailable; no AI output was used. The case remains in the qualified-review workflow.' : 'Case is now in the review queue. Review every generated value against the source information.'}</span></div>${reportVerification}${reportSurface}<div class="result-metrics"><div class="metric-card"><span>Priority</span><b>${esc(n.risk_category || 'Needs review')}</b><small>Reviewer-facing automated category</small></div><div class="metric-card"><span>Urgency signals</span><b>${riskSignals.length}</b><small>Signals require human verification</small></div></div><div class="result-section-grid"><section class="result-section"><div class="result-section-head"><span class="result-icon">${iconSvg('summary')}</span><div><h3>Clinical summary</h3><small>Structured, non-diagnostic overview</small></div></div><p>${esc(n.summary || 'No summary returned.')}</p></section><section class="result-section"><div class="result-section-head"><span class="result-icon">${iconSvg('calendar')}</span><div><h3>Timeline</h3><small>Reported sequence of events</small></div></div><p>${esc(n.timeline || 'Timeline requires reviewer verification.')}</p></section></div><div class="result-section-grid"><section class="result-section"><div class="result-section-head"><span class="result-icon">${iconSvg('report')}</span><div><h3>Key details</h3><small>Important structured information</small></div></div><ul>${keyHtml}</ul></section><section class="result-section"><div class="result-section-head"><span class="result-icon">${iconSvg('alert')}</span><div><h3>Risk & urgency details</h3><small>Signals only; not a diagnosis</small></div></div><ul class="signal-list">${signalHtml}</ul></section></div><div class="result-section-grid"><section class="result-section"><div class="result-section-head"><span class="result-icon">${iconSvg('shield')}</span><div><h3>Missing information</h3><small>Items to verify or clarify</small></div></div><ul>${missingHtml}</ul></section><section class="result-section"><div class="result-section-head"><span class="result-icon">${iconSvg('intake')}</span><div><h3>Follow-up questions</h3><small>Suggested questions for the reviewer</small></div></div><ul>${followHtml}</ul></section></div>${warning?`<p class="muted result-warning">${esc(warning)}</p>`:''}<div class="handoff-strip"><span class="result-icon">${iconSvg('check')}</span><div><b>Reviewer handoff</b><span>${esc(n.handoff || 'Verify before use.')}</span></div></div>`;
}

// Lightweight same-device voice draft cache. It stores only the current synthetic narrative/translation locally and never sends contact data to AI.
const VOICE_DRAFT_KEY='swastya_voice_draft_v1111';
function cacheVoiceDraft(transcript, translation){ try { sessionStorage.setItem(VOICE_DRAFT_KEY, JSON.stringify({transcript:String(transcript||'').slice(0,12000), translation:String(translation||'').slice(0,12000), ts:Date.now()})); } catch(_) {} }
function restoreVoiceDraft(){ try { const raw=sessionStorage.getItem(VOICE_DRAFT_KEY); if(!raw) return; const d=JSON.parse(raw); if(!d || Date.now()-(d.ts||0)>3600000) return; if(d.transcript && $('liveTranscript')) {$('liveTranscript').value=d.transcript; $('liveTranscript').textContent=d.transcript;} if(d.translation && $('aiTranslation')) {$('aiTranslation').value=d.translation; $('aiTranslation').textContent=d.translation;} } catch(_) {} }
// Voice: real recording + browser transcript + optional Gemini transcript/translation.
const voice = $('voice'), voiceStop = $('voiceStop'), voiceTools = $('voiceTools'), voicePlayback = $('voicePlayback'), voiceAi = $('voiceAi');
let mediaRec = null, speechRec = null, mediaStream = null, micActive = false, audioChunks = [], recordedBlob = null, recordingStartedAt = 0, timerHandle = null, liveFinal = '', lastObjectUrl = null, voiceBaseSymptoms = '';
function voiceStatus(message, kind=''){ const el=$('voiceDiagnostic'); if(el){el.textContent=message;el.className='status-box '+kind;} }
function setTimer() { if (!recordingStartedAt || !$('recordingTimer')) return; const sec=Math.floor((Date.now()-recordingStartedAt)/1000); $('recordingTimer').textContent = `${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')}`; }
function supportedMime() {
  if (!window.MediaRecorder) return '';
  const options=['audio/webm;codecs=opus','audio/webm','audio/mp4','audio/ogg;codecs=opus'];
  return options.find(x=>MediaRecorder.isTypeSupported?.(x)) || '';
}
function resetVoiceUI(clearDraft = false) {
  try { speechRec?.abort(); } catch (_) {}
  try { mediaRec?.stop(); } catch (_) {}
  mediaStream?.getTracks().forEach(t=>t.stop());
  micActive=false; audioChunks=[]; recordedBlob=null; liveFinal=''; recordingStartedAt=0; __lastVoiceRetryToken=''; __voiceRequestId=''; if(clearDraft){try{sessionStorage.removeItem(VOICE_DRAFT_KEY);}catch(_){}}
  clearInterval(timerHandle); timerHandle=null;
  if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl); lastObjectUrl=null;
  if (voicePlayback) { voicePlayback.pause(); voicePlayback.removeAttribute('src'); voicePlayback.load(); voicePlayback.classList.add('hidden'); }
  voice?.classList.remove('hidden'); voiceStop?.classList.add('hidden'); voiceTools?.classList.add('hidden');
  if ($('recordingStatus')) $('recordingStatus').textContent='Recording ready';
  if ($('recordingTimer')) $('recordingTimer').textContent='00:00';
  if ($('liveTranscript')) { $('liveTranscript').value='Nothing recorded yet.'; $('liveTranscript').textContent='Nothing recorded yet.'; }
  if ($('aiTranslation')) { $('aiTranslation').value='Waiting for recording.'; $('aiTranslation').textContent='Waiting for recording.'; }
  if (voiceAi) voiceAi.disabled=true;
}
async function startMic() {
  if (micActive) return;
  if (!window.isSecureContext && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') { voiceStatus('Microphone access needs a secure connection (HTTPS). Open this page over HTTPS and try again.', 'error'); return; }
  if (!navigator.mediaDevices?.getUserMedia) { voiceStatus('Microphone access is not available in this browser. Try a current Chrome or Edge browser and allow microphone access.', 'error'); return; }
  if (!window.MediaRecorder) { voiceStatus('Audio recording is not supported by this browser. Use current Chrome or Edge.', 'error'); return; }
  try {
    if (navigator.permissions?.query) { try { const perm = await navigator.permissions.query({name:'microphone'}); if (perm.state === 'denied') { voiceStatus('Microphone permission is blocked. Click the lock/site-settings icon in Chrome/Edge, allow Microphone, then reload.', 'error'); return; } } catch (_) {} }
    voiceStatus('Requesting microphone permission…');
    mediaStream = await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
    audioChunks=[]; recordedBlob=null; liveFinal=''; voiceBaseSymptoms=$('symptoms')?.value?.trim() || '';
    const mime = supportedMime();
    const recOptions = mime ? {mimeType:mime, audioBitsPerSecond: 64000} : {audioBitsPerSecond: 64000};
    mediaRec = new MediaRecorder(mediaStream, recOptions);
    voiceStatus('Microphone connected. Recording can start now.', 'ok');
    mediaRec.ondataavailable = e => { if (e.data?.size) audioChunks.push(e.data); };
    mediaRec.onerror = e => { console.error(e); $('recordingStatus').textContent='Recording error'; voiceStatus('Recording failed. Check microphone permission and browser site settings.', 'error'); };
    mediaRec.onstop = () => {
      const type = mediaRec.mimeType || mime || 'audio/webm';
      recordedBlob = new Blob(audioChunks, {type});
      if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
      lastObjectUrl = URL.createObjectURL(recordedBlob);
      voicePlayback.src = lastObjectUrl; voicePlayback.load(); voicePlayback.classList.remove('hidden');
      mediaStream?.getTracks().forEach(t=>t.stop()); mediaStream=null;
      $('recordingStatus').textContent = recordedBlob.size ? 'Recording ready — press Play or AI transcribe' : 'No audio captured'; voiceStatus(recordedBlob.size ? 'Recording captured successfully. You can play it or send it to Gemini.' : 'No audio captured.', recordedBlob.size ? 'ok' : 'error');
      if (voiceAi) voiceAi.disabled = !recordedBlob.size;
    };
    mediaRec.start(500);
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      speechRec = new SR(); speechRec.lang=$('voiceSourceLanguage').value; speechRec.interimResults=true; speechRec.continuous=true;
      speechRec.onresult = e => { let interim=''; for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript.trim(); if(e.results[i].isFinal && t) liveFinal += (liveFinal?' ':'')+t; else interim += (interim?' ':'')+t;} const shown=(liveFinal+' '+interim).trim() || 'Listening…'; $('liveTranscript').value=shown; $('liveTranscript').textContent=shown; if(liveFinal) cacheVoiceDraft(liveFinal, ''); }; 
      speechRec.onerror = e => { if(e.error!=='aborted' && e.error!=='no-speech') { $('liveTranscript').value='Live browser transcript unavailable; recording continues.'; $('liveTranscript').textContent='Live browser transcript unavailable; recording continues.'; } };
      speechRec.onend = () => { if(micActive){ try{speechRec.start();}catch(_){ } } };
      try { speechRec.start(); } catch (_) {}
    } else { $('liveTranscript').value='Live browser transcription is not supported here. The recording can still be sent to Gemini.'; $('liveTranscript').textContent='Live browser transcription is not supported here. The recording can still be sent to Gemini.'; }
    micActive=true; voice.classList.add('hidden'); voiceStop.classList.remove('hidden'); voiceTools.classList.remove('hidden');
    $('recordingStatus').textContent='Recording…'; voiceStatus('Recording… speak now. Click Stop when finished. Your browser transcript will be kept even if Gemini is busy.', 'ok'); recordingStartedAt=Date.now(); timerHandle=setInterval(setTimer,500);
    if (voiceAi) voiceAi.disabled=true;
  } catch (e) {
    console.error(e);
    mediaStream?.getTracks().forEach(t=>t.stop());
    const message = e?.name === 'NotAllowedError' || e?.name === 'SecurityError'
      ? 'Microphone permission is not available. Allow microphone access for this site, then try again.'
      : e?.name === 'NotFoundError'
        ? 'No microphone was found on this device. Connect or enable a microphone and try again.'
        : 'Microphone could not start. Check the microphone and browser permissions, then try again.';
    voiceStatus(message, 'error');
  }
}
function stopMic() {
  if (!micActive) return;
  micActive=false; clearInterval(timerHandle); timerHandle=null; setTimer();
  try { speechRec?.stop(); } catch (_) {};
  try { if(mediaRec && mediaRec.state !== 'inactive') mediaRec.stop(); } catch (_) {}
  voice.classList.remove('hidden'); voiceStop.classList.add('hidden'); $('recordingStatus').textContent='Finalizing recording…'; voiceStatus('Finalizing recording…', 'ok');
  if (liveFinal) $('symptoms').value = (voiceBaseSymptoms ? voiceBaseSymptoms+'\n' : '') + liveFinal;
}
voice?.addEventListener('click', startMic); voiceStop?.addEventListener('click', stopMic);
$('voiceSourceLanguage')?.addEventListener('change', e => { if (speechRec && micActive) { try{speechRec.stop();}catch(_){} setTimeout(()=>{if(micActive){speechRec.lang=e.target.value;try{speechRec.start();}catch(_){}}},150); } });
let __lastVoiceRetryToken = '';
let __voiceInFlight = false;
let __voiceRequestId = '';
voiceAi?.addEventListener('click', async () => {
  if (__voiceInFlight) return;
  if (!recordedBlob) { voiceStatus('Stop the recording first, then choose AI transcribe + translate.', 'error'); $('voiceAiStatus')?.replaceChildren(); return; }
  if (!$('externalAiAudioConsent')?.checked) { voiceStatus('Privacy Gate: raw audio was not sent to Gemini. Review the audio privacy note and opt in only for synthetic/public or otherwise authorized audio.', 'error'); const st=$('voiceAiStatus'); if(st) st.textContent='No external AI request was made. You can still use the browser transcript locally.'; return; }
  if (!__lastVoiceRetryToken) __voiceRequestId = newAiRequestId();
  __voiceInFlight = true;
  const btn=voiceAi; setBusy(btn,true,'AI processing…'); $('aiTranslation').value='AI is transcribing and translating…'; $('aiTranslation').textContent='AI is transcribing and translating…';
  const ext = recordedBlob.type.includes('mp4') ? 'mp4' : recordedBlob.type.includes('ogg') ? 'ogg' : recordedBlob.type.includes('wav') ? 'wav' : 'webm'; const fd=new FormData(); fd.append('audio',recordedBlob,'patient-voice.'+ext); fd.append('_ai_request_id',__voiceRequestId); fd.append('source_language',$('voiceSourceLanguage').value); fd.append('target_language',$('voiceTargetLanguage').value); fd.append('browser_transcript',liveFinal || $('liveTranscript').value || $('liveTranscript').textContent || ''); fd.append('external_ai_audio_consent',$('externalAiAudioConsent')?.checked ? 'on' : ''); fd.append('csrf_token',csrfToken); if(__lastVoiceRetryToken) fd.append('_ai_retry_token',__lastVoiceRetryToken);
  try { const x=await jsonFetch('/api/voice',{method:'POST',body:fd}); if(x.transcript){$('liveTranscript').value=x.transcript; $('liveTranscript').textContent=x.transcript; $('symptoms').value=(voiceBaseSymptoms ? voiceBaseSymptoms+'\n' : '')+x.transcript; liveFinal=x.transcript;} const translation=x.translation || x.warning || 'No translation returned.'; $('aiTranslation').value=translation; $('aiTranslation').textContent=translation; cacheVoiceDraft(liveFinal || '', x.translation || ''); __lastVoiceRetryToken=''; $('voiceAiStatus')?.replaceChildren(); $('voiceAiStatus') && ($('voiceAiStatus').textContent='AI transcription and translation completed.'); } catch(e){ const canRetry=Boolean(e.data?.retryable&&e.data?.retry_token); if(canRetry)__lastVoiceRetryToken=e.data.retry_token; $('aiTranslation').value = friendlyError(e,'Voice processing could not be completed.'); $('aiTranslation').textContent = friendlyError(e,'Voice processing could not be completed.'); const status=$('voiceAiStatus'); if(status){ status.replaceChildren(); const msg=document.createElement('span'); msg.textContent=friendlyError(e,'Voice processing could not be completed.'); status.appendChild(msg); if(canRetry){ const retryBtn=document.createElement('button'); retryBtn.type='button'; retryBtn.className='secondary compact retry-btn'; retryBtn.textContent='↻ Retry same recording'; retryBtn.addEventListener('click',()=>voiceAi.click(),{once:true}); status.appendChild(retryBtn); const note=document.createElement('small'); note.textContent='One retry is available for this recording.'; status.appendChild(note); } else { const note=document.createElement('small'); note.textContent='No further retry is available. Record a new input.'; status.appendChild(note); } } }
  finally { __voiceInFlight = false; setBusy(btn,false); }
});

$('useTranscript')?.addEventListener('click',()=>{const t=($('liveTranscript')?.value || $('liveTranscript')?.textContent || '').trim();if(t&&t!=='Nothing recorded yet.'){$('symptoms').value=(voiceBaseSymptoms?voiceBaseSymptoms+'\n':'')+t;}});
$('useTranslation')?.addEventListener('click',()=>{const t=($('aiTranslation')?.value || $('aiTranslation')?.textContent || '').trim();if(t&&t!=='Waiting for recording.'&&!t.startsWith('AI processing')&&!t.startsWith('AI is')){$('symptoms').value=(voiceBaseSymptoms?voiceBaseSymptoms+'\n':'')+t;}});

// Report upload previews
function bindFilePreview(input, preview, removeBtn) {
  if (!input || !preview) return {clear:()=>{}};
  let objectUrl = null;
  const clear = () => {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = null; input.value=''; preview.innerHTML='<span class="muted">No report selected.</span>'; removeBtn?.classList.add('hidden');
  };
  input.addEventListener('change', () => {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl=null; preview.innerHTML=''; const f=input.files?.[0];
    if (!f) { clear(); return; }
    const valid=['image/png','image/jpeg','application/pdf'];
    const type=f.type || (/\.pdf$/i.test(f.name)?'application/pdf':(/\.jpe?g$/i.test(f.name)?'image/jpeg':(/\.png$/i.test(f.name)?'image/png':'')));
    const sizeMb=(f.size/1024/1024).toFixed(2);
    if (!valid.includes(type)) { preview.innerHTML=`<div class="error-card"><b>Unsupported file</b><span>${esc(f.name)} is not PNG, JPG/JPEG or PDF.</span></div>`; input.value=''; removeBtn?.classList.add('hidden'); return; }
    if (f.size > 3*1024*1024) { preview.innerHTML=`<div class="error-card"><b>File too large</b><span>${esc(f.name)} is ${sizeMb} MB. Maximum is 3 MB.</span></div>`; input.value=''; removeBtn?.classList.add('hidden'); return; }
    if (type==='application/pdf') preview.innerHTML=`<div class="file-preview"><b>📄 ${esc(f.name)}</b><small>${sizeMb} MB · PDF selected and ready to analyze.</small></div>`;
    else { objectUrl=URL.createObjectURL(f); const img=document.createElement('img'); img.src=objectUrl; img.alt='Selected report preview'; img.loading='lazy'; img.addEventListener('error',()=>{preview.innerHTML='<div class="error-card"><b>Preview failed</b><span>The image could not be previewed. Choose another file.</span></div>';}); preview.appendChild(img); preview.insertAdjacentHTML('beforeend',`<div class="file-preview"><b>${esc(f.name)}</b><small>${sizeMb} MB · Image selected and ready to analyze.</small></div>`); }
    removeBtn?.classList.remove('hidden');
  });
  removeBtn?.addEventListener('click', clear);
  return {clear};
}

const triageUpload = bindFilePreview($('triageFile'), $('triagePreview'), $('removeTriageFile'));
const ocrUpload = bindFilePreview($('ocrFile'), $('preview'), $('ocrRemove'));
$('changeTriageFile')?.addEventListener('click', () => { const input=$('triageFile'); if(input){input.value=''; input.click();} });
$('changeOcrFile')?.addEventListener('click', () => { const input=$('ocrFile'); if(input){input.value=''; input.click();} });

// Standalone multimodal report workflow: this now supplies all required patient fields and creates a real queue case.
let __lastOcrPayload = null;
let __lastOcrRetryToken = '';
let __ocrInFlight = false;
let __ocrRequestId = '';
$('ocrForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  if (__ocrInFlight) return;
  __ocrInFlight = true;
  const form=e.currentTarget, btn=form.querySelector('button[type="submit"]'), out=$('ocrResult');
  if (form.elements.report_image?.files?.length && !form.elements.external_ai_media_consent?.checked) { out.classList.remove('hidden'); out.innerHTML='<div class="error-card"><b>Privacy Gate</b><span>Nothing was sent to Gemini. Review the file, then explicitly opt in under External AI file gate to continue. The original file is not automatically masked.</span></div>'; __ocrInFlight=false; return; }
  setBusy(btn,true,'Analyzing report…'); out.classList.remove('hidden'); out.innerHTML='<div class="loading-card"><b>Gemini is reviewing the report…</b><span>One failed AI request stops processing. No automatic retries or fallback models are used.</span></div>';
  const ref=form.elements.patient_ref; if(ref && !ref.value) ref.value='OCR-'+Math.random().toString(36).slice(2,8).toUpperCase();
  const retry = Boolean(__lastOcrRetryToken);
  if (!retry) __ocrRequestId = newAiRequestId();
  const payload = retry && __lastOcrPayload ? cloneFormData(__lastOcrPayload) : new FormData(form);
  payload.set('_ai_request_id', __ocrRequestId);
  if (retry) payload.set('_ai_retry_token', __lastOcrRetryToken);
  else { __lastOcrPayload = cloneFormData(payload); __lastOcrRetryToken = ''; }
  try { const x=await jsonFetch('/api/triage',{method:'POST',body:payload}); renderNote(x.note,x.warning,out); ocrUpload.clear(); form.reset(); __lastOcrPayload=null; __lastOcrRetryToken=''; await loadDashboard(); } catch(err){ const canRetry=Boolean(err.data?.retryable&&err.data?.retry_token); if(canRetry)__lastOcrRetryToken=err.data.retry_token; const detected = err.data?.code === 'PATIENT_NAME_MISMATCH' && err.data?.report_patient_name ? `<div class="metric"><b>Verification status:</b> NOT VERIFIED</div><div class="metric"><b>Detected report name:</b> ${esc(err.data.report_patient_name)}</div>` : `<div class="metric"><b>Verification status:</b> NOT VERIFIED</div>`; out.innerHTML=`<div class="error-card"><b>Report verification stopped</b>${detected}<span>${esc(friendlyError(err))}</span>${canRetry?'<button type="button" id="retryOcrBtn" class="secondary compact retry-btn">↻ Retry same report</button><small>This is the one allowed retry for this report.</small>':'<small>No extraction or triage output was exposed. Start a new report submission.</small>'}</div>`; if(canRetry)$('retryOcrBtn')?.addEventListener('click',()=>form.requestSubmit(),{once:true}); }
  finally { __ocrInFlight = false; setBusy(btn,false); }
});
async function checkGemini(){try{const x=await jsonFetch('/api/ocr'); $('geminiBadge').textContent=x.enabled?'● Gemini connected':'○ Gemini unavailable — add GEMINI_API_KEY';}catch(e){$('geminiBadge').textContent='○ AI status unavailable';}}
let __diagnosticInFlight = false;
async function testGeminiConnection(){
  if(__diagnosticInFlight) return; __diagnosticInFlight=true;
  const badge=$('geminiBadge');
  if(!badge) return;
  const original=badge.textContent; badge.textContent='Testing Gemini…';
  try{
    const fd=new URLSearchParams({csrf_token:csrfToken,_ai_request_id:newAiRequestId()});
    const x=await jsonFetch('/api/diagnostics/gemini',{method:'POST',body:fd});
    badge.textContent=x.ok?'● Gemini test passed':'○ Gemini unavailable';
    badge.title=x.message||x.error||'';
    if(!x.ok && x.error) { const box=$('clientError'); if(box){box.textContent=x.error;box.classList.remove('hidden');} }
  }catch(e){ badge.textContent=original; const box=$('clientError'); if(box){box.textContent=friendlyError(e);box.classList.remove('hidden');} } finally { __diagnosticInFlight=false; }
}
$('geminiBadge')?.addEventListener('click',testGeminiConnection);
$('geminiBadge')?.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();testGeminiConnection();}});


// Analytics
async function loadAnalytics(){try{const box=$('analyticsError'); if(box) box.classList.add('hidden'); const a=await jsonFetch('/api/analytics'); $('aTotal').textContent=a.total; $('aUrgent').textContent=a.urgent; $('aReviewed').textContent=a.reviewed; $('aRate').textContent=a.review_rate+'%'; bars('#riskBars',a.risks); bars('#langBars',a.languages); bars('#statusBars',a.statuses);}catch(e){console.error(e); const box=$('analyticsError'); if(box){box.textContent=friendlyError(e,'Analytics are temporarily unavailable.');box.classList.remove('hidden');}}}
function bars(sel,obj){const el=qs(sel);if(!el)return;const vals=Object.entries(obj||{}),max=Math.max(1,...vals.map(x=>x[1]));el.innerHTML=vals.length?vals.map(([k,v])=>{const pct=Math.round((v/max)*100);const bucket=Math.min(100,Math.max(0,Math.round(pct/10)*10));return `<div class="bar"><div class="bar-head"><span>${esc(k)}</span><b>${v}</b></div><div class="bar-track"><div class="bar-fill w-${bucket}"></div></div></div>`}).join(''):'<p class="empty">No data yet.</p>';}

// Safety confirmation for admin destructive actions.
document.addEventListener('submit',e=>{const f=e.target.closest('form[data-confirm]');if(f&&!confirm(f.dataset.confirm))e.preventDefault();});

setupMobileNavigation();
resetVoiceUI(false);
restoreTriageDraft();
restoreVoiceDraft();
loadDashboard();

window.__swastyaResetVoice = () => resetVoiceUI(true); clearTriageDraft();
window.__swastyaLoadDashboard = loadDashboard;
window.__swastyaAppReady = true;
window.addEventListener('error', e => {
  console.error('Swastya Assist interface error:', e.error || e.message);
  const box = document.getElementById('clientError');
  if (box) { box.hidden = false; box.textContent = 'Something went wrong in the interface. Please refresh the page and try again.'; }
});
window.addEventListener('unhandledrejection', e => console.error('Swastya Assist async error:', e.reason));


// Case Readiness Passport: local synthetic-data showcase only.
// This module intentionally makes no API calls, does not use storage, and does not sync.
function initReadinessPassport() {
  const $rp = id => document.getElementById(id);
  const ids = ['rpCaseRef','rpSymptoms','rpOnset','rpLanguage','rpReport','rpTranscript','rpConsent','rpOffline'];
  if (!$rp('rpBuild')) return;

  let demoQueue = 0;
  let currentPayload = {};
  const initialValues = {
    rpCaseRef: 'DEMO-PS03-01',
    rpSymptoms: 'Fever and headache began yesterday evening. The patient reports fatigue today.',
    rpOnset: 'Yesterday evening',
    rpLanguage: 'English',
    rpReport: true,
    rpTranscript: true,
    rpConsent: false,
    rpOffline: false
  };

  // Best-effort display sanitization for a teaching preview, not a production privacy gate.
  const minimizeText = value => String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[REDACTED_EMAIL]')
    .replace(/\b(?:\+?91[\s.-]?)?[6-9]\d{9}\b/g, '[REDACTED_PHONE]')
    .replace(/\b\d{12}\b/g, '[REDACTED_POSSIBLE_ID]')
    .replace(/\b((?:patient\s+)?(?:name|phone|mobile|address|aadhaar|aadhar|patient\s*id))\s*[:=]\s*[^,;\n]+/gi, '$1: [REDACTED]')
    .replace(/[ \t]{2,}/g, ' ')
    .trim()
    .slice(0, 800);

  const checklist = () => [
    ['Narrative captured', ($rp('rpSymptoms').value || '').trim().length >= 25, 'Add a short symptom description.'],
    ['Timeline described', ($rp('rpOnset').value || '').trim().length > 0, 'Add when the symptoms began.'],
    ['Language selected', ($rp('rpLanguage').value || '').trim().length > 0, 'Select the preferred language.'],
    ['Supporting input indicated', $rp('rpReport').checked || $rp('rpTranscript').checked, 'Mark a report or confirmed transcript if available.'],
    ['Consent represented', $rp('rpConsent').checked, 'Do not prepare the narrative preview unless consent is represented.']
  ];

  const makePayload = checks => {
    const validConsent = $rp('rpConsent').checked;
    // Restrict exported identifiers to the demo-label pattern; reject arbitrary strings.
    const enteredRef = String($rp('rpCaseRef').value || '').trim();
    const safeRef = /^DEMO-PS03-[A-Z0-9_-]{1,12}$/i.test(enteredRef) ? enteredRef.toUpperCase() : 'DEMO-PS03-01';
    return {
      mode: 'LOCAL_DEMO_PREVIEW_ONLY',
      demo_case_reference: safeRef,
      preferred_language: $rp('rpLanguage').value,
      timeline_preview: minimizeText($rp('rpOnset').value),
      minimized_narrative_preview: validConsent ? minimizeText($rp('rpSymptoms').value) : '[HIDDEN UNTIL CONSENT IS REPRESENTED]',
      report_available_demo_flag: $rp('rpReport').checked,
      confirmed_transcript_demo_flag: $rp('rpTranscript').checked,
      missing_intake_items: checks.filter(x => !x[1]).map(x => x[0]),
      completeness_percent: Math.round(checks.filter(x => x[1]).length / checks.length * 100),
      simulated_network_state: $rp('rpOffline').checked ? 'OFFLINE_DEMO' : 'ONLINE_DEMO',
      demo_queue_count_in_memory: demoQueue,
      will_call_gemini: false,
      will_persist_to_database: false,
      will_sync_to_server: false,
      clinical_priority_generated: false,
      note: 'Illustrative synthetic-data preview only. Best-effort redaction is not a guarantee of anonymization.'
    };
  };

  const update = () => {
    const checks = checklist();
    const complete = checks.filter(x => x[1]).length;
    const score = Math.round(complete / checks.length * 100);
    $rp('rpScore').textContent = score + '%';
    $rp('rpMeter').style.width = score + '%';
    $rp('rpCompleted').textContent = `${complete} of ${checks.length} checklist items complete`;
    $rp('rpChecklist').innerHTML = checks.map(([label, ok, help]) => `<div class="rp-check-row ${ok ? 'done' : 'missing'}"><span>${ok ? '✓' : '!'}</span><div><b>${label}</b><small>${ok ? 'Captured for the synthetic demo' : help}</small></div><em>${ok ? 'COMPLETE' : 'MISSING'}</em></div>`).join('');
    currentPayload = makePayload(checks);
    $rp('rpPayload').textContent = JSON.stringify(currentPayload, null, 2);
    const offline = $rp('rpOffline').checked;
    const consent = $rp('rpConsent').checked;
    $rp('rpNetworkState').className = 'rp-network ' + (offline ? 'offline' : 'online');
    $rp('rpNetworkState').textContent = offline ? '● OFFLINE SIMULATION' : '● DEMO ONLINE';
    $rp('rpQueue').textContent = demoQueue ? `Demo queue (${demoQueue})` : 'Add simulated item';
    $rp('rpQueue').disabled = !offline || !consent || demoQueue >= 99;
    $rp('rpReconnect').disabled = !offline;
    $rp('rpExport').disabled = !consent;
    $rp('rpCopy').disabled = !consent;
    if (!consent) {
      $rp('rpStatus').textContent = 'Consent is not represented. The narrative stays hidden and queue/export actions are disabled.';
    } else if (offline) {
      $rp('rpStatus').textContent = demoQueue ? `${demoQueue} synthetic item(s) in this page’s in-memory demo queue. AI remains pending; no sync or AI call occurs.` : 'Offline simulation active. Queue a synthetic demo item; no AI result will be generated offline.';
    } else {
      $rp('rpStatus').textContent = 'Demo online state. This page still makes no API request and stores no case; use Patient Intake for the existing application workflow.';
    }
  };

  ids.forEach(id => $rp(id)?.addEventListener('input', update));
  ids.forEach(id => $rp(id)?.addEventListener('change', update));
  $rp('rpBuild')?.addEventListener('click', update);
  $rp('rpQueue')?.addEventListener('click', () => {
    if (!$rp('rpOffline').checked) { $rp('rpStatus').textContent = 'Turn on offline simulation before using the demo queue.'; return; }
    if (!$rp('rpConsent').checked) { $rp('rpStatus').textContent = 'Consent is not represented; queueing is disabled.'; return; }
    if (demoQueue >= 99) { $rp('rpStatus').textContent = 'Demo queue limit reached. Reset the demo to start again.'; return; }
    demoQueue += 1;
    update();
    $rp('rpStatus').textContent = `Synthetic demo item queued in page memory (${demoQueue}). No disk write, sync or AI request occurs.`;
  });
  $rp('rpReconnect')?.addEventListener('click', () => {
    $rp('rpOffline').checked = false;
    update();
    $rp('rpStatus').textContent = demoQueue ? `Connectivity restored in the simulation. ${demoQueue} demo item(s) remain as preview-only records; no real sync or AI call was performed.` : 'Connectivity restored in the simulation. No AI request or network sync was performed.';
  });
  $rp('rpReviewer')?.addEventListener('click', () => {
    const ready = checklist().every(x => x[1]);
    $rp('rpReviewerState').textContent = ready ? 'Ready for reviewer preview · demo only' : 'Not ready · complete missing checklist fields first';
    $rp('rpReviewerState').className = 'rp-review-state ' + (ready ? 'good' : 'warn');
  });
  $rp('rpCopy')?.addEventListener('click', async () => {
    if (!$rp('rpConsent').checked) { $rp('rpStatus').textContent = 'Consent is not represented; export is disabled.'; return; }
    const content = JSON.stringify(currentPayload, null, 2);
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(content);
      } else {
        const temp = document.createElement('textarea');
        temp.value = content; temp.setAttribute('readonly', '');
        temp.style.position = 'fixed'; temp.style.opacity = '0';
        document.body.appendChild(temp); temp.select();
        const copied = document.execCommand('copy'); temp.remove();
        if (!copied) throw new Error('Copy unavailable');
      }
      $rp('rpStatus').textContent = 'Illustrative privacy preview copied. It was not sent to a server or AI service.';
    } catch (_) {
      $rp('rpStatus').textContent = 'Could not copy automatically. Select the JSON above and copy it manually.';
    }
  });
  $rp('rpExport')?.addEventListener('click', () => {
    if (!$rp('rpConsent').checked) { $rp('rpStatus').textContent = 'Consent is not represented; export is disabled.'; return; }
    const blob = new Blob([JSON.stringify(currentPayload, null, 2)], {type: 'application/json;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${currentPayload.demo_case_reference || 'DEMO-PS03'}-preview-only.json`;
    document.body.appendChild(anchor); anchor.click(); anchor.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    $rp('rpStatus').textContent = 'Preview-only JSON downloaded locally. No server request or AI processing occurred.';
  });
  $rp('rpClear')?.addEventListener('click', () => {
    Object.entries(initialValues).forEach(([id, value]) => {
      const el = $rp(id); if (!el) return;
      if (el.type === 'checkbox') el.checked = value;
      else el.value = value;
    });
    demoQueue = 0;
    $rp('rpReviewerState').textContent = 'Not marked';
    $rp('rpReviewerState').className = 'rp-review-state';
    update();
    $rp('rpStatus').textContent = 'Demo reset to synthetic sample values. Nothing was stored or synced.';
  });
  update();
}
document.addEventListener('DOMContentLoaded', initReadinessPassport);
