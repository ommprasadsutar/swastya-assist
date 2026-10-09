(function(){
  'use strict';
  function byId(id){return document.getElementById(id)}
  function esc(v){return String(v ?? '').replace(/[&<>\'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
  function showError(message){
    var box=byId('clientError');
    if(!box){box=document.createElement('div');box.id='clientError';box.setAttribute('role','alert');document.body.appendChild(box)}
    box.hidden=false;box.textContent=message||'Interface error. Please refresh the page.';
  }
  function setBusy(btn,busy){if(!btn)return;btn.disabled=busy;btn.dataset.bootBusy=busy?'1':'0';if(busy){btn.dataset.bootLabel=btn.innerHTML;btn.innerHTML='Processing…'}else if(btn.dataset.bootLabel){btn.innerHTML=btn.dataset.bootLabel}}
  function showResult(id,data){
    var out=byId(id);if(!out)return;
    out.classList.remove('hidden');
    var n=data.note||{};
    var items=a=>Array.isArray(a)?a:[];
    out.innerHTML='<div class="success-banner"><b>Encounter added to review queue</b><span>Reference: '+esc(data.patient?.reference||data.id||'created')+'</span></div>'+
      '<div class="metric"><b>Risk:</b> '+esc(n.risk_category||'Needs review')+'</div>'+ 
      '<h3>Structured summary</h3><p>'+esc(n.summary||'AI summary not returned. Verify the case in the reviewer queue.')+'</p>'+
      '<h3>Missing information</h3><ul>'+items(n.missing_information).map(x=>'<li>'+esc(typeof x==='object'?JSON.stringify(x):x)+'</li>').join('')+'</ul>'+
      (data.warning?'<p class="muted">'+esc(data.warning)+'</p>':'');
  }
  // Forms are owned by app.js. Keeping submission logic in one place prevents
  // capture-phase handlers from cancelling the richer dashboard/OCR workflow.
  function ready(){
    document.documentElement.dataset.swastyaBoot='ok';
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(function(){});
    // Navigation is owned by app.js to keep one authoritative view controller.
    window.addEventListener('error',function(){if(!window.__swastyaAppReady)showError('Something went wrong in the console. Please refresh and try again.')});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
})();
