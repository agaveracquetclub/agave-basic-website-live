const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#main-nav');
if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!open));
    nav.classList.toggle('open', !open);
  });
}

const galleryMain = document.querySelector('#gallery-main');
const galleryThumbs = document.querySelectorAll('[data-gallery-src]');
galleryThumbs.forEach((button) => {
  button.addEventListener('click', () => {
    if (!galleryMain) return;
    galleryMain.src = button.dataset.gallerySrc;
    galleryMain.alt = button.dataset.galleryAlt || '';
    galleryThumbs.forEach((thumb) => thumb.classList.toggle('active', thumb === button));
  });
});

document.querySelectorAll('[data-hide-on-error]').forEach((image) => {
  image.addEventListener('error', () => {
    const thumb = image.closest('.gallery-thumb');
    if (thumb) thumb.remove(); else image.remove();
  });
});

document.querySelectorAll('[data-card-image]').forEach((image) => {
  image.addEventListener('error', () => {
    const parent = image.parentElement;
    image.remove();
    const fallback = document.createElement('span');
    fallback.textContent = 'AGAVE';
    parent?.append(fallback);
  });
});

document.querySelectorAll('[data-image-fallback]').forEach((image) => {
  image.addEventListener('error', () => {
    const firstWorking = document.querySelector('.gallery-thumb img:not([data-broken])');
    if (firstWorking && firstWorking.src !== image.src) image.src = firstWorking.src;
  }, {once: true});
});

