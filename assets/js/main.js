/* EverFlow Experience — interactions (menu, modal, forms, map) */
// year
  document.getElementById('yr').textContent = new Date().getFullYear();

  // video: start at second 2 like the original
  const v = document.getElementById('bgvid');
  v.addEventListener('loadedmetadata', () => { try { v.currentTime = 2; } catch(e){} });

  // mobile menu
  const menu = document.getElementById('menu');
  document.getElementById('burger').addEventListener('click', () => menu.classList.toggle('open'));
  menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => menu.classList.remove('open')));

  // floating whatsapp appears after 3s (like joinchat button_delay:3)
  setTimeout(() => document.getElementById('waFloat').classList.add('show'), 3000);

  // ===== Book Now modal =====
  const modalBg = document.getElementById('modalBg');
  function openModal(){ modalBg.classList.add('open'); goStep(1); document.body.style.overflow='hidden'; }
  function closeModal(){ modalBg.classList.remove('open'); document.body.style.overflow=''; }
  modalBg.addEventListener('click', e => { if (e.target === modalBg) closeModal(); });
  function goStep(n){
    if (n === 2) { // validate step 1
      if (!document.getElementById('bkFn').value.trim() || !document.getElementById('bkEm').value.trim()) {
        alert('Please fill in your name and email.'); return;
      }
    }
    document.querySelectorAll('.step').forEach(s => s.classList.toggle('on', +s.dataset.step === n));
    document.querySelectorAll('#stepsInd span').forEach((s,i) => s.classList.toggle('on', i < Math.min(n,4)+ (n>=4?0:0) && i <= n-1));
  }
  function submitBooking(via){
    const g = id => document.getElementById(id).value.trim();
    const msg = [
      `Booking request — EverFlow Experience`,
      `Name: ${g('bkFn')} ${g('bkLn')}`,
      `Email: ${g('bkEm')}`,
      `Service: ${g('bkSrv')}`,
      (g('bkDf')||g('bkDt')) ? `Dates: ${g('bkDf')||'?'} to ${g('bkDt')||'?'}` : '',
      g('bkLv') && g('bkLv')!=='Select...' ? `Ski level: ${g('bkLv')}` : '',
      g('bkNt') ? `Notes: ${g('bkNt')}` : ''
    ].filter(Boolean).join('\n');
    if (via === 'wa') {
      window.open(`https://wa.me/491759505075?text=${encodeURIComponent(msg)}`, '_blank');
    } else {
      location.href = `mailto:info@everflowexperience.com?subject=${encodeURIComponent('Booking request — ' + g('bkFn') + ' ' + g('bkLn'))}&body=${encodeURIComponent(msg)}`;
    }
    goStep(5);
  }

  // ===== Tailor-Made Enquiry =====
  function sendTailor(){
    const g = id => document.getElementById(id).value.trim();
    if (!g('tmFn') || !g('tmEm') || !g('tmEnq')) { alert('Please fill in the required fields.'); return; }
    const body = `Name: ${g('tmFn')} ${g('tmLn')}\nEmail: ${g('tmEm')}\n\n${g('tmEnq')}`;
    location.href = `mailto:info@everflowexperience.com?subject=${encodeURIComponent('Tailor-Made Enquiry — ' + g('tmFn') + ' ' + g('tmLn'))}&body=${encodeURIComponent(body)}`;
  }

  // ===== Leaflet map (identical to original) =====
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof L === 'undefined') return;
    var map = L.map('mapa-custom', { center: [47.3, 11.0], zoom: 8, zoomControl: false, scrollWheelZoom: false });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: '', subdomains: 'abcd', maxZoom: 19 }).addTo(map);

    function createCustomIcon(labelHtml, cssClass) {
      return L.divIcon({
        className: 'custom-div-icon',
        html: `
          <div class="pin-wrapper">
            <svg class="pin-svg" width="40" height="52" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="position:absolute; top:0; left:0;">
              <path d="M12 0C7.58 0 4 3.58 4 8C4 13.5 12 24 12 24C12 24 20 13.5 20 8C20 3.58 16.42 0 12 0ZM12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11Z" fill="#1a1a1a"/>
              <circle cx="12" cy="8" r="2.5" fill="white"/>
            </svg>
            <div class="label-container ${cssClass}">${labelHtml}</div>
          </div>`,
        iconSize: [40, 52],
        iconAnchor: [20, 52]
      });
    }

    var iconMunich = createCustomIcon('MUNICH', 'text-munich');
    L.marker([48.1351, 11.5820], {icon: iconMunich}).addTo(map).on('click', () => {
      window.open('https://goo.gl/maps/place/Munich', '_blank');
    });

    var iconGarmisch = createCustomIcon('GARMISCH<br>PARTENKIRCHEN', 'text-garmisch');
    L.marker([47.4917, 11.0955], {icon: iconGarmisch}).addTo(map).on('click', () => {
      window.open('https://goo.gl/maps/place/Garmisch-Partenkirchen', '_blank');
    });

    var iconStMoritz = createCustomIcon('ST. MORITZ', 'text-stmoritz');
    L.marker([46.4984, 9.8391], {icon: iconStMoritz}).addTo(map).on('click', () => {
      window.open('https://goo.gl/maps/place/St.+Moritz', '_blank');
    });

    var germanyLabel = L.divIcon({ className: 'country-label', html: 'GERMANY', iconSize: [100, 40], iconAnchor: [50, 20] });
    L.marker([47.8, 10.5], {icon: germanyLabel, interactive: false}).addTo(map);
    var austriaLabel = L.divIcon({ className: 'country-label', html: 'AUSTRIA', iconSize: [100, 40], iconAnchor: [50, 20] });
    L.marker([47.2, 11.8], {icon: austriaLabel, interactive: false}).addTo(map);
  });
