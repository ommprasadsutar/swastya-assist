document.addEventListener('DOMContentLoaded', () => {
  const links = [...document.querySelectorAll('.ref-menu a[data-section]')];
  const targets = links.map(a => document.getElementById(a.dataset.section)).filter(Boolean);
  const activate = id => links.forEach(a => a.classList.toggle('active', a.dataset.section === id));
  links.forEach(a => a.addEventListener('click', e => {
    const target = document.getElementById(a.dataset.section);
    if (!target) return;
    e.preventDefault();
    activate(a.dataset.section);
    history.replaceState(null, '', '#' + a.dataset.section);
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }));
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      const visible = entries.filter(e => e.isIntersecting).sort((a,b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) activate(visible.target.id);
    }, { rootMargin: '-20% 0px -65% 0px', threshold: [0, .25, .5] });
    targets.forEach(t => observer.observe(t));
  }
  const initial = location.hash.slice(1);
  if (initial && document.getElementById(initial)) setTimeout(() => document.getElementById(initial).scrollIntoView({behavior:'smooth'}), 50);
});
