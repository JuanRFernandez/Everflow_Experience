/* EverFlow Experience: the one script of the site. No dependencies; Leaflet is loaded only
   after the visitor clicks "Open the interactive map". Every page works without this script. */
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
  if (location.pathname === '/experiences/' && location.hash === '#hotels-and-chalets') {
    location.replace('/stay/');  // hotels and chalets were an experience until 21.10.2026; they have their own pages
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
      prev.setAttribute('aria-disabled', first === 0 && left <= 4 ? 'true' : 'false');  // not disabled: the focus stays
      next.setAttribute('aria-disabled', v[1] === items.length - 1 || left + track.clientWidth >= track.scrollWidth - 4 ? 'true' : 'false');
    }
    function off(button) { return button.getAttribute('aria-disabled') === 'true'; }
    function go(i) {
      aim = Math.max(0, Math.min(items.length - 1, i));
      var max = track.scrollWidth - track.clientWidth;
      track.scrollTo({ left: Math.min(max, items[aim].offsetLeft - track.offsetLeft), behavior: reduceMotion ? 'auto' : 'smooth' });
    }
    prev.addEventListener('click', function () { if (!off(prev)) go((aim === null ? first : aim) - 1); });
    next.addEventListener('click', function () { if (!off(next)) go((aim === null ? first : aim) + 1); });
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
    var net = navigator.connection || {};
    if (net.saveData || (net.effectiveType && net.effectiveType !== '4g')) return;  // a slow or metered connection: the photo stays
    if (!window.matchMedia('(min-width: 48rem)').matches) return;
    var video = document.createElement('video');
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.setAttribute('playsinline', '');
    video.setAttribute('aria-hidden', 'true');
    video.preload = 'metadata';  // play() fetches the rest, after the page has loaded
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
      if (video.paused) { video.play(); button.textContent = pauseLabel; }
      else { video.pause(); button.textContent = playLabel; }
    });
  }

  /* ---------- the WhatsApp links say which page the visitor writes from ---------- */
  function initWhatsAppLinks() {
    var footer = $('.site-footer');
    var greeting = footer && footer.getAttribute('data-wa-greeting');
    if (!greeting) return;
    var text = encodeURIComponent(greeting.replace('{page}', location.pathname));
    $$('a[href^="https://wa.me/"]').forEach(function (link) {
      if (link.href.indexOf('?') === -1) link.href += '?text=' + text;
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
    ['destination', 'type', 'stay', 'house', 'interest'].forEach(function (key) {  // the link of a card fills the form in
      var value = params.get(key);
      var select = form.elements[key];
      if (!value || !select) return;
      for (var i = 0; i < select.options.length; i++) {
        if (select.options[i].value === value) { select.value = value; break; }
      }
    });
    /* Destination, stay, type and house are linked: the list the visitor just changed leads, the others follow.
       The full lists are kept apart; a list is emptied and refilled with the options that fit (an option marked
       hidden is still shown by iOS). A value that no longer fits goes back to "No preference". */
    var dest = form.elements.destination, type = form.elements.type, stay = form.elements.stay, house = form.elements.house;
    var houseField = house && house.closest('.field');
    var softType = false;  // a type the script took from the chosen stay: shown, but it does not narrow the stays
    function groups(select) {
      return $$('optgroup', select).map(function (g) {
        return { label: g.label, stay: g.getAttribute('data-stay'), options: $$('option', g) };
      });
    }
    var allStays = stay ? groups(stay) : [], allHouses = house ? groups(house) : [];
    function hasType(option, kind) { return !kind || (option.getAttribute('data-types') || '').split(' ').indexOf(kind) >= 0; }
    function refill(select, all, fits) {
      var chosen = select.value, kept = 0;
      $$('optgroup', select).forEach(function (g) { select.removeChild(g); });
      all.forEach(function (g) {
        var options = g.options.filter(function (o) { return fits(g, o); });
        if (!options.length) return;
        var el = document.createElement('optgroup');
        el.label = g.label;
        options.forEach(function (o) { el.appendChild(o.cloneNode(true)); });
        select.appendChild(el);
        kept += options.length;
      });
      select.value = chosen;
      if (select.selectedIndex < 0) select.value = '';
      return kept;
    }
    function sync(source) {
      if (!dest || !type || !stay) return;
      if (source === 'type') softType = false;  // the visitor chose the type: it narrows the stays
      if (source === 'stay') {
        var picked = stay.value ? stay.options[stay.selectedIndex] : null;
        if (picked) {
          dest.value = picked.getAttribute('data-place') || '';
          var kinds = (picked.getAttribute('data-types') || '').split(' ').filter(Boolean);
          if (kinds.length === 1) {
            if (type.value !== kinds[0]) { type.value = kinds[0]; softType = true; }  // a hotel: its type, shown
          } else if (softType || (type.value && kinds.indexOf(type.value) < 0)) {
            type.value = ''; softType = false;  // a chalet or an apartment: the guest says which; a type the stay lacks goes
          }
        } else if (softType) { type.value = ''; softType = false; }
      }
      var place = dest.value, kind = softType ? '' : type.value;
      if (source !== 'stay') {  // a chosen stay leaves its own list as it is, so the visitor can go on through it (also by arrow keys)
        refill(stay, allStays, function (g, o) { return (!place || o.getAttribute('data-place') === place) && hasType(o, kind); });
        if (!stay.value && softType) { type.value = ''; softType = false; }  // the stay that set the type is gone
      }
      if (house) {
        var n = refill(house, allHouses, function (g, o) { return g.stay === stay.value && hasType(o, type.value); });
        if (houseField) houseField.hidden = n === 0;  // only "No preference" left: the field goes
      }
    }
    [dest, type, stay].forEach(function (select) {
      if (select) select.addEventListener('change', function () { sync(select.name); });
    });
    sync(params.get('stay') ? 'stay' : 'destination');  // a stay in the link is the most concrete wish: it corrects a destination that does not match
    function label(name) {
      var el = form.elements[name];
      if (!el || !el.value) return '';
      return el.tagName === 'SELECT' ? el.options[el.selectedIndex].text : el.value.trim();
    }
    function message() {
      var lines = [
        [say('name', 'Name'), label('name')], [say('email', 'E-mail'), label('email')], [say('phone', 'Phone'), label('phone')],
        [say('destination', 'Destination'), label('destination')], [say('stay', 'Where to stay'), label('stay')],
        [say('type', 'Type of stay'), label('type')], [say('house', 'House'), label('house')],
        [say('interest', 'Interested in'), label('interest')], [say('group', 'Group size'), label('group')],
        [say('dates', 'Dates'), label('dates')]
      ].filter(function (l) { return l[1]; }).map(function (l) { return l[0] + ': ' + l[1]; });
      var note = label('message');
      if (note) lines.push('', note);
      lines.push('', say('page', 'Page') + ': ' + location.pathname + ' (' + document.documentElement.lang + ')');  // where the enquiry came from
      return lines.join('\n');
    }
    function flag(name, bad, text) {  // the error stands by the field, in the page's language
      var el = form.elements[name], note = $('#f-' + name + '-error');
      if (!el || !note) return;
      el.setAttribute('aria-invalid', bad ? 'true' : 'false');
      note.textContent = bad ? text : '';
      note.hidden = !bad;
    }
    function valid() {
      var name = form.elements.name, email = form.elements.email;
      var badName = !name.value.trim();
      var badMail = !email.value.trim() || !email.checkValidity();
      flag('name', badName, say('name_error', 'Please enter your name.'));
      flag('email', badMail, say('email_error', 'Please enter a valid e-mail address.'));
      if (!badName && !badMail) return true;
      status.textContent = say('invalid', 'Please add your name and a valid e-mail address.');
      (badName ? name : email).focus();
      return false;
    }
    ['name', 'email'].forEach(function (key) {
      form.elements[key].addEventListener('input', function () { if (this.getAttribute('aria-invalid') === 'true') flag(key, false, ''); });
    });
    var fallback = $('#mail-fallback'), copyBox = $('#f-copy'), copyButton = $('#copy-message');
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!valid()) return;
      var email = form.getAttribute('data-email');
      var text = message();
      location.href = 'mailto:' + email + '?subject=' + encodeURIComponent(say('subject', 'Trip enquiry: ') + label('name')) +
        '&body=' + encodeURIComponent(text);
      status.textContent = say('mail', 'Your e-mail app should open with the message ready. Send it from there. If nothing opens, write to {email}.');
      if (fallback && copyBox) { copyBox.value = text; fallback.hidden = false; }  // for a desktop without a mail app: copy and paste
    });
    if (copyButton && copyBox) copyButton.addEventListener('click', function () {
      copyBox.select();
      var done = function () { copyButton.textContent = say('copied', 'Message copied'); status.textContent = say('copied', 'Message copied'); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(copyBox.value).then(done, function () { document.execCommand('copy'); done(); });
      else { document.execCommand('copy'); done(); }
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
    var drawn = $('.map-static', box);  // on a phone the drawn map scrolls sideways: start in the middle
    if (drawn && drawn.scrollWidth > drawn.clientWidth) drawn.scrollLeft = (drawn.scrollWidth - drawn.clientWidth) / 2;
    button.addEventListener('click', function () {
      button.disabled = true;
      button.textContent = button.getAttribute('data-loading') || 'Loading…';
      Promise.all([
        load('link', { rel: 'stylesheet', href: '/assets/vendor/leaflet/leaflet.css' }),
        load('script', { src: '/assets/vendor/leaflet/leaflet.js' })
      ]).then(function () { buildMap(box); }, function () { button.disabled = false; button.textContent = button.getAttribute('data-error') || 'The map could not be loaded.'; });
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
    var drawn = $('.map-static', box);
    if (drawn) drawn.parentNode.removeChild(drawn);  // the interactive map takes the place of the drawn one
    var live = $('.map-live');
    if (live) live.hidden = true;
    box.classList.add('is-live');
    var map = L.map(box, { scrollWheelZoom: false, zoomControl: false });
    L.control.zoom({ zoomInTitle: box.getAttribute('data-zoom-in') || 'Zoom in', zoomOutTitle: box.getAttribute('data-zoom-out') || 'Zoom out' }).addTo(map);
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
    box.focus({ preventScroll: true });  // the button that was pressed is gone: the keyboard stays on the map
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
      '<button type="button" class="lightbox-nav lightbox-next" aria-label="Next photo">→</button>' +
      '<a class="button button--small button--light lightbox-enquire" href="/enquire/" hidden></a>';  // a real link even while hidden
    document.body.appendChild(box);
    var img = $('img', box), caption = $('figcaption', box), title = $('.lightbox-title', box), count = $('.lightbox-count', box);
    var prev = $('.lightbox-prev', box), next = $('.lightbox-next', box), ask = $('.lightbox-enquire', box);
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
      prev.setAttribute('aria-disabled', current === 0 ? 'true' : 'false');  // not disabled: the focus stays in the dialog
      next.setAttribute('aria-disabled', current === figures.length - 1 ? 'true' : 'false');
    }
    function open(g, i) {
      gallery = g;
      figures = $$('.gallery-item figure', g);
      title.textContent = g.getAttribute('data-title') || '';
      box.setAttribute('aria-label', g.getAttribute('aria-label') || 'Photos');
      $('.lightbox-close', box).setAttribute('aria-label', g.getAttribute('data-close') || 'Close');  // a translated page names its buttons
      prev.setAttribute('aria-label', g.getAttribute('data-prev-label') || 'Previous photo');
      next.setAttribute('aria-label', g.getAttribute('data-next-label') || 'Next photo');
      var href = g.getAttribute('data-enquire-href');  // the stay's enquiry button, under the photo
      ask.hidden = !href;
      box.classList.toggle('has-enquire', !!href);
      if (href) { ask.href = href; ask.textContent = g.getAttribute('data-enquire-label') || 'Enquire'; }
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
    prev.addEventListener('click', function () { if (current > 0) show(current - 1); });
    next.addEventListener('click', function () { if (current < figures.length - 1) show(current + 1); });
    $('.lightbox-close', box).addEventListener('click', function () { box.close(); });
    box.addEventListener('click', function (ev) { if (ev.target === box || ev.target.classList.contains('lightbox-figure')) box.close(); });
    document.addEventListener('keydown', function (ev) {  // the arrows work wherever the focus is while the view is open
      if (!box.open) return;
      if (ev.key === 'ArrowLeft') { ev.preventDefault(); if (current > 0) show(current - 1); }
      if (ev.key === 'ArrowRight') { ev.preventDefault(); if (current < figures.length - 1) show(current + 1); }
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

  /* ---------- "Where to stay": filter by type and destination; the address keeps the choice (?type=chalet&place=megeve) ---------- */
  function initStayFilters() {
    var box = $('[data-stay-filters]');
    var grid = $('#stay-grid');
    if (!box || !grid) return;
    var cards = $$('.card', grid);
    var buttons = $$('[data-filter-type]', box);
    var select = $('[data-filter-place]', box);
    var count = $('[data-filter-count]', box);
    var clear = $('[data-filter-clear]', box);
    var empty = $('[data-filter-empty]');
    var emptyLink = empty && $('a', empty);
    var types = buttons.map(function (b) { return b.getAttribute('data-filter-type'); });
    var places = $$('option', select).map(function (o) { return o.value; });
    var state = { type: '', place: '' };
    var params = new URLSearchParams(location.search);
    var legacy = { '#hotels': 'hotel', '#chalets': 'chalet' }[location.hash];  // the page had a section per kind until 24.10.2026
    var asked = params.get('type') || legacy || '';
    var place = params.get('place') || '';
    state.type = types.indexOf(asked) >= 0 ? asked : '';
    state.place = places.indexOf(place) >= 0 ? place : '';
    function write() {
      var q = new URLSearchParams(location.search);
      if (state.type) q.set('type', state.type); else q.delete('type');
      if (state.place) q.set('place', state.place); else q.delete('place');
      var s = q.toString();
      history.replaceState(null, '', location.pathname + (s ? '?' + s : '') + (legacy ? '' : location.hash));
    }
    function apply() {
      var shown = 0;
      cards.forEach(function (card) {
        var fits = (!state.type || (card.getAttribute('data-type') || '').split(' ').indexOf(state.type) >= 0) &&
          (!state.place || card.getAttribute('data-place') === state.place);
        card.hidden = !fits;
        if (fits) shown++;
      });
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-filter-type') === state.type ? 'true' : 'false'); });
      select.value = state.place;
      count.textContent = count.getAttribute(shown === 1 ? 'data-one' : 'data-many').replace('{n}', shown);
      clear.hidden = !state.type && !state.place;
      if (empty) empty.hidden = shown > 0;
      if (emptyLink) {  // "Tell us what you need" takes the filters into the enquiry
        var q = new URLSearchParams();
        if (state.place) q.set('destination', state.place);
        if (state.type) q.set('type', state.type);
        emptyLink.href = '/enquire/' + (q.toString() ? '?' + q.toString() : '');
      }
    }
    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        var kind = b.getAttribute('data-filter-type');
        state.type = kind && state.type === kind ? '' : kind;  // a pressed type, pressed again, lets go: all show
        write();
        apply();
      });
    });
    select.addEventListener('change', function () { state.place = select.value; write(); apply(); });
    clear.addEventListener('click', function () { state.type = ''; state.place = ''; write(); apply(); buttons[0].focus(); });
    if (params.has('type') || params.has('place') || legacy) write();  // a value the page does not know leaves the address
    box.hidden = false;
    apply();
  }

  function ready() {
    initMenu();
    $$('[data-gallery]').forEach(initGallery);
    initLightbox();
    window.addEventListener('load', initVideo);  // the video waits for the page
    initWhatsAppLinks();
    initEnquiry();
    initMap();
    initStayFilters();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
