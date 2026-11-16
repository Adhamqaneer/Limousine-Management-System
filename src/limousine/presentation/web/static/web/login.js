(() => {
  'use strict';
  const root = document.documentElement;
  const en = {};
  document.querySelectorAll('[data-i18n]').forEach(el => { en[el.dataset.i18n] = el.textContent; });
  const ar = { brandSub: 'إدارة السيارات', signIn: 'تسجيل الدخول',
    description: 'سجّل الدخول إلى مساحة إدارة سياراتك.', username: 'اسم المستخدم',
    password: 'كلمة المرور', theme: 'ليلي / نهاري', invalid: 'تأكد من اسم المستخدم وكلمة المرور.',
    unavailable: 'تسجيل الدخول غير متاح لحين تجهيز قاعدة البيانات المحلية.',
    skip: 'انتقل إلى تسجيل الدخول', storyTitle: 'لكل سيارة.', storyAccent: 'مساحتها الخاصة.',
    storyDescription: 'مساحة تجمع سياراتك، وتضع كل التفاصيل أمامك بوضوح.',
    storyCaption: 'سياراتك. مساحتك.', privateWorkspace: 'مساحة عمل خاصة',
    memberAccess: 'دخول الفريق', welcome: 'أهلًا بعودتك.',
    privateNote: 'مساحة خاصة بفريق المكتب.', footerTagline: 'لكل تفصيل مكانه.' };
  let language = 'en';
  try { if (localStorage.getItem('limousine.language') === 'ar') language = 'ar'; } catch (_) {}
  function preference(key, value) { try { localStorage.setItem(`limousine.${key}`, value); } catch (_) {} }
  function apply() {
    root.lang = language; root.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.title = language === 'ar' ? 'H SPACE | تسجيل الدخول' : 'H SPACE | Sign in';
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = (language === 'ar' ? ar : en)[el.dataset.i18n]; });
    const toggle = document.getElementById('language-toggle');
    toggle.textContent = language === 'ar' ? 'English' : 'العربية';
    toggle.setAttribute('aria-label', language === 'ar' ? 'Switch to English' : 'التبديل للعربية');
    document.querySelector('meta[name="theme-color"]').content = root.dataset.theme === 'light' ? '#f6f5f2' : '#18181b';
  }
  document.getElementById('language-toggle').addEventListener('click', () => {
    language = language === 'en' ? 'ar' : 'en'; preference('language', language); apply();
  });
  document.getElementById('theme-toggle').addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    preference('theme', root.dataset.theme); apply();
  });
  apply();
})();
