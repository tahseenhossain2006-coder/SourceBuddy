/**
 * Body markup for the landing page.
 *
 * Extracted verbatim from LandingPage.html <body> inner HTML.
 * Do not edit by hand — regenerate from the source HTML if the design changes.
 */
export const landingBody = String.raw`

<!-- ================= NAV ================= -->
<nav id="nav" class="fixed top-0 inset-x-0 z-[100] transition-all duration-300">
  <div class="flex items-center justify-between px-4 sm:px-6 py-4">
    <a href="#hero" class="flex items-center gap-2.5 shrink-0">
      <svg width="26" height="26" viewBox="0 0 256 256" fill="none" aria-hidden="true">
        <path d="M20 168 Q 76 64 128 168 T 236 168" stroke="#ffffff" stroke-width="26" stroke-linecap="round" fill="none"/>
        <circle cx="128" cy="56" r="22" fill="#5fe3c0"/>
      </svg>
      <span class="font-display italic text-2xl text-white">Source&nbsp;Buddy</span>
    </a>

    <div class="hidden md:flex absolute left-1/2 -translate-x-1/2 items-center gap-1 bg-white/10 backdrop-blur-md border border-white/15 rounded-full px-2 py-2">
      <a href="#hero"     class="nav-link active px-4 py-1.5 rounded-full text-sm font-medium text-white/60 hover:text-white hover:bg-white/10 transition-colors">Engine</a>
      <a href="#how"      class="nav-link px-4 py-1.5 rounded-full text-sm font-medium text-white/60 hover:text-white hover:bg-white/10 transition-colors">How it works</a>
      <a href="#stats"    class="nav-link px-4 py-1.5 rounded-full text-sm font-medium text-white/60 hover:text-white hover:bg-white/10 transition-colors">Coverage</a>
      <a href="#feedback" class="nav-link px-4 py-1.5 rounded-full text-sm font-medium text-white/60 hover:text-white hover:bg-white/10 transition-colors">Feedback</a>
      <a href="#cta"      class="nav-link px-4 py-1.5 rounded-full text-sm font-medium text-white/60 hover:text-white hover:bg-white/10 transition-colors">Access</a>
    </div>

    <div class="flex items-center gap-2.5">
      <!-- profile -->
      <div class="relative">
        <button id="profileBtn" type="button" aria-haspopup="menu" aria-expanded="false" aria-label="Open profile menu"
                class="w-10 h-10 grid place-items-center rounded-full border border-white/15 bg-white/5 text-white/80 hover:text-white hover:border-acc/50 hover:bg-white/10 transition-colors">
          <i data-lucide="user-round" class="w-[18px] h-[18px]"></i>
        </button>

        <!-- dropdown -->
        <div id="profileMenu" role="menu" aria-hidden="true" class="absolute right-0 top-[calc(100%+12px)] w-[272px] origin-top-right">
          <span class="absolute -top-[5px] right-[15px] w-2.5 h-2.5 rotate-45 bg-[#0a1424] border-l border-t border-white/10" aria-hidden="true"></span>
          <div class="relative rounded-2xl border border-white/10 bg-[#0a1424] shadow-[0_28px_70px_-14px_rgba(0,0,0,.75)] overflow-hidden">
            <div class="flex items-center gap-3 px-4 py-3.5 border-b border-white/10">
              <span class="grid place-items-center w-9 h-9 rounded-full bg-acc/15 border border-acc/30 text-acc shrink-0"><i data-lucide="user-round" class="w-4 h-4"></i></span>
              <div class="min-w-0">
                <p class="text-sm font-medium text-white leading-tight">Guest buyer</p>
                <p class="mono text-[9px] tracking-[.2em] text-white/40 mt-1">LOCAL SESSION</p>
              </div>
            </div>
            <div class="p-1.5">
              <a href="#" role="menuitem" class="pitem" data-toast="Search History opens with your beta invite.">
                <span class="picon grid place-items-center w-9 h-9 rounded-xl border bg-white/[.04] shrink-0"><i data-lucide="history" class="w-[17px] h-[17px]"></i></span>
                <span class="min-w-0">
                  <span class="block text-sm text-white/90">Search History</span>
                  <span class="mono block text-[9px] tracking-[.16em] text-white/35 mt-1">EVERY QUERY YOU'VE CAST</span>
                </span>
                <i data-lucide="chevron-right" class="pchev w-4 h-4 ml-auto shrink-0"></i>
              </a>
              <a href="#" role="menuitem" class="pitem" data-toast="Reached Suppliers unlocks with your beta invite.">
                <span class="picon grid place-items-center w-9 h-9 rounded-xl border bg-white/[.04] shrink-0"><i data-lucide="send" class="w-[17px] h-[17px]"></i></span>
                <span class="min-w-0">
                  <span class="block text-sm text-white/90">Reached Suppliers</span>
                  <span class="mono block text-[9px] tracking-[.16em] text-white/35 mt-1">SUPPLIERS YOU'VE CONTACTED</span>
                </span>
                <i data-lucide="chevron-right" class="pchev w-4 h-4 ml-auto shrink-0"></i>
              </a>
              <a href="#" role="menuitem" class="pitem" data-toast="Watchlists unlock with your beta invite.">
                <span class="picon grid place-items-center w-9 h-9 rounded-xl border bg-white/[.04] shrink-0"><i data-lucide="bookmark" class="w-[17px] h-[17px]"></i></span>
                <span class="min-w-0">
                  <span class="block text-sm text-white/90">Watchlists</span>
                  <span class="mono block text-[9px] tracking-[.16em] text-white/35 mt-1">KEPT ON YOUR RADAR</span>
                </span>
                <i data-lucide="chevron-right" class="pchev w-4 h-4 ml-auto shrink-0"></i>
              </a>
            </div>
            <div class="px-4 py-3 border-t border-white/10">
              <a href="#cta" class="flex items-center justify-between text-sm text-white/70 hover:text-white transition-colors">
                Get early access <i data-lucide="arrow-right" class="w-3.5 h-3.5 text-acc"></i>
              </a>
            </div>
          </div>
        </div>
      </div>

      <button id="menuBtn" class="md:hidden w-10 h-10 grid place-items-center rounded-full border border-white/15 text-white/80" aria-label="Open menu">
        <i data-lucide="menu" class="w-5 h-5"></i>
      </button>
    </div>
  </div>
</nav>

<!-- ================= MOBILE MENU ================= -->
<div id="mmenu" class="fixed inset-0 z-[200] bg-[#050b14]/95 backdrop-blur-2xl flex flex-col px-6 py-4 opacity-0 pointer-events-none transition-opacity duration-300">
  <div class="flex items-center justify-between">
    <a href="#hero" class="flex items-center gap-2.5">
      <svg width="22" height="22" viewBox="0 0 256 256" fill="none" aria-hidden="true">
        <path d="M20 168 Q 76 64 128 168 T 236 168" stroke="#ffffff" stroke-width="26" stroke-linecap="round" fill="none"/>
        <circle cx="128" cy="56" r="22" fill="#5fe3c0"/>
      </svg>
      <span class="font-display italic text-xl text-white">Source&nbsp;Buddy</span>
    </a>
    <button id="menuClose" class="w-10 h-10 grid place-items-center rounded-full border border-white/15 text-white/80" aria-label="Close menu">
      <i data-lucide="x" class="w-5 h-5"></i>
    </button>
  </div>
  <nav class="mt-12 flex flex-col">
    <a href="#how"      class="mlink"><span class="mono text-[11px] text-acc tracking-[.2em]">01</span><span class="font-display italic text-4xl text-white">How it works</span></a>
    <a href="#stats"    class="mlink"><span class="mono text-[11px] text-acc tracking-[.2em]">02</span><span class="font-display italic text-4xl text-white">Coverage</span></a>
    <a href="#feedback" class="mlink"><span class="mono text-[11px] text-acc tracking-[.2em]">03</span><span class="font-display italic text-4xl text-white">Feedback</span></a>
    <a href="#cta"      class="mlink"><span class="mono text-[11px] text-acc tracking-[.2em]">04</span><span class="font-display italic text-4xl text-white">Access</span></a>
  </nav>
  <a href="#cta" class="mt-auto mb-6 btn-primary self-stretch justify-center">Get early access <i data-lucide="arrow-right" class="w-4 h-4"></i></a>
</div>

<!-- ================= HERO ================= -->
<section id="hero" class="relative w-full overflow-hidden h-screen bg-black" style="height:100dvh">

  <!-- Layer 1 Â· the night ocean at rest â€” dim, desaturated, slow surfacing zoom -->
  <div class="hero-zoom absolute inset-0 z-10" style="filter:saturate(.4) brightness(.6) contrast(1.05)">
    <svg id="sceneBase" class="scene block w-full h-full" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="skyA" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#04070c"/><stop offset=".72" stop-color="#0a1a2b"/><stop offset="1" stop-color="#173550"/>
        </linearGradient>
        <radialGradient id="haloA">
          <stop offset="0" stop-color="#ece4cf" stop-opacity=".38"/><stop offset="1" stop-color="#ece4cf" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="1600" height="412" fill="url(#skyA)"/>
      <g class="js-stars"></g>
      <g>
        <circle cx="1040" cy="172" r="118" fill="url(#haloA)"/>
        <circle cx="1040" cy="172" r="52" fill="#ece4cf"/>
        <circle cx="1024" cy="158" r="9" fill="#ddd3b8" opacity=".65"/>
        <circle cx="1052" cy="186" r="6" fill="#ddd3b8" opacity=".5"/>
        <circle cx="1048" cy="152" r="4" fill="#ddd3b8" opacity=".45"/>
        <path d="M300 96 q 95 -28 195 -6"  stroke="#04070c" stroke-opacity=".5"  stroke-width="15" fill="none" stroke-linecap="round"/>
        <path d="M985 172 q 55 -14 115 -3"  stroke="#04070c" stroke-opacity=".38" stroke-width="12" fill="none" stroke-linecap="round"/>
        <path d="M1150 116 q 80 -20 160 -2" stroke="#04070c" stroke-opacity=".4"  stroke-width="10" fill="none" stroke-linecap="round"/>
        <path d="M120 250 q 90 -22 180 -4"  stroke="#04070c" stroke-opacity=".35" stroke-width="9"  fill="none" stroke-linecap="round"/>
      </g>
      <g class="js-sea"></g>
      <g class="js-reflect"></g>
    </svg>
  </div>

  <!-- Layer 2 Â· the revealed ocean â€” colour, light shafts, and the hidden trade network beneath the surface.
       Same wave geometry and same SMIL clocks as the base scene, so the spotlight never shows a seam. -->
  <div id="revealLayer" class="hero-zoom absolute inset-0 z-30 pointer-events-none">
    <svg id="sceneReveal" class="scene block w-full h-full" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="skyB" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#04070c"/><stop offset=".72" stop-color="#0a1a2b"/><stop offset="1" stop-color="#173550"/>
        </linearGradient>
        <radialGradient id="haloB">
          <stop offset="0" stop-color="#ece4cf" stop-opacity=".38"/><stop offset="1" stop-color="#ece4cf" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="rayB" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#ece4cf" stop-opacity=".13"/><stop offset="1" stop-color="#ece4cf" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <rect width="1600" height="412" fill="url(#skyB)"/>
      <g class="js-stars"></g>
      <g>
        <circle cx="1040" cy="172" r="118" fill="url(#haloB)"/>
        <circle cx="1040" cy="172" r="52" fill="#ece4cf"/>
        <circle cx="1024" cy="158" r="9" fill="#ddd3b8" opacity=".65"/>
        <circle cx="1052" cy="186" r="6" fill="#ddd3b8" opacity=".5"/>
        <circle cx="1048" cy="152" r="4" fill="#ddd3b8" opacity=".45"/>
        <path d="M300 96 q 95 -28 195 -6"  stroke="#04070c" stroke-opacity=".5"  stroke-width="15" fill="none" stroke-linecap="round"/>
        <path d="M985 172 q 55 -14 115 -3"  stroke="#04070c" stroke-opacity=".38" stroke-width="12" fill="none" stroke-linecap="round"/>
        <path d="M1150 116 q 80 -20 160 -2" stroke="#04070c" stroke-opacity=".4"  stroke-width="10" fill="none" stroke-linecap="round"/>
        <path d="M120 250 q 90 -22 180 -4"  stroke="#04070c" stroke-opacity=".35" stroke-width="9"  fill="none" stroke-linecap="round"/>
      </g>
      <g class="js-sea"></g>
      <g class="js-reflect"></g>

      <!-- moonlight shafts down through the water -->
      <g>
        <animate attributeName="opacity" values=".55;1;.55" dur="11s" repeatCount="indefinite"/>
        <path d="M960 412 L 1030 412 L 1180 900 L 1050 900 Z" fill="url(#rayB)"/>
        <path d="M740 412 L 788 412 L 690 900 L 610 900 Z" fill="url(#rayB)" opacity=".7"/>
      </g>

      <!-- ============ THE DEEP â€” everything below is only visible through the spotlight ============ -->
      <g id="deep">
        <!-- bathymetric contours -->
        <g fill="none" stroke="#5fe3c0" stroke-opacity=".2" stroke-width="1.3">
          <path d="M420 540 C 560 498 760 518 860 590 C 932 646 850 722 690 742 C 520 762 398 680 420 540 Z"/>
          <path d="M500 572 C 610 545 750 560 820 610 C 866 652 804 702 690 714 C 558 726 478 672 500 572 Z"/>
          <path d="M580 602 C 650 590 720 600 750 632 C 772 660 726 686 664 688 C 598 690 562 654 580 602 Z"/>
          <path d="M1150 520 C 1262 494 1392 520 1442 580 C 1472 632 1400 682 1290 692 C 1180 702 1108 652 1150 520 Z"/>
          <path d="M1120 556 C 1200 540 1300 552 1340 592 C 1366 626 1312 660 1230 664 C 1142 668 1096 620 1120 556 Z"/>
          <path d="M148 700 C 240 678 332 700 362 746 C 384 792 300 822 210 812 C 128 802 98 746 148 700 Z"/>
        </g>
        <g class="ct">
          <text x="872" y="590">&#8722;200</text>
          <text x="828" y="618">&#8722;1000</text>
          <text x="758" y="646">&#8722;4000</text>
          <text x="1452" y="588">&#8722;200</text>
          <text x="1348" y="626">&#8722;800</text>
          <text x="370" y="750">&#8722;1000</text>
        </g>

        <!-- shipping lanes -->
        <g fill="none" stroke="#5fe3c0" stroke-width="1.4" stroke-dasharray="5 8" stroke-linecap="round">
          <path stroke-opacity=".75" d="M600 610 Q 460 480 380 470">
            <animate attributeName="stroke-dashoffset" from="0" to="-130" dur="2.6s" begin="0s" repeatCount="indefinite"/>
          </path>
          <path stroke-opacity=".75" d="M600 610 Q 900 380 1150 500">
            <animate attributeName="stroke-dashoffset" from="0" to="-130" dur="2.6s" begin="-.6s" repeatCount="indefinite"/>
          </path>
          <path stroke-opacity=".75" d="M600 610 Q 820 790 980 760">
            <animate attributeName="stroke-dashoffset" from="0" to="-130" dur="2.6s" begin="-1.2s" repeatCount="indefinite"/>
          </path>
          <path stroke-opacity=".75" d="M600 610 Q 400 830 300 820">
            <animate attributeName="stroke-dashoffset" from="0" to="-130" dur="2.6s" begin="-1.8s" repeatCount="indefinite"/>
          </path>
          <path stroke-opacity=".75" d="M600 610 Q 1080 700 1420 620">
            <animate attributeName="stroke-dashoffset" from="0" to="-130" dur="2.6s" begin="-.9s" repeatCount="indefinite"/>
          </path>
          <path stroke-opacity=".28" d="M380 470 Q 760 300 1150 500">
            <animate attributeName="stroke-dashoffset" from="0" to="-130" dur="3.4s" repeatCount="indefinite"/>
          </path>
          <path stroke-opacity=".28" d="M980 760 Q 1220 660 1420 620">
            <animate attributeName="stroke-dashoffset" from="0" to="-130" dur="3.4s" begin="-1.1s" repeatCount="indefinite"/>
          </path>
        </g>

        <!-- ports -->
        <g class="port">
          <circle cx="380" cy="470" r="4" fill="#fff"/>
          <circle cx="380" cy="470" r="4" fill="none" stroke="#5fe3c0" stroke-width="1.2">
            <animate attributeName="r" values="4;26" dur="3s" repeatCount="indefinite"/>
            <animate attributeName="stroke-opacity" values=".8;0" dur="3s" repeatCount="indefinite"/>
          </circle>
          <text class="pt" x="396" y="468">ROTTERDAM</text>
          <text class="ps" x="396" y="483">EU HUB</text>
        </g>
        <g class="port">
          <circle cx="1150" cy="500" r="4" fill="#fff"/>
          <circle cx="1150" cy="500" r="4" fill="none" stroke="#5fe3c0" stroke-width="1.2">
            <animate attributeName="r" values="4;26" dur="3s" begin="-1.1s" repeatCount="indefinite"/>
            <animate attributeName="stroke-opacity" values=".8;0" dur="3s" begin="-1.1s" repeatCount="indefinite"/>
          </circle>
          <text class="pt" x="1166" y="498">SHENZHEN</text>
          <text class="ps" x="1166" y="513">MOQ 500</text>
        </g>
        <g class="port">
          <circle cx="980" cy="760" r="4" fill="#fff"/>
          <circle cx="980" cy="760" r="4" fill="none" stroke="#5fe3c0" stroke-width="1.2">
            <animate attributeName="r" values="4;26" dur="3s" begin="-2.2s" repeatCount="indefinite"/>
            <animate attributeName="stroke-opacity" values=".8;0" dur="3s" begin="-2.2s" repeatCount="indefinite"/>
          </circle>
          <text class="pt" x="996" y="758">SINGAPORE</text>
          <text class="ps" x="996" y="773">$2.31/PC</text>
        </g>
        <g class="port">
          <circle cx="300" cy="820" r="4" fill="#fff"/>
          <circle cx="300" cy="820" r="4" fill="none" stroke="#5fe3c0" stroke-width="1.2">
            <animate attributeName="r" values="4;26" dur="3s" begin="-.5s" repeatCount="indefinite"/>
            <animate attributeName="stroke-opacity" values=".8;0" dur="3s" begin="-.5s" repeatCount="indefinite"/>
          </circle>
          <text class="pt" x="316" y="818">SANTOS</text>
          <text class="ps" x="316" y="833">LEAD 21D</text>
        </g>
        <g class="port">
          <circle cx="1420" cy="620" r="4" fill="#fff"/>
          <circle cx="1420" cy="620" r="4" fill="none" stroke="#5fe3c0" stroke-width="1.2">
            <animate attributeName="r" values="4;26" dur="3s" begin="-1.6s" repeatCount="indefinite"/>
            <animate attributeName="stroke-opacity" values=".8;0" dur="3s" begin="-1.6s" repeatCount="indefinite"/>
          </circle>
          <text class="pt" x="1404" y="618" text-anchor="end">BUSAN</text>
          <text class="ps" x="1404" y="633" text-anchor="end">F.O.B READY</text>
        </g>

        <!-- your request: sonar hub -->
        <g>
          <circle cx="600" cy="610" r="95" fill="none" stroke="#5fe3c0" stroke-opacity=".3" stroke-width="1" stroke-dasharray="2 14">
            <animateTransform attributeName="transform" type="rotate" from="0 600 610" to="360 600 610" dur="14s" repeatCount="indefinite"/>
          </circle>
          <circle cx="600" cy="610" r="5" fill="#fff"/>
          <circle cx="600" cy="610" r="13" fill="none" stroke="#5fe3c0" stroke-width="1.4"/>
          <circle cx="600" cy="610" r="13" fill="none" stroke="#5fe3c0" stroke-width="1.4" stroke-opacity=".8">
            <animate attributeName="r" values="13;70" dur="3s" repeatCount="indefinite"/>
            <animate attributeName="stroke-opacity" values=".8;0" dur="3s" repeatCount="indefinite"/>
          </circle>
          <circle cx="600" cy="610" r="13" fill="none" stroke="#5fe3c0" stroke-width="1.4" stroke-opacity=".8">
            <animate attributeName="r" values="13;70" dur="3s" begin="1.5s" repeatCount="indefinite"/>
            <animate attributeName="stroke-opacity" values=".8;0" dur="3s" begin="1.5s" repeatCount="indefinite"/>
          </circle>
          <g>
            <animateTransform attributeName="transform" type="rotate" from="0 600 610" to="360 600 610" dur="8s" repeatCount="indefinite"/>
            <path d="M600 610 L 622 474 A 140 140 0 0 0 580 478 Z" fill="#5fe3c0" fill-opacity=".09"/>
            <line x1="600" y1="610" x2="622" y2="474" stroke="#5fe3c0" stroke-width="1.2" stroke-opacity=".5"/>
          </g>
          <text class="hl" x="600" y="530" text-anchor="middle">YOUR REQUEST</text>
          <rect x="534" y="542" width="134" height="26" rx="13" fill="#5fe3c0"/>
          <text class="mt" x="601" y="560" text-anchor="middle">MATCH &#183; 96</text>
        </g>

        <!-- the whale â€” a huge shadow on an 80-second crossing -->
        <g>
          <animateTransform attributeName="transform" type="translate" from="1980 640" to="-560 700" dur="80s" repeatCount="indefinite"/>
          <g>
            <animateTransform attributeName="transform" type="translate" values="0 0; 0 -18; 0 0" keyTimes="0;.5;1" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" dur="9s" repeatCount="indefinite"/>
            <path fill="#020910" fill-opacity=".94" d="M18 58 C 30 20 84 6 138 12 C 186 17 218 34 232 52 C 236 60 232 68 222 74 C 196 92 148 100 100 96 C 58 92 26 80 18 58 Z M226 56 C 244 34 270 24 292 22 C 280 40 276 54 280 70 C 258 66 240 62 226 62 C 222 60 222 58 226 56 Z M96 88 C 108 104 128 112 142 108 C 132 96 118 86 104 82 Z"/>
            <path d="M20 56 C 32 20 86 6 140 12 C 188 17 220 34 233 52" fill="none" stroke="#a9ded2" stroke-width="2.4" stroke-opacity=".5" stroke-linecap="round"/>
            <path d="M60 80 q 22 9 46 7 M70 86 q 18 8 40 6" fill="none" stroke="#a9ded2" stroke-width="1.4" stroke-opacity=".18" stroke-linecap="round"/>
            <circle cx="56" cy="42" r="2.6" fill="#a9ded2" fill-opacity=".45"/>
          </g>
        </g>

        <!-- a small school of fish -->
        <g transform="translate(235,548)">
          <g>
            <animateTransform attributeName="transform" type="translate" values="0 0; 34 -14; 0 0" keyTimes="0;.5;1" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" dur="14s" repeatCount="indefinite"/>
            <g fill="#7fd8c6" fill-opacity=".5">
              <path d="M0 0 C 5 -4 12 -4 16 0 C 12 4 5 4 0 0 Z M0 0 L -6 -4 L -6 4 Z"/>
              <path transform="translate(24,-10) scale(1.15)" d="M0 0 C 5 -4 12 -4 16 0 C 12 4 5 4 0 0 Z M0 0 L -6 -4 L -6 4 Z"/>
              <path transform="translate(42,6) scale(.9)" d="M0 0 C 5 -4 12 -4 16 0 C 12 4 5 4 0 0 Z M0 0 L -6 -4 L -6 4 Z"/>
              <path transform="translate(60,-4) scale(1.05)" d="M0 0 C 5 -4 12 -4 16 0 C 12 4 5 4 0 0 Z M0 0 L -6 -4 L -6 4 Z"/>
              <path transform="translate(14,14) scale(.85)" d="M0 0 C 5 -4 12 -4 16 0 C 12 4 5 4 0 0 Z M0 0 L -6 -4 L -6 4 Z"/>
              <path transform="translate(34,18) scale(1)" d="M0 0 C 5 -4 12 -4 16 0 C 12 4 5 4 0 0 Z M0 0 L -6 -4 L -6 4 Z"/>
              <path transform="translate(54,10) scale(.8)" d="M0 0 C 5 -4 12 -4 16 0 C 12 4 5 4 0 0 Z M0 0 L -6 -4 L -6 4 Z"/>
            </g>
          </g>
        </g>

        <!-- bioluminescent plankton (injected by JS) -->
        <g class="js-spark"></g>
      </g>
    </svg>
  </div>

  <!-- Hidden canvas used to bake the soft radial mask for the reveal layer -->
  <canvas id="maskCanvas" class="absolute inset-0 pointer-events-none" style="display:none"></canvas>

  <!-- Precision crosshair (desktop pointers) -->
  <div id="crosshair" class="fixed z-40 pointer-events-none opacity-0 top-0 left-0" style="transition:opacity .3s">
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <line x1="8" y1="0"     x2="8"    y2="4.5"  stroke="white" stroke-opacity=".9"/>
      <line x1="8" y1="11.5"  x2="8"    y2="16"   stroke="white" stroke-opacity=".9"/>
      <line x1="0" y1="8"     x2="4.5"  y2="8"    stroke="white" stroke-opacity=".9"/>
      <line x1="11.5" y1="8"  x2="16"   y2="8"    stroke="white" stroke-opacity=".9"/>
      <circle cx="8" cy="8" r="2.5" stroke="#5fe3c0" stroke-width="1"/>
    </svg>
  </div>

  <!-- Layer 3 Â· the seagulls â€” above the surface, above the mask -->
  <div id="gulls" class="absolute inset-0 z-40 pointer-events-none" aria-hidden="true">
    <!-- hero gull, crossing right, will pass the moon -->
    <div class="flight r" style="--dur:30s; --delay:-7s; top:13%;">
      <div class="bob" style="--bdur:3.8s">
        <svg class="gull" width="150" viewBox="-85 -42 170 84" fill="none" style="--fdur:.78s">
          <path class="wingF" d="M0 0 C -10 -8 -34 -14 -56 -12 C -57 -9 -52 -4 -44 -1 C -26 4 -8 5 0 5 Z" fill="#39445a"/>
          <path d="M-28 8 C -22 -6 -6 -11 8 -8 C 19 -5 25 1 24 6 C 21 12 7 15 -7 13 C -19 11 -26 10 -28 8 Z" fill="#c7d3de"/>
          <path d="M-26 9 L -45 5 L -25 15 Z" fill="#c7d3de"/>
          <path d="M24 3 L 36 6 L 24 9 Z" fill="#8b93a5"/>
          <path class="wingN" d="M0 0 C -12 -3 -42 -6 -66 -3 C -68 -2 -68 2 -63 3 C -38 8 -14 9 0 7 Z" fill="#46536b"/>
        </svg>
      </div>
    </div>
    <!-- mid gull, heading back left -->
    <div class="flight l" style="--dur:22s; --delay:-14s; top:21%;">
      <div class="bob" style="--bdur:3s">
        <svg class="gull rev" width="96" viewBox="-85 -42 170 84" fill="none" style="--fdur:.6s; opacity:.9">
          <path class="wingF" d="M0 0 C -10 -8 -34 -14 -56 -12 C -57 -9 -52 -4 -44 -1 C -26 4 -8 5 0 5 Z" fill="#39445a"/>
          <path d="M-28 8 C -22 -6 -6 -11 8 -8 C 19 -5 25 1 24 6 C 21 12 7 15 -7 13 C -19 11 -26 10 -28 8 Z" fill="#c7d3de"/>
          <path d="M-26 9 L -45 5 L -25 15 Z" fill="#c7d3de"/>
          <path d="M24 3 L 36 6 L 24 9 Z" fill="#8b93a5"/>
          <path class="wingN" d="M0 0 C -12 -3 -42 -6 -66 -3 C -68 -2 -68 2 -63 3 C -38 8 -14 9 0 7 Z" fill="#46536b"/>
        </svg>
      </div>
    </div>
    <!-- mid gull, far and slow, crosses the moonlight -->
    <div class="flight r" style="--dur:36s; --delay:-4s; top:17%;">
      <div class="bob" style="--bdur:4.4s">
        <svg class="gull" width="76" viewBox="-85 -42 170 84" fill="none" style="--fdur:.68s; opacity:.75">
          <path class="wingF" d="M0 0 C -10 -8 -34 -14 -56 -12 C -57 -9 -52 -4 -44 -1 C -26 4 -8 5 0 5 Z" fill="#39445a"/>
          <path d="M-28 8 C -22 -6 -6 -11 8 -8 C 19 -5 25 1 24 6 C 21 12 7 15 -7 13 C -19 11 -26 10 -28 8 Z" fill="#c7d3de"/>
          <path d="M-26 9 L -45 5 L -25 15 Z" fill="#c7d3de"/>
          <path d="M24 3 L 36 6 L 24 9 Z" fill="#8b93a5"/>
          <path class="wingN" d="M0 0 C -12 -3 -42 -6 -66 -3 C -68 -2 -68 2 -63 3 C -38 8 -14 9 0 7 Z" fill="#46536b"/>
        </svg>
      </div>
    </div>
    <!-- two distant gulls -->
    <div class="flight l" style="--dur:28s; --delay:-11s; top:26%;">
      <div class="bob" style="--bdur:3s">
        <svg width="40" viewBox="0 0 36 16" fill="none" style="opacity:.7">
          <path stroke="#9db0c2" stroke-width="3" stroke-linecap="round" d="M2 10 Q 10 1 18 9 Q 26 1 34 10">
            <animate attributeName="d" dur=".62s" repeatCount="indefinite"
              values="M2 10 Q 10 1 18 9 Q 26 1 34 10; M2 9 Q 10 15 18 9 Q 26 15 34 9; M2 10 Q 10 1 18 9 Q 26 1 34 10"/>
          </path>
        </svg>
      </div>
    </div>
    <div class="flight r" style="--dur:42s; --delay:-20s; top:11%;">
      <div class="bob" style="--bdur:3.6s">
        <svg width="30" viewBox="0 0 36 16" fill="none" style="opacity:.55">
          <path stroke="#9db0c2" stroke-width="3" stroke-linecap="round" d="M2 10 Q 10 1 18 9 Q 26 1 34 10">
            <animate attributeName="d" dur=".55s" repeatCount="indefinite"
              values="M2 10 Q 10 1 18 9 Q 26 1 34 10; M2 9 Q 10 15 18 9 Q 26 15 34 9; M2 10 Q 10 1 18 9 Q 26 1 34 10"/>
          </path>
        </svg>
      </div>
    </div>
  </div>

  <!-- Layer 4 Â· heading -->
  <div class="absolute top-[12%] sm:top-[14%] left-0 right-0 z-50 flex flex-col items-center text-center px-5 pointer-events-none">
    <p class="hero-anim hero-fade mono uppercase text-[10px] sm:text-[11px] tracking-[.3em] text-white/50" style="animation-delay:.15s">AI Procurement Engine &#183; Private Beta</p>
    <h1 class="mt-5 text-white leading-[0.95]">
      <span class="hero-anim hero-reveal block font-display italic font-normal text-5xl sm:text-7xl md:text-8xl" style="animation-delay:.25s; letter-spacing:-.02em">Every supplier,</span>
      <span class="hero-anim hero-reveal block font-medium text-5xl sm:text-7xl md:text-8xl -mt-1 sm:-mt-2" style="animation-delay:.42s; letter-spacing:-.045em">beneath the surface.</span>
    </h1>
  </div>

  <!-- Layer 5 Â· bottom-left note -->
  <div class="hero-anim hero-fade hidden sm:block absolute bottom-14 left-10 md:left-14 max-w-[260px] z-50" style="animation-delay:.7s">
    <p class="mono text-[10px] tracking-[.22em] text-acc/90">INPUT</p>
    <p class="mt-3 text-sm text-white/80 leading-relaxed">No more marketplace tabs, no more weeks of supplier email. Describe the product once â€” the way you'd say it on deck.</p>
  </div>

  <!-- Layer 6 Â· bottom-right copy + CTA -->
  <div class="hero-anim hero-fade absolute bottom-10 sm:bottom-24 left-5 right-5 sm:left-auto sm:right-10 md:right-14 max-w-full sm:max-w-[280px] z-50 flex flex-col items-start gap-4 sm:gap-5" style="animation-delay:.85s">
    <div>
      <p class="mono text-[10px] tracking-[.22em] text-acc/90">OUTPUT</p>
      <p class="mt-3 text-xs sm:text-sm text-white/80 leading-relaxed">What surfaces is a ranked, contact-ready shortlist: price, MOQ, lead time, fit score â€” before your coffee goes cold.</p>
    </div>
    <div class="flex items-center gap-5">
      <a href="#cta" class="btn-primary">Start sourcing <i data-lucide="arrow-right" class="w-4 h-4"></i></a>
      <a href="#how" class="group inline-flex items-center gap-1.5 text-sm text-white/60 hover:text-white transition-colors">
        Sound the depths <i data-lucide="arrow-down" class="w-3.5 h-3.5 transition-transform group-hover:translate-y-0.5"></i>
      </a>
    </div>
  </div>

  <!-- spotlight hint (desktop) -->
  <div id="spotHint" class="hidden md:flex absolute bottom-6 left-0 right-0 z-50 justify-center pointer-events-none transition-opacity duration-700">
    <span class="mono text-[10px] tracking-[.26em] text-white/40 flex items-center gap-3">
      <span class="hintdot"></span>MOVE TO LOOK BENEATH THE SURFACE<span class="hintdot"></span>
    </span>
  </div>
</section>

<!-- ================= LIVE FEED TICKER ================= -->
<div class="border-y border-white/10 bg-[#070d17]">
  <div class="flex items-center">
    <div class="shrink-0 flex items-center gap-2.5 pl-5 sm:pl-8 pr-4 sm:pr-6 py-3 border-r border-white/10">
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-acc opacity-60"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-acc"></span>
      </span>
      <span class="mono text-[10px] tracking-[.22em] text-white/50">LIVE FEED</span>
    </div>
    <div class="marquee-wrap flex-1 overflow-hidden py-3"
         style="mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent); -webkit-mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);">
      <div id="ticker" class="marquee flex w-max items-center mono text-[11px] uppercase tracking-[.14em] text-white/45"></div>
    </div>
  </div>
</div>

<!-- wave divider -->
<div class="wave-line" aria-hidden="true">
  <svg class="block w-full" style="height:26px" viewBox="0 0 1200 26" preserveAspectRatio="none" fill="none">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-200 0" dur="7s" repeatCount="indefinite"/>
      <path vector-effect="non-scaling-stroke" stroke="rgba(255,255,255,.14)" stroke-width="1.5" stroke-linecap="round"
        d="M0 13 q 50 -11 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0"/>
    </g>
  </svg>
</div>

<!-- ================= HOW IT WORKS ================= -->
<section id="how" class="py-24 md:py-32 scroll-mt-24">
  <div class="max-w-6xl mx-auto px-5">
    <p class="eyebrow reveal">01 &#183; How it works</p>
    <h2 class="mt-5 text-4xl sm:text-5xl md:text-6xl tracking-tight leading-[1.05] reveal" style="transition-delay:.06s">
      <span class="block font-display italic font-normal">Three steps.</span>
      <span class="block font-medium mt-1">Zero portals.</span>
    </h2>

    <div id="howSteps" class="relative mt-14 md:mt-20">
      <div class="absolute left-[8px] top-3 bottom-10 w-px bg-white/10"></div>
      <div id="spineFill" class="absolute left-[8px] top-3 w-px bg-acc" style="height:0"></div>

      <!-- step 01 -->
      <div class="relative pl-10 md:pl-14 py-10 md:py-14 reveal">
        <span class="absolute left-0 top-[72px] md:top-[64px] grid place-items-center w-[17px] h-[17px] rounded-full border border-white/20 bg-ink">
          <span class="w-[5px] h-[5px] rounded-full bg-acc"></span>
        </span>
        <div class="md:grid md:grid-cols-12 gap-8">
          <div class="font-display italic text-5xl md:text-6xl text-white/25 md:col-span-3">01</div>
          <div class="mt-4 md:mt-0 md:col-span-8 md:col-start-5">
            <div class="flex items-center gap-4">
              <span class="grid place-items-center w-10 h-10 rounded-xl border border-white/15 text-white/80 shrink-0"><i data-lucide="message-square" class="w-[18px] h-[18px]"></i></span>
              <h3 class="text-2xl font-medium">Describe it once</h3>
            </div>
            <p class="mt-4 text-white/60 leading-relaxed max-w-xl">One plain sentence â€” product, quantity, where it needs to land. No category trees. No RFQ templates. No marketplace maze.</p>
            <p class="mlabel mt-5 text-acc/80">Input â€” one plain sentence</p>
          </div>
        </div>
      </div>

      <!-- step 02 -->
      <div class="relative pl-10 md:pl-14 py-10 md:py-14 reveal">
        <span class="absolute left-0 top-[72px] md:top-[64px] grid place-items-center w-[17px] h-[17px] rounded-full border border-white/20 bg-ink">
          <span class="w-[5px] h-[5px] rounded-full bg-acc"></span>
        </span>
        <div class="md:grid md:grid-cols-12 gap-8">
          <div class="font-display italic text-5xl md:text-6xl text-white/25 md:col-span-3">02</div>
          <div class="mt-4 md:mt-0 md:col-span-7 md:col-start-6">
            <div class="flex items-center gap-4">
              <span class="grid place-items-center w-10 h-10 rounded-xl border border-white/15 text-white/80 shrink-0"><i data-lucide="radar" class="w-[18px] h-[18px]"></i></span>
              <h3 class="text-2xl font-medium">The engine sounds the depths</h3>
            </div>
            <p class="mt-4 text-white/60 leading-relaxed max-w-xl">Your request is parsed into sourcing requirements and searched across multiple supplier sources. Results are cross-checked for relevant details such as price, MOQ, certifications, capacity, and lead time where available.</p>
            <p class="mlabel mt-5 text-acc/80">Searching &mdash; across supplier sources</p>
          </div>
        </div>
      </div>

      <!-- step 03 -->
      <div class="relative pl-10 md:pl-14 py-10 md:py-14 reveal">
        <span class="absolute left-0 top-[72px] md:top-[64px] grid place-items-center w-[17px] h-[17px] rounded-full border border-white/20 bg-ink">
          <span class="w-[5px] h-[5px] rounded-full bg-acc"></span>
        </span>
        <div class="md:grid md:grid-cols-12 gap-8">
          <div class="font-display italic text-5xl md:text-6xl text-white/25 md:col-span-3">03</div>
          <div class="mt-4 md:mt-0 md:col-span-8 md:col-start-5">
            <div class="flex items-center gap-4">
              <span class="grid place-items-center w-10 h-10 rounded-xl border border-white/15 text-white/80 shrink-0"><i data-lucide="anchor" class="w-[18px] h-[18px]"></i></span>
              <h3 class="text-2xl font-medium">The shortlist surfaces</h3>
            </div>
            <p class="mt-4 text-white/60 leading-relaxed max-w-xl">Get a focused shortlist with supplier details, contacts, MOQ, pricing information, source evidence, and other available signals. You decide who to contact.</p>
            <p class="mlabel mt-5 text-acc/80">Surfaced â€” ranked + contact-ready</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- wave divider -->
<div class="wave-line" aria-hidden="true">
  <svg class="block w-full" style="height:26px" viewBox="0 0 1200 26" preserveAspectRatio="none" fill="none">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-200 0" dur="7s" repeatCount="indefinite"/>
      <path vector-effect="non-scaling-stroke" stroke="rgba(255,255,255,.14)" stroke-width="1.5" stroke-linecap="round"
        d="M0 13 q 50 -11 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0"/>
    </g>
  </svg>
</div>

<!-- ================= COVERAGE ================= -->
<section id="stats" class="py-20 md:py-28 scroll-mt-24">
  <div class="max-w-6xl mx-auto px-5">
    <p class="eyebrow reveal">02 &#183; Coverage</p>
    <div class="mt-12 md:mt-16 grid gap-8 sm:grid-cols-2 md:grid-cols-4">
      <div class="reveal">
        <p class="text-xl sm:text-2xl font-medium tracking-tight text-white">Supplier sources</p>
        <p class="mt-3 text-sm text-white/55 leading-relaxed">Multiple search engines, marketplaces, and supplier websites.</p>
      </div>
      <div class="reveal md:border-l md:border-white/10 md:pl-8" style="transition-delay:.07s">
        <p class="text-xl sm:text-2xl font-medium tracking-tight text-white">Supplier intelligence</p>
        <p class="mt-3 text-sm text-white/55 leading-relaxed">MOQ &#183; pricing &#183; location &#183; contact &#183; certifications</p>
      </div>
      <div class="reveal md:border-l md:border-white/10 md:pl-8" style="transition-delay:.14s">
        <p class="text-xl sm:text-2xl font-medium tracking-tight text-white">Search depth</p>
        <p class="mt-3 text-sm text-white/55 leading-relaxed">Multi-source discovery with evidence-backed results.</p>
      </div>
      <div class="reveal md:border-l md:border-white/10 md:pl-8" style="transition-delay:.21s">
        <p class="text-xl sm:text-2xl font-medium tracking-tight text-white">Buyer effort</p>
        <p class="mt-3 text-sm text-white/55 leading-relaxed">One request &#8594; researched supplier shortlist</p>
      </div>
    </div>
  </div>
</section>

<!-- wave divider -->
<div class="wave-line" aria-hidden="true">
  <svg class="block w-full" style="height:26px" viewBox="0 0 1200 26" preserveAspectRatio="none" fill="none">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-200 0" dur="7s" repeatCount="indefinite"/>
      <path vector-effect="non-scaling-stroke" stroke="rgba(255,255,255,.14)" stroke-width="1.5" stroke-linecap="round"
        d="M0 13 q 50 -11 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0"/>
    </g>
  </svg>
</div>

<!-- ================= FEEDBACK ================= -->
<section id="feedback" class="relative py-24 md:py-32 scroll-mt-24 overflow-hidden">
  <!-- faint drifting bottle backdrop -->
  <div class="absolute inset-0 pointer-events-none" aria-hidden="true">
    <svg class="absolute right-[5%] top-1/2 -translate-y-1/2 hidden lg:block h-[400px]" viewBox="0 0 200 400" fill="none">
      <g class="fb-drift" style="transform-box:fill-box; transform-origin:50% 50%;">
        <g stroke="rgba(95,227,192,.13)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="85" y="14" width="30" height="24" rx="5"/>
          <path d="M91 38 v50 c0 12 -35 24 -35 60 v168 c0 17 13 30 30 30 h28 c17 0 30 -13 30 -30 v-168 c0 -36 -35 -48 -35 -60 v-50"/>
          <path d="M80 246 c 13 -20 27 -20 40 0 v58 c-13 20 -27 20 -40 0 z"/>
          <path d="M80 246 l 20 -13 l 20 13 M80 304 l 20 13 l 20 -13"/>
        </g>
      </g>
      <g fill="rgba(95,227,192,.35)">
        <circle cx="150" cy="330" r="2.5">
          <animate attributeName="cy" values="330;200" dur="7s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0;.7;0" dur="7s" repeatCount="indefinite"/>
        </circle>
        <circle cx="163" cy="340" r="1.8">
          <animate attributeName="cy" values="340;215" dur="9s" begin="-3s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0;.6;0" dur="9s" begin="-3s" repeatCount="indefinite"/>
        </circle>
        <circle cx="140" cy="335" r="1.4">
          <animate attributeName="cy" values="335;230" dur="11s" begin="-6s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0;.5;0" dur="11s" begin="-6s" repeatCount="indefinite"/>
        </circle>
      </g>
    </svg>
  </div>

  <div class="relative max-w-3xl mx-auto px-5">
    <p class="eyebrow reveal">03 &#183; Feedback</p>
    <h2 class="mt-5 text-4xl sm:text-5xl md:text-6xl tracking-tight leading-[1.05] reveal" style="transition-delay:.06s">
      <span class="block font-display italic font-normal">Message in a bottle.</span>
      <span class="block font-medium mt-1">We read every one.</span>
    </h2>
    <p class="mt-6 text-white/60 max-w-md leading-relaxed reveal" style="transition-delay:.12s">Rough waters, a missing supplier, an idea that would save you hours â€” cast it our way. Every bottle reaches the chart table, and the good ones change the course.</p>

    <div class="mt-10 reveal" style="transition-delay:.18s">
      <form id="fbForm" novalidate>
        <p class="mlabel">What kind of message?</p>
        <div class="mt-3.5 flex flex-wrap gap-2.5">
          <button type="button" class="fb-type is-on" data-val="idea"><i data-lucide="lightbulb" class="w-3.5 h-3.5"></i>Feature idea</button>
          <button type="button" class="fb-type" data-val="broken"><i data-lucide="wrench" class="w-3.5 h-3.5"></i>Something's broken</button>
          <button type="button" class="fb-type" data-val="praise"><i data-lucide="heart" class="w-3.5 h-3.5"></i>Praise the crew</button>
          <button type="button" class="fb-type" data-val="supplier"><i data-lucide="ship" class="w-3.5 h-3.5"></i>Missing supplier</button>
        </div>

        <p class="mlabel mt-9">How's the voyage so far?</p>
        <div id="fbRate" class="mt-3.5 flex items-center gap-2.5 flex-wrap" role="radiogroup" aria-label="Rate your experience">
          <button type="button" class="fb-rate" data-val="1" role="radio" aria-checked="false" aria-label="1 of 5"><i data-lucide="anchor" class="w-[17px] h-[17px]"></i></button>
          <button type="button" class="fb-rate" data-val="2" role="radio" aria-checked="false" aria-label="2 of 5"><i data-lucide="anchor" class="w-[17px] h-[17px]"></i></button>
          <button type="button" class="fb-rate" data-val="3" role="radio" aria-checked="false" aria-label="3 of 5"><i data-lucide="anchor" class="w-[17px] h-[17px]"></i></button>
          <button type="button" class="fb-rate" data-val="4" role="radio" aria-checked="false" aria-label="4 of 5"><i data-lucide="anchor" class="w-[17px] h-[17px]"></i></button>
          <button type="button" class="fb-rate" data-val="5" role="radio" aria-checked="false" aria-label="5 of 5"><i data-lucide="anchor" class="w-[17px] h-[17px]"></i></button>
          <span id="fbRateWord" class="ml-2 mono text-[10px] tracking-[.2em] text-white/40">SET A RATING</span>
        </div>

        <label class="mlabel mt-9 block" for="fbMsg">Your message</label>
        <div class="relative mt-3.5">
          <textarea id="fbMsg" rows="4" maxlength="600" placeholder="Tell us what to change, what's missing, or what made your day&hellip;"></textarea>
          <span id="fbCount" class="absolute bottom-3.5 right-4 mono text-[10px] text-white/30">0 / 600</span>
        </div>

        <div class="mt-9 flex items-baseline gap-3">
          <label class="mlabel" for="fbEmail">Want a reply?</label>
          <span class="mono text-[10px] text-white/25">OPTIONAL</span>
        </div>
        <input id="fbEmail" type="email" autocomplete="email" placeholder="work@company.com" class="mt-3.5" />

        <p id="fbErr" class="hidden mt-4 text-xs text-[#ff7a66]"></p>

        <div class="mt-9 flex flex-wrap items-center gap-5">
          <button type="submit" class="btn-primary">Cast the bottle <i data-lucide="send" class="w-4 h-4"></i></button>
          <span class="mono text-[10px] tracking-[.22em] text-white/35">ANONYMOUS BY DEFAULT</span>
        </div>
      </form>

      <!-- success state -->
      <div id="fbDone" class="hidden rounded-3xl border border-acc/25 bg-acc/[.05] px-6 py-12 sm:px-12 text-center">
        <span class="inline-grid place-items-center w-14 h-14 rounded-full border border-acc/40 bg-acc/10 text-acc mb-6"><i data-lucide="send" class="w-6 h-6"></i></span>
        <p class="font-display italic text-4xl text-white">Your bottle is at sea.</p>
        <p id="fbSummary" class="mono text-[10px] tracking-[.22em] text-acc/80 mt-4"></p>
        <p class="mt-4 text-sm text-white/55 max-w-sm mx-auto leading-relaxed">The crew reads every message that washes aboard. If you left an email, we'll write back when there's news worth sending â€” never before.</p>
        <button id="fbAgain" type="button" class="mt-8 inline-flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors">
          <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i> Send another
        </button>
      </div>
    </div>
  </div>
</section>

<!-- wave divider -->
<div class="wave-line" aria-hidden="true">
  <svg class="block w-full" style="height:26px" viewBox="0 0 1200 26" preserveAspectRatio="none" fill="none">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-200 0" dur="7s" repeatCount="indefinite"/>
      <path vector-effect="non-scaling-stroke" stroke="rgba(255,255,255,.14)" stroke-width="1.5" stroke-linecap="round"
        d="M0 13 q 50 -11 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0"/>
    </g>
  </svg>
</div>

<!-- ================= EARLY ACCESS ================= -->
<section id="cta" class="relative py-28 md:py-36 scroll-mt-24 overflow-hidden">
  <!-- faint contour backdrop -->
  <div class="absolute inset-0 pointer-events-none" aria-hidden="true">
    <svg class="w-full h-full" viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice" fill="none">
      <path d="M100 300 C 300 120 700 120 900 300 C 1050 430 700 520 400 480 C 180 450 60 400 100 300 Z" stroke="rgba(255,255,255,.05)" stroke-width="1.4"/>
      <path d="M210 320 C 370 190 660 190 810 320 C 920 410 660 470 430 445 C 270 428 170 385 210 320 Z" stroke="rgba(95,227,192,.07)" stroke-width="1.4"/>
      <path d="M330 345 C 440 260 620 260 720 345 C 790 400 620 435 470 420 C 370 410 300 380 330 345 Z" stroke="rgba(95,227,192,.05)" stroke-width="1.4"/>
    </svg>
  </div>

  <div class="relative max-w-3xl mx-auto px-5 text-center">
    <p class="eyebrow reveal">04 &#183; Early access</p>
    <h2 class="mt-6 text-5xl sm:text-6xl md:text-7xl leading-[1.02] reveal" style="transition-delay:.06s">
      <span class="block font-display italic font-normal">Stop drifting.</span>
      <span class="block font-medium mt-1 tracking-tight">Start sourcing.</span>
    </h2>
    <p class="mt-6 text-white/60 max-w-md mx-auto leading-relaxed reveal" style="transition-delay:.12s">We're onboarding a small circle of buyers first. Leave a work email and we'll send exactly one message â€” the moment your invite opens.</p>

    <div id="waitWrap" class="mt-10 max-w-md mx-auto reveal" style="transition-delay:.18s">
      <form id="waitForm" class="flex flex-col sm:flex-row gap-3">
        <input id="waitEmail" type="email" placeholder="work@company.com"
               class="flex-1 bg-white/[.05] border border-white/15 rounded-full px-5 py-3.5 text-sm placeholder:text-white/25 focus:outline-none focus:border-acc/60 focus:bg-white/[.08] transition-colors" />
        <button type="submit" class="btn-primary justify-center">Get early access <i data-lucide="arrow-right" class="w-4 h-4"></i></button>
      </form>
      <p id="waitErr" class="hidden mt-3 text-center text-xs text-[#ff7a66]"></p>
    </div>

    <p class="mlabel mt-6">No spam &#183; one email &#183; unsubscribe anytime</p>
  </div>
</section>

<!-- wave divider above footer -->
<div class="wave-line" aria-hidden="true">
  <svg class="block w-full" style="height:26px" viewBox="0 0 1200 26" preserveAspectRatio="none" fill="none">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-200 0" dur="7s" repeatCount="indefinite"/>
      <path vector-effect="non-scaling-stroke" stroke="rgba(255,255,255,.14)" stroke-width="1.5" stroke-linecap="round"
        d="M0 13 q 50 -11 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0"/>
    </g>
  </svg>
</div>

<!-- ================= FOOTER ================= -->
<footer class="py-10">
  <div class="max-w-6xl mx-auto px-5 flex flex-col md:flex-row items-center justify-between gap-6">
    <a href="#hero" class="flex items-center gap-2.5">
      <svg width="20" height="20" viewBox="0 0 256 256" fill="none" aria-hidden="true">
        <path d="M20 168 Q 76 64 128 168 T 236 168" stroke="#ffffff" stroke-width="26" stroke-linecap="round" fill="none"/>
        <circle cx="128" cy="56" r="22" fill="#5fe3c0"/>
      </svg>
      <span class="font-display italic text-xl text-white">Source&nbsp;Buddy</span>
    </a>
    <div class="flex flex-wrap justify-center gap-x-7 gap-y-2">
      <a href="#how"      class="mono text-[11px] tracking-[.18em] text-white/40 hover:text-white transition-colors">HOW IT WORKS</a>
      <a href="#stats"    class="mono text-[11px] tracking-[.18em] text-white/40 hover:text-white transition-colors">COVERAGE</a>
      <a href="#feedback" class="mono text-[11px] tracking-[.18em] text-white/40 hover:text-white transition-colors">FEEDBACK</a>
      <a href="#cta"      class="mono text-[11px] tracking-[.18em] text-white/40 hover:text-white transition-colors">ACCESS</a>
    </div>
    <p class="mono text-[11px] text-white/30">&#169; 2025 SOURCE BUDDY</p>
  </div>
</footer>

<!-- ================= DEPTH GAUGE (scroll narrative) ================= -->
<div id="gauge" class="fixed right-6 top-1/2 -translate-y-1/2 z-[95] hidden xl:flex flex-col items-center gap-4 pointer-events-none">
  <span class="mono text-[9px] tracking-[.3em] text-white/35">DEPTH</span>
  <div id="gaugeRail" class="relative h-[34vh] w-[2px] bg-white/10">
    <div id="gaugeFill" class="absolute top-0 left-0 w-[2px] bg-acc" style="height:0"></div>
    <div id="gaugeDot" class="absolute -left-[3px] w-2 h-2 rounded-full bg-acc" style="top:-4px"></div>
  </div>
  <span id="gaugeVal" class="mono text-[9px] tracking-[.18em] text-acc">SURFACE</span>
</div>

<!-- film grain, sits under the nav -->
<div class="grain fixed inset-0 z-[90] pointer-events-none" aria-hidden="true"></div>





`;
