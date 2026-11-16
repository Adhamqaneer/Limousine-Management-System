(() => {
  'use strict';
  let arabic = false;
  try { arabic = localStorage.getItem('limousine.language') === 'ar'; } catch (_) {}
  if (!arabic) return;
  document.documentElement.lang = 'ar'; document.documentElement.dir = 'rtl';
  const strings = { download: 'تنزيل الملف الأصلي', description: 'معاينة النص والجداول. قد يختلف التنسيق والصور والصيغ عن الملف الأصلي.',
    unavailable: 'تعذّرت معاينة هذا الملف. يمكنك تنزيل النسخة الأصلية.', truncated: 'هذه معاينة محدودة لملف كبير. نزّل الملف الأصلي لعرضه كاملًا.',
    empty: 'لا يوجد نص أو جداول قابلة للمعاينة في هذا الملف.' };
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = strings[el.dataset.i18n]; });
})();
