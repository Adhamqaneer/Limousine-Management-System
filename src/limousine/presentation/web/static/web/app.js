(() => {
  'use strict';

  const getElement = (id) => document.getElementById(id);
  const root = document.documentElement;
  const en = {};
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    en[el.dataset.i18n] = el.textContent;
  });
  document.querySelectorAll('[data-i18n-aria]').forEach((el) => {
    en[el.dataset.i18nAria] = el.getAttribute('aria-label');
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    en[el.dataset.i18nPlaceholder] = el.placeholder;
  });
  Object.assign(en, {
    renameNamed: 'Rename {name}',
    renameSaved: 'Attachment name updated.',
    invalidAttachmentName:
      'Enter a name without path/reserved characters, up to 180 characters including its extension.',
    renameConflict:
      'Someone changed this name. Close this window and open Rename again to review the current name.',
    deleteVehicle: 'Delete vehicle',
    confirmDeleteVehicle:
      'Move vehicle {plate} and its visible files to deleted items? Only the administrator can restore it.',
    vehicleDeleted: 'Vehicle moved to deleted items.',
    filters: 'Filters',
    doneFilters: 'Done',
    printResults: 'Print results',
    ownerFilterSummary: '{owner} · {shown} matching vehicles (of {total} total)',
    filterSummary: 'Showing {shown} of {total} vehicles',
    title: 'H SPACE | Vehicles',
    teamAccess: 'Team',
    switchArabic: 'Switch to Arabic',
    switchEnglish: 'Switch to English',
    lightMode: 'Switch to light mode',
    darkMode: 'Switch to dark mode',
    vehicleCount: '{count} vehicles',
    vehicleCountOne: '1 vehicle',
    added: 'Added {date}',
    attachments: '{count} attachments',
    openVehicle: 'Open vehicle',
    saveUnavailable: 'Saving is unavailable until the local database is connected.',
    saving: 'Saving…',
    saved: 'Changes saved.',
    unavailable: 'Vehicle storage is unavailable. Please try again.',
    requestFailed: 'Something went wrong. Please try again.',
    notFound: 'This vehicle could not be found.',
    invalidPlate: 'Use English digits and optional hyphens between digits, up to 64 characters.',
    invalidDetails: 'Check the allowed characters and length of each field.',
    invalidFile:
      'This file is unsupported, damaged, or exceeds the allowed image dimensions. Check the format and limits below.',
    fileTooLarge: 'Each file must be no larger than 10 MB.',
    download: 'Download {name}',
    viewPhoto: 'View photo: {name}',
    viewFile: 'View',
    cardPhoto: 'Card photo',
    changeCardPhoto: 'Change card photo',
    deleteAttachment: 'Delete',
    deleteNamed: 'Delete {name}',
    removeCardPhoto: 'Remove card photo',
    confirmDelete: 'Move "{name}" to deleted items? Only the administrator can restore it.',
    confirmRemoveCover:
      'Move the card photo for {plate} to deleted items? Only the administrator can restore it.',
    deleting: 'Deleting…',
    deleted: 'Attachment deleted.',
    coverDeleted: 'Card photo removed.',
    coverSaving: 'Saving card photo…',
    coverSaved: 'Card photo saved.',
    uploading: 'Uploading {current} of {total}…',
    uploadComplete: '{count} attachments added.',
    partialUpload: '{count} attachments added. {error}',
    pending: 'Checking the database connection…',
    emptyDisconnected: 'Connect the local database to save vehicles, photos and files.',
    languageChanged: 'Language changed to English.',
    lightEnabled: 'Light mode enabled.',
    darkEnabled: 'Dark mode enabled.',
  });
  en.navOffice = 'Office files';
  const ar = {
    navOffice: 'ملفات المكتب',
    renameAttachment: 'تغيير اسم المرفق',
    fileName: 'اسم الملف',
    renameHint: 'اكتب الاسم فقط. امتداد الملف ثابت ولا يتغيّر.',
    renameSave: 'حفظ الاسم',
    renameNamed: 'تغيير اسم {name}',
    renameSaved: 'تم تغيير اسم المرفق.',
    invalidAttachmentName:
      'اكتب اسمًا بدون رموز المسارات والرموز المحجوزة، حتى 180 خانة مع الامتداد.',
    renameConflict:
      'غيّر مستخدم آخر الاسم. أغلق هذا المربع وافتح التعديل من جديد لمراجعة الاسم الحالي.',
    downloadPhotos: 'تنزيل كل الصور (ZIP)',
    downloadFiles: 'تنزيل كل الملفات (ZIP)',
    ownerNameHint: 'اختار مالكًا موجودًا أو اكتب اسمًا جديدًا. أحرف عربية أو إنجليزية ومسافات فقط.',
    deleteVehicle: 'حذف السيارة',
    confirmDeleteVehicle:
      'نقل السيارة {plate} وملفاتها الظاهرة إلى المحذوفات؟ الاسترجاع للأدمن فقط.',
    vehicleDeleted: 'تم نقل السيارة إلى المحذوفات.',
    filters: 'الفلاتر',
    doneFilters: 'تم',
    printResults: 'طباعة النتائج',
    ownerFilterSummary: '{owner} · {shown} سيارة مطابقة (من أصل {total})',
    filterVehicles: 'فلترة السيارات',
    allOwners: 'كل المالكين',
    allModels: 'كل الموديلات',
    allTypes: 'كل الأنواع',
    clearFilters: 'مسح الفلاتر',
    filterSummary: 'عرض {shown} من أصل {total} سيارة',
    heroAccent: 'كل التفاصيل قدامك.',
    navDrivers: 'سجل الشوفيرين',
    navTrash: 'المحذوفات',
    navReports: 'طباعة البيانات',
    navVehicles: 'السيارات',
    title: 'H SPACE | السيارات',
    skip: 'انتقل إلى المحتوى',
    brandSub: 'إدارة السيارات',
    vehicles: 'سياراتك.',
    workspace: 'مساحة عملك',
    teamAccess: 'إدارة الفريق',
    vehicleCollection: 'مجموعة السيارات',
    footerTagline: 'لكل تفصيل مكانه.',
    listDescription: 'لكل تفصيل مكانه. ولكل سيارة مساحتها.',
    addVehicle: 'إضافة سيارة',
    databaseTitle: 'تخزين السيارات غير متاح حاليًا',
    databaseDescription: 'أعد المحاولة عند توفر اتصال قاعدة البيانات المحلية.',
    retry: 'إعادة المحاولة',
    search: 'البحث بالنمرة أو النوع',
    searchPlaceholder: 'ابحث بالنمرة أو النوع…',
    loading: 'جارٍ تحميل السيارات…',
    loadFailed: 'تعذّر تحميل السيارات',
    loadFailedDescription: 'تحقّق من الاتصال ثم أعد المحاولة.',
    emptyTitle: 'سياراتك رح تظهر هون',
    emptyDescription: 'أضف أول سيارة لتجمع بياناتها وصورها وملفاتها في مكان واحد.',
    noResults: 'لا توجد سيارات مطابقة',
    trySearch: 'جرّب بحثًا آخر أو امسح الفلاتر.',
    backToVehicles: 'العودة للسيارات',
    vehicleRecord: 'ملف السيارة',
    loadingDetails: 'جارٍ تحميل السيارة…',
    vehicleInformation: 'بيانات السيارة',
    ownerName: 'اسم المالك',
    ownerPhone: 'رقم تلفون المالك',
    driverPhone: 'رقم تلفون الشوفير',
    nameRule: 'أحرف عربية أو إنجليزية ومسافات فقط.',
    phoneRule: 'أرقام فقط.',
    digitsRule: 'أرقام إنجليزية فقط (0–9).',
    chassisRule: 'أحرف إنجليزية أو أرقام إنجليزية أو الاثنان معًا.',
    plateRule: 'أرقام إنجليزية؛ تُسمح الشرطة بين مجموعات الأرقام.',
    plateNumber: 'رقم المركبة',
    vehicleType: 'نوع المركبة',
    driverName: 'اسم الشوفير',
    chassisNumber: 'رقم الشصي',
    manufactureYear: 'موديل المركبة',
    signOut: 'تسجيل الخروج',
    saveChanges: 'حفظ التعديلات',
    photos: 'الصور',
    photoDescription: 'الصور الخاصة بهذه السيارة.',
    addPhotos: 'إضافة صور',
    noPhotos: 'لم تُضف صور بعد.',
    photoHint: 'JPG أو PNG أو WebP · حتى 10 ميجابايت و25 مليون بكسل للصورة',
    files: 'الملفات',
    fileDescription: 'المستندات الخاصة بهذه السيارة.',
    addFiles: 'إضافة ملفات',
    noFiles: 'لم تُضف ملفات بعد.',
    fileHint: 'PDF أو TXT أو DOCX أو XLSX · حتى 10 ميجابايت للملف',
    addDescription: 'أدخل نوع السيارة ونمرتها، ثم أكمل باقي البيانات من صفحتها.',
    close: 'إغلاق',
    plateExample: 'مثال: 12-34567',
    cancel: 'إلغاء',
    saveVehicle: 'إضافة السيارة',
    switchArabic: 'التبديل للعربية',
    switchEnglish: 'Switch to English',
    lightMode: 'تفعيل الوضع النهاري',
    darkMode: 'تفعيل الوضع الليلي',
    vehicleCount: '{count} سيارة',
    vehicleCountOne: 'سيارة واحدة',
    added: 'أُضيفت في {date}',
    attachments: '{count} مرفق',
    openVehicle: 'فتح السيارة',
    saveUnavailable: 'الحفظ غير متاح قبل اتصال قاعدة البيانات المحلية.',
    saving: 'جارٍ الحفظ…',
    saved: 'تم حفظ التعديلات.',
    unavailable: 'تخزين السيارات غير متاح حاليًا. أعد المحاولة.',
    requestFailed: 'حدث خطأ. أعد المحاولة.',
    notFound: 'لم نتمكّن من العثور على هذه السيارة.',
    invalidPlate: 'استخدم أرقامًا إنجليزية وشرطة بين الأرقام فقط، حتى 64 خانة.',
    invalidDetails: 'تحقّق من الأحرف والأرقام المسموحة وطول كل خانة.',
    invalidFile:
      'الملف غير مدعوم أو تالف أو أبعاد الصورة أكبر من المسموح. تحقّق من الصيغة والحدود المذكورة.',
    fileTooLarge: 'حجم كل ملف يجب ألا يتجاوز 10 ميجابايت.',
    download: 'تنزيل {name}',
    viewPhoto: 'عرض الصورة: {name}',
    uploading: 'جارٍ رفع {current} من {total}…',
    viewFile: 'عرض',
    cardPhoto: 'صورة البطاقة',
    changeCardPhoto: 'تغيير صورة البطاقة',
    deleteAttachment: 'حذف',
    deleteNamed: 'حذف {name}',
    removeCardPhoto: 'حذف صورة البطاقة',
    confirmDelete: 'نقل "{name}" إلى المحذوفات؟ الاسترجاع للأدمن فقط.',
    confirmRemoveCover: 'نقل صورة بطاقة السيارة {plate} إلى المحذوفات؟ الاسترجاع للأدمن فقط.',
    deleting: 'جارٍ الحذف…',
    deleted: 'تم حذف المرفق.',
    coverDeleted: 'تم حذف صورة البطاقة.',
    coverSaving: 'جارٍ حفظ صورة البطاقة…',
    coverSaved: 'تم حفظ صورة البطاقة.',
    uploadComplete: 'تمت إضافة {count} مرفق.',
    partialUpload: 'تمت إضافة {count} مرفق. {error}',
    pending: 'جارٍ فحص اتصال قاعدة البيانات…',
    emptyDisconnected: 'جهّز اتصال قاعدة البيانات المحلية لإضافة السيارات وحفظ صورها وملفاتها.',
    languageChanged: 'تم التبديل إلى العربية.',
    lightEnabled: 'تم تفعيل الوضع النهاري.',
    darkEnabled: 'تم تفعيل الوضع الليلي.',
  };
  let language = 'en';
  try {
    if (localStorage.getItem('limousine.language') === 'ar') language = 'ar';
  } catch (_) {}
  let vehicles = [];
  let currentVehicle = null;
  const vehicleDrafts = new Map();
  let storageReady = false;
  let listState = 'loading';
  let detailState = 'loading';
  let detailError = '';
  let addBusy = false;
  let informationBusy = false;
  let uploadBusy = false;
  let coverBusy = false;
  let deleteBusy = false;
  let renameBusy = false;
  let renameTarget = null;
  let activeDetailId = null;
  let listRequest = 0;
  let detailRequest = 0;
  const messages = new Map();
  const detailFields = {
    plate_number: 'detail-plate',
    owner_name: 'detail-owner',
    driver_name: 'detail-driver',
    vehicle_type: 'detail-type',
    manufacture_year: 'detail-year',
    chassis_number: 'detail-chassis',
    owner_phone: 'detail-owner-phone',
    driver_phone: 'detail-driver-phone',
  };
  function validateForm(formId, mapping, original = null) {
    Object.entries(mapping).forEach(([name, id]) => {
      const input = getElement(id);
      const value = input.value.trim();
      const key =
        original && value === (original[name] || '')
          ? ''
          : HSpaceVehicleValidation.error(name, value);
      input.setCustomValidity(key ? getText(key) : '');
      if (key) input.setAttribute('aria-invalid', 'true');
      else input.removeAttribute('aria-invalid');
    });
    return getElement(formId).reportValidity();
  }
  ['new-type', 'new-plate'].forEach((id) =>
    getElement(id).addEventListener('input', () => {
      getElement(id).setCustomValidity('');
      getElement(id).removeAttribute('aria-invalid');
    }),
  );
  function detailValues() {
    return Object.fromEntries(
      Object.entries(detailFields).map(([name, id]) => [name, getElement(id).value.trim()]),
    );
  }
  function getText(key, values = {}) {
    let result = (language === 'ar' ? ar[key] : en[key]) ?? en[key] ?? key;
    Object.entries(values).forEach(([name, value]) => {
      const text =
        value && typeof value === 'object' && value.key
          ? getText(value.key, value.values)
          : String(value);
      result = result.replaceAll(`{${name}}`, () => text);
    });
    return result;
  }
  function savePreference(key, value) {
    try {
      localStorage.setItem(`limousine.${key}`, value);
    } catch (_) {}
  }
  function announce(message) {
    getElement('announcement').textContent = message;
  }
  function show(id, visible) {
    getElement(id).hidden = !visible;
  }
  function renderMessage(id) {
    const { key, values, style } = messages.get(id);
    getElement(id).textContent = key ? getText(key, values) : '';
    getElement(id).className =
      `${id === 'upload-message' ? 'upload-message' : 'form-message'} ${style}`;
  }
  function message(id, key = '', style = '', values = {}) {
    messages.set(id, {
      key,
      values,
      style,
    });
    renderMessage(id);
  }
  function icon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('icon');
    svg.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', `#${name}`);
    svg.append(use);
    return svg;
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
    return new Intl.DateTimeFormat(language === 'ar' ? 'ar-JO' : 'en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(parsed);
  }
  function fileSize(value) {
    return value >= 1048576
      ? `${(value / 1048576).toFixed(1)} MB`
      : `${Math.max(1, Math.ceil(value / 1024))} KB`;
  }
  function errorKey(error) {
    const code = error.code || '';
    if (code === 'invalid_attachment_name') return 'invalidAttachmentName';
    if (code === 'attachment_name_conflict') return 'renameConflict';
    if (['storage_unavailable', 'database_unavailable'].includes(code)) return 'unavailable';
    if (['not_found', 'vehicle_not_found', 'attachment_not_found'].includes(code))
      return 'notFound';
    if (['invalid_plate', 'invalid_plate_number'].includes(code)) return 'invalidPlate';
    if (code === 'validation_error') return 'invalidDetails';
    if (['file_too_large', 'upload_too_large'].includes(code)) return 'fileTooLarge';
    if (
      ['invalid_file', 'unsupported_file', 'unsupported_file_type', 'invalid_image'].includes(code)
    )
      return 'invalidFile';
    return 'requestFailed';
  }
  async function api(url, options = {}) {
    const headers = new Headers(options.headers);
    if (options.body && !(options.body instanceof FormData))
      headers.set('Content-Type', 'application/json');
    if (options.method && !['GET', 'HEAD'].includes(options.method)) {
      const token = document.cookie
        .split('; ')
        .find((part) => part.startsWith('csrftoken='))
        ?.slice(10);
      if (token) headers.set('X-CSRFToken', decodeURIComponent(token));
    }
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'same-origin',
      cache: 'no-store',
    });
    if (response.status === 401) {
      window.location.assign('/login/');
      throw new Error('Sign in required');
    }
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
    getElement('theme-toggle').setAttribute('aria-label', getText(dark ? 'lightMode' : 'darkMode'));
    getElement('theme-toggle').title = getText(dark ? 'lightMode' : 'darkMode');
    document.querySelector('meta[name="theme-color"]').content = dark ? '#101113' : '#f5f3ef';
  }
  function applyLanguage() {
    root.lang = language;
    root.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.title =
      currentVehicle && activeDetailId
        ? `${currentVehicle.plate_number} | ${getText('title')}`
        : getText('title');
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      el.textContent = getText(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
      el.placeholder = getText(el.dataset.i18nPlaceholder);
    });
    document.querySelectorAll('[data-i18n-aria]').forEach((el) => {
      el.setAttribute('aria-label', getText(el.dataset.i18nAria));
    });
    getElement('language-label').textContent = language === 'ar' ? 'English' : 'العربية';
    getElement('language-label').lang = language === 'ar' ? 'en' : 'ar';
    getElement('language-toggle').setAttribute(
      'aria-label',
      getText(language === 'ar' ? 'switchEnglish' : 'switchArabic'),
    );
    updateThemeButton();
    renderFilters();
    renderList();
    renderDetail(false);
    updateAddState();
    messages.forEach((_, id) => renderMessage(id));
    window.dispatchEvent(new Event('hspace:language'));
  }
  const filterInputs = {
    owner_name: 'filter-owner',
    manufacture_year: 'filter-model',
    vehicle_type: 'filter-type',
  };
  const filterAllLabels = {
    owner_name: 'allOwners',
    manufacture_year: 'allModels',
    vehicle_type: 'allTypes',
  };
  function selectedFilters() {
    return Object.fromEntries(
      Object.entries(filterInputs).map(([field, id]) => [field, getElement(id).value]),
    );
  }
  let ownerNames = [];
  let ownerSuggestionsLoading = false;
  function renderOwnerSuggestions() {
    getElement('owner-suggestions').replaceChildren(
      ...ownerNames
        .filter((name) => !HSpaceVehicleValidation.error('owner_name', name))
        .map((name) => {
          const option = document.createElement('option');
          option.value = name;
          return option;
        }),
    );
  }
  async function loadOwnerSuggestions() {
    if (ownerSuggestionsLoading) return;
    ownerSuggestionsLoading = true;
    try {
      const payload = await api('/api/vehicles/');
      ownerNames = HSpaceVehicleFilters.options(payload.vehicles, 'owner_name', language);
      renderOwnerSuggestions();
    } catch (_) {
      /* Suggestions are optional; the detail form stays usable. */
    } finally {
      ownerSuggestionsLoading = false;
    }
  }
  function renderFilters() {
    Object.entries(filterInputs).forEach(([field, id]) => {
      const select = getElement(id),
        selected = select.value;
      const values = HSpaceVehicleFilters.options(vehicles, field, language);
      // Keep a selected value after a refresh even when it no longer matches any car.
      if (selected && !values.includes(selected)) values.push(selected);
      const all = document.createElement('option');
      all.value = '';
      all.textContent = getText(filterAllLabels[field]);
      const choices = values.map((value) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        option.dir = field === 'manufacture_year' ? 'ltr' : 'auto';
        return option;
      });
      select.replaceChildren(all, ...choices);
      select.value = selected;
    });
  }
  const cardCache = new Map();
  function plateLabel(plateNumber) {
    const plate = element('bdi');
    plate.dir = 'ltr';
    const query = HSpaceSearch.normalize(getElement('vehicle-search').value).replace(
      /[\s\-–—]/g,
      '',
    );
    const positions = [];
    let digits = '';
    for (let i = 0; i < plateNumber.length; i++) {
      const digit = HSpaceSearch.normalize(plateNumber[i]);
      if (/^[0-9]$/.test(digit)) {
        digits += digit;
        positions.push(i);
      }
    }
    const match = /^[0-9]+$/.test(query) ? digits.indexOf(query) : -1;
    if (match >= 0) {
      const start = positions[match],
        end = positions[match + query.length - 1] + 1;
      plate.append(
        document.createTextNode(plateNumber.slice(0, start)),
        element('mark', '', plateNumber.slice(start, end)),
        document.createTextNode(plateNumber.slice(end)),
      );
    } else plate.textContent = plateNumber;
    return plate;
  }
  let cardFocus = null;
  function renderList() {
    const focused = document.activeElement;
    const focusedCard = focused?.closest?.('.vehicle-card');
    if (focusedCard)
      cardFocus = {
        id: focusedCard.dataset.vehicleId,
        action: focused.dataset.action || 'open',
        index: Array.from(getElement('vehicle-grid').children).indexOf(focusedCard),
      };
    show('list-loading', listState === 'loading');
    show('list-error', listState === 'error');
    show('connection-notice', listState === 'unavailable');
    const selected = selectedFilters();
    const filtered = HSpaceSearch.search(
      HSpaceVehicleFilters.apply(vehicles, selected),
      getElement('vehicle-search').value,
    );
    Object.values(filterInputs).forEach((id) => {
      getElement(id).disabled = listState !== 'ready';
    });
    getElement('clear-filters').disabled = !Object.values(selected).some(Boolean);
    getElement('filter-summary').textContent =
      listState === 'ready'
        ? getText(selected.owner_name ? 'ownerFilterSummary' : 'filterSummary', {
            owner: selected.owner_name,
            shown: filtered.length,
            total: vehicles.length,
          })
        : '';
    const active = Object.values(selected).filter(Boolean).length;
    getElement('filter-active-count').hidden = !active;
    getElement('filter-active-count').textContent = String(active);
    getElement('print-results').disabled = listState !== 'ready' || !filtered.length;
    const empty = !vehicles.length && ['ready', 'unavailable'].includes(listState);
    show('empty-fleet', empty);
    getElement('empty-description').textContent = getText(
      listState === 'unavailable' ? 'emptyDisconnected' : 'emptyDescription',
    );
    show('no-results', listState === 'ready' && vehicles.length > 0 && !filtered.length);
    getElement('vehicle-count').textContent =
      listState === 'ready'
        ? getText(filtered.length === 1 ? 'vehicleCountOne' : 'vehicleCount', {
            count: filtered.length,
          })
        : '';
    const cards =
      listState === 'ready'
        ? filtered.map((vehicle) => {
            const cached = cardCache.get(vehicle.id);
            if (cached && cached.vehicle === vehicle && cached.language === language) {
              cached.card.querySelector('h2').replaceChildren(plateLabel(vehicle.plate_number));
              cached.card.querySelectorAll('button').forEach((button) => {
                button.disabled = coverBusy;
              });
              return cached.card;
            }
            const card = element('article', 'vehicle-card');
            card.dataset.vehicleId = String(vehicle.id);
            const link = element('a', 'vehicle-card-link');
            link.href = `#vehicle/${vehicle.id}`;
            link.setAttribute(
              'aria-label',
              `${getText('openVehicle')}: ${vehicle.vehicle_type} ${vehicle.plate_number}`,
            );
            const image = element('div', 'vehicle-image');
            if (vehicle.cover_url) {
              const img = document.createElement('img');
              img.src = vehicle.cover_url;
              img.alt = '';
              img.loading = 'lazy';
              image.append(img);
            } else image.append(icon('car'));
            const body = element('div', 'vehicle-body');
            const title = element('h2');
            const plate = plateLabel(vehicle.plate_number);
            title.append(plate);
            const type = element('p', 'vehicle-kind');
            type.append(element('bdi', '', vehicle.vehicle_type));
            body.append(
              type,
              title,
              element(
                'p',
                'vehicle-meta',
                getText('added', {
                  date: date(vehicle.created_at),
                }),
              ),
            );
            const footer = element('div', 'vehicle-card-footer');
            const open = element('span', 'open-label', getText('openVehicle'));
            open.append(icon('arrow'));
            footer.append(
              element(
                'span',
                '',
                getText('attachments', {
                  count: vehicle.attachment_count,
                }),
              ),
              open,
            );
            body.append(footer);
            link.append(image, body);
            const photoLabel =
              getText(vehicle.cover_url ? 'changeCardPhoto' : 'cardPhoto') +
              ': ' +
              vehicle.plate_number;
            const button = element('button', 'icon-button card-photo-button');
            button.title = photoLabel;
            button.dataset.action = 'photo';
            button.type = 'button';
            button.disabled = coverBusy;
            button.prepend(icon('photo'));
            button.setAttribute('aria-label', photoLabel);
            const input = document.createElement('input');
            input.type = 'file';
            input.hidden = true;
            input.accept = 'image/jpeg,image/png,image/webp';
            button.addEventListener('click', () => input.click());
            input.addEventListener('change', () => {
              const file = input.files[0];
              input.value = '';
              saveCardPhoto(vehicle.id, file);
            });
            const actions = element('div', 'vehicle-card-actions');
            actions.append(button);
            card.append(link, actions, input);
            const removeVehicle = element('button', 'icon-button danger remove-vehicle-button');
            removeVehicle.dataset.action = 'delete';
            removeVehicle.append(icon('trash'));
            removeVehicle.title = getText('deleteVehicle') + ': ' + vehicle.plate_number;
            removeVehicle.type = 'button';
            removeVehicle.disabled = coverBusy;
            removeVehicle.setAttribute(
              'aria-label',
              getText('deleteVehicle') + ': ' + vehicle.plate_number,
            );
            removeVehicle.addEventListener('click', async () => {
              if (
                coverBusy ||
                !window.confirm(
                  getText('confirmDeleteVehicle', {
                    plate: vehicle.plate_number,
                  }),
                )
              )
                return;
              coverBusy = true;
              renderList();
              try {
                await api('/api/vehicles/' + vehicle.id + '/', {
                  method: 'DELETE',
                });
                vehicles = vehicles.filter((item) => item.id !== vehicle.id);
                renderFilters();
                message('cover-message', 'vehicleDeleted', 'success');
              } catch (error) {
                message('cover-message', errorKey(error), 'error');
              } finally {
                coverBusy = false;
                renderList();
              }
            });
            actions.append(removeVehicle);
            cardCache.set(vehicle.id, {
              vehicle,
              language,
              card,
            });
            return card;
          })
        : [];
    document.dispatchEvent(new Event('hspace:cards-changed'));
    const retained = new Set(vehicles.map((vehicle) => vehicle.id));
    for (const id of cardCache.keys()) if (!retained.has(id)) cardCache.delete(id);
    if (
      cards.length !== getElement('vehicle-grid').children.length ||
      cards.some((card, index) => card !== getElement('vehicle-grid').children[index])
    )
      getElement('vehicle-grid').replaceChildren(...cards);
    if (cardFocus && !coverBusy && listState === 'ready') {
      // Do not steal focus if the user moved to search, navigation or another view while waiting.
      if (!activeDetailId && (focusedCard || !focused || focused === document.body)) {
        const card =
          cards.find((item) => item.dataset.vehicleId === cardFocus.id) ||
          cards[Math.min(cardFocus.index || 0, cards.length - 1)];
        const target =
          card?.querySelector('[data-action="' + cardFocus.action + '"]') ||
          card?.querySelector('a') ||
          getElement('vehicle-search');
        target.focus({
          preventScroll: true,
        });
      }
      cardFocus = null;
    }
  }
  async function loadVehicles() {
    const request = ++listRequest;
    listState = 'loading';
    storageReady = false;
    renderList();
    updateAddState();
    try {
      const payload = await api('/api/vehicles/');
      if (request !== listRequest) return;
      vehicles = payload.vehicles;
      listState = 'ready';
      storageReady = true;
      ownerNames = HSpaceVehicleFilters.options(vehicles, 'owner_name', language);
      renderOwnerSuggestions();
    } catch (error) {
      if (request !== listRequest) return;
      vehicles = [];
      listState = error.status === 503 ? 'unavailable' : 'error';
    }
    renderFilters();
    renderList();
    updateAddState();
  }
  async function saveCardPhoto(id, file) {
    if (!file || coverBusy) return;
    if (file.size > 10 * 1024 * 1024) {
      message('cover-message', 'fileTooLarge', 'error');
      return;
    }
    if (!['jpg', 'jpeg', 'png', 'webp'].includes(file.name.split('.').pop().toLowerCase())) {
      message('cover-message', 'invalidFile', 'error');
      return;
    }
    cardFocus = {
      id: String(id),
      action: 'photo',
    };
    coverBusy = true;
    renderList();
    message('cover-message', 'coverSaving');
    try {
      const body = new FormData();
      body.append('file', file);
      const payload = await api(`/api/vehicles/${id}/cover/`, {
        method: 'POST',
        body,
      });
      vehicles = vehicles.map((vehicle) => (vehicle.id === id ? payload.vehicle : vehicle));
      message('cover-message', 'coverSaved', 'success');
    } catch (error) {
      message('cover-message', errorKey(error), 'error');
    } finally {
      coverBusy = false;
      renderList();
    }
  }
  function updateAddState() {
    getElement('save-vehicle').disabled = !storageReady || addBusy;
    getElement('new-plate').disabled = addBusy;
    getElement('new-type').disabled = addBusy;
    getElement('close-dialog').disabled = addBusy;
    getElement('cancel-add').disabled = addBusy;
    getElement('save-vehicle').textContent = getText(addBusy ? 'saving' : 'saveVehicle');
    getElement('save-vehicle').setAttribute('aria-busy', String(addBusy));
    if (!storageReady) {
      message('add-message', listState === 'loading' ? 'pending' : 'saveUnavailable');
      getElement('add-message').dataset.connectionNotice = 'true';
    } else if (
      getElement('add-message').dataset.connectionNotice === 'true' ||
      !getElement('add-dialog').open
    ) {
      message('add-message', '');
      getElement('add-message').dataset.connectionNotice = 'false';
    }
  }
  function openAdd() {
    getElement('add-form').reset();
    message('add-message', '');
    updateAddState();
    getElement('add-dialog').showModal();
    getElement('new-type').focus();
  }
  function renderDetail(resetInput = false) {
    show('detail-loading', detailState === 'loading');
    show('detail-error', detailState === 'error');
    show('detail-content', detailState === 'ready' && !!currentVehicle);
    getElement('detail-error-text').textContent = detailError ? getText(detailError) : '';
    if (currentVehicle) {
      const plate = element('bdi', '', currentVehicle.plate_number);
      plate.dir = 'ltr';
      getElement('detail-title').replaceChildren(
        element('bdi', '', currentVehicle.vehicle_type),
        document.createTextNode(' · '),
        plate,
      );
    } else getElement('detail-title').textContent = getText('vehicleRecord');
    getElement('detail-created').textContent = currentVehicle
      ? getText('added', {
          date: date(currentVehicle.created_at),
        })
      : '';
    if (!currentVehicle) return;
    if (resetInput)
      Object.entries(detailFields).forEach(([name, id]) => {
        getElement(id).value = currentVehicle[name] || '';
        getElement(id).setCustomValidity('');
        getElement(id).removeAttribute('aria-invalid');
      });
    const photos = currentVehicle.attachments.filter((file) => file.kind === 'image');
    const files = currentVehicle.attachments.filter((file) => file.kind !== 'image');
    show('photos-empty', !photos.length);
    show('files-empty', !files.length);
    function download(file) {
      const link = element('a', 'download-link');
      link.href = file.download_url;
      link.setAttribute(
        'aria-label',
        getText('download', {
          name: file.name,
        }),
      );
      link.title = getText('download', {
        name: file.name,
      });
      link.append(icon('download'));
      return link;
    }
    function remove(file) {
      const button = element(
        'button',
        'button ghost small danger attachment-delete',
        getText('deleteAttachment'),
      );
      button.type = 'button';
      button.disabled = deleteBusy || uploadBusy || informationBusy;
      button.setAttribute(
        'aria-label',
        getText('deleteNamed', {
          name: file.name,
        }),
      );
      button.addEventListener('click', () => deleteAttachment(currentVehicle.id, file));
      return button;
    }
    function preview(file, photo = false) {
      const link = element('a', 'button secondary small', getText('viewFile'));
      link.href = file.preview_url;
      link.target = '_blank';
      link.rel = 'noopener';
      link.setAttribute(
        'aria-label',
        photo
          ? getText('viewPhoto', {
              name: file.name,
            })
          : `${getText('viewFile')}: ${file.name}`,
      );
      return link;
    }
    function fileName(file) {
      const line = element('div', 'attachment-name');
      const name = element('bdi', 'filename', file.name);
      name.title = file.name;
      const edit = element('button', 'icon-button attachment-rename');
      edit.type = 'button';
      edit.dataset.attachmentId = String(file.id);
      edit.title = getText('renameNamed', {
        name: file.name,
      });
      edit.setAttribute('aria-label', edit.title);
      edit.append(icon('pencil'));
      edit.addEventListener('click', () => openRename(file));
      line.append(name, edit);
      return line;
    }
    getElement('photo-grid').replaceChildren(
      ...photos.map((file) => {
        const row = element('div', 'file-row photo-row');
        const link = element('a', 'photo-link');
        link.href = file.preview_url;
        link.target = '_blank';
        link.rel = 'noopener';
        link.setAttribute(
          'aria-label',
          getText('viewPhoto', {
            name: file.name,
          }),
        );
        const img = document.createElement('img');
        img.src = file.preview_url;
        img.alt = '';
        img.loading = 'lazy';
        img.width = 64;
        img.height = 48;
        link.append(img);
        const info = element('div', 'file-info');
        info.append(
          fileName(file),
          element('span', 'file-meta', `${fileSize(file.size)} · ${date(file.uploaded_at)}`),
        );
        const actions = element('div', 'file-actions');
        actions.append(preview(file, true), download(file), remove(file));
        row.append(link, info, actions);
        return row;
      }),
    );
    getElement('file-list').replaceChildren(
      ...files.map((file) => {
        const row = element('div', 'file-row');
        const info = element('div', 'file-info');
        info.append(
          fileName(file),
          element('span', 'file-meta', `${fileSize(file.size)} · ${date(file.uploaded_at)}`),
        );
        const actions = element('div', 'file-actions');
        actions.append(preview(file), download(file), remove(file));
        row.append(icon('file'), info, actions);
        return row;
      }),
    );
    updateDetailControls();
  }
  function updateDetailControls() {
    const busy = informationBusy || uploadBusy || deleteBusy || renameBusy;
    for (const [section, kind] of [
      ['photos', 'image'],
      ['files', 'file'],
    ]) {
      const link = getElement('download-' + section);
      const available =
        !busy &&
        detailState === 'ready' &&
        currentVehicle?.attachments.some((file) => file.kind === kind);
      link.setAttribute('aria-disabled', String(!available));
      link.tabIndex = available ? 0 : -1;
      if (available)
        link.href = `/api/vehicles/${currentVehicle.id}/attachments/archive/${section}/`;
      else link.removeAttribute('href');
    }
    document.querySelectorAll('.attachment-delete').forEach((button) => {
      button.disabled = busy;
    });
    document.querySelectorAll('.attachment-rename').forEach((button) => {
      button.disabled = busy;
    });
    Object.values(detailFields).forEach((id) => {
      getElement(id).disabled = busy;
    });
    const unchanged =
      currentVehicle &&
      Object.entries(detailValues()).every(
        ([name, value]) => value === (currentVehicle[name] || ''),
      );
    getElement('save-information').disabled = busy || !currentVehicle || unchanged;
    getElement('save-information').textContent = getText(
      informationBusy ? 'saving' : 'saveChanges',
    );
    getElement('save-information').setAttribute('aria-busy', String(informationBusy));
    getElement('add-photos').disabled = busy;
    getElement('add-files').disabled = busy;
  }
  async function deleteAttachment(id, file) {
    if (
      deleteBusy ||
      uploadBusy ||
      informationBusy ||
      renameBusy ||
      !window.confirm(
        getText('confirmDelete', {
          name: file.name,
        }),
      )
    )
      return;
    deleteBusy = true;
    updateDetailControls();
    message('upload-message', 'deleting');
    try {
      await api(`/api/vehicles/${id}/attachments/${file.id}/`, {
        method: 'DELETE',
      });
      if (activeDetailId !== id || !currentVehicle) return;
      currentVehicle = {
        ...currentVehicle,
        attachments: currentVehicle.attachments.filter((item) => item.id !== file.id),
        attachment_count: currentVehicle.attachments.filter((item) => item.id !== file.id).length,
      };
      renderDetail();
      message('upload-message', 'deleted', 'success');
      getElement('upload-message').focus({
        preventScroll: true,
      });
    } catch (error) {
      if (activeDetailId === id) message('upload-message', errorKey(error), 'error');
    } finally {
      deleteBusy = false;
      updateDetailControls();
    }
  }
  async function loadDetail(id, resetInput = true) {
    const request = ++detailRequest;
    if (resetInput) {
      detailState = 'loading';
      detailError = '';
      currentVehicle = null;
      renderDetail();
    }
    try {
      const payload = await api(`/api/vehicles/${id}/`);
      if (request !== detailRequest || id !== activeDetailId) return;
      currentVehicle = payload.vehicle;
      detailState = 'ready';
      renderDetail(resetInput);
      if (resetInput && vehicleDrafts.has(id)) {
        const previous = vehicleDrafts.get(id);
        const merged = HSpaceDraft.merge(previous.original, previous.values, currentVehicle);
        Object.entries(detailFields).forEach(([key, inputId]) => {
          getElement(inputId).value = merged[key];
        });
        vehicleDrafts.delete(id); // The visible form now owns this draft until navigation.
        updateDetailControls();
      }
      if (resetInput)
        document.dispatchEvent(
          new CustomEvent('hspace:detail-ready', {
            detail: {
              vehicle: currentVehicle,
            },
          }),
        );
      document.title = `${currentVehicle.plate_number} | ${getText('title')}`;
      if (resetInput)
        getElement('detail-title').focus({
          preventScroll: true,
        });
    } catch (error) {
      if (request !== detailRequest || id !== activeDetailId) return;
      detailError = errorKey(error);
      detailState = 'error';
      renderDetail();
      if (resetInput)
        getElement('detail-title').focus({
          preventScroll: true,
        });
    }
  }
  let listScroll = 0;
  function route() {
    getElement('rename-dialog').close();
    renameTarget = null;
    if (currentVehicle && activeDetailId) {
      const values = Object.fromEntries(
        Object.entries(detailFields).map(([key, id]) => [key, getElement(id).value]),
      );
      if (
        Object.entries(values).some(([key, value]) => value.trim() !== (currentVehicle[key] || ''))
      )
        vehicleDrafts.set(activeDetailId, {
          original: currentVehicle,
          values,
        });
      else vehicleDrafts.delete(activeDetailId);
    }
    const previousDetailId = activeDetailId;
    const match = window.location.hash.match(/^#vehicle\/(\d+)$/);
    if (!previousDetailId && match) listScroll = window.scrollY;
    activeDetailId = match ? Number(match[1]) : null;
    show('list-view', !activeDetailId);
    show('detail-view', !!activeDetailId);
    message('information-message', '');
    message('upload-message', '');
    if (activeDetailId) {
      loadDetail(activeDetailId);
      loadOwnerSuggestions();
    } else {
      detailRequest++;
      document.title = getText('title');
      loadVehicles().then(() => {
        if (!activeDetailId && previousDetailId) window.scrollTo(0, listScroll);
      });
      if (previousDetailId !== null)
        getElement('vehicle-search').focus({
          preventScroll: true,
        });
    }
    if (activeDetailId || !previousDetailId) window.scrollTo(0, 0);
  }
  getElement('language-toggle').addEventListener('click', () => {
    language = language === 'en' ? 'ar' : 'en';
    savePreference('language', language);
    applyLanguage();
    announce(getText('languageChanged'));
  });
  getElement('theme-toggle').addEventListener('click', () => {
    const theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    root.dataset.theme = theme;
    savePreference('theme', theme);
    updateThemeButton();
    announce(getText(theme === 'light' ? 'lightEnabled' : 'darkEnabled'));
  });
  ['add-vehicle', 'empty-add'].forEach((id) => getElement(id).addEventListener('click', openAdd));
  ['close-dialog', 'cancel-add'].forEach((id) =>
    getElement(id).addEventListener('click', () => getElement('add-dialog').close()),
  );
  getElement('add-dialog').addEventListener('cancel', (event) => {
    if (addBusy) event.preventDefault();
  });
  ['retry-connection', 'retry-list'].forEach((id) =>
    getElement(id).addEventListener('click', loadVehicles),
  );
  let searchFrame = null;
  getElement('vehicle-search').addEventListener('input', () => {
    if (searchFrame !== null) cancelAnimationFrame(searchFrame);
    searchFrame = requestAnimationFrame(() => {
      searchFrame = null;
      renderList();
    });
  });
  getElement('close-filters').addEventListener('click', () => {
    getElement('filter-popover').open = false;
    getElement('filter-popover').querySelector('summary').focus();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && getElement('filter-popover').open) {
      getElement('filter-popover').open = false;
      getElement('filter-popover').querySelector('summary').focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (!getElement('filter-popover').contains(event.target))
      getElement('filter-popover').open = false;
  });
  getElement('print-results').addEventListener('click', () => {
    if (!getElement('print-results').disabled)
      location.assign(
        '/reports/vehicles/' +
          HSpaceVehicleFilters.reportHash(selectedFilters(), getElement('vehicle-search').value),
      );
  });
  Object.values(filterInputs).forEach((id) =>
    getElement(id).addEventListener('change', renderList),
  );
  getElement('clear-filters').addEventListener('click', () => {
    Object.values(filterInputs).forEach((id) => {
      getElement(id).value = '';
    });
    renderList();
  });
  getElement('add-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!storageReady || addBusy) return;
    const plate = getElement('new-plate').value.trim();
    const type = getElement('new-type').value.trim();
    if (
      !validateForm('add-form', {
        plate_number: 'new-plate',
        vehicle_type: 'new-type',
      })
    )
      return;
    addBusy = true;
    updateAddState();
    message('add-message', '');
    try {
      const payload = await api('/api/vehicles/', {
        method: 'POST',
        body: JSON.stringify({
          plate_number: plate,
          vehicle_type: type,
        }),
      });
      getElement('add-dialog').close();
      window.location.hash = `vehicle/${payload.vehicle.id}`;
    } catch (error) {
      message('add-message', errorKey(error), 'error');
    } finally {
      addBusy = false;
      updateAddState();
    }
  });
  Object.values(detailFields).forEach((id) =>
    getElement(id).addEventListener('input', () => {
      getElement(id).setCustomValidity('');
      getElement(id).removeAttribute('aria-invalid');
      message('information-message', '');
      updateDetailControls();
    }),
  );
  getElement('vehicle-information-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!currentVehicle || informationBusy || uploadBusy || deleteBusy || renameBusy) return;
    const id = currentVehicle.id;
    if (!validateForm('vehicle-information-form', detailFields, currentVehicle)) return;
    const fields = Object.fromEntries(
      Object.entries(detailValues()).filter(
        ([name, value]) => value !== (currentVehicle[name] || ''),
      ),
    );
    if (!Object.keys(fields).length) return;
    informationBusy = true;
    updateDetailControls();
    message('information-message', '');
    try {
      const payload = await api(`/api/vehicles/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(fields),
      });
      vehicleDrafts.delete(id);
      if (activeDetailId !== id) return;
      currentVehicle = payload.vehicle;
      renderDetail(true);
      loadOwnerSuggestions();
      message('information-message', 'saved', 'success');
      document.title = `${currentVehicle.plate_number} | ${getText('title')}`;
    } catch (error) {
      if (activeDetailId === id) message('information-message', errorKey(error), 'error');
    } finally {
      informationBusy = false;
      updateDetailControls();
    }
  });
  function focusRename(id) {
    Array.from(document.querySelectorAll('.attachment-rename'))
      .find((button) => button.dataset.attachmentId === String(id))
      ?.focus({
        preventScroll: true,
      });
  }
  function openRename(file, assignmentId = null) {
    if (!currentVehicle || informationBusy || uploadBusy || deleteBusy || renameBusy) return;
    const dot = file.name.lastIndexOf('.'),
      extension = dot > 0 ? file.name.slice(dot) : '';
    renameTarget = {
      vehicleId: currentVehicle.id,
      file,
      assignmentId,
    };
    getElement('rename-current').textContent = file.name;
    getElement('rename-extension').textContent = extension;
    getElement('rename-name').value = extension ? file.name.slice(0, -extension.length) : file.name;
    getElement('rename-name').maxLength = 180 - extension.length;
    getElement('rename-name').removeAttribute('aria-invalid');
    message('rename-message', '');
    getElement('rename-dialog').showModal();
    getElement('rename-name').focus();
  }
  getElement('cancel-rename').addEventListener('click', () => {
    const id = renameTarget?.file.id;
    getElement('rename-dialog').close();
    renameTarget = null;
    if (id) focusRename(id);
  });
  getElement('rename-dialog').addEventListener('cancel', (event) => {
    if (renameBusy) event.preventDefault();
  });
  getElement('rename-dialog').addEventListener('close', () => {
    if (!getElement('rename-dialog').open && renameTarget && !renameBusy) {
      focusRename(renameTarget.file.id);
      renameTarget = null;
    }
  });
  getElement('rename-name').addEventListener('input', () => {
    getElement('rename-name').removeAttribute('aria-invalid');
    message('rename-message', '');
  });
  getElement('rename-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!renameTarget || renameBusy) return;
    const target = renameTarget,
      name = getElement('rename-name').value.trim();
    if (!name) {
      message('rename-message', 'invalidAttachmentName', 'error');
      getElement('rename-name').setAttribute('aria-invalid', 'true');
      getElement('rename-name').focus();
      return;
    }
    renameBusy = true;
    let saved = false;
    updateDetailControls();
    getElement('rename-name').disabled = true;
    getElement('cancel-rename').disabled = true;
    getElement('save-rename').disabled = true;
    getElement('save-rename').setAttribute('aria-busy', 'true');
    message('rename-message', 'saving');
    try {
      const prefix =
        `/api/vehicles/${target.vehicleId}` +
        (target.assignmentId ? `/drivers/${target.assignmentId}` : '');
      const result = await api(`${prefix}/attachments/${target.file.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          name,
          expected_name: target.file.name,
        }),
      });
      if (activeDetailId === target.vehicleId && currentVehicle) {
        if (target.assignmentId)
          document.dispatchEvent(
            new CustomEvent('hspace:driver-file-renamed', {
              detail: {
                assignmentId: target.assignmentId,
                attachment: result.attachment,
              },
            }),
          );
        else {
          currentVehicle = {
            ...currentVehicle,
            attachments: currentVehicle.attachments.map((file) =>
              file.id === target.file.id ? result.attachment : file,
            ),
          };
          renderDetail(false);
        }
        message('upload-message', 'renameSaved', 'success');
        saved = true;
      }
    } catch (error) {
      if (activeDetailId === target.vehicleId && getElement('rename-dialog').open) {
        if (error.code === 'attachment_name_conflict') {
          if (target.assignmentId)
            document.dispatchEvent(
              new CustomEvent('hspace:driver-file-renamed', {
                detail: {
                  assignmentId: target.assignmentId,
                },
              }),
            );
          else {
            try {
              const result = await api(`/api/vehicles/${target.vehicleId}/`);
              if (activeDetailId === target.vehicleId && currentVehicle) {
                currentVehicle = {
                  ...currentVehicle,
                  attachments: result.vehicle.attachments,
                  attachment_count: result.vehicle.attachment_count,
                };
                renderDetail(false);
              }
            } catch (_) {
              /* Keep the entered name available if refreshing fails. */
            }
          }
        }
        message('rename-message', errorKey(error), 'error');
        getElement('rename-name').setAttribute('aria-invalid', 'true');
      }
    } finally {
      renameBusy = false;
      getElement('rename-name').disabled = false;
      getElement('cancel-rename').disabled = false;
      getElement('save-rename').disabled = false;
      getElement('save-rename').setAttribute('aria-busy', 'false');
      updateDetailControls();
    }
    if (saved) {
      getElement('rename-dialog').close();
      renameTarget = null;
      focusRename(target.file.id);
    } else if (getElement('rename-dialog').open) getElement('rename-name').focus();
  });
  document.addEventListener('hspace:rename-driver-file', (event) => {
    if (Number(event.detail.vehicleId) === activeDetailId)
      openRename(event.detail.file, event.detail.assignmentId);
  });
  getElement('add-photos').addEventListener('click', () => getElement('photo-input').click());
  getElement('add-files').addEventListener('click', () => getElement('file-input').click());
  async function upload(input) {
    const selected = [...input.files];
    input.value = '';
    if (
      !selected.length ||
      !currentVehicle ||
      uploadBusy ||
      informationBusy ||
      deleteBusy ||
      renameBusy
    )
      return;
    if (selected.some((file) => file.size > 10 * 1024 * 1024)) {
      message('upload-message', 'fileTooLarge', 'error');
      return;
    }
    const extensions =
      input.id === 'photo-input' ? ['jpg', 'jpeg', 'png', 'webp'] : ['pdf', 'txt', 'docx', 'xlsx'];
    if (selected.some((file) => !extensions.includes(file.name.split('.').pop().toLowerCase()))) {
      message('upload-message', 'invalidFile', 'error');
      return;
    }
    const id = currentVehicle.id;
    let completed = 0;
    let failure = '';
    uploadBusy = true;
    updateDetailControls();
    try {
      for (const file of selected) {
        if (activeDetailId !== id) break;
        message('upload-message', 'uploading', '', {
          current: completed + 1,
          total: selected.length,
        });
        const body = new FormData();
        body.append('file', file);
        await api(`/api/vehicles/${id}/attachments/`, {
          method: 'POST',
          body,
        });
        completed++;
      }
    } catch (error) {
      failure = errorKey(error);
    } finally {
      uploadBusy = false;
      if (activeDetailId === id) {
        await loadDetail(id, false);
        message(
          'upload-message',
          failure ? 'partialUpload' : 'uploadComplete',
          failure ? 'error' : 'success',
          {
            count: completed,
            error: {
              key: failure,
            },
          },
        );
      }
      updateDetailControls();
    }
  }
  getElement('photo-input').addEventListener('change', () => upload(getElement('photo-input')));
  getElement('file-input').addEventListener('change', () => upload(getElement('file-input')));
  document.addEventListener('hspace:driver-updated', (event) => {
    if (currentVehicle && currentVehicle.id === event.detail.vehicle.id) {
      const draft = Object.fromEntries(
        Object.entries(detailFields).map(([key, id]) => [key, getElement(id).value]),
      );
      const merged = HSpaceDraft.merge(currentVehicle, draft, event.detail.vehicle);
      currentVehicle = event.detail.vehicle;
      Object.entries(detailFields).forEach(([key, id]) => {
        getElement(id).value = merged[key];
      });
      renderDetail(false);
    }
  });
  window.addEventListener('beforeunload', (event) => {
    if (
      vehicleDrafts.size ||
      (activeDetailId &&
        currentVehicle &&
        Object.entries(detailValues()).some(
          ([key, value]) => value !== (currentVehicle[key] || ''),
        ))
    ) {
      event.preventDefault();
      event.returnValue = '';
    }
  });
  window.addEventListener('hashchange', route);
  applyLanguage();
  route();
})();
