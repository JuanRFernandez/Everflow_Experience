/* EverFlow Experience: the one script of the site. No dependencies; Leaflet is loaded only
   after the visitor clicks "Show map". Every page works without this script. */
(function () {
  'use strict';

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- old one-page links (/#experiences ...) lead to the new pages ---------- */
  var LEGACY = {
    '#experiences': '/experiences/', '#reach': '/destinations/', '#stay': '/stay/', '#meet': '/about/#team',
    '#about': '/about/', '#contact': '/enquire/'
  };
  if ((location.pathname === '/' || location.pathname === '/index.html') && LEGACY[location.hash] &&
      !document.getElementById(location.hash.slice(1))) {
    location.replace(LEGACY[location.hash]);
  }

  /* ---------- mobile menu ---------- */
  function initMenu() {
    var header = $('.site-header');
    var toggle = $('.menu-toggle');
    if (!header || !toggle) return;
    function set(open) {
      header.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    toggle.addEventListener('click', function () { set(toggle.getAttribute('aria-expanded') !== 'true'); });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && header.classList.contains('is-open')) { set(false); toggle.focus(); }
    });
    $$('#site-nav a').forEach(function (a) { a.addEventListener('click', function () { set(false); }); });
  }

  /* ---------- galleries: counter "01 / 06" (or "01–03 / 06" when three fit) and previous / next ---------- */
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function initGallery(g) {
    var track = $('.gallery-track', g);
    var items = $$('.gallery-item', g);
    var controls = $('.gallery-controls', g);
    var count = $('.gallery-count', g);
    var prev = $('[data-prev]', g);
    var next = $('[data-next]', g);
    if (!track || items.length < 2 || !controls) return;
    controls.hidden = false;
    var first = 0;      // the first photo or card fully in view
    var aim = null;     // where a click is scrolling to, so quick clicks add up
    var settle = null;
    function inView() {
      var box = track.getBoundingClientRect();
      var from = -1, to = -1, near = 0;
      items.forEach(function (it, i) {
        var r = it.getBoundingClientRect();
        if (r.left >= box.left - 2 && r.right <= box.right + 2) { if (from < 0) from = i; to = i; }
        if (Math.abs(r.left - box.left) < Math.abs(items[near].getBoundingClientRect().left - box.left)) near = i;
      });
      return from < 0 ? [near, near] : [from, to];  // an item wider than the track: the one at its left edge
    }
    function update() {
      var v = inView();
      first = v[0];
      count.textContent = (v[0] === v[1] ? pad(v[0] + 1) : pad(v[0] + 1) + '–' + pad(v[1] + 1)) + ' / ' + pad(items.length);
      var left = track.scrollLeft;
      prev.disabled = first === 0 && left <= 4;
      next.disabled = v[1] === items.length - 1 || left + track.clientWidth >= track.scrollWidth - 4;
    }
    function go(i) {
      aim = Math.max(0, Math.min(items.length - 1, i));
      var max = track.scrollWidth - track.clientWidth;
      track.scrollTo({ left: Math.min(max, items[aim].offsetLeft - track.offsetLeft), behavior: reduceMotion ? 'auto' : 'smooth' });
    }
    prev.addEventListener('click', function () { go((aim === null ? first : aim) - 1); });
    next.addEventListener('click', function () { go((aim === null ? first : aim) + 1); });
    var ticking = false;
    track.addEventListener('scroll', function () {
      window.clearTimeout(settle);
      settle = window.setTimeout(function () { aim = null; update(); }, 200);  // the scroll has come to rest
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () { ticking = false; update(); });
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  /* ---------- home video: only on wide screens, without reduced motion or data saving ---------- */
  function initVideo() {
    var media = $('.hero-media[data-src]');
    var button = $('.video-toggle');
    if (!media || !button || reduceMotion) return;
    var saveData = navigator.connection && navigator.connection.saveData;
    if (saveData || !window.matchMedia('(min-width: 48rem)').matches) return;
    var video = document.createElement('video');
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.setAttribute('playsinline', '');
    video.setAttribute('aria-hidden', 'true');
    video.preload = 'auto';
    video.src = media.getAttribute('data-src');
    video.addEventListener('canplay', function () {
      var img = $('img', media);
      media.insertBefore(video, img);
      if (img) img.hidden = true;
      button.hidden = false;
    }, { once: true });
    var p = video.play();
    if (p && p.catch) p.catch(function () {});
    var pauseLabel = button.getAttribute('data-pause') || 'Pause video';
    var playLabel = button.getAttribute('data-play') || 'Play video';
    button.addEventListener('click', function () {
      if (video.paused) { video.play(); button.textContent = pauseLabel; button.setAttribute('aria-pressed', 'false'); }
      else { video.pause(); button.textContent = playLabel; button.setAttribute('aria-pressed', 'true'); }
    });
  }

  /* ---------- enquiry: prefill from the link, open the visitor's own e-mail or WhatsApp ---------- */
  function initEnquiry() {
    var form = $('#enquiry');
    if (!form) return;
    var status = $('#form-status');
    var words = {};  // the page's language: the Spanish and Portuguese pages carry their texts in data-i18n
    try { words = JSON.parse(form.getAttribute('data-i18n') || '{}'); } catch (err) { words = {}; }
    function say(key, english) { return (words[key] || english).replace('{email}', form.getAttribute('data-email')); }
    var params = new URLSearchParams(location.search);
    ['destination', 'stay', 'interest'].forEach(function (key) {
      var value = params.get(key);
      var select = form.elements[key];
      if (!value || !select) return;
      for (var i = 0; i < select.options.length; i++) {
        if (select.options[i].value === value) { select.value = value; break; }
      }
    });
    function label(name) {
      var el = form.elements[name];
      if (!el || !el.value) return '';
      return el.tagName === 'SELECT' ? el.options[el.selectedIndex].text : el.value.trim();
    }
    function message() {
      var lines = [
        [say('name', 'Name'), label('name')], [say('email', 'E-mail'), label('email')], [say('phone', 'Phone'), label('phone')],
        [say('destination', 'Destination'), label('destination')], [say('stay', 'Where to stay'), label('stay')],
        [say('interest', 'Interested in'), label('interest')], [say('group', 'Group size'), label('group')],
        [say('dates', 'Dates'), label('dates')]
      ].filter(function (l) { return l[1]; }).map(function (l) { return l[0] + ': ' + l[1]; });
      var note = label('message');
      if (note) lines.push('', note);
      return lines.join('\n');
    }
    function valid() {
      if (form.reportValidity()) return true;
      status.textContent = say('invalid', 'Please add your name and a valid e-mail address.');
      return false;
    }
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!valid()) return;
      var email = form.getAttribute('data-email');
      location.href = 'mailto:' + email + '?subject=' + encodeURIComponent(say('subject', 'Trip enquiry: ') + label('name')) +
        '&body=' + encodeURIComponent(message());
      status.textContent = say('mail', 'Your e-mail app should open with the message ready. Send it from there. If nothing opens, write to {email}.');
    });
    var wa = $('#send-whatsapp');
    if (wa) wa.addEventListener('click', function () {
      if (!valid()) return;
      window.open('https://wa.me/' + form.getAttribute('data-whatsapp') + '?text=' + encodeURIComponent(message()), '_blank', 'noopener');
      status.textContent = say('wa', 'WhatsApp should open with the message ready. Send it from there.');
    });
  }

  /* ---------- map: Leaflet and the OpenStreetMap tiles load only after the click ---------- */
  function load(tag, attrs) {
    return new Promise(function (resolve, reject) {
      var el = document.createElement(tag);
      Object.keys(attrs).forEach(function (k) { el[k] = attrs[k]; });
      el.onload = resolve;
      el.onerror = reject;
      document.head.appendChild(el);
    });
  }
  function initMap() {
    var box = $('#map');
    var button = $('#map-load');
    if (!box || !button) return;
    button.addEventListener('click', function () {
      button.disabled = true;
      button.textContent = 'Loading…';
      Promise.all([
        load('link', { rel: 'stylesheet', href: '/assets/vendor/leaflet/leaflet.css' }),
        load('script', { src: '/assets/vendor/leaflet/leaflet.js' })
      ]).then(function () { buildMap(box); }, function () { button.textContent = 'The map could not be loaded'; });
    });
  }
  function el(tag, text, href) {
    var n = document.createElement(tag);
    if (href) n.href = href;
    n.textContent = text;
    return n;
  }
  function buildMap(box) {
    var pins = JSON.parse(box.getAttribute('data-pins'));
    var consent = $('.map-consent', box);
    if (consent) consent.parentNode.removeChild(consent);
    var map = L.map(box, { scrollWheelZoom: false });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> contributors'
    }).addTo(map);
    var bounds = [];
    pins.forEach(function (p) {
      var icon = L.divIcon({ className: 'map-pin' + (p.s.length ? ' map-pin--stay' : ''), html: '<span></span>', iconSize: [20, 20], iconAnchor: [10, 10] });
      var popup = document.createElement('div');
      var title = el('p', '');
      title.className = 'map-popup-title';
      title.appendChild(el('a', p.n, p.u));
      popup.appendChild(title);
      if (p.s.length) {
        var ul = document.createElement('ul');
        ul.className = 'map-popup-list';
        p.s.forEach(function (s) { var li = document.createElement('li'); li.appendChild(el('a', s[0], s[1])); ul.appendChild(li); });
        popup.appendChild(ul);
      }
      L.marker([p.lat, p.lon], { icon: icon, title: p.n, alt: p.n }).addTo(map).bindPopup(popup);
      bounds.push([p.lat, p.lon]);
    });
    map.fitBounds(L.latLngBounds(bounds).pad(0.08));
  }

  /* ---------- photos open large: tap a photo of a gallery; arrows, swipe, Esc ---------- */
  function initLightbox() {
    var galleries = $$('[data-gallery]').filter(function (g) { return !g.classList.contains('gallery--cards'); });
    if (!galleries.length || typeof HTMLDialogElement === 'undefined') return;
    var box = document.createElement('dialog');
    box.className = 'lightbox';
    box.innerHTML = '<div class="lightbox-bar"><p class="lightbox-title"></p><span class="lightbox-count" aria-live="polite"></span>' +
      '<button type="button" class="lightbox-close" aria-label="Close">×</button></div>' +
      '<figure class="lightbox-figure"><img alt=""><figcaption class="credit"></figcaption></figure>' +
      '<button type="button" class="lightbox-nav lightbox-prev" aria-label="Previous photo">←</button>' +
      '<button type="button" class="lightbox-nav lightbox-next" aria-label="Next photo">→</button>';
    document.body.appendChild(box);
    var img = $('img', box), caption = $('figcaption', box), title = $('.lightbox-title', box), count = $('.lightbox-count', box);
    var prev = $('.lightbox-prev', box), next = $('.lightbox-next', box);
    var figures = [], current = 0, gallery = null;
    function sharpest(source) {
      // the smallest file that is sharp on this screen; set as src so the photo is never shown larger than it is
      var need = window.innerWidth * (window.devicePixelRatio || 1);
      var files = (source.getAttribute('srcset') || '').split(',').map(function (part) {
        var bits = part.trim().split(/\s+/);
        return { url: bits[0], w: parseInt(bits[1], 10) || 0 };
      }).filter(function (f) { return f.url; }).sort(function (x, y) { return x.w - y.w; });
      for (var k = 0; k < files.length; k++) if (files[k].w >= need) return files[k].url;
      return files.length ? files[files.length - 1].url : source.getAttribute('src');
    }
    function show(i) {
      current = Math.max(0, Math.min(figures.length - 1, i));
      var source = $('img', figures[current]);
      var credit = $('figcaption', figures[current]);
      img.removeAttribute('src');
      img.src = sharpest(source);
      img.alt = source.alt;
      caption.innerHTML = credit ? credit.innerHTML : '';
      count.textContent = pad(current + 1) + ' / ' + pad(figures.length);
      prev.disabled = current === 0;
      next.disabled = current === figures.length - 1;
    }
    function open(g, i) {
      gallery = g;
      figures = $$('.gallery-item figure', g);
      title.textContent = g.getAttribute('data-title') || '';
      box.setAttribute('aria-label', g.getAttribute('aria-label') || 'Photos');
      show(i);
      document.documentElement.classList.add('has-lightbox');
      box.showModal();
    }
    box.addEventListener('close', function () {
      document.documentElement.classList.remove('has-lightbox');
      var track = $('.gallery-track', gallery);
      var item = figures[current] && figures[current].closest('.gallery-item');
      if (track && item) track.scrollLeft = item.offsetLeft - track.offsetLeft;  // the gallery shows the photo seen last
      var back = figures[current] && $('.photo-open', figures[current]);
      if (back) back.focus({ preventScroll: true });
    });
    prev.addEventListener('click', function () { show(current - 1); });
    next.addEventListener('click', function () { show(current + 1); });
    $('.lightbox-close', box).addEventListener('click', function () { box.close(); });
    box.addEventListener('click', function (ev) { if (ev.target === box || ev.target.classList.contains('lightbox-figure')) box.close(); });
    box.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowLeft') { ev.preventDefault(); show(current - 1); }
      if (ev.key === 'ArrowRight') { ev.preventDefault(); show(current + 1); }
    });
    var startX = null;
    box.addEventListener('touchstart', function (ev) { startX = ev.touches.length === 1 ? ev.touches[0].clientX : null; }, { passive: true });
    box.addEventListener('touchend', function (ev) {
      if (startX === null) return;
      var dx = ev.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) show(current + (dx < 0 ? 1 : -1));
      startX = null;
    }, { passive: true });
    galleries.forEach(function (g) {
      $$('.gallery-item figure', g).forEach(function (fig, i) {
        var photo = $('img', fig);
        if (!photo) return;
        var button = document.createElement('button');  // the photo becomes a button: keyboard and screen readers can open it too
        button.type = 'button';
        button.className = 'photo-open';
        button.setAttribute('aria-haspopup', 'dialog');
        fig.insertBefore(button, photo);
        button.appendChild(photo);
        button.addEventListener('click', function () { open(g, i); });
      });
    });
  }

  function ready() {
    initMenu();
    $$('[data-gallery]').forEach(initGallery);
    initLightbox();
    initVideo();
    initEnquiry();
    initMap();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
