document.addEventListener('DOMContentLoaded', () => {
  const roles = document.querySelectorAll('.role-card');
  const hint = document.getElementById('roleHint');
  const user = document.getElementById('username');
  const selected = document.getElementById('selectedRole');
  const toggle = document.getElementById('togglePassword');
  const initial = selected?.value || 'clinical';
  roles.forEach(card => {
    const active = card.dataset.role === initial;
    card.classList.toggle('active', active);
  });
  function setRole(role) {
    const admin = role === 'admin';
    roles.forEach(card => card.classList.toggle('active', card.dataset.role === role));
    if (selected) selected.value = role;
    if (hint) hint.innerHTML = admin
      ? '<b>Administrator workspace</b><span>Authorized admins are routed to the Admin Dashboard.</span>'
      : '<b>Clinical workspace</b><span>Doctors and reviewers are routed to the clinical console.</span>';
    if (user) user.placeholder = admin ? 'Enter administrator username' : 'Enter doctor/reviewer username';
  }
  roles.forEach(card => card.addEventListener('click', () => setRole(card.dataset.role)));
  toggle?.addEventListener('click', () => {
    const p = document.getElementById('password');
    if (!p) return;
    p.type = p.type === 'password' ? 'text' : 'password';
    toggle.textContent = p.type === 'password' ? 'Show' : 'Hide';
  });
});
