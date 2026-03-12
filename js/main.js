/**
 * Titanym — main.js
 * Handles: scroll-based nav, reveal animations,
 * nav scroll-spy, hamburger menu, gauge animation,
 * and subtle parallax on hero.
 */

(function () {
  'use strict';

  /* ─────────────────────────────────────────
     Sticky header
  ───────────────────────────────────────── */
  const header = document.getElementById('site-header');

  function updateHeader() {
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  }

  window.addEventListener('scroll', updateHeader, { passive: true });
  updateHeader();

  /* ─────────────────────────────────────────
     Hamburger / mobile nav
  ───────────────────────────────────────── */
  const hamburger = document.getElementById('nav-hamburger');
  const navLinks  = document.getElementById('nav-links');

  if (hamburger && navLinks) {
    hamburger.addEventListener('click', function () {
      const isOpen = navLinks.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', isOpen);

      const spans = hamburger.querySelectorAll('span');
      if (isOpen) {
        spans[0].style.transform = 'translateY(7px) rotate(45deg)';
        spans[1].style.opacity   = '0';
        spans[2].style.transform = 'translateY(-7px) rotate(-45deg)';
      } else {
        spans[0].style.transform = '';
        spans[1].style.opacity   = '';
        spans[2].style.transform = '';
      }
    });

    // Close on nav link click
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
        const spans = hamburger.querySelectorAll('span');
        spans[0].style.transform = '';
        spans[1].style.opacity   = '';
        spans[2].style.transform = '';
      });
    });
  }

  /* ─────────────────────────────────────────
     Intersection Observer — reveal
  ───────────────────────────────────────── */
  const revealEls = document.querySelectorAll('.reveal');

  const revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.12,
    rootMargin: '0px 0px -40px 0px'
  });

  revealEls.forEach(function (el) {
    revealObserver.observe(el);
  });

  /* ─────────────────────────────────────────
     Gauge needle — animate when visible
  ───────────────────────────────────────── */
  const needle = document.getElementById('gauge-needle');

  if (needle) {
    const gaugeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          needle.classList.add('animated');
          gaugeObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    gaugeObserver.observe(needle);
  }

  /* ─────────────────────────────────────────
     Scroll-spy — highlight active nav link
  ───────────────────────────────────────── */
  const sections  = document.querySelectorAll('section[id], div[id]');
  const navAnchors = document.querySelectorAll('.nav-links a[href^="#"]');

  const spyObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        navAnchors.forEach(function (a) {
          a.classList.toggle('active', a.getAttribute('href') === '#' + id);
        });
      }
    });
  }, {
    rootMargin: '-30% 0px -60% 0px',
    threshold: 0
  });

  sections.forEach(function (section) {
    spyObserver.observe(section);
  });

  /* ─────────────────────────────────────────
     Smooth scroll override for older browsers
  ───────────────────────────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href').slice(1);
      const target   = document.getElementById(targetId);
      if (target) {
        e.preventDefault();
        const offset = 72; // header height
        const top    = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: top, behavior: 'smooth' });
      }
    });
  });

  /* ─────────────────────────────────────────
     Scroll indicator — fade out on scroll
  ───────────────────────────────────────── */
  const scrollIndicator = document.getElementById('scroll-indicator');
  if (scrollIndicator) {
    window.addEventListener('scroll', function () {
      const opacity = Math.max(0, 0.45 - window.scrollY / 300);
      scrollIndicator.style.opacity = opacity;
    }, { passive: true });
  }

  /* ─────────────────────────────────────────
     Stagger children of stat-row and scope-grid
  ───────────────────────────────────────── */
  function staggerChildren(selector, itemSelector) {
    document.querySelectorAll(selector).forEach(function (parent) {
      parent.querySelectorAll(itemSelector).forEach(function (child, index) {
        child.style.transitionDelay = (index * 80) + 'ms';
      });
    });
  }

  staggerChildren('.stat-row',   '.stat-card');
  staggerChildren('.scope-grid', '.scope-item');
  staggerChildren('.qual-cards', '.qual-card');
  staggerChildren('.exec-grid',  '.exec-card');
  staggerChildren('.qual-path',  '.qual-step');

  /* ─────────────────────────────────────────
     Subtle parallax on hero grid
  ───────────────────────────────────────── */
  const heroBgGrid = document.querySelector('.hero-bg-grid');
  if (heroBgGrid) {
    window.addEventListener('scroll', function () {
      const y = window.scrollY;
      heroBgGrid.style.transform = 'translateY(' + (y * 0.15) + 'px)';
    }, { passive: true });
  }

  /* ─────────────────────────────────────────
     Numbers counter for stat cards
  ───────────────────────────────────────── */
  // Minimal: just ensure cards pop in nicely via stagger already set

  /* ─────────────────────────────────────────
     Add link rel stylesheet for enhancements
  ───────────────────────────────────────── */
  (function addEnhancementsCSS() {
    const link = document.createElement('link');
    link.rel  = 'stylesheet';
    link.href = 'css/enhancements.css';
    document.head.appendChild(link);
  }());

})();
