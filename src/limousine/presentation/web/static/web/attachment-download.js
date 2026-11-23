(() => {
  const root = document.documentElement,
    get = (id) => document.getElementById(id);
  const copy = {
    en: {
      title: 'Download attachments',
      description: 'Choose what you need and download the original files in one ZIP.',
      skip: 'Skip to content',
      types: 'Document types',
      download: 'Download ZIP',
      back: 'Back to vehicles',
      scope: 'Vehicles: ',
      availability: 'Availability by vehicle',
      plate: 'Vehicle number',
      present: 'Available',
      absent: 'Missing',
      checking: 'Checking attachments…',
      checkFailed: 'Could not check attachments. Use Refresh status to try again.',
      refresh: 'Refresh status',
      loading: 'Loading…',
      preparing: 'Preparing your download…',
      done: 'Download prepared. Files: ',
      missing: 'Missing documents: ',
      missingHint: 'See _missing-documents.txt inside the ZIP.',
      failed: 'Could not download. Refresh the page and try again.',
      empty: 'No matching attachments to download.',
      invalid: 'Invalid filters. Return to Vehicles and choose Download attachments again.',
      vehicle_license: 'Vehicle license',
      direction_card: 'Direction card',
      customs_declaration: 'Customs declaration',
      other: 'Other',
      navVehicles: 'Vehicles',
      navReports: 'Print data',
      navDrivers: 'Driver history',
      navOffice: 'Office files',
      navTrash: 'Deleted items',
      brandSub: 'Vehicle management',
      signOut: 'Sign out',
    },
    ar: {
      title: 'تنزيل المرفقات',
      description: 'اختار اللي بدك إياه ونزّل الملفات الأصلية بملف ZIP واحد.',
      skip: 'انتقل إلى المحتوى',
      types: 'أنواع المرفقات',
      download: 'تنزيل ZIP',
      back: 'العودة للسيارات',
      scope: 'عدد السيارات: ',
      availability: 'حالة المرفقات لكل سيارة',
      plate: 'رقم السيارة',
      present: 'موجود',
      absent: 'غير موجود',
      checking: 'جارٍ فحص المرفقات…',
      checkFailed: 'تعذّر فحص المرفقات. اكبس تحديث الحالة للمحاولة مجددًا.',
      refresh: 'تحديث الحالة',
      loading: 'جارٍ التحميل…',
      preparing: 'جارٍ تجهيز التنزيل…',
      done: 'تم تجهيز التنزيل. عدد الملفات: ',
      missing: 'مرفقات ناقصة: ',
      missingHint: 'تفاصيلها بملف _missing-documents.txt داخل ZIP.',
      failed: 'تعذّر التنزيل. حدّث الصفحة وحاول مجددًا.',
      empty: 'لا توجد مرفقات مطابقة لتنزيلها.',
      invalid: 'الفلاتر غير صالحة. ارجع للسيارات واختر تنزيل المرفقات مجددًا.',
      vehicle_license: 'رخصة السيارة',
      direction_card: 'كرت الاتجاه',
      customs_declaration: 'البيان الجمركي',
      other: 'أخرى',
      navVehicles: 'السيارات',
      navReports: 'طباعة البيانات',
      navDrivers: 'سجل الشوفيرين',
      navOffice: 'ملفات المكتب',
      navTrash: 'المحذوفات',
      brandSub: 'إدارة السيارات',
      signOut: 'تسجيل الخروج',
    },
  };
  const text = (key) => copy[root.lang === 'ar' ? 'ar' : 'en'][key] || key;
  let categories = [],
    vehicles = [],
    busy = false,
    loaded = false,
    messageKey = 'loading',
    result = null,
    sequence = 0,
    previewSequence = 0,
    previewBusy = false,
    previewError = false,
    availability = null;
  const chosen = () =>
    Array.from(
      get('download-types').querySelectorAll('input:checked'),
      (input) =>
        Number(input.value),
    );
  function state() {
    get('download-types').disabled = busy || !loaded;
    get('download-selected').disabled =
      busy ||
      previewBusy ||
      !loaded ||
      !vehicles.length ||
      !chosen().length ||
      !availability?.file_count;
    get('availability-refresh').disabled = busy || previewBusy;
    get('download-status').textContent = result
      ? text('done') +
        result.files +
        (result.missing
          ? ' · ' + text('missing') + result.missing + '. ' + text('missingHint')
          : '')
      : text(messageKey);
    get('download-status').setAttribute(
      'role',
      ['failed', 'empty', 'invalid'].includes(messageKey) ? 'alert' : 'status',
    );
  }
  function renderTypes() {
    const selected = new Set(chosen());
    get('download-types').replaceChildren(
      ...categories.map((category) => {
        const label = document.createElement('label');
        label.className = 'download-type-choice';
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.value = String(category.id);
        input.checked = selected.has(category.id);
        input.addEventListener(
          'change',
          updateAvailability,
        );
        const title = document.createElement('span');
        title.dir = 'auto';
        title.textContent = category.code ? text(category.code) : category.name;
        label.append(
          input,
          title,
        );
        return label;
      }),
    );
  }
  async function request(
    url,
    options = {},
  ) {
    const response = await fetch(
      url,
      {
        ...options,
        credentials: 'same-origin',
        cache: 'no-store',
      },
    );
    if (response.status === 401) {
      location.assign('/login/');
      throw new Error();
    }
    if (!response.ok) {
      const error = new Error();
      error.status = response.status;
      throw error;
    }
    return response;
  }
  async function load() {
    const current = ++sequence;
    busy = true;
    loaded = false;
    result = null;
    ++previewSequence;
    availability = null;
    previewBusy = false;
    previewError = false;
    renderAvailability();
    messageKey = 'loading';
    state();
    try {
      const scope = HSpaceVehicleFilters.reportScope(location.hash);
      if (!scope.valid) {
        messageKey = 'invalid';
        return;
      }
      const [types, list] = await Promise.all([
        request('/api/attachment-categories/').then((response) => response.json()),
        request('/api/vehicles/').then((response) => response.json()),
      ]);
      if (current !== sequence) {
        return;
      }
      categories = types.categories;
      vehicles = scope.filtered
        ? HSpaceSearch.search(
            HSpaceVehicleFilters.apply(
              list.vehicles,
              scope.selected,
            ),
            scope.query,
          )
        : list.vehicles;
      loaded = true;
      messageKey = '';
      renderTypes();
      translate();
      updateAvailability();
    } catch (_) {
      if (current === sequence) {
        messageKey = 'failed';
      }
    } finally {
      if (current === sequence) {
        busy = false;
        state();
      }
    }
  }
  get('attachment-download-form').addEventListener(
    'submit',
    async (event) => {
      event.preventDefault();
      if (
        busy
        ||
        previewBusy
        ||
        !loaded
        ||
        !chosen().length
        ||
        !vehicles.length
        ||
        !availability?.file_count
      ) {
        return;
      }
      busy = true;
      result = null;
      messageKey = 'preparing';
      state();
      try {
        const response = await request(
          '/api/attachment-download/',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': get('csrf-token').value },
            body: JSON.stringify({
              vehicle_ids: vehicles.map((vehicle) => vehicle.id),
              category_ids: chosen(),
            }),
          },
        );
        const blob = await response.blob(),
          url = URL.createObjectURL(blob),
          link = document.createElement('a');
        link.href = url;
        link.download = 'HSPACE-attachments.zip';
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(
          () => URL.revokeObjectURL(url),
          60000,
        );
        result = {
          files: Number(response.headers.get('X-HSpace-File-Count') || 0),
          missing: Number(response.headers.get('X-HSpace-Missing-Count') || 0),
        };
        messageKey = '';
      } catch (error) {
        messageKey = error.status === 404 ? 'empty' : 'failed';
      } finally {
        busy = false;
        state();
      }
    },
  );
  function cell(
    tag,
    value,
  ) {
    const item = document.createElement(tag);
    item.textContent = value;
    return item;
  }
  function renderAvailability() {
    const selected = chosen();
    get('download-availability').hidden = !loaded || !selected.length;
    get('availability-status').textContent = previewBusy
      ? text('checking')
      : previewError
        ? text('checkFailed')
        : availability?.file_count === 0
          ? text('empty')
          : '';
    get('download-availability').setAttribute(
      'aria-busy',
      String(previewBusy),
    );
    get('availability-head').replaceChildren();
    get('availability-body').replaceChildren();
    if (
      !availability
      ||
      previewBusy
      ||
      previewError
    ) {
      return;
    }
    const types = categories.filter((category) => selected.includes(category.id)),
      heading = document.createElement('tr');
    for (const value of [
      text('plate'),
      ...types.map((category) => (category.code ? text(category.code) : category.name)),
    ]) {
      const title = cell(
        'th',
        value,
      );
      title.scope = 'col';
      heading.append(title);
    }
    get('availability-head').append(heading);
    for (const vehicle of availability.vehicles) {
      const row = document.createElement('tr'),
        number = document.createElement('th'),
        plate = cell(
          'bdi',
          vehicle.plate_number,
        );
      number.scope = 'row';
      plate.dir = 'ltr';
      number.append(plate);
      row.append(number);
      for (const category of types) {
        const count =
          vehicle.documents.find((item) => item.category_id === category.id)?.count || 0;
        const column = document.createElement('td'),
          badge = cell(
            'span',
            text(count ? 'present' : 'absent') + (count > 1 ? ' (' + count + ')' : ''),
          );
        badge.className = 'document-status ' + (count ? 'available' : 'missing');
        column.append(badge);
        row.append(column);
      }
      get('availability-body').append(row);
    }
  }
  async function updateAvailability() {
    const current = ++previewSequence,
      ids = chosen();
    availability = null;
    previewError = false;
    result = null;
    messageKey = '';
    if (
      !loaded
      ||
      !ids.length
      ||
      !vehicles.length
    ) {
      previewBusy = false;
      renderAvailability();
      state();
      return;
    }
    previewBusy = true;
    renderAvailability();
    state();
    try {
      const response = await request(
        '/api/attachment-download/availability/',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': get('csrf-token').value },
          body: JSON.stringify({
            vehicle_ids: vehicles.map((vehicle) => vehicle.id),
            category_ids: ids,
          }),
        },
      );
      const data = await response.json();
      if (current === previewSequence) {
        availability = data;
      }
    } catch (_) {
      if (current === previewSequence) {
        previewError = true;
      }
    } finally {
      if (current === previewSequence) {
        previewBusy = false;
        renderAvailability();
        state();
      }
    }
  }
  get('availability-refresh').addEventListener(
    'click',
    updateAvailability,
  );
  function translate() {
    document.title = 'H SPACE | ' + text('title');
    document.querySelectorAll('[data-download-i18n],[data-i18n]').forEach((item) => {
      const key = item.dataset.downloadI18n || item.dataset.i18n;
      if (copy.en[key]) {
        item.textContent = text(key);
      }
    });
    document
      .querySelectorAll('[data-i18n-aria]')
      .forEach((item) => item.setAttribute(
        'aria-label',
        text(item.dataset.i18nAria),
      ));
    get('download-scope').textContent = loaded ? text('scope') + vehicles.length : '';
    renderTypes();
    renderAvailability();
    state();
  }
  window.addEventListener(
    'hspace:language',
    translate,
  );
  window.addEventListener(
    'hashchange',
    load,
  );
  translate();
  load();
})();
