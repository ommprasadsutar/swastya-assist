(() => {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const $ = (id) => document.getElementById(id);
  const esc = (v) => String(v ?? '').replace(/[&<>\'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  async function loadSystem(){
    try{
      const r = await fetch('/api/admin/system', {headers:{'X-CSRF-Token':csrf,'X-Requested-With':'XMLHttpRequest'}});
      const d = await r.json();
      if(!r.ok) throw new Error(d.error || 'System status unavailable');
      const c=d.checks||{};
      $('adminSystemBadge').textContent=d.ok?'Healthy':'Action needed';
      $('adminSystemBadge').className='admin-pill '+(d.ok?'status-ok':'status-warn');
      $('adminDbStatus').textContent=c.database?'Healthy':'Unavailable';
      $('adminSecurityStatus').textContent=(c.secret&&c.encryption&&c.secure_cookie)?'Healthy':'Review config';
      $('adminAiStatus').textContent=d.ai_enabled?'Configured':'Not configured';
      $('adminRateStatus').textContent=c.rate_limit_store?'Distributed':'Memory fallback'; if($('adminSecurityEvents')) $('adminSecurityEvents').textContent=String(d.security_events_24h ?? '—'); if($('adminFailedLogins')) $('adminFailedLogins').textContent=String(d.failed_logins_24h ?? '—');
    }catch(e){$('adminSystemBadge').textContent='Unavailable';$('adminSystemBadge').className='admin-pill status-warn';['adminDbStatus','adminSecurityStatus','adminAiStatus','adminRateStatus'].forEach(id=>{if($(id))$(id).textContent='—';});}
  }
  async function loadAudit(){
    const status=$('auditStatus'), body=document.querySelector('#auditTable tbody'); if(!status||!body)return;
    status.textContent='Loading audit events…';
    const action=($('auditActionFilter')?.value||'').trim();
    try{
      const r=await fetch('/api/admin/audit?limit=100&action='+encodeURIComponent(action),{headers:{'X-Requested-With':'XMLHttpRequest'}});
      const d=await r.json(); if(!r.ok) throw new Error(d.error||'Audit history unavailable');
      body.innerHTML=(d.events||[]).map(e=>`<tr><td>${esc((e.created_at||'').slice(0,19).replace('T',' '))}</td><td><span class="admin-pill">${esc(e.action)}</span></td><td>${esc(e.case_id?e.case_id.slice(0,8):'—')}</td><td>${esc(e.user_id?e.user_id.slice(0,8):'system')}</td><td><code class="audit-meta">${esc(JSON.stringify(e.metadata||{}))}</code></td></tr>`).join('')||'<tr><td colspan="5" class="muted">No audit events match this filter.</td></tr>';
      status.textContent=`Showing ${(d.events||[]).length} event(s).`;
    }catch(e){status.textContent='Audit history is temporarily unavailable.';body.innerHTML='<tr><td colspan="5" class="muted">Unable to load audit events.</td></tr>';}
  }
  $('auditRefresh')?.addEventListener('click',loadAudit);
  $('auditActionFilter')?.addEventListener('keydown',e=>{if(e.key==='Enter')loadAudit();});
  loadSystem(); loadAudit();
})();
