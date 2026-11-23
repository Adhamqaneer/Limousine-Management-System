/* Apply presentation preferences before paint. Business data stays on the server. */
(() => {
  let theme = 'dark',
    language = 'en';
  try {
    if (localStorage.getItem('limousine.theme') === 'light') {
      theme = 'light';
    }
    if (localStorage.getItem('limousine.language') === 'ar') {
      language = 'ar';
    }
  } catch (_) {}
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.lang = language;
  root.dir = language === 'ar' ? 'rtl' : 'ltr';
})();
