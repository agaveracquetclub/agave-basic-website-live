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

