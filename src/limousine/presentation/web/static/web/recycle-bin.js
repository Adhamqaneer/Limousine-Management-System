(() => {
  'use strict';

  const getElement = (id) => document.getElementById(id),
    en = {};
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    en[el.dataset.i18n] = el.textContent;
  });
  Object.assign(
    en,
    {
      restore: 'Restore',
      categoryInUse:
        'This vehicle already has an attachment in that category. Delete or recategorize it before restoring this one.',
      unknown: 'Unknown (older record)',
      createdBy: 'Added by',
      deletedBy: 'Deleted by',
      driverFiles: 'Driver attachments',
      vehicle: 'Vehicle',
      attachment: 'Attachment',
      cover: 'Card photo',
      empty: 'No deleted items.',
      noHistory: 'No recorded activity yet.',
      failed: 'Could not complete the request. Refresh and try again.',
      saved: 'Item restored.',
      parentDeleted: 'Restore the vehicle first.',
      confirmRestore: 'Restore {label}?',
      CREATE: 'Added',
      DELETE: 'Deleted',
      RESTORE: 'Restored',
      RENAME: 'Renamed',
      category: 'Category',
      LABEL: 'Classified',
      ALIAS: 'Alternative name added',
      MERGE: 'Merged categories',
      replaced: 'Replaced card photo',
      removeCurrentPhoto: 'Remove current card photo',
      confirmCurrentPhoto:
        'Move the current card photo for {plate} to deleted items? You can then restore an older photo.',
      currentPhotoRemoved: 'Current card photo moved to deleted items.',
      coverConflict: 'Remove the current card photo before restoring an older photo.',
      loading: 'Loading…',
      signOut: 'Sign out',
    },
  );
  en.navOffice = 'Office files';
  en.office = 'Office file';
  const ar = {
    navOffice: 'ملفات المكتب',
    office: 'ملف المكتب',
    navDrivers: 'سجل الشوفيرين',
    navTrash: 'المحذوفات',
    navReports: 'طباعة البيانات',
    navVehicles: 'السيارات',
    brandSub: 'إدارة السيارات',
    skip: 'انتقل إلى المحتوى',
    signOut: 'تسجيل الخروج',
    trashTitle: 'المحذوفات',
    refreshTrash: 'تحديث',
    deletedTitle: 'الاسترجاع',
    restoreNote:
      'استرجع السيارة أولًا. الملفات المحذوفة بشكل منفصل تظل محذوفة. لاسترجاع صورة كارد قديمة، احذف الصورة الحالية أولًا.',
    activityTitle: 'سجل العمليات',
    historyNote:
      'تُسجل الإضافات وتغيير الأسماء والحذف والاسترجاع الجديدة. هوية من أضاف السجلات القديمة غير معروفة.',
    olderActivity: 'تحميل عمليات أقدم',
    restore: 'استرجاع',
    categoryInUse: 'هاي السيارة فيها مرفق بنفس التصنيف. احذفه أو غيّر تصنيفه قبل استرجاع هالمرفق.',
    unknown: 'غير معروف (سجل قديم)',
    createdBy: 'أضافه',
    deletedBy: 'حذفه',
    driverFiles: 'مرفقات الشوفير',
    vehicle: 'سيارة',
    attachment: 'مرفق',
    cover: 'صورة الكارد',
    empty: 'لا توجد محذوفات.',
    noHistory: 'لا توجد عمليات مسجلة بعد.',
    failed: 'تعذّر إكمال الطلب. حدّث الصفحة وحاول مجددًا.',
    saved: 'تم الاسترجاع.',
    parentDeleted: 'استرجع السيارة أولًا.',
    removeCurrentPhoto: 'حذف صورة الكارد الحالية',
    confirmCurrentPhoto:
      'نقل صورة الكارد الحالية للسيارة {plate} إلى المحذوفات؟ بعدها بتقدر تسترجع صورة قديمة.',
    currentPhotoRemoved: 'تم نقل صورة الكارد الحالية إلى المحذوفات.',
    confirmRestore: 'استرجاع {label}؟',
    CREATE: 'إضافة',
    DELETE: 'حذف',
    RESTORE: 'استرجاع',
    RENAME: 'تغيير الاسم',
    category: 'تصنيف',
    LABEL: 'تغيير التصنيف',
    ALIAS: 'إضافة اسم بديل',
    MERGE: 'دمج تصنيفات',
    replaced: 'استبدال صورة الكارد',
    coverConflict: 'احذف صورة الكارد الحالية قبل استرجاع صورة قديمة.',
    loading: 'جارٍ التحميل…',
  };
  let items = [],
    events = [],
    busy = false,
    more = false,
    messageKey = '';
  const getText = (key) =>
    (document.documentElement.lang === 'ar' ? ar[key] : en[key]) ?? en[key] ?? key;
  const createElement = (
    tag,
    text,
    cls = '',
  ) => {
    const node = document.createElement(tag);
    node.textContent = text;
    node.className = cls;
    return node;
  };
  const date = (value) =>
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
        headers: {
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
      throw error;
    }
    return response.status === 204 ? null : response.json();
  }
  function render() {
    getElement('trash-message').textContent = messageKey ? getText(messageKey) : '';
    getElement('refresh-trash').disabled = busy;
    getElement('older-activity').disabled = busy;
    getElement('older-activity').hidden = !more;
    getElement('deleted-list').setAttribute(
      'aria-busy',
      String(busy),
    );
    getElement('deleted-list').replaceChildren(
      ...(items.length
        ? items.map((item) => {
            const card = createElement(
              'article',
              '',
              'panel recycle-card',
            ),
              info = createElement('div');
            const title = createElement(
              'h3',
              item.label,
            );
            title.dir = 'auto';
            info.append(
              createElement(
                'p',
                getText(item.kind) +
                  ' · ' +
                  item.plate_number +
                  (item.driver_name
                    ? ' · ' + getText('driverFiles') + ': ' + item.driver_name
                    : ''),
                'muted',
              ),
              title,
              createElement(
                'p',
                getText('createdBy') +
                  ': ' +
                  (item.created_by || getText('unknown')) +
                  ' · ' +
                  date(item.created_at),
                'muted',
              ),
              createElement(
                'p',
                getText('deletedBy') +
                  ': ' +
                  (item.deleted_by || getText('unknown')) +
                  ' · ' +
                  date(item.deleted_at),
                'muted',
              ),
            );
            const button = createElement(
              'button',
              getText(item.kind !== 'vehicle' && item.parent_deleted ? 'parentDeleted' : 'restore'),
              'button secondary',
            );
            button.type = 'button';
            button.disabled = busy || (item.kind !== 'vehicle' && item.parent_deleted);
            button.addEventListener(
              'click',
              () => restore(item),
            );
            card.append(
              info,
              button,
            );
            if (
              item.kind === 'cover'
              &&
              item.has_current_cover
              &&
              !item.parent_deleted
            ) {
              const remove = createElement(
                'button',
                getText('removeCurrentPhoto'),
                'button secondary danger',
              );
              remove.type = 'button';
              remove.disabled = busy;
              remove.addEventListener(
                'click',
                () => removeCurrentPhoto(item),
              );
              card.append(remove);
            }
            return card;
          })
        : [createElement(
          'p',
          getText(busy ? 'loading' : 'empty'),
          'section-empty',
        )]),
    );
    getElement('activity-list').replaceChildren(
      ...(events.length
        ? events.map((event) => {
            const card = createElement(
              'article',
              '',
              'panel activity-card',
            ),
              label = createElement(
                'strong',
                event.label,
              );
            label.dir = 'auto';
            card.append(
              createElement(
                'p',
                getText(event.action) +
                  ' · ' +
                  getText(event.entity_kind) +
                  ' · ' +
                  event.plate_number +
                  (event.driver_name
                    ? ' · ' + getText('driverFiles') + ': ' + event.driver_name
                    : ''),
              ),
              label,
              createElement(
                'p',
                event.actor_name + ' · ' + date(event.created_at),
                'muted',
              ),
            );
            if (event.reason === 'replaced') {
              card.append(createElement(
                'p',
                getText('replaced'),
                'muted',
              ));
            }
            return card;
          })
        : [createElement(
          'p',
          getText('noHistory'),
          'section-empty',
        )]),
    );
  }
  async function load(older = false) {
    if (busy) {
      return;
    }
    busy = true;
    render();
    try {
      if (older) {
        const result = await request('/api/activity/?before=' + events[events.length - 1].id);
        events.push(...result.events);
        more = result.events.length === 100;
      } else {
        const [deleted, history] = await Promise.all([
          request('/api/recycle-bin/'),
          request('/api/activity/'),
        ]);
        items = deleted.items;
        events = history.events;
        more = events.length === 100;
      }
    } catch (_) {
      messageKey = 'failed';
    } finally {
      busy = false;
      render();
    }
  }
  async function restore(item) {
    if (
      busy
      ||
      !window.confirm(getText('confirmRestore').replace(
        '{label}',
        item.label,
      ))
    ) {
      return;
    }
    busy = true;
    messageKey = '';
    render();
    try {
      await request(
        '/api/recycle-bin/' + item.kind + '/' + item.id + '/restore/',
        {
          method: 'POST',
        },
      );
      messageKey = 'saved';
    } catch (error) {
      messageKey =
        error.status === 409 && item.kind === 'attachment'
          ? 'categoryInUse'
          : error.status === 400 && item.kind === 'cover'
            ? 'coverConflict'
            : 'failed';
    } finally {
      busy = false;
      await load();
    }
  }
  async function removeCurrentPhoto(item) {
    if (
      busy
      ||
      !window.confirm(getText('confirmCurrentPhoto').replace(
        '{plate}',
        item.plate_number,
      ))
    ) {
      return;
    }
    busy = true;
    messageKey = '';
    render();
    try {
      await request(
        '/api/vehicles/' + item.vehicle_id + '/cover/',
        {
          method: 'DELETE',
        },
      );
      messageKey = 'currentPhotoRemoved';
    } catch (_) {
      messageKey = 'failed';
    } finally {
      busy = false;
      await load();
    }
  }
  function translate() {
    document.title = 'H SPACE | ' + getText('trashTitle');
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      el.textContent = getText(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-aria]').forEach((el) => {
      el.setAttribute(
        'aria-label',
        getText(el.dataset.i18nAria),
      );
    });
    render();
  }
  getElement('refresh-trash').addEventListener(
    'click',
    () => {
      messageKey = '';
      load();
    },
  );
  getElement('older-activity').addEventListener(
    'click',
    () => load(true),
  );
  window.addEventListener(
    'hspace:language',
    translate,
  );
  window.addEventListener(
    'pageshow',
    (event) => {
      if (event.persisted) {
        load();
      }
    },
  );
  translate();
  load();
})();
