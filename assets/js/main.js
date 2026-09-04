/* EverFlow Experience — site behavior (vanilla JS, no dependencies except Leaflet for the map) */
(function () {
  'use strict';

  var DESTS = [
    ['Garmisch-Partenkirchen', 'Germany · Home base'],
    ['Munich', 'Germany'],
    ['Innsbruck', 'Austria'],
    ['Kitzbühel', 'Austria'],
    ['St. Moritz', 'Switzerland'],
    ['Gstaad', 'Switzerland'],
    ['Zermatt', 'Switzerland'],
    ['Courchevel', 'France'],
    ["Cortina d'Ampezzo", 'Italy']
  ];

  function $(id) { return document.getElementById(id); }
  function val(id) { var e = $(id); return e ? e.value.trim() : ''; }

  /* ---------- Destinations gallery ---------- */
  function initDestinations() {
    var layers = document.querySelectorAll('[data-dest-layer]');
    var items = document.querySelectorAll('[data-dest]');
    function select(i) {
      layers.forEach(function (l) { l.classList.toggle('active', +l.dataset.destLayer === i); });
      items.forEach(function (it) { it.classList.toggle('active', +it.dataset.dest === i); });
      $('dest-name').textContent = DESTS[i][0];
      $('dest-country').textContent = DESTS[i][1];
    }
    items.forEach(function (it) {
      var i = +it.dataset.dest;
      it.addEventListener('click', function () { select(i); });
      it.addEventListener('mouseenter', function () { select(i); });
    });
  }

  /* ---------- Booking modal (4-step wizard) ---------- */
  function initModal() {
    var modal = $('bk-modal');
    if (!modal) return;
    function show(step) {
      for (var n = 1; n <= 5; n++) {
        var el = $('bk-step-' + n);
        if (el) el.style.display = (n === step) ? '' : 'none';
      }
      modal.querySelectorAll('.bk-dot').forEach(function (d, idx) {
        d.classList.toggle('on', idx + 1 <= Math.min(step, 4));
      });
    }
    function open() { show(1); modal.style.display = ''; document.body.style.overflow = 'hidden'; }
    function close() { modal.style.display = 'none'; document.body.style.overflow = ''; }
    function goStep(n) {
      if (n === 2 && (!val('bkFn') || !val('bkEm'))) { alert('Please fill in your name and email.'); return; }
      show(n);
    }
    function submit(via) {
      var msg = [
        'Booking request — EverFlow Experience',
        'Name: ' + val('bkFn') + ' ' + val('bkLn'),
        'Email: ' + val('bkEm'),
        'Experience: ' + val('bkSrv'),
        (val('bkDf') || val('bkDt')) ? 'Dates: ' + (val('bkDf') || '?') + ' to ' + (val('bkDt') || '?') : '',
        (val('bkLv') && val('bkLv') !== 'Select...') ? 'Ski level: ' + val('bkLv') : '',
        val('bkNt') ? 'Notes: ' + val('bkNt') : ''
      ].filter(Boolean).join('\n');
      if (via === 'wa') {
        window.open('https://wa.me/491759505075?text=' + encodeURIComponent(msg), '_blank');
      } else {
        location.href = 'mailto:info@everflowexperience.com?subject=' +
          encodeURIComponent('Booking request — ' + val('bkFn') + ' ' + val('bkLn')) +
          '&body=' + encodeURIComponent(msg);
      }
      show(5);
    }
    document.querySelectorAll('[data-open-modal]').forEach(function (b) { b.addEventListener('click', open); });
    modal.querySelectorAll('[data-close-modal]').forEach(function (b) { b.addEventListener('click', close); });
    modal.addEventListener('click', function (e) { if (e.target.dataset && e.target.dataset.modalBg) close(); });
    modal.querySelectorAll('[data-goto-step]').forEach(function (b) {
      b.addEventListener('click', function () { goStep(+b.dataset.gotoStep); });
    });
    modal.querySelectorAll('[data-submit]').forEach(function (b) {
      b.addEventListener('click', function () { submit(b.dataset.submit); });
    });
  }

  /* ---------- Tailor-made enquiry ---------- */
  function initTailor() {
    var btn = $('tm-send');
    if (!btn) return;
    btn.addEventListener('click', function () {
      if (!val('tmFn') || !val('tmEm') || !val('tmEnq')) { alert('Please fill in the required fields.'); return; }
      var body = 'Name: ' + val('tmFn') + ' ' + val('tmLn') + '\nEmail: ' + val('tmEm') + '\n\n' + val('tmEnq');
      location.href = 'mailto:info@everflowexperience.com?subject=' +
        encodeURIComponent('Tailor-Made Enquiry — ' + val('tmFn') + ' ' + val('tmLn')) +
        '&body=' + encodeURIComponent(body);
    });
  }

  /* ---------- Leaflet map (privacy: built only after the visitor clicks "Show map") ---------- */
  var mapTry = 0, mapBuilt = false;
  function initMap() {
    var btn = $('map-load');
    if (!btn) return;
    btn.addEventListener('click', buildMap);
  }
  function buildMap() {
    var el = $('mapa-custom');
    if (!el || mapBuilt) return;
    if (typeof L === 'undefined') { // Leaflet not loaded yet — retry briefly
      if (mapTry++ < 40) setTimeout(buildMap, 250);
      return;
    }
    mapBuilt = true;
    var consent = $('map-consent');
    if (consent) consent.parentNode.removeChild(consent);
    var map = L.map(el, { zoomControl: false, scrollWheelZoom: false });
    map.fitBounds([[45.15, 6.1], [48.4, 12.8]], { padding: [8, 8] });
    // Tiles from the OpenStreetMap Foundation (no API key). Attribution is required by the OSM tile usage policy.
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map);
    var icon = function (labelHtml, cssClass) {
      return L.divIcon({
        className: 'custom-div-icon',
        html: '<div class="pin-wrapper"><svg width="40" height="52" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="position:absolute;top:0;left:0;"><path d="M12 0C7.58 0 4 3.58 4 8C4 13.5 12 24 12 24C12 24 20 13.5 20 8C20 3.58 16.42 0 12 0ZM12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11Z" fill="#1a1a1a"/><circle cx="12" cy="8" r="2.5" fill="white"/></svg><div class="label-container ' + cssClass + '">' + labelHtml + '</div></div>',
        iconSize: [40, 52], iconAnchor: [20, 52]
      });
    };
    var bases = [
      [48.1351, 11.5820, 'MUNICH', 'text-r', 'Munich'],
      [47.4917, 11.0955, 'GARMISCH<br>PARTENKIRCHEN', 'text-l', 'Garmisch-Partenkirchen'],
      [47.2692, 11.4041, 'INNSBRUCK', 'text-b', 'Innsbruck'],
      [47.4467, 12.3925, 'KITZBÜHEL', 'text-r', 'Kitzbühel'],
      [46.4984, 9.8391, 'ST. MORITZ', 'text-b', 'St.+Moritz'],
      [46.4728, 7.2864, 'GSTAAD', 'text-l', 'Gstaad'],
      [46.0207, 7.7491, 'ZERMATT', 'text-b', 'Zermatt'],
      [45.4154, 6.6349, 'COURCHEVEL', 'text-r', 'Courchevel'],
      [46.5405, 12.1357, "CORTINA<br>D'AMPEZZO", 'text-l', "Cortina+d'Ampezzo"]
    ];
    bases.forEach(function (b) {
      L.marker([b[0], b[1]], { icon: icon(b[2], b[3]) }).addTo(map)
        .on('click', function () { window.open('https://www.google.com/maps/search/' + b[4], '_blank'); });
    });
    var countries = [[48.05, 10.55, 'GERMANY'], [47.35, 13.55, 'AUSTRIA'], [46.75, 8.35, 'SWITZERLAND'], [45.85, 10.9, 'ITALY'], [45.35, 5.7, 'FRANCE']];
    countries.forEach(function (c) {
      L.marker([c[0], c[1]], {
        icon: L.divIcon({ className: 'country-label', html: c[2], iconSize: [140, 40], iconAnchor: [70, 20] }),
        interactive: false
      }).addTo(map);
    });
  }

  /* ---------- Boot ---------- */
  function ready() {
    initDestinations();
    initModal();
    initTailor();
    initMap();
    var y = $('ft-year');
    if (y) y.textContent = new Date().getFullYear();
    var wa = $('wa-float');
    if (wa) setTimeout(function () { wa.style.display = 'flex'; }, 3000);
    var v = $('hero-vid');
    if (v) { v.muted = true; var p = v.play(); if (p && p.catch) p.catch(function () {}); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
