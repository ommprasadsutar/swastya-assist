document.addEventListener('DOMContentLoaded', () => {
  const roles = document.querySelectorAll('.role-card');
  const hint = document.getElementById('roleHint');
  const user = document.getElementById('username');
  const selected = document.getElementById('selectedRole');
  const toggle = document.getElementById('togglePassword');
  const configs = {
    clinical: {title:'Clinical workspace', copy:'Authorized clinical team members are routed to the Clinical Console.', placeholder:'Enter clinical team username'},
    patient: {title:'Patient self-entry', copy:'Patient accounts can submit their own information and view submission status.', placeholder:'Enter patient username'},
    admin: {title:'Administrator workspace', copy:'Authorized administrators are routed to the Admin Dashboard.', placeholder:'Enter administrator username'}
  };
  const initial = selected?.value || 'clinical';
  function setRole(role) {
    const cfg = configs[role] || configs.clinical;
    roles.forEach(card => card.classList.toggle('active', card.dataset.role === role));
    if (selected) selected.value = role;
    if (hint) hint.innerHTML = `<b>${cfg.title}</b><span>${cfg.copy}</span>`;
    if (user) user.placeholder = cfg.placeholder;
  }
  setRole(initial);
  roles.forEach(card => card.addEventListener('click', () => setRole(card.dataset.role)));
  const form = document.querySelector('.login-form');
  form?.addEventListener('submit', () => {
    const submit = form.querySelector('.login-submit');
    if (!submit || submit.dataset.submitting === '1') return;
    submit.dataset.submitting = '1';
    submit.disabled = true;
    submit.setAttribute('aria-busy','true');
    submit.innerHTML = 'Signing in…';
  }, {once:false});
  toggle?.addEventListener('click', () => {
    const p = document.getElementById('password');
    if (!p) return;
    p.type = p.type === 'password' ? 'text' : 'password';
    toggle.textContent = p.type === 'password' ? 'Show' : 'Hide';
    toggle.setAttribute('aria-label', p.type === 'password' ? 'Show password' : 'Hide password');
  });
});
