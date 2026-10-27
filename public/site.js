// Only interaction code; the pages, recipes, and navigation are static HTML.
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const menu = document.querySelector('.menu-toggle');
const panel = document.querySelector('.ast-mobile-header-content');
if (menu && panel) {
  menu.setAttribute('aria-controls', 'mobile-navigation-panel');
  panel.id = 'mobile-navigation-panel';
  const close = () => { menu.setAttribute('aria-expanded', 'false'); document.body.classList.remove('ast-main-header-nav-open'); };
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('ast-main-header-nav-open', open);
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') { close(); menu.focus(); } });
  panel.addEventListener('click', event => { if (event.target.closest('a')) close(); });
}
for (const button of document.querySelectorAll('[data-video-id]')) {
  button.addEventListener('click', () => {
    const iframe = document.createElement('iframe');
    iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(button.dataset.videoId)}?autoplay=1&rel=0`;
    iframe.title = button.dataset.title || 'Recipe video';
    iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    button.replaceWith(iframe);
    iframe.focus();
  });
}
for (const button of document.querySelectorAll('[data-print]')) button.addEventListener('click', () => window.print());
const topLink = document.querySelector('.back-to-top');
if (topLink) {
  const update = () => { topLink.hidden = window.scrollY < 600; };
  window.addEventListener('scroll', update, { passive: true }); update();
  topLink.addEventListener('click', event => { event.preventDefault(); window.scrollTo({ top: 0, behavior: reducedMotion ? 'instant' : 'smooth' }); document.querySelector('.custom-logo-link')?.focus({ preventScroll: true }); });
}
for (const button of document.querySelectorAll('[data-instagram-url]')) {
  button.addEventListener('click', () => {
    const url = new URL(button.dataset.instagramUrl);
    if (!['www.instagram.com', 'instagram.com'].includes(url.hostname)) return;
    const iframe = document.createElement('iframe');
    iframe.src = `${url.origin}${url.pathname.replace(/\/$/, '')}/embed/`;
    iframe.title = 'Instagram post from The Healthy Malteser';
    iframe.loading = 'lazy';
    iframe.style.cssText = 'width:100%;height:480px;border:0';
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    button.replaceWith(iframe);
  });
}
