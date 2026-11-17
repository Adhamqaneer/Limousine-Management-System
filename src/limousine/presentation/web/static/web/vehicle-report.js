(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const en = {};
  document.querySelectorAll('[data-i18n]').forEach(el => { en[el.dataset.i18n] = el.textContent; });
  Object.assign(en, {
    choosePrintStyle:'Choose paper style', paperStyleDescription:'Is your paper blank or already printed with the office letterhead?',
    withLetterhead:'With letterhead', withoutLetterhead:'Without letterhead', cancelPrint:'Cancel',
    withLetterheadHint:'For blank paper or PDF: include the office letterhead and H SPACE watermark.',
    withoutLetterheadHint:'For preprinted office paper: leave the letterhead area empty and omit the watermark.',
    owner_name:'Owner name', owner_phone:'Owner phone number', driver_name:'Driver name', driver_phone:'Driver phone number',
    vehicle_type:'Vehicle type', manufacture_year:'Vehicle model', chassis_number:'Chassis number', plate_number:'Vehicle number',
    noFields:'Choose at least one field to preview and print.', emptyReport:'No vehicles yet. Add a vehicle first.', noMatches:'No vehicles match these filters. Return to Vehicles to change the filters, or open Print all vehicles.',
    failedReport:'Could not load vehicle data. Use Refresh data to try again.', signOut:'Sign out',
    filteredTitle:'Filtered vehicle report', filteredScope:'Matching vehicles only', printAll:'Print all vehicles', searchTerms:'Search',
    invalidScope:'The report filters are invalid. Return to Vehicles and choose Print results again.',
    matchedAll:'Current results without additional filters',
    selection:'{count} of 8 fields selected · {orientation}', portrait:'A4 portrait', landscape:'A4 landscape',
    rowCount:'Vehicles: {count}'
  });
  const ar = {
    choosePrintStyle:'اختيار نوع الورق', paperStyleDescription:'الورق أبيض، أو عليه ترويسة المكتب مسبقًا؟',
    withLetterhead:'مع الترويسة', withoutLetterhead:'بدون ترويسة', cancelPrint:'إلغاء',
    withLetterheadHint:'للورق الأبيض أو PDF: طباعة ترويسة المكتب وعلامة H SPACE المائية.',
    withoutLetterheadHint:'لورق المكتب الجاهز: ترك مكان الترويسة فارغًا بدون طباعة العلامة المائية.',
    skip:'انتقل إلى المحتوى', navVehicles:'السيارات', navDrivers:'سجل الشوفيرين', navTrash:'المحذوفات', navReports:'طباعة البيانات', teamAccess:'إدارة الفريق', brandSub:'إدارة السيارات', signOut:'تسجيل الخروج',
    reportEyebrow:'بيانات مكتبك، على ورق', reportTitle:'طباعة بيانات السيارات',
    reportDescription:'اختار الخانات، عاين كل السيارات، واطبع الكشف أو احفظه PDF.',
    chooseFields:'اختيار الخانات', selectAll:'اختيار الكل', clearFields:'إلغاء الاختيار', refreshReport:'تحديث البيانات', printReport:'طباعة / حفظ PDF',

    previewTitle:'معاينة الكشف', allVehicles:'جميع السيارات · حسب ترتيب الإضافة', sheetTitle:'كشف بيانات السيارات',
    loadingReport:'جارٍ تحميل السيارات…', noFields:'اختار خانة واحدة على الأقل لمعاينة الكشف وطباعته.',
    emptyReport:'لا توجد سيارات بعد. أضف سيارة أولًا.', noMatches:'لا توجد سيارات تطابق الفلاتر. ارجع لتغيير الفلاتر أو افتح طباعة كل السيارات.', failedReport:'تعذّر تحميل بيانات السيارات. اضغط تحديث البيانات للمحاولة مجددًا.',
    owner_name:'اسم المالك', owner_phone:'رقم تلفون المالك', driver_name:'اسم الشوفير', driver_phone:'رقم تلفون الشوفير',
    vehicle_type:'نوع المركبة', manufacture_year:'موديل المركبة', chassis_number:'رقم الشصي', plate_number:'رقم المركبة',
    filteredTitle:'كشف نتائج السيارات', filteredScope:'السيارات المطابقة فقط', printAll:'طباعة كل السيارات', searchTerms:'البحث',
    invalidScope:'فلاتر الكشف غير صالحة. ارجع للسيارات واضغط طباعة النتائج مجددًا.', matchedAll:'النتائج الحالية بدون فلاتر إضافية',
    selection:'تم اختيار {count} من 8 خانات · {orientation}', portrait:'A4 بالطول', landscape:'A4 بالعرض', rowCount:'عدد السيارات: {count}'
  };
  const selected = new Set(['plate_number']);
  let scope = HSpaceVehicleFilters.reportScope(location.hash);
  let vehicles = [], state = '', loading = false, preprinted = false;
  const t = (key, values = {}) => {
    let text = (document.documentElement.lang === 'ar' ? ar[key] : en[key]) ?? en[key] ?? key;
    Object.entries(values).forEach(([name, value]) => { text = text.replaceAll(`{${name}}`, String(value)); });
    return text;
  };
  function element(tag, text) { const node = document.createElement(tag); node.textContent = text; return node; }
  function render() {
    const names = HSpaceReport.columns([...selected]);
    const landscape = HSpaceReport.landscape(names);
    $('selection-summary').textContent = t('selection', {count:names.length, orientation:t(landscape ? 'landscape' : 'portrait')});
    const status = !scope.valid ? 'invalidScope' : state || (!names.length ? 'noFields' : !vehicles.length ? (scope.filtered ? 'noMatches' : 'emptyReport') : '');
    const criteria = HSpaceVehicleFilters.fields.filter(field => scope.selected[field]).map(field => `${t(field)}: ${scope.selected[field]}`);
    if (scope.query) criteria.push(`${t('searchTerms')}: ${scope.query}`);
    $('report-criteria').textContent = scope.filtered ? criteria.join(' · ') || t('matchedAll') : '';
    $('report-criteria').hidden = !scope.filtered;
    $('report-scope-description').textContent = t(scope.filtered ? 'filteredScope' : 'allVehicles');
    $('print-all-vehicles').hidden = !scope.filtered;
    document.querySelectorAll('[data-i18n="sheetTitle"]').forEach(el => { el.textContent = t(scope.filtered ? 'filteredTitle' : 'sheetTitle'); });
    $('report-status').textContent = status ? t(status) : '';
    $('report-status').hidden = !status;
    $('report-paper').hidden = Boolean(status);
    $('report-paper').classList.toggle('landscape', landscape);
    $('report-paper').classList.toggle('preprinted-paper', preprinted);
    $('print-report').disabled = Boolean(status);
    $('refresh-report').disabled = state === 'loadingReport';
    $('report-choices').setAttribute('aria-busy', String(state === 'loadingReport'));
    const header = document.createElement('tr');
    names.forEach(name => { const th = element('th', t(name)); th.scope = 'col'; header.append(th); });
    $('report-head').replaceChildren(...header.children);
    $('report-letterhead-cell').colSpan = Math.max(1, names.length);
    const rows = HSpaceReport.rows(status ? [] : vehicles, names).map(values => {
      const row = document.createElement('tr');
      values.forEach((value, index) => {
        const td = document.createElement('td'); const content = element('bdi', value);
        content.dir = ['owner_name','driver_name','vehicle_type'].includes(names[index]) ? 'auto' : 'ltr';
        td.append(content); row.append(td);
      });
      return row;
    });
    $('report-body').replaceChildren(...rows);
    $('report-count').textContent = t('rowCount', {count:vehicles.length});

  }
  function translate() {
    document.title = `H SPACE | ${t('reportTitle')}`;
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
    HSpaceReport.fields.forEach(name => { $('label-' + name).textContent = t(name); });
    render();
  }
  HSpaceReport.fields.forEach(name => {
    const label = document.createElement('label'); label.className = 'report-choice';
    const input = document.createElement('input'); input.type = 'checkbox'; input.value = name; input.checked = selected.has(name);
    const caption = element('span', t(name)); caption.id = 'label-' + name;
    input.addEventListener('change', () => { if (input.checked) selected.add(name); else selected.delete(name); render(); });
    label.append(input, caption); $('report-choices').append(label);
  });
  function select(all) {
    selected.clear();
    $('report-choices').querySelectorAll('input').forEach(input => { input.checked = all; if (all) selected.add(input.value); });
    render();
  }
  async function load() {
    if (loading) return;
    if (!scope.valid) { vehicles = []; state = ''; render(); return; }
    loading = true;
    state = 'loadingReport'; vehicles = []; render();
    try {
      const response = await fetch('/api/vehicles/', {credentials:'same-origin', cache:'no-store'});
      if (response.status === 401) { location.assign('/login/'); return; }
      if (!response.ok) throw new Error();
      const payload = await response.json();
      if (!Array.isArray(payload.vehicles)) throw new Error();
      vehicles = scope.filtered ? HSpaceSearch.search(HSpaceVehicleFilters.apply(payload.vehicles, scope.selected), scope.query) : payload.vehicles;
      state = '';
    } catch (_) { state = 'failedReport'; }
    finally { loading = false; }
    render();
  }
  $('select-all').addEventListener('click', () => select(true));
  $('clear-fields').addEventListener('click', () => select(false));
  $('refresh-report').addEventListener('click', load);
  $('print-report').addEventListener('click', () => { if (!$('print-report').disabled) $('print-style-dialog').showModal(); });
  function printStyle(usePreprinted) {
    if ($('print-report').disabled) { $('print-style-dialog').close(); return; }
    preprinted = usePreprinted; render(); $('print-style-dialog').close(); window.print();
  }
  $('print-with-letterhead').addEventListener('click', () => printStyle(false));
  $('print-without-letterhead').addEventListener('click', () => printStyle(true));
  $('cancel-print-style').addEventListener('click', () => $('print-style-dialog').close());
  window.addEventListener('hspace:language', translate);
  window.addEventListener('hashchange', () => { scope = HSpaceVehicleFilters.reportScope(location.hash); load(); });
  // Clear sensitive report contents when restored from the back/forward cache.
  window.addEventListener('pageshow', event => { if (event.persisted) load(); });
  translate(); load();
})();
