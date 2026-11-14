/* Apply the saved palette before CSS loads, without requiring storage access. */
(() => {
  let theme = 'dark';
  try {
    if (localStorage.getItem('limousine.theme') === 'light') theme = 'light';
  } catch (_) { /* Preferences still work for this visit when storage is blocked. */ }
  document.documentElement.dataset.theme = theme;
})();
