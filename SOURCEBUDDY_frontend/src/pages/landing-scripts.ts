/**
 * Landing page interactions.
 *
 * Ported from the <script> blocks in LandingPage.html.
 *
 * The original scripts were top-level IIFEs that assumed they ran exactly
 * once. React StrictMode mounts effects twice in development, so every
 * listener, observer, interval, timeout, RAF, and created DOM node is
 * tracked here and undone by the returned cleanup function.
 *
 * Known limitation: the original page loaded `window.lucide` from a CDN and
 * called lucide.createIcons() to render <i data-lucide="..."> elements.
 * That CDN is intentionally not loaded here (see Batch 6 spec item 15).
 * The icon <i> tags are therefore empty placeholders. Wiring lucide (the
 * vanilla package, not lucide-react) into this file is a follow-up.
 */

type Cleanup = () => void;

export function initLandingPage(): Cleanup {
  // Guard against double-init (e.g. React 18 StrictMode in dev, or a second
  // call before the first cleanup runs).
  if (typeof window === 'undefined') return () => {};
  const w = window as typeof window & { __sbLandingInit?: boolean };
  if (w.__sbLandingInit) {
    // Still return a no-op; the mounted instance owns cleanup.
    return () => {};
  }
  w.__sbLandingInit = true;

  const cleanups: Cleanup[] = [];

  /* ============================================================
   * 1. Live feed ticker
   * ============================================================ */
  const tickerEl = document.getElementById('ticker');
  if (tickerEl) {
    const FEED = [
      '1,200 canvas totes \u2192 Tirupur, IN \u00b7 1.4s',
      '316L flanges \u00d7 400 \u2192 Wenzhou, CN \u00b7 1.7s',
      'LED strip 500 m \u2192 Shenzhen, CN \u00b7 1.2s',
      'kraft mailers 50,000 \u2192 Ahmedabad, IN \u00b7 1.9s',
      'ceramic mugs 2,400 \u2192 Chaozhou, CN \u00b7 1.5s',
      'alu enclosures \u00d7 800 \u2192 Ho Chi Minh City, VN \u00b7 2.1s',
      'organic hoodies 1,500 \u2192 Dhaka, BD \u00b7 1.6s',
      'glass jars 10,000 \u2192 Cairo, EG \u00b7 1.8s',
      'solar connectors 60k \u2192 Izmir, TR \u00b7 1.3s',
      'box springs \u00d7 300 \u2192 Bogot\u00e1, CO \u00b7 2.0s',
    ];
    const group = FEED.map(
      (t) =>
        '<span class="flex items-center gap-3 shrink-0"><span class="w-1 h-1 rounded-full bg-acc/70"></span><span>' +
        t +
        '</span></span>',
    ).join('');
    const previous = tickerEl.innerHTML;
    tickerEl.innerHTML =
      '<div class="flex items-center gap-10 pr-10">' + group + '</div>' +
      '<div class="flex items-center gap-10 pr-10" aria-hidden="true">' + group + '</div>';
    cleanups.push(() => { if (tickerEl) tickerEl.innerHTML = previous; });
  }

  /* ============================================================
   * 2. Procedural night-ocean scene (stars, waves, moonlight, plankton)
   * ============================================================ */
  const NS = 'http://www.w3.org/2000/svg';
  const mk = <K extends keyof SVGElementTagNameMap>(
    tag: K,
    attrs: Record<string, string | number>,
  ): SVGElementTagNameMap[K] => {
    const e = document.createElementNS(NS, tag as string);
    for (const k in attrs) e.setAttribute(k, String(attrs[k]));
    return e as SVGElementTagNameMap[K];
  };

  const STARS: Array<[number, number, number, number]> = [
    [90,60,1.4,.8],[210,150,1.1,.6],[330,40,1.6,.9],[420,220,1,.5],[520,110,1.3,.75],
    [640,60,1,.55],[720,190,1.5,.85],[830,90,1.1,.6],[900,260,1,.45],[1120,70,1.4,.8],
    [1230,180,1.2,.65],[1320,40,1.6,.9],[1400,240,1,.5],[1480,120,1.3,.7],[260,300,1,.4],
    [560,320,1.1,.45],[760,330,1,.4],[1000,300,1.2,.5],[1240,330,1,.4],[1520,60,1,.6],
    [60,200,1.2,.6],[1460,330,1,.35],
  ];
  const WAVES = [
    { y: 410, A: 5,  P: 380, dur: 26, fill: '#1c3b56' },
    { y: 468, A: 9,  P: 420, dur: 20, fill: '#132e4a' },
    { y: 543, A: 13, P: 500, dur: 16, fill: '#0e2339' },
    { y: 628, A: 17, P: 600, dur: 13, fill: '#091b2d' },
    { y: 719, A: 23, P: 700, dur: 10, fill: '#051320' },
    { y: 810, A: 29, P: 800, dur: 8,  fill: '#030b15' },
  ];
  const CRESTS = [1, 2, 3, 4];
  const MOONX = 1040;
  const REFLECT: Array<{ y: number; x: number; w: number; h: number; o: number; dur: number; begin: number; drift: number }> = [];
  for (let i = 0; i < 14; i++) {
    const y = 418 + i * 34;
    const t = i / 13;
    const width = 34 + t * t * 168 + (i % 3) * 12;
    REFLECT.push({
      y,
      x: MOONX - width / 2 + Math.sin(i * 1.7) * (6 + t * 42),
      w: width,
      h: 2.2 + (i % 4) * 0.5,
      o: 0.34 - t * 0.23,
      dur: 2.4 + (i % 5) * 0.9,
      begin: -(i * 0.83),
      drift: (i % 2 ? 1 : -1) * (4 + t * 15),
    });
  }

  const createdNodes: Element[] = [];

  const starEl = (s: [number, number, number, number], i: number): SVGCircleElement => {
    const c = mk('circle', { cx: s[0], cy: s[1], r: s[2], fill: '#ece4cf', opacity: s[3] });
    if (i % 3 === 0) {
      c.appendChild(mk('animate', {
        attributeName: 'opacity',
        values: `${s[3]};${(s[3] * 0.2).toFixed(2)};${s[3]}`,
        dur: `${(2.6 + (i % 5) * 1.4).toFixed(1)}s`,
        begin: `${(-(i * 0.9)).toFixed(1)}s`,
        repeatCount: 'indefinite',
      }));
    }
    return c;
  };

  const waveGroup = (wv: typeof WAVES[number], i: number): SVGGElement => {
    const g = mk('g', {});
    const P = wv.P, A = wv.A, y = wv.y, x0 = -P * 2;
    let x = x0 + P / 2;
    let line = `M ${x0} ${y} q ${P / 4} ${-A} ${P / 2} 0`;
    while (x < 1600 + P * 2) { line += ` t ${P / 2} 0`; x += P / 2; }
    g.appendChild(mk('path', { d: `${line} V 900 H ${x0} Z`, fill: wv.fill }));
    if (CRESTS.indexOf(i) > -1) {
      const crest = mk('path', { d: line, fill: 'none', stroke: 'rgba(170,214,224,.17)', 'stroke-width': 1.4 });
      crest.appendChild(mk('animate', {
        attributeName: 'opacity',
        values: '.5;1;.5',
        dur: `${(wv.dur * 1.6).toFixed(1)}s`,
        repeatCount: 'indefinite',
      }));
      g.appendChild(crest);
    }
    g.appendChild(mk('animateTransform', {
      attributeName: 'transform', type: 'translate',
      from: '0 0', to: `${i % 2 ? P : -P} 0`,
      dur: `${wv.dur}s`, repeatCount: 'indefinite',
    }));
    return g;
  };

  const reflectEl = (r: typeof REFLECT[number]): SVGRectElement => {
    const rect = mk('rect', {
      x: r.x.toFixed(1), y: r.y, width: r.w.toFixed(1), height: r.h.toFixed(1),
      rx: (r.h / 2).toFixed(1), fill: '#ece4cf', opacity: r.o.toFixed(3),
    });
    rect.appendChild(mk('animate', {
      attributeName: 'opacity',
      values: `${r.o.toFixed(3)};${(r.o * 0.2).toFixed(3)};${r.o.toFixed(3)}`,
      dur: `${r.dur.toFixed(1)}s`, begin: `${r.begin.toFixed(2)}s`, repeatCount: 'indefinite',
    }));
    rect.appendChild(mk('animate', {
      attributeName: 'x',
      values: `${r.x.toFixed(1)};${(r.x + r.drift).toFixed(1)};${r.x.toFixed(1)}`,
      dur: `${(r.dur * 1.9).toFixed(1)}s`, begin: `${r.begin.toFixed(2)}s`, repeatCount: 'indefinite',
    }));
    return rect;
  };

  document.querySelectorAll<SVGSVGElement>('svg.scene').forEach((svg) => {
    const stars = svg.querySelector('.js-stars');
    if (stars) STARS.forEach((s, i) => { const el = starEl(s, i); stars.appendChild(el); createdNodes.push(el); });
    const sea = svg.querySelector('.js-sea');
    if (sea) WAVES.forEach((wv, i) => { const el = waveGroup(wv, i); sea.appendChild(el); createdNodes.push(el); });
    const refl = svg.querySelector('.js-reflect');
    if (refl) REFLECT.forEach((r) => { const el = reflectEl(r); refl.appendChild(el); createdNodes.push(el); });
  });

  const spark = document.querySelector('#sceneReveal .js-spark');
  if (spark) {
    for (let i = 0; i < 26; i++) {
      const dur = 2.2 + Math.random() * 3.6;
      const begin = -(Math.random() * dur);
      const o = (0.25 + Math.random() * 0.5).toFixed(2);
      const c = mk('circle', {
        cx: (40 + Math.random() * 1520).toFixed(0),
        cy: (445 + Math.random() * 415).toFixed(0),
        r: (0.9 + Math.random() * 1.5).toFixed(1),
        fill: Math.random() < 0.72 ? '#5fe3c0' : '#cfeee6',
        opacity: 0,
      });
      c.appendChild(mk('animate', {
        attributeName: 'opacity', values: `0;${o};0`,
        dur: `${dur.toFixed(2)}s`, begin: `${begin.toFixed(2)}s`, repeatCount: 'indefinite',
      }));
      c.appendChild(mk('animateTransform', {
        attributeName: 'transform', type: 'translate',
        values: `0 0; ${(Math.random() * 22 - 11).toFixed(1)} ${(-(6 + Math.random() * 16)).toFixed(1)}; 0 0`,
        dur: `${(dur * 2).toFixed(2)}s`, begin: `${begin.toFixed(2)}s`, repeatCount: 'indefinite',
      }));
      spark.appendChild(c);
      createdNodes.push(c);
    }
  }

  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll<SVGSVGElement>('svg').forEach((s) => {
      try { s.pauseAnimations(); } catch { /* ignore */ }
    });
  }

  cleanups.push(() => {
    createdNodes.forEach((n) => n.parentNode?.removeChild(n));
    createdNodes.length = 0;
  });

  /* ============================================================
   * 3. The spotlight
   * ============================================================ */
  const hero = document.getElementById('hero');
  const layer = document.getElementById('revealLayer');
  const canvas = document.getElementById('maskCanvas') as HTMLCanvasElement | null;
  const cross = document.getElementById('crosshair');
  const hint = document.getElementById('spotHint');

  let spotlightRAF = 0;

  if (hero && layer && canvas) {
    const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

    const S = 512;
    canvas.width = canvas.height = S;
    const ctx = canvas.getContext('2d');
    let maskURL = '';
    if (ctx) {
      const grad = ctx.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
      grad.addColorStop(0, 'rgba(255,255,255,1)');
      grad.addColorStop(0.42, 'rgba(255,255,255,.94)');
      grad.addColorStop(0.72, 'rgba(255,255,255,.5)');
      grad.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, S, S);
      maskURL = `url("${canvas.toDataURL()}")`;
    }

    let R = 340;
    let x = hero.clientWidth * 0.58, y = hero.clientHeight * 0.56, tx = x, ty = y;
    let locked = false;
    let lastTouch = -1e5;

    const paint = () => {
      const pos = `${Math.round(x - R)}px ${Math.round(y - R)}px`;
      layer.style.setProperty('-webkit-mask-position', pos);
      layer.style.setProperty('mask-position', pos);
    };
    const sizeMask = () => {
      R = Math.round(Math.min(420, Math.max(240, Math.min(hero.clientWidth, hero.clientHeight) * 0.46)));
      const px = `${R * 2}px`;
      ['-webkit-mask-', 'mask-'].forEach((p) => {
        layer.style.setProperty(p + 'image', maskURL);
        layer.style.setProperty(p + 'repeat', 'no-repeat');
        layer.style.setProperty(p + 'size', px);
      });
      paint();
    };
    sizeMask();

    const onResize = () => sizeMask();
    window.addEventListener('resize', onResize);
    cleanups.push(() => window.removeEventListener('resize', onResize));

    const onPointerMove = (e: PointerEvent) => {
      const r = hero.getBoundingClientRect();
      tx = e.clientX - r.left;
      ty = e.clientY - r.top;
      if (e.pointerType === 'touch') lastTouch = performance.now();
      else locked = true;
      if (fine && cross) {
        (cross as HTMLElement).style.opacity = '1';
        (cross as HTMLElement).style.transform = `translate3d(${e.clientX - 8}px,${e.clientY - 8}px,0)`;
      }
      if (hint) (hint as HTMLElement).style.opacity = '0';
    };
    hero.addEventListener('pointermove', onPointerMove, { passive: true });
    cleanups.push(() => hero.removeEventListener('pointermove', onPointerMove));

    const onPointerLeave = () => { if (cross) (cross as HTMLElement).style.opacity = '0'; };
    hero.addEventListener('pointerleave', onPointerLeave);
    cleanups.push(() => hero.removeEventListener('pointerleave', onPointerLeave));

    const hintTimer = window.setTimeout(() => { if (hint) (hint as HTMLElement).style.opacity = '0'; }, 10000);
    cleanups.push(() => window.clearTimeout(hintTimer));

    const drift = (t: number) => {
      const w = hero.clientWidth, h = hero.clientHeight, s = t / 1000;
      return {
        x: w * 0.52 + Math.sin(s * 0.19) * w * 0.23 + Math.sin(s * 0.043 + 2) * w * 0.09,
        y: h * 0.56 + Math.cos(s * 0.16) * h * 0.17 + Math.sin(s * 0.071) * h * 0.07,
      };
    };

    const frame = (t: number) => {
      if (window.scrollY < window.innerHeight * 1.05) {
        if (!locked && !reduced && performance.now() - lastTouch > 2600) {
          const d = drift(t);
          tx = d.x; ty = d.y;
        }
        x += (tx - x) * 0.085;
        y += (ty - y) * 0.085;
        paint();
      }
      spotlightRAF = requestAnimationFrame(frame);
    };
    spotlightRAF = requestAnimationFrame(frame);
    cleanups.push(() => cancelAnimationFrame(spotlightRAF));
  }

  /* ============================================================
   * 4. Nav + mobile menu
   * ============================================================ */
  const nav = document.getElementById('nav');
  const navLinks = Array.from(document.querySelectorAll<HTMLAnchorElement>('.nav-link'));
  const sectionIds = ['hero', 'how', 'stats', 'feedback', 'cta'];
  const sections = sectionIds.map((id) => document.getElementById(id));
  let lastY = window.scrollY;

  const onScrollNav = () => {
    if (!nav) return;
    const y = window.scrollY;
    nav.classList.toggle('scrolled', y > 40);
    if (y > 160 && y > lastY + 4) nav.classList.add('nav-hide');
    else if (y < lastY - 4 || y <= 160) nav.classList.remove('nav-hide');
    lastY = y;

    const mark = y + window.innerHeight * 0.38;
    let idx = 0;
    sections.forEach((s, i) => { if (s && mark >= (s as HTMLElement).offsetTop) idx = i; });
    navLinks.forEach((l, i) => l.classList.toggle('active', i === idx));
  };
  window.addEventListener('scroll', onScrollNav, { passive: true });
  cleanups.push(() => window.removeEventListener('scroll', onScrollNav));
  onScrollNav();

  const mmenu = document.getElementById('mmenu');
  const menuBtn = document.getElementById('menuBtn');
  const menuClose = document.getElementById('menuClose');

  const setMenu = (open: boolean) => {
    if (!mmenu) return;
    mmenu.classList.toggle('open', open);
    mmenu.classList.toggle('opacity-0', !open);
    mmenu.classList.toggle('pointer-events-none', !open);
    document.documentElement.style.overflow = open ? 'hidden' : '';
  };

  const onMenuBtn = () => setMenu(true);
  const onMenuClose = () => setMenu(false);
  if (menuBtn) menuBtn.addEventListener('click', onMenuBtn);
  if (menuClose) menuClose.addEventListener('click', onMenuClose);
  cleanups.push(() => {
    if (menuBtn) menuBtn.removeEventListener('click', onMenuBtn);
    if (menuClose) menuClose.removeEventListener('click', onMenuClose);
  });

  const mmenuLinks = mmenu ? Array.from(mmenu.querySelectorAll<HTMLAnchorElement>('a')) : [];
  const onMmenuLink = () => setMenu(false);
  mmenuLinks.forEach((a) => a.addEventListener('click', onMmenuLink));
  cleanups.push(() => mmenuLinks.forEach((a) => a.removeEventListener('click', onMmenuLink)));

  /* ============================================================
   * 5. Scroll reveals
   * ============================================================ */
  const revealEls = Array.from(document.querySelectorAll('.reveal'));
  let revealIO: IntersectionObserver | null = null;
  if (!('IntersectionObserver' in window)) {
    revealEls.forEach((el) => el.classList.add('in'));
  } else {
    revealIO = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add('in');
          revealIO?.unobserve(en.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    revealEls.forEach((el) => revealIO!.observe(el));
  }
  cleanups.push(() => { revealIO?.disconnect(); });

  /* ============================================================
   * 6. Step spine + depth gauge
   * ============================================================ */
  const steps = document.getElementById('howSteps');
  const spine = document.getElementById('spineFill');
  const rail = document.getElementById('gaugeRail');
  const fill = document.getElementById('gaugeFill');
  const dot = document.getElementById('gaugeDot');
  const val = document.getElementById('gaugeVal');
  const DEPTHS = ['SURFACE', '\u2212200 M', '\u2212800 M', '\u22122000 M', '\u22124000 M', 'THE DEEP'];

  const onScrollGauge = () => {
    if (steps && spine) {
      const r = steps.getBoundingClientRect();
      const track = r.height - 52;
      const p = Math.max(0, Math.min(1, (window.innerHeight * 0.78 - r.top) / r.height));
      spine.style.height = `${Math.round(p * track)}px`;
    }
    if (rail && fill && dot) {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      const h = rail.offsetHeight;
      fill.style.height = `${(p * h).toFixed(1)}px`;
      dot.style.top = `${(p * h - 4).toFixed(1)}px`;
      if (val) {
  const idx = Math.min(DEPTHS.length - 1, Math.floor(p * DEPTHS.length));
  val.textContent = DEPTHS[idx] ?? DEPTHS[DEPTHS.length - 1] ?? 'SURFACE';
}
    }
  };
  window.addEventListener('scroll', onScrollGauge, { passive: true });
  window.addEventListener('resize', onScrollGauge);
  cleanups.push(() => {
    window.removeEventListener('scroll', onScrollGauge);
    window.removeEventListener('resize', onScrollGauge);
  });
  onScrollGauge();

  /* ============================================================
   * 7. Count-up stats
   * ============================================================ */
  const counters = Array.from(document.querySelectorAll<HTMLElement>('[data-count]'));
  let countIO: IntersectionObserver | null = null;
  const countRAFs = new Set<number>();

  const play = (el: HTMLElement) => {
    const target = parseFloat(el.getAttribute('data-count') || '0');
    const dec = parseInt(el.getAttribute('data-dec') || '0', 10);
    const t0 = performance.now(), D = 1800;
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / D);
      const v = target * (1 - Math.pow(1 - p, 4));
      el.textContent = dec ? v.toFixed(dec) : Math.round(v).toLocaleString('en-US');
      if (p < 1) {
        const id = requestAnimationFrame(tick);
        countRAFs.add(id);
      }
    };
    const id = requestAnimationFrame(tick);
    countRAFs.add(id);
  };

  if (counters.length) {
    if (!('IntersectionObserver' in window)) {
      counters.forEach(play);
    } else {
      countIO = new IntersectionObserver((entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            play(en.target as HTMLElement);
            countIO?.unobserve(en.target);
          }
        });
      }, { threshold: 0.5 });
      counters.forEach((n) => countIO!.observe(n));
    }
  }
  cleanups.push(() => {
    countIO?.disconnect();
    countRAFs.forEach((id) => cancelAnimationFrame(id));
    countRAFs.clear();
  });

  /* ============================================================
   * 8. Early access form
   * ============================================================ */
  const waitForm = document.getElementById('waitForm') as HTMLFormElement | null;
  if (waitForm) {
    const input = document.getElementById('waitEmail') as HTMLInputElement | null;
    const err = document.getElementById('waitErr');
    const wrap = document.getElementById('waitWrap');
    const esc = (s: string) =>
      s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] ?? c));
    const wrapSnapshot = wrap ? wrap.innerHTML : '';

    const onSubmit = (e: Event) => {
      e.preventDefault();
      if (!input || !err || !wrap) return;
      const v = (input.value || '').trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) {
        err.textContent = "That doesn't look like an email \u2014 mind double-checking it?";
        err.classList.remove('hidden');
        input.focus();
        return;
      }
      wrap.innerHTML =
        '<div class="flex flex-col items-center gap-4 py-3">' +
          '<span class="grid place-items-center w-12 h-12 rounded-full border border-acc/40 bg-acc/10 text-acc"><i data-lucide="anchor" class="w-5 h-5"></i></span>' +
          '<p class="font-display italic text-3xl text-white">You&rsquo;re on the manifest.</p>' +
          '<p class="text-sm text-white/55 -mt-2">Your invite drops anchor at <span class="mono text-xs text-acc">' + esc(v) + '</span> \u2014 exactly one email, then silence.</p>' +
        '</div>';
    };
    const onInput = () => { err?.classList.add('hidden'); };

    waitForm.addEventListener('submit', onSubmit);
    input?.addEventListener('input', onInput);
    cleanups.push(() => {
      waitForm.removeEventListener('submit', onSubmit);
      input?.removeEventListener('input', onInput);
      if (wrap) wrap.innerHTML = wrapSnapshot;
    });
  }

  /* ============================================================
   * 9. Profile dropdown + toast
   * ============================================================ */
  const pBtn = document.getElementById('profileBtn');
  const pMenu = document.getElementById('profileMenu');
  let toastEl: HTMLElement | null = null;
  let toastTimer = 0;

  if (pBtn && pMenu) {
    let open = false;
    const set = (v: boolean) => {
      open = v;
      pMenu.classList.toggle('open', open);
      pMenu.setAttribute('aria-hidden', open ? 'false' : 'true');
      pBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      pBtn.classList.toggle('ring-open', open);
    };

    const showToast = (msg: string) => {
      if (!toastEl) {
        toastEl = document.createElement('div');
        toastEl.id = 'toast';
        document.body.appendChild(toastEl);
      }
      toastEl.innerHTML = '<i data-lucide="anchor" class="w-4 h-4 text-acc shrink-0"></i><span>' + msg + '</span>';
      requestAnimationFrame(() => requestAnimationFrame(() => toastEl?.classList.add('show')));
      window.clearTimeout(toastTimer);
      toastTimer = window.setTimeout(() => toastEl?.classList.remove('show'), 3200);
    };

    const onBtn = (e: MouseEvent) => { e.stopPropagation(); set(!open); };
    const onDocClick = (e: MouseEvent) => {
      if (open && e.target instanceof Node && !pMenu.contains(e.target)) set(false);
    };
    const onDocKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        set(false);
        (pBtn as HTMLElement).focus();
      }
    };
    const onScrollClose = () => { if (open) set(false); };
    const onResizeClose = () => { if (open) set(false); };

    pBtn.addEventListener('click', onBtn);
    document.addEventListener('click', onDocClick);
    document.addEventListener('keydown', onDocKey);
    window.addEventListener('scroll', onScrollClose, { passive: true });
    window.addEventListener('resize', onResizeClose);

    const pLinks = Array.from(pMenu.querySelectorAll<HTMLAnchorElement>('a'));
    const pHandlers = pLinks.map((a) => {
      const h = (e: Event) => {
        if (a.classList.contains('pitem')) {
          e.preventDefault();
          showToast(a.getAttribute('data-toast') || '');
        }
        set(false);
      };
      a.addEventListener('click', h);
      return { a, h };
    });

    cleanups.push(() => {
      pBtn.removeEventListener('click', onBtn);
      document.removeEventListener('click', onDocClick);
      document.removeEventListener('keydown', onDocKey);
      window.removeEventListener('scroll', onScrollClose);
      window.removeEventListener('resize', onResizeClose);
      pHandlers.forEach(({ a, h }) => a.removeEventListener('click', h));
      window.clearTimeout(toastTimer);
      if (toastEl) {
        toastEl.remove();
        toastEl = null;
      }
    });
  }

  /* ============================================================
   * 10. Feedback form
   * ============================================================ */
  const fbForm = document.getElementById('fbForm') as HTMLFormElement | null;
  if (fbForm) {
    const types = Array.from(fbForm.querySelectorAll<HTMLButtonElement>('.fb-type'));
    const rates = Array.from(fbForm.querySelectorAll<HTMLButtonElement>('.fb-rate'));
    const rateRow = document.getElementById('fbRate');
    const rateWord = document.getElementById('fbRateWord');
    const msg = document.getElementById('fbMsg') as HTMLTextAreaElement | null;
    const count = document.getElementById('fbCount');
    const email = document.getElementById('fbEmail') as HTMLInputElement | null;
    const err = document.getElementById('fbErr');
    const done = document.getElementById('fbDone');
    const summary = document.getElementById('fbSummary');
    const again = document.getElementById('fbAgain');

    const WORDS: Record<number, string> = { 1: 'TROUBLED WATERS', 2: 'CHOPPY SEAS', 3: 'FAIR WINDS', 4: 'SMOOTH SAILING', 5: 'FULL SAIL' };
    const TYPES: Record<string, string> = { idea: 'FEATURE IDEA', broken: 'SOMETHING\u2019S BROKEN', praise: 'PRAISE FOR THE CREW', supplier: 'MISSING SUPPLIER' };
    let type = 'idea';
    let rating = 0;

    const typeHandlers = types.map((b) => {
      const h = () => {
        type = b.getAttribute('data-val') || 'idea';
        types.forEach((x) => x.classList.toggle('is-on', x === b));
      };
      b.addEventListener('click', h);
      return { b, h };
    });

    const paint = (n: number) => {
      rates.forEach((r, i) => {
        r.classList.toggle('on', i < n);
        r.setAttribute('aria-checked', i === n - 1 ? 'true' : 'false');
      });
    };

    const rateClickHandlers = rates.map((r, i) => {
      const h = () => {
        rating = i + 1;
        if (rateWord) rateWord.textContent = WORDS[rating] ?? '';
        paint(rating);
      };
      r.addEventListener('click', h);
      return { r, h };
    });
    const rateHoverHandlers = rates.map((r, i) => {
      const h = () => paint(i + 1);
      r.addEventListener('mouseenter', h);
      r.addEventListener('focus', h);
      return { r, h };
    });
    const rateRowLeave = () => paint(rating);
    rateRow?.addEventListener('mouseleave', rateRowLeave);

    const onMsgInput = () => {
      if (count && msg) count.textContent = `${msg.value.length} / 600`;
      err?.classList.add('hidden');
    };
    const onEmailInput = () => err?.classList.add('hidden');
    msg?.addEventListener('input', onMsgInput);
    email?.addEventListener('input', onEmailInput);

    const onSubmit = (e: Event) => {
      e.preventDefault();
      if (!msg || !email || !err) return;
      const m = msg.value.trim();
      const em = email.value.trim();
      if (m.length < 10) {
        err.textContent = 'A few more words would help the crew \u2014 give us at least a sentence.';
        err.classList.remove('hidden');
        msg.focus();
        return;
      }
      if (em && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(em)) {
        err.textContent = 'That reply address doesn\u2019t look quite right \u2014 mind checking it?';
        err.classList.remove('hidden');
        email.focus();
        return;
      }
      if (summary) {
        summary.textContent = [TYPES[type], rating ? WORDS[rating] : 'UNRATED', em ? 'REPLY EXPECTED' : 'ANONYMOUS'].join(' \u00b7 ');
      }
      fbForm.classList.add('hidden');
      done?.classList.remove('hidden');
      done?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };
    fbForm.addEventListener('submit', onSubmit);

    const onAgain = () => {
      if (msg) msg.value = '';
      if (email) email.value = '';
      if (count) count.textContent = '0 / 600';
      rating = 0;
      type = 'idea';
      if (rateWord) rateWord.textContent = 'SET A RATING';
      paint(0);
      types.forEach((x) => x.classList.toggle('is-on', x.getAttribute('data-val') === 'idea'));
      done?.classList.add('hidden');
      fbForm.classList.remove('hidden');
      msg?.focus();
    };
    again?.addEventListener('click', onAgain);

    cleanups.push(() => {
      typeHandlers.forEach(({ b, h }) => b.removeEventListener('click', h));
      rateClickHandlers.forEach(({ r, h }) => r.removeEventListener('click', h));
      rateHoverHandlers.forEach(({ r, h }) => {
        r.removeEventListener('mouseenter', h);
        r.removeEventListener('focus', h);
      });
      rateRow?.removeEventListener('mouseleave', rateRowLeave);
      msg?.removeEventListener('input', onMsgInput);
      email?.removeEventListener('input', onEmailInput);
      fbForm.removeEventListener('submit', onSubmit);
      again?.removeEventListener('click', onAgain);
    });
  }

  /* ============================================================
   * Return the combined cleanup.
   * ============================================================ */
  return () => {
    cleanups.forEach((fn) => {
      try { fn(); } catch { /* individual cleanup failure must not abort the rest */ }
    });
    cleanups.length = 0;
    w.__sbLandingInit = false;
  };
}