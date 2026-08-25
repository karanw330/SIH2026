// Nav scroll state
  const nav = document.getElementById('nav');
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  });

  // Mobile menu
  const burger = document.getElementById('burger');
  const mobileMenu = document.getElementById('mobile-menu');
  burger.addEventListener('click', () => mobileMenu.classList.toggle('open'));
  mobileMenu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => mobileMenu.classList.remove('open')));

  // Scroll reveal
  const revealEls = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  revealEls.forEach(el => io.observe(el));

  // Live clock + ticking mock telemetry
  function pad(n){ return n.toString().padStart(2,'0'); }
  function updateClock(){
    const d = new Date();
    const t = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())} IST`;
    const hc = document.getElementById('hero-clock');
    if (hc) hc.innerHTML = `UPDATED <b>${t}</b>`;
  }
  updateClock();
  setInterval(updateClock, 1000);

  function jitter(el, base, min, max, suffix){
    if(!el) return;
    let v = base + (Math.random()*4 - 2);
    v = Math.max(min, Math.min(max, v));
    el.textContent = Math.round(v) + suffix;
  }
  setInterval(() => {
    jitter(document.getElementById('wx-rain-hw'), 83, 77, 91, ' mm');
    jitter(document.getElementById('wx-soil-hw'), 77, 71, 84, '%');
  }, 3200);

  // Hero cards: mouse-follow glow (radial gradient tracks cursor position)
  document.querySelectorAll('.hcard').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', `${e.clientX - r.left}px`);
      card.style.setProperty('--my', `${e.clientY - r.top}px`);
    });
  });

  // Animated counters (stats section)
  const counters = document.querySelectorAll('#stats .s-num');
  const counterIO = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      counterIO.unobserve(el);
      if (el.dataset.text) { el.textContent = el.dataset.text; return; }
      const target = parseInt(el.dataset.count, 10);
      const suffix = el.dataset.suffix || '';
      let cur = 0;
      const step = Math.max(1, Math.ceil(target / 40));
      const t = setInterval(() => {
        cur += step;
        if (cur >= target) { cur = target; clearInterval(t); }
        el.textContent = cur + suffix;
      }, 30);
    });
  }, { threshold: 0.4 });
  counters.forEach(c => counterIO.observe(c));

  // GIS map: marker click -> side panel + layer toggles (visual only)
  const riskLabel = { crit:['Critical','risk-crit'], high:['High','risk-high'], mod:['Moderate','risk-mod'], low:['Low','risk-low'] };
  document.querySelectorAll('#map-stage .marker').forEach(m => {
    m.addEventListener('click', () => {
      document.getElementById('sp-name').textContent = m.dataset.name;
      document.getElementById('sp-rain').textContent = m.dataset.rain === '—' ? '—' : m.dataset.rain + ' mm';
      document.getElementById('sp-soil').textContent = m.dataset.soil === '—' ? '—' : m.dataset.soil + '%';
      document.getElementById('sp-road').textContent = m.dataset.road;
      document.getElementById('sp-ai').textContent = m.dataset.ai;
      const chip = document.getElementById('sp-risk');
      const [label, cls] = riskLabel[m.dataset.risk];
      chip.className = 'risk-chip ' + cls;
      chip.innerHTML = '<span class="sw"></span>' + label;
    });
  });
  document.querySelectorAll('.map-ctrl-btn').forEach(btn => {
    btn.addEventListener('click', () => btn.classList.toggle('active'));
  });
