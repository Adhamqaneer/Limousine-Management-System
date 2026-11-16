(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const root = document.documentElement;
  const en = {};
  document.querySelectorAll('[data-i18n]').forEach(el => { en[el.dataset.i18n] = el.textContent; });
  document.querySelectorAll('[data-i18n-aria]').forEach(el => { en[el.dataset.i18nAria] = el.getAttribute('aria-label'); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { en[el.dataset.i18nPlaceholder] = el.placeholder; });
  Object.assign(en, {
    title: 'H SPACE | Vehicles', teamAccess: 'Team', switchArabic: 'Switch to Arabic', switchEnglish: 'Switch to English',
    lightMode: 'Switch to light mode', darkMode: 'Switch to dark mode', vehicleCount: '{count} vehicles', vehicleCountOne: '1 vehicle',
    added: 'Added {date}', attachments: '{count} attachments', openVehicle: 'Open vehicle',
    saveUnavailable: 'Saving is unavailable until the local database is connected.', saving: 'Saving…', saved: 'Changes saved.',
    unavailable: 'Vehicle storage is unavailable. Please try again.',
    requestFailed: 'Something went wrong. Please try again.', notFound: 'This vehicle could not be found.',
    invalidPlate: 'Enter a plate number of up to 64 characters.',
    invalidDetails: 'Check the vehicle type and the length of each field.',
    invalidFile: 'This file is unsupported, damaged, or exceeds the allowed image dimensions. Check the format and limits below.',
    fileTooLarge: 'Each file must be no larger than 10 MB.',
    download: 'Download {name}', viewPhoto: 'View photo: {name}',
    viewFile: 'View', cardPhoto: 'Card photo', changeCardPhoto: 'Change card photo',
    deleteAttachment: 'Delete', deleteNamed: 'Delete {name}', removeCardPhoto: 'Remove card photo',
    confirmDelete: 'Permanently delete "{name}"? This cannot be undone.',
    confirmRemoveCover: 'Remove the card photo for {plate}? This cannot be undone.',
    deleting: 'Deleting…', deleted: 'Attachment deleted.', coverDeleted: 'Card photo removed.',
    coverSaving: 'Saving card photo…', coverSaved: 'Card photo saved.',
    uploading: 'Uploading {current} of {total}…', uploadComplete: '{count} attachments added.',
    partialUpload: '{count} attachments added. {error}', pending: 'Checking the database connection…',
    emptyDisconnected: 'Connect the local database to save vehicles, photos and files.',
    languageChanged: 'Language changed to English.', lightEnabled: 'Light mode enabled.', darkEnabled: 'Dark mode enabled.'
  });
  const ar = {
    heroAccent: 'كل التفاصيل قدامك.', navVehicles: 'السيارات', title: 'H SPACE | السيارات', skip: 'انتقل إلى المحتوى', brandSub: 'إدارة السيارات', vehicles: 'سياراتك.',
    workspace: 'مساحة عملك', teamAccess: 'إدارة الفريق', vehicleCollection: 'مجموعة السيارات', footerTagline: 'لكل تفصيل مكانه.',
    listDescription: 'لكل تفصيل مكانه. ولكل سيارة مساحتها.', addVehicle: 'إضافة سيارة',
    databaseTitle: 'تخزين السيارات غير متاح حاليًا',
    databaseDescription: 'أعد المحاولة عند توفر اتصال قاعدة البيانات المحلية.',
    retry: 'إعادة المحاولة', search: 'البحث بالنمرة أو النوع', searchPlaceholder: 'ابحث بالنمرة أو النوع…',
    loading: 'جارٍ تحميل السيارات…', loadFailed: 'تعذّر تحميل السيارات', loadFailedDescription: 'تحقّق من الاتصال ثم أعد المحاولة.',
    emptyTitle: 'سياراتك رح تظهر هون', emptyDescription: 'أضف أول سيارة لتجمع بياناتها وصورها وملفاتها في مكان واحد.',
    noResults: 'لا توجد سيارات مطابقة', trySearch: 'جرّب رقم سيارة آخر.', backToVehicles: 'العودة للسيارات',
    vehicleRecord: 'ملف السيارة', loadingDetails: 'جارٍ تحميل السيارة…', vehicleInformation: 'بيانات السيارة',
    plateNumber: 'نمرة السيارة', vehicleType: 'نوع السيارة', driverName: 'اسم الشوفير',
    chassisNumber: 'رقم الشصي', manufactureYear: 'سنة التصنيع', signOut: 'تسجيل الخروج', saveChanges: 'حفظ التعديلات',
    photos: 'الصور', photoDescription: 'الصور الخاصة بهذه السيارة.', addPhotos: 'إضافة صور', noPhotos: 'لم تُضف صور بعد.',
    photoHint: 'JPG أو PNG أو WebP · حتى 10 ميجابايت و25 مليون بكسل للصورة', files: 'الملفات', fileDescription: 'المستندات الخاصة بهذه السيارة.',
    addFiles: 'إضافة ملفات', noFiles: 'لم تُضف ملفات بعد.', fileHint: 'PDF أو TXT أو DOCX أو XLSX · حتى 10 ميجابايت للملف',
    addDescription: 'أدخل نوع السيارة ونمرتها، ثم أكمل باقي البيانات من صفحتها.', close: 'إغلاق', plateExample: 'مثال: 12-34567',
    cancel: 'إلغاء', saveVehicle: 'إضافة السيارة', switchArabic: 'التبديل للعربية', switchEnglish: 'Switch to English',
    lightMode: 'تفعيل الوضع النهاري', darkMode: 'تفعيل الوضع الليلي', vehicleCount: '{count} سيارة', vehicleCountOne: 'سيارة واحدة',
    added: 'أُضيفت في {date}', attachments: '{count} مرفق', openVehicle: 'فتح السيارة',
    saveUnavailable: 'الحفظ غير متاح قبل اتصال قاعدة البيانات المحلية.', saving: 'جارٍ الحفظ…', saved: 'تم حفظ التعديلات.',
    unavailable: 'تخزين السيارات غير متاح حاليًا. أعد المحاولة.', requestFailed: 'حدث خطأ. أعد المحاولة.',
    notFound: 'لم نتمكّن من العثور على هذه السيارة.', invalidPlate: 'أدخل نمرة سيارة لا تتجاوز 64 حرفًا.',
    invalidDetails: 'تحقّق من نوع السيارة وأطوال الخانات المدخلة.',
    invalidFile: 'الملف غير مدعوم أو تالف أو أبعاد الصورة أكبر من المسموح. تحقّق من الصيغة والحدود المذكورة.', fileTooLarge: 'حجم كل ملف يجب ألا يتجاوز 10 ميجابايت.',
    download: 'تنزيل {name}', viewPhoto: 'عرض الصورة: {name}', uploading: 'جارٍ رفع {current} من {total}…',
    viewFile: 'عرض', cardPhoto: 'صورة البطاقة', changeCardPhoto: 'تغيير صورة البطاقة',
    deleteAttachment: 'حذف', deleteNamed: 'حذف {name}', removeCardPhoto: 'حذف صورة البطاقة',
    confirmDelete: 'حذف "{name}" نهائيًا؟ لا يمكن التراجع عن الحذف.',
    confirmRemoveCover: 'حذف صورة بطاقة السيارة {plate}؟ لا يمكن التراجع عن الحذف.',
    deleting: 'جارٍ الحذف…', deleted: 'تم حذف المرفق.', coverDeleted: 'تم حذف صورة البطاقة.',
    coverSaving: 'جارٍ حفظ صورة البطاقة…', coverSaved: 'تم حفظ صورة البطاقة.',
    uploadComplete: 'تمت إضافة {count} مرفق.', partialUpload: 'تمت إضافة {count} مرفق. {error}',
    pending: 'جارٍ فحص اتصال قاعدة البيانات…', emptyDisconnected: 'جهّز اتصال قاعدة البيانات المحلية لإضافة السيارات وحفظ صورها وملفاتها.',
    languageChanged: 'تم التبديل إلى العربية.', lightEnabled: 'تم تفعيل الوضع النهاري.', darkEnabled: 'تم تفعيل الوضع الليلي.'
  };
  let language = 'en';
  try { if (localStorage.getItem('limousine.language') === 'ar') language = 'ar'; } catch (_) {}
  let vehicles = [];
  let currentVehicle = null;
  let storageReady = false;
  let listState = 'loading';
  let detailState = 'loading';
  let detailError = '';
  let addBusy = false;
  let informationBusy = false;
  let uploadBusy = false;
  let coverBusy = false;
  let deleteBusy = false;
  let activeDetailId = null;
  let listRequest = 0;
  let detailRequest = 0;
  const messages = new Map();
  const detailFields = { plate_number: 'detail-plate', vehicle_type: 'detail-type',
    driver_name: 'detail-driver', chassis_number: 'detail-chassis', manufacture_year: 'detail-year' };
  function detailValues() {
    return Object.fromEntries(Object.entries(detailFields).map(([name, id]) => [name, $(id).value.trim()]));
  }

  function t(key, values = {}) {
    let result = (language === 'ar' ? ar[key] : en[key]) ?? en[key] ?? key;
    Object.entries(values).forEach(([name, value]) => {
      const text = value && typeof value === 'object' && value.key ? t(value.key, value.values) : String(value);
      result = result.replaceAll(`{${name}}`, () => text);
    });
    return result;
  }
  function savePreference(key, value) { try { localStorage.setItem(`limousine.${key}`, value); } catch (_) {} }
  function announce(message) { $('announcement').textContent = message; }
  function show(id, visible) { $(id).hidden = !visible; }
  function renderMessage(id) {
    const { key, values, style } = messages.get(id);
    $(id).textContent = key ? t(key, values) : '';
    $(id).className = `${id === 'upload-message' ? 'upload-message' : 'form-message'} ${style}`;
  }
  function message(id, key = '', style = '', values = {}) {
    messages.set(id, { key, values, style });
    renderMessage(id);
  }
  function icon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('icon'); svg.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', `#${name}`); svg.append(use); return svg;
  }
  function element(tag, className, text) {
    const result = document.createElement(tag);
    if (className) result.className = className;
    if (text !== undefined) result.textContent = text;
    return result;
  }
  function date(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '';
    return new Intl.DateTimeFormat(language === 'ar' ? 'ar-JO' : 'en-GB', { year: 'numeric', month: 'short', day: 'numeric' }).format(parsed);
  }
  function fileSize(value) {
    return value >= 1048576 ? `${(value / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.ceil(value / 1024))} KB`;
  }
  function errorKey(error) {
    const code = error.code || '';
    if (['storage_unavailable', 'database_unavailable'].includes(code)) return 'unavailable';
    if (['not_found', 'vehicle_not_found', 'attachment_not_found'].includes(code)) return 'notFound';
    if (['invalid_plate', 'invalid_plate_number'].includes(code)) return 'invalidPlate';
    if (code === 'validation_error') return 'invalidDetails';
    if (['file_too_large', 'upload_too_large'].includes(code)) return 'fileTooLarge';
    if (['invalid_file', 'unsupported_file', 'unsupported_file_type', 'invalid_image'].includes(code)) return 'invalidFile';
    return 'requestFailed';
  }
  async function api(url, options = {}) {
    const headers = new Headers(options.headers);
    if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    if (options.method && !['GET', 'HEAD'].includes(options.method)) {
      const token = document.cookie.split('; ').find(part => part.startsWith('csrftoken='))?.slice(10);
      if (token) headers.set('X-CSRFToken', decodeURIComponent(token));
    }
    const response = await fetch(url, { ...options, headers, credentials: 'same-origin', cache: 'no-store' });
    if (response.status === 401) { window.location.assign('/login/'); throw new Error('Sign in required'); }
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error('Request failed');
      error.code = payload.error?.code;
      error.status = response.status;
      throw error;
    }
    return payload;
  }
  function updateThemeButton() {
    const dark = root.dataset.theme !== 'light';
    $('theme-toggle').setAttribute('aria-label', t(dark ? 'lightMode' : 'darkMode'));
    $('theme-toggle').title = t(dark ? 'lightMode' : 'darkMode');
    document.querySelector('meta[name="theme-color"]').content = dark ? '#101113' : '#f5f3ef';
  }
  function applyLanguage() {
    root.lang = language; root.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.title = currentVehicle && activeDetailId ? `${currentVehicle.plate_number} | ${t('title')}` : t('title');
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
    $('language-label').textContent = language === 'ar' ? 'English' : 'العربية';
    $('language-label').lang = language === 'ar' ? 'en' : 'ar';
    $('language-toggle').setAttribute('aria-label', t(language === 'ar' ? 'switchEnglish' : 'switchArabic'));
    updateThemeButton(); renderList(); renderDetail(false); updateAddState();
    messages.forEach((_, id) => renderMessage(id));
  }
  function renderList() {
    show('list-loading', listState === 'loading'); show('list-error', listState === 'error');
    show('connection-notice', listState === 'unavailable');
    const query = $('vehicle-search').value.trim().toLocaleLowerCase();
    const filtered = vehicles.filter(vehicle => `${vehicle.vehicle_type} ${vehicle.plate_number}`.toLocaleLowerCase().includes(query));
    const empty = !vehicles.length && ['ready', 'unavailable'].includes(listState);
    show('empty-fleet', empty);
    $('empty-description').textContent = t(listState === 'unavailable' ? 'emptyDisconnected' : 'emptyDescription');
    show('no-results', listState === 'ready' && vehicles.length > 0 && !filtered.length);
    $('vehicle-count').textContent = listState === 'ready' ? t(filtered.length === 1 ? 'vehicleCountOne' : 'vehicleCount', { count: filtered.length }) : '';
    const cards = listState === 'ready' ? filtered.map(vehicle => {
      const card = element('article', 'vehicle-card');
      const link = element('a', 'vehicle-card-link'); link.href = `#vehicle/${vehicle.id}`;
      link.setAttribute('aria-label', `${t('openVehicle')}: ${vehicle.vehicle_type} ${vehicle.plate_number}`);
      const image = element('div', 'vehicle-image');
      if (vehicle.cover_url) { const img = document.createElement('img'); img.src = vehicle.cover_url; img.alt = ''; img.loading = 'lazy'; image.append(img); }
      else image.append(icon('car'));
      const body = element('div', 'vehicle-body'); const title = element('h2');
      title.append(element('bdi', '', vehicle.plate_number));
      const type = element('p', 'vehicle-kind'); type.append(element('bdi', '', vehicle.vehicle_type));
      body.append(type, title, element('p', 'vehicle-meta', t('added', { date: date(vehicle.created_at) })));
      const footer = element('div', 'vehicle-card-footer');
      const open = element('span', 'open-label', t('openVehicle')); open.append(icon('arrow'));
      footer.append(element('span', '', t('attachments', { count: vehicle.attachment_count })), open);
      body.append(footer); link.append(image, body);
      const button = element('button', 'button secondary small card-photo-button', t(vehicle.cover_url ? 'changeCardPhoto' : 'cardPhoto'));
      button.type = 'button'; button.disabled = coverBusy;
      button.prepend(icon('photo'));
      button.setAttribute('aria-label', `${button.textContent}: ${vehicle.plate_number}`);
      const input = document.createElement('input'); input.type = 'file'; input.hidden = true;
      input.accept = 'image/jpeg,image/png,image/webp';
      button.addEventListener('click', () => input.click());
      input.addEventListener('change', () => saveCardPhoto(vehicle.id, input.files[0]));
      card.append(link, button, input);
      if (vehicle.cover_url) {
        const remove = element('button', 'button ghost small remove-cover-button danger', t('removeCardPhoto'));
        remove.type = 'button'; remove.disabled = coverBusy;
        remove.setAttribute('aria-label', `${t('removeCardPhoto')}: ${vehicle.plate_number}`);
        remove.addEventListener('click', () => removeCardPhoto(vehicle)); card.append(remove);
      }
      return card;
    }) : [];
    document.dispatchEvent(new Event('hspace:cards-changed'));
    $('vehicle-grid').replaceChildren(...cards);
  }
  async function loadVehicles() {
    const request = ++listRequest;
    listState = 'loading'; storageReady = false; renderList(); updateAddState();
    try {
      const payload = await api('/api/vehicles/');
      if (request !== listRequest) return;
      vehicles = payload.vehicles; listState = 'ready'; storageReady = true;
    } catch (error) {
      if (request !== listRequest) return;
      vehicles = []; listState = error.status === 503 ? 'unavailable' : 'error';
    }
    renderList(); updateAddState();
  }
  async function saveCardPhoto(id, file) {
    if (!file || coverBusy) return;
    if (file.size > 10 * 1024 * 1024) { message('cover-message', 'fileTooLarge', 'error'); return; }
    if (!['jpg', 'jpeg', 'png', 'webp'].includes(file.name.split('.').pop().toLowerCase())) {
      message('cover-message', 'invalidFile', 'error'); return;
    }
    coverBusy = true; renderList(); message('cover-message', 'coverSaving');
    try {
      const body = new FormData(); body.append('file', file);
      const payload = await api(`/api/vehicles/${id}/cover/`, { method: 'POST', body });
      vehicles = vehicles.map(vehicle => vehicle.id === id ? payload.vehicle : vehicle);
      message('cover-message', 'coverSaved', 'success');
    } catch (error) { message('cover-message', errorKey(error), 'error'); }
    finally { coverBusy = false; renderList(); }
  }
  async function removeCardPhoto(vehicle) {
    if (coverBusy || !window.confirm(t('confirmRemoveCover', { plate: vehicle.plate_number }))) return;
    coverBusy = true; renderList(); message('cover-message', 'deleting');
    try {
      await api(`/api/vehicles/${vehicle.id}/cover/`, { method: 'DELETE' });
      vehicles = vehicles.map(item => item.id === vehicle.id ? { ...item, cover_url: null } : item);
      message('cover-message', 'coverDeleted', 'success');
    } catch (error) { message('cover-message', errorKey(error), 'error'); }
    finally { coverBusy = false; renderList(); }
  }
  function updateAddState() {
    $('save-vehicle').disabled = !storageReady || addBusy;
    $('new-plate').disabled = addBusy;
    $('new-type').disabled = addBusy;
    $('close-dialog').disabled = addBusy; $('cancel-add').disabled = addBusy;
    $('save-vehicle').textContent = t(addBusy ? 'saving' : 'saveVehicle');
    $('save-vehicle').setAttribute('aria-busy', String(addBusy));
    if (!storageReady) {
      message('add-message', listState === 'loading' ? 'pending' : 'saveUnavailable');
      $('add-message').dataset.connectionNotice = 'true';
    } else if ($('add-message').dataset.connectionNotice === 'true' || !$('add-dialog').open) {
      message('add-message', '');
      $('add-message').dataset.connectionNotice = 'false';
    }
  }
  function openAdd() {
    $('add-form').reset(); message('add-message', ''); updateAddState(); $('add-dialog').showModal();
    $('new-type').focus();
  }
  function renderDetail(resetInput = false) {
    show('detail-loading', detailState === 'loading'); show('detail-error', detailState === 'error');
    show('detail-content', detailState === 'ready' && !!currentVehicle);
    $('detail-error-text').textContent = detailError ? t(detailError) : '';
    if (currentVehicle) {
      $('detail-title').replaceChildren(element('bdi', '', currentVehicle.vehicle_type),
        document.createTextNode(' · '), element('bdi', '', currentVehicle.plate_number));
    } else $('detail-title').textContent = t('vehicleRecord');
    $('detail-created').textContent = currentVehicle ? t('added', { date: date(currentVehicle.created_at) }) : '';
    $('record-id').textContent = currentVehicle ? `#${currentVehicle.id}` : '';
    $('record-id').hidden = !currentVehicle;
    if (!currentVehicle) return;
    if (resetInput) Object.entries(detailFields).forEach(([name, id]) => { $(id).value = currentVehicle[name] || ''; });
    const photos = currentVehicle.attachments.filter(file => file.kind === 'image');
    const files = currentVehicle.attachments.filter(file => file.kind !== 'image');
    show('photos-empty', !photos.length); show('files-empty', !files.length);
    function download(file) {
      const link = element('a', 'download-link'); link.href = file.download_url;
      link.setAttribute('aria-label', t('download', { name: file.name })); link.title = t('download', { name: file.name });
      link.append(icon('download')); return link;
    }
    function remove(file) {
      const button = element('button', 'button ghost small danger attachment-delete', t('deleteAttachment'));
      button.type = 'button'; button.disabled = deleteBusy || uploadBusy || informationBusy;
      button.setAttribute('aria-label', t('deleteNamed', { name: file.name }));
      button.addEventListener('click', () => deleteAttachment(currentVehicle.id, file)); return button;
    }
    $('photo-grid').replaceChildren(...photos.map(file => {
      const card = element('div', 'photo-card'); const link = element('a', 'photo-link');
      link.href = file.preview_url; link.target = '_blank'; link.rel = 'noopener';
      link.setAttribute('aria-label', t('viewPhoto', { name: file.name }));
      const img = document.createElement('img'); img.src = file.preview_url; img.alt = file.name; img.loading = 'lazy'; link.append(img);
      const caption = element('div', 'photo-caption'); const name = element('bdi', 'filename', file.name); name.title = file.name;
      const actions = element('div', 'file-actions'); actions.append(download(file), remove(file));
      caption.append(name, actions); card.append(link, caption); return card;
    }));
    $('file-list').replaceChildren(...files.map(file => {
      const row = element('div', 'file-row'); const info = element('div', 'file-info');
      const name = element('bdi', 'filename', file.name); name.title = file.name;
      info.append(name, element('span', 'file-meta', `${fileSize(file.size)} · ${date(file.uploaded_at)}`));
      const actions = element('div', 'file-actions');
      const preview = element('a', 'button secondary small', t('viewFile'));
      preview.href = file.preview_url; preview.target = '_blank'; preview.rel = 'noopener';
      preview.setAttribute('aria-label', `${t('viewFile')}: ${file.name}`);
      actions.append(preview, download(file), remove(file)); row.append(icon('file'), info, actions); return row;
    }));
    updateDetailControls();
  }
  function updateDetailControls() {
    const busy = informationBusy || uploadBusy || deleteBusy;
    document.querySelectorAll('.attachment-delete').forEach(button => { button.disabled = busy; });
    Object.values(detailFields).forEach(id => { $(id).disabled = busy; });
    const unchanged = currentVehicle && Object.entries(detailValues()).every(([name, value]) => value === (currentVehicle[name] || ''));
    $('save-information').disabled = busy || !currentVehicle || unchanged;
    $('save-information').textContent = t(informationBusy ? 'saving' : 'saveChanges');
    $('save-information').setAttribute('aria-busy', String(informationBusy));
    $('add-photos').disabled = busy; $('add-files').disabled = busy;
  }
  async function deleteAttachment(id, file) {
    if (deleteBusy || uploadBusy || informationBusy || !window.confirm(t('confirmDelete', { name: file.name }))) return;
    deleteBusy = true; updateDetailControls(); message('upload-message', 'deleting');
    try {
      await api(`/api/vehicles/${id}/attachments/${file.id}/`, { method: 'DELETE' });
      if (activeDetailId !== id || !currentVehicle) return;
      currentVehicle = { ...currentVehicle, attachments: currentVehicle.attachments.filter(item => item.id !== file.id),
        attachment_count: currentVehicle.attachments.filter(item => item.id !== file.id).length };
      renderDetail(); message('upload-message', 'deleted', 'success');
      $('upload-message').focus({ preventScroll: true });
    } catch (error) {
      if (activeDetailId === id) message('upload-message', errorKey(error), 'error');
    } finally { deleteBusy = false; updateDetailControls(); }
  }
  async function loadDetail(id, resetInput = true) {
    const request = ++detailRequest;
    if (resetInput) { detailState = 'loading'; detailError = ''; currentVehicle = null; renderDetail(); }
    try {
      const payload = await api(`/api/vehicles/${id}/`);
      if (request !== detailRequest || id !== activeDetailId) return;
      currentVehicle = payload.vehicle; detailState = 'ready'; renderDetail(resetInput);
      if (resetInput) document.dispatchEvent(new Event('hspace:detail-ready'));
      document.title = `${currentVehicle.plate_number} | ${t('title')}`;
      if (resetInput) $('detail-title').focus({ preventScroll: true });
    } catch (error) {
      if (request !== detailRequest || id !== activeDetailId) return;
      detailError = errorKey(error); detailState = 'error'; renderDetail();
      if (resetInput) $('detail-title').focus({ preventScroll: true });
    }
  }
  function route() {
    const previousDetailId = activeDetailId;
    const match = window.location.hash.match(/^#vehicle\/(\d+)$/);
    activeDetailId = match ? Number(match[1]) : null;
    show('list-view', !activeDetailId); show('detail-view', !!activeDetailId);
    message('information-message', ''); message('upload-message', '');
    if (activeDetailId) loadDetail(activeDetailId);
    else {
      detailRequest++; document.title = t('title'); loadVehicles();
      if (previousDetailId !== null) $('list-title').focus({ preventScroll: true });
    }
    window.scrollTo(0, 0);
  }
  $('language-toggle').addEventListener('click', () => {
    language = language === 'en' ? 'ar' : 'en'; savePreference('language', language); applyLanguage(); announce(t('languageChanged'));
  });
  $('theme-toggle').addEventListener('click', () => {
    const theme = root.dataset.theme === 'light' ? 'dark' : 'light'; root.dataset.theme = theme;
    savePreference('theme', theme); updateThemeButton(); announce(t(theme === 'light' ? 'lightEnabled' : 'darkEnabled'));
  });
  ['add-vehicle', 'empty-add'].forEach(id => $(id).addEventListener('click', openAdd));
  ['close-dialog', 'cancel-add'].forEach(id => $(id).addEventListener('click', () => $('add-dialog').close()));
  $('add-dialog').addEventListener('cancel', event => { if (addBusy) event.preventDefault(); });
  ['retry-connection', 'retry-list'].forEach(id => $(id).addEventListener('click', loadVehicles));
  $('vehicle-search').addEventListener('input', renderList);
  $('add-form').addEventListener('submit', async event => {
    event.preventDefault(); if (!storageReady || addBusy) return;
    const plate = $('new-plate').value.trim();
    const type = $('new-type').value.trim();
    if (!plate || plate.length > 64) { message('add-message', 'invalidPlate', 'error'); return; }
    if (!type || type.length > 120) { message('add-message', 'invalidDetails', 'error'); return; }
    addBusy = true; updateAddState(); message('add-message', '');
    try {
      const payload = await api('/api/vehicles/', { method: 'POST', body: JSON.stringify({ plate_number: plate, vehicle_type: type }) });
      $('add-dialog').close(); window.location.hash = `vehicle/${payload.vehicle.id}`;
    } catch (error) { message('add-message', errorKey(error), 'error'); }
    finally { addBusy = false; updateAddState(); }
  });
  Object.values(detailFields).forEach(id => $(id).addEventListener('input', () => { message('information-message', ''); updateDetailControls(); }));
  $('vehicle-information-form').addEventListener('submit', async event => {
    event.preventDefault(); if (!currentVehicle || informationBusy || uploadBusy || deleteBusy) return;
    const id = currentVehicle.id; const fields = detailValues();
    if (!fields.plate_number || fields.plate_number.length > 64) { message('information-message', 'invalidPlate', 'error'); return; }
    if (!fields.vehicle_type) { message('information-message', 'invalidDetails', 'error'); return; }
    informationBusy = true; updateDetailControls(); message('information-message', '');
    try {
      const payload = await api(`/api/vehicles/${id}/`, { method: 'PATCH', body: JSON.stringify(fields) });
      if (activeDetailId !== id) return;
      currentVehicle = payload.vehicle; renderDetail(true); message('information-message', 'saved', 'success');
      document.title = `${currentVehicle.plate_number} | ${t('title')}`;
    } catch (error) { if (activeDetailId === id) message('information-message', errorKey(error), 'error'); }
    finally { informationBusy = false; updateDetailControls(); }
  });
  $('add-photos').addEventListener('click', () => $('photo-input').click());
  $('add-files').addEventListener('click', () => $('file-input').click());
  async function upload(input) {
    const selected = [...input.files]; input.value = '';
    if (!selected.length || !currentVehicle || uploadBusy || informationBusy || deleteBusy) return;
    if (selected.some(file => file.size > 10 * 1024 * 1024)) { message('upload-message', 'fileTooLarge', 'error'); return; }
    const extensions = input.id === 'photo-input' ? ['jpg', 'jpeg', 'png', 'webp'] : ['pdf', 'txt', 'docx', 'xlsx'];
    if (selected.some(file => !extensions.includes(file.name.split('.').pop().toLowerCase()))) { message('upload-message', 'invalidFile', 'error'); return; }
    const id = currentVehicle.id; let completed = 0; let failure = '';
    uploadBusy = true; updateDetailControls();
    try {
      for (const file of selected) {
        if (activeDetailId !== id) break;
        message('upload-message', 'uploading', '', { current: completed + 1, total: selected.length });
        const body = new FormData(); body.append('file', file);
        await api(`/api/vehicles/${id}/attachments/`, { method: 'POST', body }); completed++;
      }
    } catch (error) { failure = errorKey(error); }
    finally {
      uploadBusy = false;
      if (activeDetailId === id) {
        await loadDetail(id, false);
        message('upload-message', failure ? 'partialUpload' : 'uploadComplete', failure ? 'error' : 'success', {
          count: completed, error: { key: failure }
        });
      }
      updateDetailControls();
    }
  }
  $('photo-input').addEventListener('change', () => upload($('photo-input')));
  $('file-input').addEventListener('change', () => upload($('file-input')));
  window.addEventListener('hashchange', route);
  applyLanguage(); route();
})();
