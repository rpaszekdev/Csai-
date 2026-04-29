// Mobile hamburger drawer for lesson*.html pages.
// Injects a hamburger button into the topbar and a drawer that contains
// the lesson navigation + (optionally) a copy of the TOC items, so a single
// affordance covers both menus on small screens.
(() => {
  const header = document.querySelector('header.topbar');
  if (!header) return;

  const lessonNav = header.querySelector('.lesson-nav');
  const tocBtn = header.querySelector('#toc-btn');
  const tocEl = document.getElementById('toc');

  // Hamburger button — sits in the topbar, only visible on mobile via CSS.
  const burger = document.createElement('button');
  burger.className = 'nav-burger';
  burger.id = 'nav-burger';
  burger.setAttribute('aria-label', 'Open menu');
  burger.setAttribute('aria-expanded', 'false');
  burger.innerHTML = '<span></span><span></span><span></span>';
  // Insert immediately after .brand so it appears at the right edge on mobile.
  header.appendChild(burger);

  // Drawer — contains a clone of the lesson nav + a "Contents" section.
  const drawer = document.createElement('div');
  drawer.className = 'nav-drawer';
  drawer.id = 'nav-drawer';
  drawer.setAttribute('aria-hidden', 'true');

  const lessonsLabel = document.createElement('div');
  lessonsLabel.className = 'nav-drawer-label';
  lessonsLabel.textContent = 'Lessons';
  drawer.appendChild(lessonsLabel);

  if (lessonNav) {
    const navClone = lessonNav.cloneNode(true);
    navClone.classList.add('nav-drawer-list');
    drawer.appendChild(navClone);
  }

  if (tocEl) {
    const tocLabel = document.createElement('div');
    tocLabel.className = 'nav-drawer-label';
    tocLabel.textContent = 'Contents';
    drawer.appendChild(tocLabel);

    const tocClone = tocEl.cloneNode(true);
    tocClone.removeAttribute('id');
    tocClone.classList.remove('toc');
    tocClone.classList.add('nav-drawer-toc');
    drawer.appendChild(tocClone);
  }

  document.body.appendChild(drawer);

  // Backdrop for tap-to-close.
  const backdrop = document.createElement('div');
  backdrop.className = 'nav-backdrop';
  document.body.appendChild(backdrop);

  const close = () => {
    document.body.classList.remove('nav-open');
    burger.setAttribute('aria-expanded', 'false');
    drawer.setAttribute('aria-hidden', 'true');
  };
  const open = () => {
    document.body.classList.add('nav-open');
    burger.setAttribute('aria-expanded', 'true');
    drawer.setAttribute('aria-hidden', 'false');
  };

  burger.addEventListener('click', () => {
    document.body.classList.contains('nav-open') ? close() : open();
  });
  backdrop.addEventListener('click', close);
  drawer.querySelectorAll('a').forEach(a => a.addEventListener('click', close));
  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });

  // On the existing toc-btn (desktop), keep its behavior. On mobile, repurpose
  // it to open the drawer too — but since CSS hides it on mobile, this is a
  // no-op there. We only intercept if the button is visible.
  if (tocBtn) {
    // existing onclick still toggles #toc on desktop — leave it intact.
  }
})();
