(() => {
  'use strict';

  const getElement = (id) => document.getElementById(id),
    globalPage = document.body.dataset.driverHistory === 'true';
  const en = {
    sameDayHandover: 'Same-day handover',
    stalePeriod: 'This period is no longer current. Refresh the history.',
    attachments: 'Attachments',
    endPeriod: 'End period',
    addDriver: 'Add driver',
    noCurrentDriver: 'No current driver is assigned.',
    lastWorked: 'Last working day',
    endHint:
      'Keep the driver and documents in history; clear the current driver until a new one is assigned.',
    endRequired: 'Enter the last working date.',
    futureEnd: 'The last working date cannot be in the future.',
    endBeforeStart: 'The last working date cannot precede the start date.',
    periodEnded: 'Period ended',
    phoneHint: 'English digits only; keep the leading zero.',
    nameRule:
      'Enter an Arabic or English name, using letters and spaces only (up to 200 characters).',
    phoneRule: 'Use English digits only, up to 32 digits.',
    startRequired: 'Enter the new driver’s start date.',
    dateInvalid: 'Enter a valid start date.',
    futureStart: 'The start date cannot be in the future.',
    overlapStart: 'The start date overlaps a previous period. Check the earlier dates.',
    knownStart: 'Keep the known start date or correct it; it cannot be cleared.',
    before: 'Before correction',
    after: 'After correction',
    skip: 'Skip to content',
    currentDriverHint: 'Use the driver actions below to change or correct this value.',
    driverHistory: 'Driver history',
    changeDriver: 'Change driver',
    correctDriver: 'Correct current driver',
    searchHistory: 'Search / print history',
    corrections: 'Change history',
    name: 'Driver name',
    phone: 'Driver phone',
    start: 'Start date',
    end: 'Last working day',
    current: 'Current',
    unknown: 'Unknown',
    recordedBy: 'Recorded by',
    vehicle: 'Vehicle number',
    type: 'Vehicle type',
    startHint:
      'Changing drivers requires a date. For an older current record, leave an unknown start date empty when correcting.',
    cancel: 'Cancel',
    save: 'Save',
    searchName: 'Driver name',
    onDate: 'Working on date',
    search: 'Search',
    print: 'Print results',
    historyDescription:
      'Find drivers, their vehicle periods and the phone number recorded for each period.',
    allVehicles: 'All vehicles',
    periodHint:
      'Periods include the last working day and may have gaps. Unknown start dates are excluded when searching a specific date.',
    loading: 'Loading…',
    empty: 'No driver records match.',
    failed: 'Could not load or save driver history. Try again.',
    invalid:
      'Check the name, English phone digits and dates. A start date cannot be in the future or overlap an earlier period.',
    saved: 'Driver history saved.',
    count: '{count} records',
    refresh: 'Refresh',
    paperStyle: 'Choose paper style',
    withHeader: 'With letterhead and watermark',
    withoutHeader: 'Preprinted paper: no letterhead or watermark',
    navVehicles: 'Vehicles',
    navReports: 'Print data',
    navTrash: 'Deleted items',
    navDrivers: 'Driver history',
    brandSub: 'Vehicle management',
    signOut: 'Sign out',
  };
  en.navOffice = 'Office files';
  const ar = {
    navOffice: 'ملفات المكتب',
    sameDayHandover: 'تبديل بنفس اليوم',
    stalePeriod: 'هذه الفترة لم تعد الحالية. حدّث سجل الشوفيرين.',
    attachments: 'المرفقات',
    endPeriod: 'إنهاء الفترة',
    addDriver: 'إضافة شوفير',
    noCurrentDriver: 'لا يوجد شوفير حالي للسيارة.',
    lastWorked: 'آخر يوم عمل',
    endHint: 'سيبقى الشوفير وأوراقه محفوظين بالسجل، وتصبح السيارة بدون شوفير حالي حتى إضافة بديل.',
    endRequired: 'أدخل آخر يوم عمل.',
    futureEnd: 'آخر يوم عمل لا يمكن أن يكون بالمستقبل.',
    endBeforeStart: 'آخر يوم عمل لا يمكن أن يسبق تاريخ البداية.',
    periodEnded: 'إنهاء الفترة',
    phoneHint: 'أرقام إنجليزية فقط، مع الحفاظ على الصفر في البداية.',
    nameRule: 'أدخل اسمًا بأحرف عربية أو إنجليزية ومسافات فقط، حتى 200 حرف.',
    phoneRule: 'رقم الهاتف يقبل أرقامًا إنجليزية فقط، حتى 32 خانة.',
    startRequired: 'أدخل تاريخ بداية الشوفير الجديد.',
    dateInvalid: 'أدخل تاريخ بداية صالحًا.',
    futureStart: 'تاريخ البداية لا يمكن أن يكون بالمستقبل.',
    overlapStart: 'تاريخ البداية يتداخل مع فترة سابقة. راجع تواريخ الشوفيرين.',
    knownStart: 'تاريخ البداية المعروف لا يمكن مسحه؛ صححه عند الحاجة.',
    before: 'قبل التصحيح',
    after: 'بعد التصحيح',
    skip: 'انتقل إلى المحتوى',
    currentDriverHint: 'استخدم أزرار الشوفير بالأسفل للتغيير أو التصحيح.',
    driverHistory: 'سجل الشوفيرين',
    changeDriver: 'تغيير الشوفير',
    correctDriver: 'تصحيح الشوفير الحالي',
    searchHistory: 'بحث / طباعة السجل',
    corrections: 'سجل التغييرات',
    name: 'اسم الشوفير',
    phone: 'رقم الشوفير',
    start: 'تاريخ البداية',
    end: 'آخر يوم عمل',
    current: 'حالي',
    unknown: 'غير معروف',
    recordedBy: 'سجّله',
    vehicle: 'رقم المركبة',
    type: 'نوع المركبة',
    startHint:
      'تغيير الشوفير يتطلب تاريخ بداية. عند تصحيح سجل قديم، اترك تاريخ البداية فارغًا إذا كان غير معروف.',
    cancel: 'إلغاء',
    save: 'حفظ',
    searchName: 'اسم الشوفير',
    onDate: 'كان يعمل بتاريخ',
    search: 'بحث',
    print: 'طباعة النتائج',
    historyDescription: 'اعرف الشوفير والسيارات وفترات عمله ورقم تلفونه المسجل بكل فترة.',
    allVehicles: 'كل السيارات',
    periodHint:
      'تشمل الفترة آخر يوم عمل، وقد توجد أيام بدون شوفير بين الفترات. عند البحث بتاريخ محدد، تُستبعد الفترات التي بدايتها غير معروفة.',
    loading: 'جارٍ التحميل…',
    empty: 'لا توجد فترات مطابقة.',
    failed: 'تعذّر تحميل سجل الشوفيرين أو حفظه. حاول مجددًا.',
    invalid:
      'تحقق من الاسم ورقم الهاتف الإنجليزي والتواريخ. البداية لا تكون بالمستقبل ولا تتداخل مع فترة سابقة.',
    saved: 'تم حفظ سجل الشوفيرين.',
    count: '{count} سجل',
    refresh: 'تحديث',
    paperStyle: 'اختيار نوع الورق',
    withHeader: 'مع الترويسة والعلامة المائية',
    withoutHeader: 'ورق جاهز: بدون ترويسة أو علامة مائية',
    navVehicles: 'السيارات',
    navReports: 'طباعة البيانات',
    navTrash: 'المحذوفات',
    navDrivers: 'سجل الشوفيرين',
    brandSub: 'إدارة السيارات',
    signOut: 'تسجيل الخروج',
  };
  const getText = (key) =>
    (document.documentElement.lang === 'ar' ? ar[key] : en[key]) || en[key] || key;
  const createElement = (
    tag,
    text = '',
    cls = '',
  ) => {
    const node = document.createElement(tag);
    node.textContent = text;
    node.className = cls;
    return node;
  };
  const stamp = (value) =>
    value
      ? new Intl.DateTimeFormat(
        document.documentElement.lang === 'ar' ? 'ar-JO' : 'en-GB',
        {
            dateStyle: 'medium',
            timeStyle: 'short',
            timeZone: 'Asia/Amman',
          },
      ).format(new Date(value))
      : getText('unknown');
  let openEnd = () => {};
  let rows = [],
    changes = [],
    busy = false,
    vehicleId = null,
    requestId = 0,
    correcting = false,
    loaded = false,
    query = '',
    onDate = '',
    statusKey = '';
  async function api(
    url,
    options = {},
  ) {
    const response = await fetch(
      url,
      {
        ...options,
        credentials: 'same-origin',
        cache: 'no-store',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getElement('csrf-token').value,
        },
      },
    );
    if (response.status === 401) {
      location.assign('/login/');
      throw new Error();
    }
    if (!response.ok) {
      const error = new Error();
      error.status = response.status;
      if (response.status === 400) {
        try {
          const data = await response.json();
          error.field = data.error?.field;
          error.reason = data.error?.reason;
        } catch (_) {}
      }
      throw error;
    }
    return response.json();
  }
  const isolated = (
    text,
    dir = 'auto',
  ) => {
    const node = createElement(
      'bdi',
      text,
    );
    node.dir = dir;
    return node;
  };
  const lastDay = (iso) => {
    const day = new Date(iso + 'T00:00:00Z');
    day.setUTCDate(day.getUTCDate() - 1);
    return day.toISOString().slice(
      0,
      10,
    );
  };
  const columns = [
    ['driver_name', 'name'],
    ['driver_phone', 'phone'],
    ['plate_number', 'vehicle'],
    ['vehicle_type', 'type'],
    ['started_on', 'start'],
    ['ended_on', 'end'],
  ];
  function value(
    row,
    key,
  ) {
    if (key === 'ended_on') {
      return row.is_current
        ? getText('current')
        : row.started_on && row.started_on === row.ended_on
          ? getText('sameDayHandover')
          : row.last_worked_on || row[key] || getText('unknown');
    }
    return row[key] || getText('unknown');
  }
  function render() {
    getElement('driver-status').textContent = statusKey
      ? getText(statusKey)
      : !globalPage && loaded && !rows.some((row) => row.is_current)
        ? getText('noCurrentDriver')
        : '';
    if (globalPage) {
      getElement('driver-search').disabled = busy;
      getElement('print-driver-history').disabled = busy || !loaded || !rows.length;
      getElement('report-paper').hidden = !loaded || !rows.length;
      const head = columns.map(([, label]) => {
        const th = createElement(
          'th',
          getText(label),
        );
        th.scope = 'col';
        return th;
      });
      getElement('driver-report-head').replaceChildren(...head);
      getElement('driver-report-body').replaceChildren(
        ...rows.map((row) => {
          const tr = createElement('tr');
          columns.forEach(([key]) => {
            const td = createElement('td'),
              bdi = createElement(
                'bdi',
                value(
                  row,
                  key,
                ),
              );
            bdi.dir = ['driver_phone', 'plate_number', 'started_on', 'ended_on'].includes(key)
              ? 'ltr'
              : 'auto';
            td.append(bdi);
            tr.append(td);
          });
          return tr;
        }),
      );
      const scope = [createElement(
        'span',
        getText('count').replace(
          '{count}',
          rows.length,
        ),
      )];
      for (const [label, text, dir] of [
        [vehicleId ? 'vehicle' : '', rows[0]?.plate_number || vehicleId, 'ltr'],
        [query ? 'name' : '', query, 'auto'],
        [onDate ? 'onDate' : '', onDate, 'ltr'],
      ]) {
        if (!label) {
          continue;
        }
        const part = createElement(
          'span',
          getText(label) + ': ',
        );
        part.append(isolated(
          text,
          dir,
        ));
        scope.push(part);
      }
      const parts = [];
      scope.forEach((
        part,
        index,
      ) => {
        if (index) {
          parts.push(createElement(
            'span',
            ' · ',
          ));
        }
        parts.push(part);
      });
      getElement('driver-report-scope').replaceChildren(...parts);
    } else {
      getElement('change-driver').textContent = getText(
        rows.some((row) => row.is_current) ? 'changeDriver' : 'addDriver',
      );
      getElement('change-driver').disabled = busy || !loaded;
      getElement('correct-driver').disabled =
        busy || !loaded || !rows.some((row) => row.is_current);
      getElement('all-driver-history').href = '/drivers/?vehicle_id=' + vehicleId;
      getElement('vehicle-driver-history').replaceChildren(
        ...rows.map((row) => {
          const line = createElement(
            'div',
            '',
            'driver-record',
          );
          const name = createElement(
            'strong',
            row.driver_name || getText('unknown'),
          );
          name.dir = 'auto';
          line.append(
            name,
            isolated(
              row.driver_phone || getText('unknown'),
              'ltr',
            ),
            isolated(
              (row.started_on || getText('unknown')) + ' → ' + value(
                row,
                'ended_on',
              ),
              'ltr',
            ),
            createElement(
              'span',
              getText('recordedBy') + ': ' + (row.created_by_name || getText('unknown')),
            ),
          );
          const actions = createElement(
            'span',
            '',
            'driver-row-actions',
          );
          const files = createElement(
            'button',
            getText('attachments') + ' (' + (row.attachment_count || 0) + ')',
            'button secondary small driver-docs-button',
          );
          files.dataset.assignmentId = String(row.id);
          files.type = 'button';
          files.disabled = busy;
          files.setAttribute(
            'aria-label',
            getText('attachments') + ': ' + row.driver_name,
          );
          files.addEventListener(
            'click',
            () =>
              document.dispatchEvent(
                new CustomEvent(
                  'hspace:open-driver-files',
                  {
                    detail: {
                      vehicleId,
                      assignment: row,
                    },
                  },
                ),
              ),
          );
          actions.append(files);
          if (row.is_current) {
            const end = createElement(
              'button',
              getText('endPeriod'),
              'button secondary small danger',
            );
            end.type = 'button';
            end.disabled = busy;
            end.addEventListener(
              'click',
              () => openEnd(row),
            );
            actions.append(end);
          }
          line.append(actions);
          return line;
        }),
      );
      getElement('driver-corrections').replaceChildren(
        ...changes.map((change) => {
          const row = createElement(
            'div',
            '',
            'driver-record',
          );
          for (const [key, data] of [
            ['before', change.before_data || {}],
            ['after', change.after_data || {}],
          ]) {
            const group = createElement(
              'span',
              '',
              'driver-revision',
            );
            group.append(
              createElement(
                'strong',
                getText(key) + ': ',
              ),
              isolated(data.driver_name || getText('unknown')),
              isolated(
                data.driver_phone || getText('unknown'),
                'ltr',
              ),
              isolated(
                data.started_on || getText('unknown'),
                'ltr',
              ),
              isolated(
                data.ended_on ? lastDay(data.ended_on) : getText('current'),
                'ltr',
              ),
            );
            row.append(group);
          }
          if (change.action === 'END') {
            row.prepend(createElement(
              'strong',
              getText('periodEnded'),
            ));
          }
          row.append(isolated(change.actor_name + ' · ' + stamp(change.created_at)));
          return row;
        }),
      );
    }
  }
  function translate() {
    document.querySelectorAll('[data-driver-i18n]').forEach((node) => {
      node.textContent = getText(node.dataset.driverI18n);
    });
    if (globalPage) {
      document.title = 'H SPACE | ' + getText('driverHistory');
      document.querySelectorAll('[data-i18n]').forEach((node) => {
        if (en[node.dataset.i18n]) {
          node.textContent = getText(node.dataset.i18n);
        }
      });
      document.querySelectorAll('[data-i18n-aria]').forEach((node) => {
        if (en[node.dataset.i18nAria]) {
          node.setAttribute(
            'aria-label',
            getText(node.dataset.i18nAria),
          );
        }
      });
    }
    render();
  }
  async function load() {
    const id = ++requestId;
    loaded = false;
    busy = true;
    rows = [];
    changes = [];
    statusKey = 'loading';
    render();
    try {
      let url;
      if (globalPage) {
        const params = new URLSearchParams();
        if (vehicleId) {
          params.set(
            'vehicle_id',
            vehicleId,
          );
        }
        if (query) {
          params.set(
            'q',
            query,
          );
        }
        if (onDate) {
          params.set(
            'on_date',
            onDate,
          );
        }
        url = '/api/drivers/?' + params;
      } else {
        vehicleId = location.hash.match(/^#vehicle\/(\d+)$/)?.[1];
        if (!vehicleId) {
          busy = false;
          render();
          return;
        }
        url = '/api/vehicles/' + vehicleId + '/drivers/';
      }
      const payload = await api(url);
      if (id !== requestId) {
        return;
      }
      rows = payload.assignments;
      changes = payload.corrections || [];
      loaded = true;
      statusKey = rows.length ? '' : 'empty';
    } catch (_) {
      if (id === requestId) {
        statusKey = 'failed';
      }
    } finally {
      if (id === requestId) {
        busy = false;
        render();
      }
    }
  }
  document.addEventListener(
    'hspace:driver-files-changed',
    (event) => {
      if (String(event.detail.vehicleId) === String(vehicleId)) {
        rows = rows.map((row) =>
          row.id === event.detail.assignmentId
            ? {
                ...row,
                attachment_count: event.detail.count,
              }
            : row,
        );
        render();
      }
    },
  );
  window.addEventListener(
    'hspace:language',
    translate,
  );
  if (globalPage) {
    const param = new URLSearchParams(location.search).get('vehicle_id');
    if (
      param
      && /^[0-9]+$/.test(param)
    ) {
      vehicleId = param;
    }
    getElement('driver-search-form').addEventListener(
      'submit',
      (event) => {
        event.preventDefault();
        query = getElement('driver-query').value.trim();
        onDate = getElement('driver-on-date').value;
        load();
      },
    );
    getElement('print-driver-history').addEventListener(
      'click',
      () => {
        if (!getElement('print-driver-history').disabled) {
          getElement('driver-print-dialog').showModal();
        }
      },
    );
    const print = (plain) => {
      if (getElement('print-driver-history').disabled) {
        return;
      }
      getElement('report-paper').classList.toggle(
        'preprinted-paper',
        plain,
      );
      getElement('driver-print-dialog').close();
      window.print();
    };
    getElement('driver-print-with').addEventListener(
      'click',
      () => print(false),
    );
    getElement('driver-print-without').addEventListener(
      'click',
      () => print(true),
    );
    getElement('driver-print-cancel').addEventListener(
      'click',
      () =>
        getElement('driver-print-dialog').close(),
    );
    translate();
    load();
  } else {
    let endTarget = null;
    openEnd = (row) => {
      if (
        busy
        || !loaded
      ) {
        return;
      }
      endTarget = {
        vehicleId,
        assignment: row,
      };
      getElement('driver-end-name').textContent = row.driver_name;
      getElement('driver-last-worked').value = '';
      getElement('driver-end-message').textContent = '';
      getElement('driver-end-dialog').showModal();
      getElement('driver-last-worked').focus();
    };
    getElement('driver-end-cancel').addEventListener(
      'click',
      () => {
        if (!busy) {
          getElement('driver-end-dialog').close();
        }
      },
    );
    getElement('driver-end-dialog').addEventListener(
      'cancel',
      (event) => {
        if (busy) {
          event.preventDefault();
        }
      },
    );
    getElement('driver-dialog').addEventListener(
      'cancel',
      (event) => {
        if (busy) {
          event.preventDefault();
        }
      },
    );
    getElement('driver-end-form').addEventListener(
      'submit',
      async (event) => {
        event.preventDefault();
        if (
          busy
          || !endTarget
        ) {
          return;
        }
        const target = endTarget,
          date = getElement('driver-last-worked').value;
        if (!date) {
          getElement('driver-end-message').textContent = getText('endRequired');
          getElement('driver-last-worked').focus();
          return;
        }
        busy = true;
        getElement('driver-end-save').disabled = true;
        getElement('driver-end-cancel').disabled = true;
        getElement('driver-last-worked').disabled = true;
        render();
        try {
          const payload = await api(
            '/api/vehicles/' + target.vehicleId + '/drivers/' + target.assignment.id + '/end/',
            {
              method: 'POST',
              body: JSON.stringify({
                last_worked_on: date,
              }),
            },
          );
          getElement('driver-end-dialog').close();
          document.dispatchEvent(
            new CustomEvent(
              'hspace:driver-updated',
              {
                detail: payload,
              },
            ),
          );
          await load();
        } catch (error) {
          getElement('driver-end-message').textContent = getText(
            error.reason && en[error.reason] ? error.reason : 'failed',
          );
        } finally {
          busy = false;
          getElement('driver-end-save').disabled = false;
          getElement('driver-end-cancel').disabled = false;
          getElement('driver-last-worked').disabled = false;
          render();
        }
      },
    );
    const driverInputs = {
      driver_name: 'new-driver-name',
      driver_phone: 'new-driver-phone',
      started_on: 'driver-start',
    };
    function clearErrors() {
      Object.entries(driverInputs).forEach(([field, id]) => {
        getElement(id).setAttribute(
          'aria-invalid',
          'false',
        );
        const message = getElement('error-' + field);
        if (message) {
          message.textContent = '';
        }
      });
    }
    Object.entries(driverInputs).forEach(([field, id]) =>
      getElement(id).addEventListener(
        'input',
        () => {
          getElement(id).setAttribute(
            'aria-invalid',
            'false',
          );
          const message = getElement('error-' + field);
          if (message) {
            message.textContent = '';
          }
          getElement('driver-form-message').textContent = '';
        },
      ),
    );
    function open(correction) {
      if (
        busy
        || !loaded
      ) {
        return;
      }
      clearErrors();
      correcting = correction;
      const current = rows.find((row) => row.is_current);
      getElement('driver-dialog-title').textContent = getText(
        correction ? 'correctDriver' : 'changeDriver',
      );
      getElement('new-driver-name').value = correction && current ? current.driver_name : '';
      getElement('new-driver-phone').value = correction && current ? current.driver_phone : '';
      getElement('driver-start').value = correction && current ? current.started_on || '' : '';
      getElement('driver-start').required = !correction;
      getElement('driver-form-message').textContent = '';
      getElement('driver-dialog').showModal();
    }
    getElement('change-driver').addEventListener(
      'click',
      () => open(false),
    );
    getElement('correct-driver').addEventListener(
      'click',
      () => open(true),
    );
    getElement('cancel-driver').addEventListener(
      'click',
      () =>
        getElement('driver-dialog').close(),
    );
    const refresh = createElement(
      'button',
      getText('refresh'),
      'button secondary small',
    );
    refresh.type = 'button';
    refresh.dataset.driverI18n = 'refresh';
    refresh.addEventListener(
      'click',
      load,
    );
    getElement('change-driver').parentElement.append(refresh);
    getElement('driver-form').addEventListener(
      'submit',
      async (event) => {
        event.preventDefault();
        if (busy) {
          return;
        }
        const target = vehicleId;
        busy = true;
        getElement('save-driver').disabled = true;
        getElement('cancel-driver').disabled = true;
        try {
          const payload = await api(
            '/api/vehicles/' + target + '/drivers/' + (correcting ? 'current/' : ''),
            {
              method: correcting ? 'PATCH' : 'POST',
              body: JSON.stringify({
                driver_name: getElement('new-driver-name').value.trim(),
                driver_phone: getElement('new-driver-phone').value.trim(),
                started_on: getElement('driver-start').value || null,
              }),
            },
          );
          getElement('driver-dialog').close();
          document.dispatchEvent(
            new CustomEvent(
              'hspace:driver-updated',
              {
                detail: payload,
              },
            ),
          );
          await load();
        } catch (error) {
          const field = driverInputs[error.field];
          if (
            field
            && en[error.reason]
          ) {
            const input = getElement(field);
            input.setAttribute(
              'aria-invalid',
              'true',
            );
            const message = getElement('error-' + error.field);
            if (message) {
              message.textContent = getText(error.reason);
            }
            input.focus();
            getElement('driver-form-message').textContent = getText(error.reason);
          } else {
            getElement('driver-form-message').textContent = getText(
              error.status === 400 ? 'invalid' : 'failed',
            );
          }
        } finally {
          busy = false;
          getElement('save-driver').disabled = false;
          getElement('cancel-driver').disabled = false;
          render();
        }
      },
    );
    document.addEventListener(
      'hspace:detail-ready',
      load,
    );
    window.addEventListener(
      'hashchange',
      () => {
        getElement('driver-dialog').close();
        getElement('driver-end-dialog').close();
        endTarget = null;
        if (!location.hash.startsWith('#vehicle/')) {
          requestId++;
          rows = [];
          loaded = false;
          busy = false;
          render();
        }
      },
    );
    translate();
    if (location.hash.startsWith('#vehicle/')) {
      load();
    }
  }
})();
