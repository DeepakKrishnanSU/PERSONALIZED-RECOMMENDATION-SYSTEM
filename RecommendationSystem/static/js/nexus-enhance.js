/* NexusAI enhancement layer. Load with defer AFTER app.js. Progressive: page works without it. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover:hover) and (pointer:fine)').matches;
  document.documentElement.classList.add('js');
  const icons = () => window.lucide && typeof window.lucide.createIcons === 'function' && window.lucide.createIcons();

  /* Skip link, main landmark, progress bar */
  const main = $('main');
  if (main) {
    main.id = main.id || 'main';
    main.tabIndex = -1;
  }
  if (!$('.skip-link')) {
    document.body.insertAdjacentHTML('afterbegin', '<a class="skip-link" href="#main">Skip to content</a><div class="scroll-progress" aria-hidden="true"></div>');
  }

  /* Mobile nav */
  const menu = $('.nav-menu'), nc = $('.nav-container');
  if (menu && nc && !$('.nav-toggle', nc)) {
    menu.id = menu.id || 'primaryNav';
    const t = document.createElement('button');
    t.className = 'nav-toggle';
    t.type = 'button';
    t.setAttribute('aria-label', 'Toggle Navigation Menu');
    t.setAttribute('aria-expanded', 'false');
    t.setAttribute('aria-controls', menu.id);
    t.innerHTML = '<i data-lucide="menu"></i>';
    nc.insertBefore(t, $('.nav-actions'));
    const set = o => {
      menu.classList.toggle('open', o);
      t.setAttribute('aria-expanded', o);
      const icon = t.querySelector('i');
      if (icon) {
        icon.setAttribute('data-lucide', o ? 'x' : 'menu');
        icons();
      }
    };
    t.onclick = () => set(!menu.classList.contains('open'));
    menu.addEventListener('click', e => e.target.closest('a') && set(false));
    addEventListener('keydown', e => e.key === 'Escape' && menu.classList.contains('open') && (set(false), t.focus()));
    icons();
  }

  /* Header state + scrollspy + fallback scroll progress */
  const hdr = $('#mainHeader');
  const progressBar = $('.scroll-progress');
  const supportsScrollTimeline = typeof CSS !== 'undefined' && CSS.supports && CSS.supports('animation-timeline', 'scroll()');

  const onScroll = () => {
    if (hdr) hdr.classList.toggle('scrolled', window.scrollY > 24);
    if (progressBar && !supportsScrollTimeline) {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      progressBar.style.transform = max > 0 ? `scaleX(${Math.min(1, Math.max(0, window.scrollY / max))})` : 'scaleX(0)';
    }
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const links = $$('.nav-link');
  if ('IntersectionObserver' in window) {
    const spy = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      links.forEach(l => {
        const on = l.getAttribute('href') === '#' + e.target.id;
        l.classList.toggle('active', on);
        if (on) l.setAttribute('aria-current', 'true');
        else l.removeAttribute('aria-current');
      });
    }), { rootMargin: '-45% 0px -50% 0px' });
    $$('main section[id]').forEach(s => spy.observe(s));
  }

  /* Accessible tabs */
  const tabs = $$('[role=tab]');
  tabs.forEach(b => {
    const p = $('#' + b.dataset.tab);
    if (!p) return;
    b.setAttribute('aria-controls', p.id);
    p.setAttribute('role', 'tabpanel');
    p.setAttribute('aria-labelledby', b.id);
    p.tabIndex = 0;
  });
  const sync = () => tabs.forEach(b => {
    const on = b.classList.contains('active');
    b.setAttribute('aria-selected', on ? 'true' : 'false');
    b.tabIndex = on ? 0 : -1;
  });
  tabs.forEach(b => new MutationObserver(sync).observe(b, { attributes: true, attributeFilter: ['class'] }));
  sync();

  $('[role=tablist]')?.addEventListener('keydown', e => {
    const i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    const n = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
    if (n === undefined) return;
    e.preventDefault();
    const b = tabs[(n + tabs.length) % tabs.length];
    b.focus();
    b.click();
  });

  /* Accessible modals: dialog semantics, focus trap, Esc, backdrop click, focus restore */
  const FOCUS = 'a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])';
  $$('.modal-overlay').forEach(o => {
    const card = $('.modal-card', o), title = $('.modal-title', o), close = $('.modal-close-btn', o);
    if (card) {
      card.setAttribute('role', 'dialog');
      card.setAttribute('aria-modal', 'true');
      if (title) {
        title.id = title.id || (o.id || 'modal') + 'Title';
        card.setAttribute('aria-labelledby', title.id);
      }
    }
    close && close.setAttribute('aria-label', 'Close dialog');
    let last = null, was = o.style.display !== 'none';
    const obs = new MutationObserver(() => {
      const open = o.style.display !== 'none';
      if (open === was) return;
      was = open;
      o.setAttribute('aria-hidden', !open);
      if (open) {
        last = document.activeElement;
        if (card) {
          card.tabIndex = -1;
          const focusable = $$(FOCUS, card).find(x => x !== close) || close || card;
          focusable && focusable.focus();
        }
      } else if (last && last.isConnected) {
        last.focus();
      }
    });
    obs.observe(o, { attributes: true, attributeFilter: ['style'] });
    o.addEventListener('mousedown', e => e.target === o && close?.click());
    o.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        close?.click();
      }
      if (e.key !== 'Tab' || !card) return;
      const f = $$(FOCUS, card).filter(x => x.offsetParent);
      if (!f.length) return;
      const a = f[0], z = f[f.length - 1];
      if (e.shiftKey && document.activeElement === a) {
        e.preventDefault();
        z.focus();
      } else if (!e.shiftKey && document.activeElement === z) {
        e.preventDefault();
        a.focus();
      }
    });
  });

  /* Scroll reveals with stagger */
  if ('IntersectionObserver' in window) {
    const groups = ['.section-heading', '.hero-content > *', '.studio-card', '.results-meta-bar', '.tabular-ranking-card', '.refinement-glass-card', '.intent-box', '.save-vault-banner'];
    const targets = [];
    groups.forEach(g => $$(g).forEach((el, i) => {
      el.setAttribute('data-reveal', '');
      el.style.setProperty('--i', (i % 6).toString());
      targets.push(el);
    }));
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        io.unobserve(e.target);
      }
    }), { threshold: .12, rootMargin: '0px 0px -6% 0px' });
    targets.forEach(el => io.observe(el));
  }

  /* Cursor spotlight (rAF-throttled) and hero terminal 3D tilt */
  if (fine && !reduce) {
    let raf = 0, ev;
    document.addEventListener('pointermove', e => {
      ev = e;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const c = ev.target.closest?.('.studio-card, .recommendation-card, .refinement-glass-card, .intent-box, .save-vault-banner');
        if (c) {
          const r = c.getBoundingClientRect();
          c.style.setProperty('--mx', (ev.clientX - r.left) + 'px');
          c.style.setProperty('--my', (ev.clientY - r.top) + 'px');
        }
      });
    }, { passive: true });

    const term = $('#heroTerminal');
    if (term) {
      term.addEventListener('pointermove', e => {
        const r = term.getBoundingClientRect();
        term.style.setProperty('--ry', (((e.clientX - r.left) / r.width - .5) * 8).toFixed(2) + 'deg');
        term.style.setProperty('--rx', ((.5 - (e.clientY - r.top) / r.height) * 6).toFixed(2) + 'deg');
      });
      term.addEventListener('pointerleave', () => {
        term.style.setProperty('--rx', '0deg');
        term.style.setProperty('--ry', '0deg');
      });
    }
  }
})();
