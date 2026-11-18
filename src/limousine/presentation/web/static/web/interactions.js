/* Pointer response is decorative; links, touch and keyboard remain native. */
(() => {
  'use strict';

  const grid = document.getElementById('vehicle-grid');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  let active = null,
    bounds = null,
    frame = 0,
    point = null;
  let detailAnimation = null;
  function reset() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    point = null;
    bounds = null;
    if (active) {
      active.removeAttribute('data-engaged');
      ['--tilt-x', '--tilt-y', '--pointer-x', '--pointer-y'].forEach((name) =>
        active.style.removeProperty(name),
      );
    }
    active = null;
  }
  function allowed(event) {
    return finePointer.matches && !reducedMotion.matches && event.pointerType === 'mouse';
  }
  if (grid) {
    grid.addEventListener(
      'pointermove',
      (event) => {
        if (!allowed(event) || event.target.closest('button, input')) {
          reset();
          return;
        }
        const card = event.target.closest('.vehicle-card');
        if (!card || !grid.contains(card)) {
          reset();
          return;
        }
        if (active !== card) {
          reset();
          active = card;
          bounds = card.getBoundingClientRect();
          active.dataset.engaged = 'true';
        }
        if (!bounds.width || !bounds.height) {
          reset();
          return;
        }
        point = {
          x: event.clientX,
          y: event.clientY,
        };
        if (frame) return;
        frame = requestAnimationFrame(() => {
          frame = 0;
          if (!active?.isConnected || !point) {
            reset();
            return;
          }
          const x = Math.max(0, Math.min(1, (point.x - bounds.left) / bounds.width));
          const y = Math.max(0, Math.min(1, (point.y - bounds.top) / bounds.height));
          active.style.setProperty('--tilt-x', ((0.5 - y) * 3).toFixed(2) + 'deg');
          active.style.setProperty('--tilt-y', ((x - 0.5) * 3).toFixed(2) + 'deg');
          active.style.setProperty('--pointer-x', (x * 100).toFixed(1) + '%');
          active.style.setProperty('--pointer-y', (y * 100).toFixed(1) + '%');
        });
      },
      {
        passive: true,
      },
    );
    grid.addEventListener('pointerleave', reset);
    grid.addEventListener('pointercancel', reset);
    // Reset before a click; upload/delete buttons keep a steady target.
    grid.addEventListener('pointerdown', reset);
    document.addEventListener('hspace:cards-changed', reset);
    window.addEventListener('blur', reset);
    window.addEventListener('resize', reset, {
      passive: true,
    });
    window.addEventListener('scroll', reset, {
      passive: true,
      capture: true,
    });
  }
  function stopMotion() {
    reset();
    detailAnimation?.cancel();
    detailAnimation = null;
  }
  reducedMotion.addEventListener('change', stopMotion);
  finePointer.addEventListener('change', reset);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopMotion();
  });
  document.addEventListener('hspace:detail-ready', () => {
    detailAnimation?.cancel();
    detailAnimation = null;
    const content = document.getElementById('detail-content');
    if (reducedMotion.matches || !content || content.hidden || !content.animate) return;
    detailAnimation = content.animate(
      [
        {
          opacity: 0.65,
          transform: 'translateY(6px)',
        },
        {
          opacity: 1,
          transform: 'translateY(0)',
        },
      ],
      {
        duration: 200,
        easing: 'cubic-bezier(.2,.7,.2,1)',
      },
    );
  });
})();
