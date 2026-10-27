(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Hero name rises in once the page is ready */
  requestAnimationFrame(function () { document.body.classList.add('loaded'); });

  /* Staggered entrances, once per element */
  var groups = new Map();
  document.querySelectorAll('[data-reveal]').forEach(function (el) {
    var sec = el.closest('section, footer') || document.body;
    var i = groups.get(sec) || 0;
    el.style.setProperty('--d', Math.min(i, 6) * 80 + 'ms');
    groups.set(sec, i + 1);
  });
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    document.querySelectorAll('[data-reveal]').forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll('[data-reveal]').forEach(function (el) { el.classList.add('in'); });
  }

  /* Header takes the colour of the chapter beneath it */
  var bar = document.getElementById('bar');
  var chapters = Array.prototype.slice.call(document.querySelectorAll('[data-chapter]')).filter(function (el) { return el !== bar; });
  var navLinks = document.querySelectorAll('.bar-nav a');
  var hero = document.querySelector('.hero-media img');
  var cut = document.getElementById('cutaway');
  var ticking = false;

  function onScroll() {
    ticking = false;
    var probe = bar.offsetHeight / 2;
    for (var i = 0; i < chapters.length; i++) {
      var r = chapters[i].getBoundingClientRect();
      if (r.top <= probe && r.bottom > probe) {
        var c = chapters[i].getAttribute('data-chapter');
        if (bar.getAttribute('data-chapter') !== c) bar.setAttribute('data-chapter', c);
        var id = chapters[i].id;
        navLinks.forEach(function (a) { a.classList.toggle('is-active', a.getAttribute('href') === '#' + id); });
        break;
      }
    }
    var vh = window.innerHeight;
    /* hero picture drifts with the scroll */
    if (hero && !reduce) {
      var y = Math.min(window.scrollY, vh);
      hero.parentElement.style.transform = 'translateY(' + (y * 0.12).toFixed(1) + 'px)';
    }
    /* the wafer pulls apart as it comes into view */
    if (cut) {
      var cr = cut.getBoundingClientRect();
      var p = reduce ? 1 : (vh - cr.top) / (vh * 0.75);
      p = Math.max(0, Math.min(1, p));
      cut.style.setProperty('--e', p.toFixed(3));
    }
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();

  /* Mobile menu */
  var toggle = document.getElementById('menu-toggle');
  var menu = document.getElementById('menu');
  function setMenu(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    menu.classList.toggle('open', open);
  }
  toggle.addEventListener('click', function () { setMenu(toggle.getAttribute('aria-expanded') !== 'true'); });
  menu.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

  /* Wafer layer tabs, also driven by clicking the drawing */
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  function select(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    });
    cut.setAttribute('data-layer', tab.getAttribute('data-layer'));
    if (focus) tab.focus();
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { select(t); });
    t.addEventListener('keydown', function (e) {
      var n = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (n) { e.preventDefault(); select(tabs[(i + n + tabs.length) % tabs.length], true); }
    });
  });
  if (tabs.length) select(tabs[0]);
  cut.querySelectorAll('.layer').forEach(function (g) {
    g.addEventListener('click', function () {
      var t = tabs.filter(function (x) { return x.getAttribute('data-layer') === g.getAttribute('data-layer'); })[0];
      if (t) select(t);
    });
  });

  /* Applications open one at a time */
  var rows = document.querySelectorAll('.app-row');
  rows.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var open = btn.getAttribute('aria-expanded') === 'true';
      rows.forEach(function (b) {
        b.setAttribute('aria-expanded', 'false');
        document.getElementById(b.getAttribute('aria-controls')).hidden = true;
      });
      if (!open) {
        btn.setAttribute('aria-expanded', 'true');
        document.getElementById(btn.getAttribute('aria-controls')).hidden = false;
      }
    });
  });

  /* Contact form: same Formspree endpoint as before. Success is shown only on a real OK response. */
  var form = document.getElementById('contact-form');
  var submitBtn = document.getElementById('contact-submit');
  var statusEl = document.getElementById('form-status');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      submitBtn.textContent = 'Sending...';
      submitBtn.disabled = true;
      statusEl.textContent = '';
      statusEl.className = 'form-status';
      fetch('https://formspree.io/f/xeelnkqj', {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' }
      }).then(function (r) {
        if (r.ok) {
          statusEl.textContent = 'Message sent. We will be in touch.';
          statusEl.classList.add('ok');
          form.reset();
        } else {
          statusEl.textContent = 'Something went wrong. Please email contact@titanym.com directly.';
          statusEl.classList.add('err');
        }
      }).catch(function () {
        statusEl.textContent = 'Something went wrong. Please email contact@titanym.com directly.';
        statusEl.classList.add('err');
      }).then(function () {
        submitBtn.textContent = 'Send message';
        submitBtn.disabled = false;
      });
    });
  }
})();
