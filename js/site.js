/* Titanym site motion: 3D wafers, scroll cutaway, compare diagram, entrances, contact form. */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };
  var easeInOut = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };

  /* Wafer layers are stacks of thin discs, which gives each layer real thickness in 3D. */
  document.querySelectorAll('.w-layer[data-slices]').forEach(function (layer) {
    var n = parseInt(layer.dataset.slices, 10);
    var frag = document.createDocumentFragment();
    for (var i = 0; i < n; i++) {
      var s = document.createElement('div');
      s.className = 'slice' + (i === n - 1 ? ' face' : '');
      s.style.setProperty('--i', i);
      frag.appendChild(s);
    }
    layer.insertBefore(frag, layer.firstChild);
  });

  /* Split headings into words that rise into place. */
  document.querySelectorAll('[data-split]').forEach(function (el) {
    var idx = 0;
    var walk = function (node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (child) {
        if (child.nodeType === 3) {
          var parts = child.textContent.split(/(\s+)/);
          var frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(' ')); return; }
            var w = document.createElement('span');
            w.className = 'w';
            var inner = document.createElement('span');
            inner.textContent = p;
            inner.style.setProperty('--i', idx++);
            w.appendChild(inner);
            frag.appendChild(w);
          });
          node.replaceChild(frag, child);
        } else if (child.nodeType === 1) {
          walk(child);
        }
      });
    };
    walk(el);
    el.classList.add('split');
  });

  /* Entrances, staggered among siblings. */
  var revealables = document.querySelectorAll('[data-reveal], [data-rise], [data-split]');
  revealables.forEach(function (el) {
    var sibs = el.parentElement ? el.parentElement.querySelectorAll(':scope > [data-reveal]') : [];
    var i = Array.prototype.indexOf.call(sibs, el);
    if (i > 0) el.style.setProperty('--delay', Math.min(i, 5) * 0.09 + 's');
  });
  if ('IntersectionObserver' in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    revealables.forEach(function (el) { io.observe(el); });
  } else {
    revealables.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* Header, progress bar and mobile menu. */
  var bar = document.getElementById('bar');
  var progress = document.getElementById('progress');
  var toggle = document.getElementById('menu-toggle');
  var menu = document.getElementById('menu');
  var setMenu = function (open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    menu.classList.toggle('is-open', open);
    if (open) bar.classList.add('is-solid');
  };
  toggle.addEventListener('click', function () { setMenu(toggle.getAttribute('aria-expanded') !== 'true'); });
  menu.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

  /* Hero wafer follows the pointer a little. */
  var hero = document.querySelector('.hero');
  var heroWafer = document.getElementById('hero-wafer');
  var tilt = { x: 0, y: 0, tx: 0, ty: 0 };
  if (!reduced && window.matchMedia('(pointer: fine)').matches) {
    hero.addEventListener('pointermove', function (e) {
      var r = hero.getBoundingClientRect();
      tilt.tx = ((e.clientY - r.top) / r.height - .5) * -14;
      tilt.ty = ((e.clientX - r.left) / r.width - .5) * 14;
    });
    hero.addEventListener('pointerleave', function () { tilt.tx = 0; tilt.ty = 0; });
  }

  /* Hero signal field: a dot grid that ripples outward from the wafer. */
  var canvas = document.getElementById('field');
  var ctx = canvas.getContext('2d');
  var field = { w: 0, h: 0, dpr: 1, cx: 0, cy: 0, on: true };
  var sizeField = function () {
    var r = hero.getBoundingClientRect();
    field.dpr = Math.min(window.devicePixelRatio || 1, 2);
    field.w = r.width; field.h = r.height;
    canvas.width = Math.round(r.width * field.dpr);
    canvas.height = Math.round(r.height * field.dpr);
    var wr = heroWafer.getBoundingClientRect();
    field.cx = wr.left - r.left + wr.width / 2;
    field.cy = wr.top - r.top + wr.height / 2;
  };
  var drawField = function (t) {
    ctx.setTransform(field.dpr, 0, 0, field.dpr, 0, 0);
    ctx.clearRect(0, 0, field.w, field.h);
    var gap = field.w < 700 ? 24 : 30;
    var maxD = Math.hypot(field.w, field.h);
    for (var y = gap / 2; y < field.h; y += gap) {
      for (var x = gap / 2; x < field.w; x += gap) {
        var dx = x - field.cx, dy = y - field.cy;
        var d = Math.sqrt(dx * dx + dy * dy);
        var v = Math.sin(d * 0.032 - t * 1.5);
        var peak = v > 0 ? v * v * v : 0;
        var fall = 1 - d / maxD;
        var a = 0.07 + 0.5 * peak * fall;
        var push = peak * 3 / (d || 1);
        var px = x + dx * push, py = y + dy * push;
        ctx.fillStyle = peak > 0.55 && fall > 0.55 ? 'rgba(240,192,96,' + a + ')' : 'rgba(143,163,184,' + a + ')';
        ctx.fillRect(px - 0.9, py - 0.9, 1.8, 1.8);
      }
    }
  };
  sizeField();
  window.addEventListener('resize', sizeField);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (e) { field.on = e[0].isIntersecting; }).observe(hero);
  }

  /* Problem diagram: today versus Titanym. */
  var fig = document.getElementById('compare-fig');
  var swBtns = fig.querySelectorAll('.compare-switch button');
  var thumb = fig.querySelector('.switch-thumb');
  var userPicked = false;
  var placeThumb = function () {
    var on = fig.querySelector('.compare-switch button[aria-pressed="true"]');
    thumb.style.setProperty('--tl', on.offsetLeft + 'px');
    thumb.style.setProperty('--tw', on.offsetWidth + 'px');
  };
  var setMode = function (mode) {
    fig.dataset.mode = mode;
    swBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.mode === mode)); });
    placeThumb();
  };
  swBtns.forEach(function (b) {
    b.addEventListener('click', function () { userPicked = true; setMode(b.dataset.mode); });
  });
  placeThumb();
  window.addEventListener('resize', placeThumb);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeThumb);
  var cycle = null;
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      var vis = entries[0].isIntersecting;
      clearInterval(cycle);
      if (vis && !userPicked) {
        setTimeout(function () { if (!userPicked) setMode('titanym'); }, 1200);
        cycle = setInterval(function () {
          if (userPicked) return clearInterval(cycle);
          setMode(fig.dataset.mode === 'today' ? 'titanym' : 'today');
        }, 5200);
      }
    }, { threshold: 0.5 }).observe(fig);
  }

  /* Pinned cutaway: scroll pulls the wafer apart and walks through each layer. */
  var tech = document.getElementById('technology');
  var cut = document.getElementById('cut-wafer');
  var visual = cut.parentElement;
  var steps = document.querySelectorAll('#steps .step');
  var dots = document.querySelectorAll('#step-dots i');
  var tags = document.querySelectorAll('.w-tag');
  var faces = {};
  cut.querySelectorAll('.w-layer').forEach(function (l) { faces[l.dataset.tag] = l.querySelector('.face'); });
  var current = -1;
  var updateTech = function () {
    var r = tech.getBoundingClientRect();
    var run = r.height - window.innerHeight;
    var p = clamp(-r.top / run, 0, 1);
    var idx = Math.min(steps.length - 1, Math.floor(p * steps.length));
    var d = cut.offsetWidth;
    var ex = easeInOut(clamp(p / 0.18, 0, 1)) * d * 0.3;
    cut.style.setProperty('--ex', ex.toFixed(2));
    cut.style.setProperty('--rz', (-34 + p * 64).toFixed(2) + 'deg');
    if (idx !== current) {
      current = idx;
      steps.forEach(function (s, i) { s.classList.toggle('is-on', i === idx); });
      dots.forEach(function (s, i) { s.classList.toggle('is-on', i === idx); });
      cut.dataset.layer = steps[idx].dataset.layer;
    }
    if (r.bottom < 0 || r.top > window.innerHeight) return;
    var vr = visual.getBoundingClientRect();
    var show = ex > d * 0.08;
    var layer = cut.dataset.layer;
    tags.forEach(function (tag) {
      var f = faces[tag.dataset.for].getBoundingClientRect();
      var w = tag.offsetWidth;
      var x = f.right - vr.left + 12;
      var y = f.top + f.height / 2 - vr.top - 8;
      x = Math.min(x, vr.width - w);
      tag.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
      tag.style.opacity = show ? '' : '0';
      tag.classList.toggle('is-dim', layer !== 'all' && layer !== 'int' && layer !== tag.dataset.for);
    });
  };

  /* One frame loop for everything that moves continuously. */
  var start = performance.now();
  var lastScroll = -1;
  var frame = function (now) {
    var y = window.scrollY;
    if (y !== lastScroll) {
      lastScroll = y;
      bar.classList.toggle('is-solid', y > 24 || menu.classList.contains('is-open'));
      var max = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.transform = 'scaleX(' + (max > 0 ? y / max : 0).toFixed(4) + ')';
    }
    updateTech();
    tilt.x += (tilt.tx - tilt.x) * 0.08;
    tilt.y += (tilt.ty - tilt.y) * 0.08;
    heroWafer.style.setProperty('--tx', tilt.x.toFixed(2) + 'deg');
    heroWafer.style.setProperty('--ty', tilt.y.toFixed(2) + 'deg');
    if (field.on) drawField((now - start) / 1000);
    if (!reduced) requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
  if (reduced) {
    var still = function () { requestAnimationFrame(frame); };
    window.addEventListener('scroll', still, { passive: true });
    window.addEventListener('resize', still);
    document.querySelectorAll('svg').forEach(function (s) { if (s.pauseAnimations) s.pauseAnimations(); });
  }

  /* Lattice drawing for the materials card. */
  var lat = document.getElementById('lattice');
  if (lat) {
    var ns = 'http://www.w3.org/2000/svg';
    for (var row = 0; row < 8; row++) {
      for (var col = 0; col < 16; col++) {
        var cx = 14 + col * 14 + (row % 2 ? 7 : 0);
        var cy = 11 + row * 14;
        if (cx > 232) continue;
        var c = document.createElementNS(ns, 'circle');
        c.setAttribute('cx', cx);
        c.setAttribute('cy', cy);
        c.setAttribute('r', 3.2);
        if ((row * 3 + col) % 5 === 0) c.setAttribute('class', 'ge');
        c.style.setProperty('--d', Math.round(Math.hypot(cx - 120, cy - 60) * 18));
        lat.appendChild(c);
      }
    }
  }

  /* Contact form: posts to Formspree and reports success only on an OK response. */
  var form = document.getElementById('contact-form');
  var status = document.getElementById('form-status');
  var submit = document.getElementById('contact-submit');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      submit.disabled = true;
      status.textContent = 'Sending...';
      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'Accept': 'application/json' }
      }).then(function (r) {
        if (r.ok) {
          status.textContent = 'Message sent. We will be in touch.';
          form.reset();
        } else {
          status.textContent = 'Something went wrong. Please email contact@titanym.com directly.';
        }
      }).catch(function () {
        status.textContent = 'Something went wrong. Please email contact@titanym.com directly.';
      }).then(function () {
        submit.disabled = false;
      });
    });
  }
})();
