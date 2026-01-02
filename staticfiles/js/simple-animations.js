(function(){
  'use strict';
  function prefersReducedMotion(){ try{ return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches }catch(e){ return false } }
  document.addEventListener('DOMContentLoaded', function(){
    if(prefersReducedMotion()) return;

    // Choose a broad set of element selectors to animate on load
    const selectors = [
      '.panel', '.card', '.card-hero', '.chart-card', '.detected-card', '.result-item', '.stat', '.macro', '.streak-badge', '.upload-preview', '.logo', '.title', '.subtitle', '.btn', '.muted-btn', '.charts-grid', '.left-charts'
    ];
    const elems = Array.from(document.querySelectorAll(selectors.join(','))).filter(Boolean);
    // If none found, fall back to animating top-level sections
    if(elems.length === 0) elems.push(...Array.from(document.querySelectorAll('header, main, footer, section, aside')).slice(0,8));

    // Mark elements for prepare state
    elems.forEach(el => el.classList.add('anim-prepare'));

    // Add body class to indicate stagger mode
    document.body.classList.add('anim-stagger');

    // Stagger apply
    // Allowed hover selectors (buttons and top bar) — hover is now opt-in via 'hover-lift' class
    const allowedHoverSelectors = ['.btn', '.muted-btn', 'header', '.brand', '.logo'];

    // Make small pages feel like larger pages by adding a small startup delay when
    // there are few elements to animate. This keeps the entrance stagger more 'meaty'.
    const step = 60; // per-item step in ms
    const startDelay = elems.length < 8 ? 180 : 60;

    elems.forEach((el, i) => {
      const delay = Math.min(600, startDelay + (i * step));
      setTimeout(() => {
        el.classList.add('anim-play');
        // Only add hover lift when element explicitly opts-in via 'hover-lift' class
        // or when it matches allowedHoverSelectors (backwards compatibility)
        try{
          const allow = allowedHoverSelectors.some(sel => el.matches(sel));
          if(el.classList.contains('hover-lift') || allow){
            el.classList.add('anim-hover-lift');
          }
        }catch(e){ /* ignore matching errors for non-element nodes */ }
        el.classList.remove('anim-prepare');
      }, delay);
    });

    // Optional: small entrance ripple from top when page reload (pulse on body)
    setTimeout(()=>{ document.body.classList.remove('anim-stagger'); }, Math.min(600 + elems.length * 60, 2500));

    // Simple re-trigger on history back/forward (page show)
    window.addEventListener('pageshow', function(e){ if(e.persisted){ elems.forEach(el=>{ el.classList.remove('anim-play'); el.classList.add('anim-prepare'); }); setTimeout(()=> elems.forEach((el,i)=> setTimeout(()=>{ el.classList.add('anim-play'); el.classList.remove('anim-prepare') }, i*50)), 60); } });

  });
})();