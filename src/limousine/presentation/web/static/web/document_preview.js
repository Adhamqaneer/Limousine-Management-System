(() => {
  const en = {};
  document.querySelectorAll('[data-i18n]').forEach(el => { en[el.dataset.i18n]=el.textContent; });
  const ar = { download:'تنزيل الملف الأصلي', description:'معاينة النص والجداول. قد يختلف التنسيق والصور والصيغ عن الملف الأصلي.',
    unavailable:'تعذّرت معاينة هذا الملف. يمكنك تنزيل النسخة الأصلية.', truncated:'هذه معاينة محدودة لملف كبير. نزّل الملف الأصلي لعرضه كاملًا.',
    empty:'لا يوجد نص أو جداول قابلة للمعاينة في هذا الملف.', back:'العودة للسيارات', navDrivers:'سجل الشوفيرين', navTrash:'المحذوفات', navReports:'طباعة البيانات', navVehicles:'السيارات', teamAccess:'الفريق', brandSub:'إدارة السيارات', signOut:'تسجيل الخروج' };
  function apply() {
    const strings=document.documentElement.lang==='ar'?ar:en;
    document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=strings[el.dataset.i18n]??en[el.dataset.i18n];});
    document.querySelectorAll('[data-i18n-aria]').forEach(el=>{el.setAttribute('aria-label',strings[el.dataset.i18nAria]??'Sign out');});
  }
  window.addEventListener('hspace:language',apply); apply();
})();