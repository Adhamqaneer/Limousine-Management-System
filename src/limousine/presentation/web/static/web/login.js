(() => {
  'use strict';

  const root = document.documentElement,
    en = {};
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    en[el.dataset.i18n] = el.textContent;
  });
  const ar = {
    brandSub: 'إدارة السيارات',
    signIn: 'تسجيل الدخول',
    setupTitle: 'تعيين كلمة المرور',
    setupDescription: 'اختار كلمة مرور لحساب H space.',
    setupInvalid: 'اكتب كلمة مرور مطابقة من ٨ خانات على الأقل وتحتوي على رمز غير رقمي.',
    confirmPassword: 'تأكيد كلمة المرور',
    setPassword: 'حفظ كلمة المرور',
    description: 'سجّل الدخول إلى مساحة إدارة سياراتك.',
    username: 'اسم المستخدم',
    password: 'كلمة المرور',
    invalid: 'تأكد من اسم المستخدم وكلمة المرور.',
    unavailable: 'تسجيل الدخول غير متاح لحين تجهيز قاعدة البيانات المحلية.',
    skip: 'انتقل إلى تسجيل الدخول',
    storyTitle: 'لكل سيارة.',
    storyAccent: 'مساحتها الخاصة.',
    storyDescription: 'مساحة تجمع سياراتك، وتضع كل التفاصيل أمامك بوضوح.',
    storyCaption: 'سياراتك. مساحتك.',
    privateWorkspace: 'مساحة عملك الخاصة',
    welcome: 'أهلًا بعودتك.',
    privateNote: 'مساحة خاصة بفريق المكتب.',
    footerTagline: 'لكل تفصيل مكانه.',
  };
  let language = root.lang === 'ar' ? 'ar' : 'en';
  const password = document.getElementById('password'),
    toggle = document.getElementById('password-toggle');
  function save(
    key,
    value,
  ) {
    try {
      localStorage.setItem(
        'limousine.' + key,
        value,
      );
    } catch (_) {}
  }
  function apply() {
    const arabic = language === 'ar',
      dark = root.dataset.theme !== 'light';
    root.lang = language;
    root.dir = arabic ? 'rtl' : 'ltr';
    document.title = arabic ? 'H SPACE | تسجيل الدخول' : 'H SPACE | Sign in';
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      el.textContent = (arabic ? ar : en)[el.dataset.i18n] ?? en[el.dataset.i18n];
    });
    const label = document.getElementById('language-label');
    label.textContent = arabic ? 'English' : 'العربية';
    label.lang = arabic ? 'en' : 'ar';
    document
      .getElementById('language-toggle')
      .setAttribute(
        'aria-label',
        arabic ? 'Switch to English' : 'التبديل للعربية',
      );
    const themeLabel = arabic
      ? dark
        ? 'تفعيل الوضع النهاري'
        : 'تفعيل الوضع الليلي'
      : dark
        ? 'Switch to light mode'
        : 'Switch to dark mode';
    const theme = document.getElementById('theme-toggle');
    theme.setAttribute(
      'aria-label',
      themeLabel,
    );
    theme.title = themeLabel;
    toggle.textContent = arabic
      ? password.type === 'password'
        ? 'إظهار'
        : 'إخفاء'
      : password.type === 'password'
        ? 'Show'
        : 'Hide';
    toggle.setAttribute(
      'aria-label',
      arabic
        ? password.type === 'password'
          ? 'إظهار كلمة المرور'
          : 'إخفاء كلمة المرور'
        : password.type === 'password'
          ? 'Show password'
          : 'Hide password',
    );
    toggle.setAttribute(
      'aria-pressed',
      String(password.type === 'text'),
    );
    document.querySelector('meta[name="theme-color"]').content = dark ? '#101113' : '#f5f3ef';
  }
  document.getElementById('language-toggle').addEventListener(
    'click',
    () => {
      language = language === 'en' ? 'ar' : 'en';
      save(
        'language',
        language,
      );
      apply();
    },
  );
  document.getElementById('theme-toggle').addEventListener(
    'click',
    () => {
      root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
      save(
        'theme',
        root.dataset.theme,
      );
      apply();
    },
  );
  toggle.addEventListener(
    'click',
    () => {
      password.type = password.type === 'password' ? 'text' : 'password';
      apply();
    },
  );
  apply();
})();
