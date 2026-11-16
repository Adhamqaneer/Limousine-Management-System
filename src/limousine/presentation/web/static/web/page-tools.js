/* Shared language/theme controls for Team and Office-document pages. */
(() => {
  const root = document.documentElement;
  function save(key, value) { try { localStorage.setItem('limousine.' + key, value); } catch (_) {} }
  function refresh() {
    const arabic = root.lang === 'ar', dark = root.dataset.theme !== 'light';
    const language = document.getElementById('language-label');
    language.textContent = arabic ? 'English' : 'العربية'; language.lang = arabic ? 'en' : 'ar';
    document.getElementById('language-toggle').setAttribute('aria-label', arabic ? 'Switch to English' : 'التبديل للعربية');
    const title = arabic ? (dark ? 'تفعيل الوضع النهاري' : 'تفعيل الوضع الليلي') : (dark ? 'Switch to light mode' : 'Switch to dark mode');
    const theme = document.getElementById('theme-toggle'); theme.setAttribute('aria-label', title); theme.title = title;
    document.querySelector('meta[name="theme-color"]').content = dark ? '#101113' : '#f5f3ef';
  }
  document.getElementById('language-toggle').addEventListener('click', () => {
    root.lang = root.lang === 'ar' ? 'en' : 'ar'; root.dir = root.lang === 'ar' ? 'rtl' : 'ltr';
    save('language', root.lang); refresh(); window.dispatchEvent(new Event('hspace:language'));
  });
  document.getElementById('theme-toggle').addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    save('theme', root.dataset.theme); refresh();
  });
  refresh();
})();