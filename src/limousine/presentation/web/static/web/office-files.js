/* Shared office originals; server owns authorization, validation and retention. */
(() => {
  const getElement = (id) => document.getElementById(id),
    root = document.documentElement;
  const copy = {
    en: {
      title: 'Office files',
      description: 'Shared office documents and photos, separate from vehicle records.',
      skip: 'Skip to content',
      refresh: 'Refresh',
      photos: 'Photos',
      files: 'Files',
      zipphotos: 'Download photos (ZIP)',
      zipfiles: 'Download files (ZIP)',
      addphotos: 'Add photos',
      addfiles: 'Add files',
      hintphotos: 'JPG, PNG or WebP · Up to 10 MB and 25 MP per photo',
      hintfiles: 'PDF, TXT, DOCX or XLSX · Up to 10 MB per file',
      emptyphotos: 'No office photos yet. Add your first photo.',
      emptyfiles: 'No office files yet. Add your first document.',
      view: 'View',
      download: 'Download',
      remove: 'Delete',
      rename: 'Rename',
      renameHint: 'The file extension stays the same.',
      name: 'Name',
      cancel: 'Cancel',
      save: 'Save name',
      loading: 'Loading office files…',
      uploading: 'Uploading…',
      failed: 'Could not complete the request. Refresh and try again.',
      loadFailed: 'Could not load office files. Use Refresh to try again.',
      deleted: 'Moved to Deleted items.',
      renamed: 'Name saved.',
      uploaded: 'Files added.',
      confirm: 'Move this item to Deleted items?',
      invalid: 'Choose a supported file, up to 10 MB.',
      badName: 'Enter a valid name, without path separators or reserved characters.',
      conflict: 'Someone changed this name. Cancel and reopen Rename to review the latest name.',
      navVehicles: 'Vehicles',
      navReports: 'Print data',
      navDrivers: 'Driver history',
      navOffice: 'Office files',
      navTrash: 'Deleted items',
      brandSub: 'Vehicle management',
      signOut: 'Sign out',
    },
    ar: {
      title: 'ملفات المكتب',
      description: 'صور ومستندات المكتب المشتركة، مستقلة عن ملفات السيارات.',
      skip: 'انتقل إلى المحتوى',
      refresh: 'تحديث',
      photos: 'الصور',
      files: 'الملفات',
      zipphotos: 'تنزيل الصور (ZIP)',
      zipfiles: 'تنزيل الملفات (ZIP)',
      addphotos: 'إضافة صور',
      addfiles: 'إضافة ملفات',
      hintphotos: 'JPG أو PNG أو WebP · حتى 10 MB و25 MP للصورة',
      hintfiles: 'PDF أو TXT أو DOCX أو XLSX · حتى 10 MB للملف',
      emptyphotos: 'لا توجد صور للمكتب بعد. أضف أول صورة.',
      emptyfiles: 'لا توجد ملفات للمكتب بعد. أضف أول مستند.',
      view: 'عرض',
      download: 'تنزيل',
      remove: 'حذف',
      rename: 'تغيير الاسم',
      renameHint: 'امتداد الملف يبقى كما هو.',
      name: 'الاسم',
      cancel: 'إلغاء',
      save: 'حفظ الاسم',
      loading: 'جارٍ تحميل ملفات المكتب…',
      uploading: 'جارٍ الرفع…',
      failed: 'تعذّر إكمال الطلب. حدّث وحاول مجددًا.',
      loadFailed: 'تعذّر تحميل ملفات المكتب. اضغط تحديث للمحاولة مجددًا.',
      deleted: 'نُقل إلى المحذوفات. يستطيع الأدمن استرجاعه.',
      renamed: 'تم حفظ الاسم.',
      uploaded: 'تمت إضافة الملفات.',
      confirm: 'نقل هذا العنصر إلى المحذوفات؟',
      invalid: 'اختر ملفًا من الأنواع المسموحة بحجم لا يتجاوز 10 MB.',
      badName: 'أدخل اسمًا صالحًا دون فواصل مسارات أو رموز محجوزة.',
      conflict: 'غيّر مستخدم آخر الاسم. ألغِ وأعد فتح تغيير الاسم لمراجعة الاسم الأحدث.',
      navVehicles: 'السيارات',
      navReports: 'طباعة البيانات',
      navDrivers: 'سجل الشوفيرين',
      navOffice: 'ملفات المكتب',
      navTrash: 'المحذوفات',
      brandSub: 'إدارة السيارات',
      signOut: 'تسجيل الخروج',
    },
  };
  let items = [],
    busy = false,
    loaded = false,
    message = '',
    renameItem = null,
    returnId = '',
    renameBusy = false;
  const getText = (key) => copy[root.lang === 'ar' ? 'ar' : 'en'][key] || key;
  function node(tag, text = '', cls = '') {
    const el = document.createElement(tag);
    el.textContent = text;
    el.className = cls;
    return el;
  }
  function icon(name) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    el.classList.add('icon');
    el.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS(el.namespaceURI, 'use');
    use.setAttribute('href', '#' + name);
    el.append(use);
    return el;
  }
  async function request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      credentials: 'same-origin',
      cache: 'no-store',
      headers: {
        'X-CSRFToken': getElement('csrf-token').value,
        ...options.headers,
      },
    });
    if (response.status === 401) {
      location.assign('/login/');
      throw new Error('Sign in');
    }
    if (!response.ok) {
      const error = new Error();
      error.status = response.status;
      throw error;
    }
    return response.status === 204 ? null : response.json();
  }
  function focus(id) {
    const el = getElement(id);
    if (el && !el.disabled) {
      el.focus({
        preventScroll: true,
      });
    }
  }
  function render() {
    getElement('office-sections').setAttribute('aria-busy', String(busy));
    getElement('office-refresh').disabled = busy;
    getElement('office-message').textContent = message ? getText(message) : '';
    getElement('office-message').setAttribute(
      'role',
      ['failed', 'loadFailed', 'invalid'].includes(message) ? 'alert' : 'status',
    );
    for (const section of ['photos', 'files']) {
      const rows = items.filter((item) => item.kind === (section === 'photos' ? 'image' : 'file'));
      getElement('office-add-' + section).disabled = busy || !loaded;
      const zip = getElement('office-' + section + '-zip'),
        disabled = busy || !loaded || !rows.length;
      zip.setAttribute('aria-disabled', String(disabled));
      zip.tabIndex = disabled ? -1 : 0;
      if (disabled) {
        zip.removeAttribute('href');
      } else {
        zip.href = '/api/office/attachments/archive/' + section + '/';
      }
      const list = getElement('office-' + section + '-list');
      list.replaceChildren(
        ...rows.map((item) => {
          const row = node('article', '', 'file-row'),
            info = node('div', '', 'file-info'),
            nameGroup = node('div', '', 'attachment-name');
          const title = node('span', item.name);
          title.dir = 'auto';
          nameGroup.append(title);
          const rename = node('button', '', 'icon-button');
          rename.type = 'button';
          rename.id = 'office-rename-' + item.id;
          rename.disabled = busy;
          rename.title = getText('rename');
          rename.setAttribute('aria-label', getText('rename') + ': ' + item.name);
          rename.append(icon('pencil'));
          rename.addEventListener('click', () => openRename(item, rename.id));
          nameGroup.append(rename);
          const detail = node('div');
          detail.append(nameGroup);
          if (window.HSpaceCategories) {
            detail.append(HSpaceCategories.createButton(item));
          }
          const meta = node(
            'p',
            new Intl.NumberFormat(root.lang).format(Math.ceil(item.size / 1024)) +
              ' KB · ' +
              new Intl.DateTimeFormat(root.lang === 'ar' ? 'ar-JO' : 'en-GB', {
                dateStyle: 'medium',
                timeZone: 'Asia/Amman',
              }).format(new Date(item.uploaded_at)),
            'muted',
          );
          meta.dir = 'auto';
          detail.append(meta);
          if (item.kind === 'image') {
            const link = node('a', '', 'photo-link');
            link.href = item.preview_url;
            link.target = '_blank';
            link.rel = 'noopener';
            link.setAttribute('aria-label', getText('view') + ': ' + item.name);
            const img = node('img');
            img.src = item.preview_url;
            img.alt = '';
            img.width = 64;
            img.height = 48;
            img.loading = 'lazy';
            link.append(img);
            info.append(link);
          } else {
            info.append(icon('file'));
          }
          info.append(detail);
          const actions = node('div', '', 'file-actions');
          const view = node('a', getText('view'), 'button secondary');
          view.href = item.preview_url;
          view.target = '_blank';
          view.rel = 'noopener';
          view.setAttribute('aria-label', getText('view') + ': ' + item.name);
          const download = node('a', '', 'icon-button');
          download.href = item.download_url;
          download.download = '';
          download.target = '_blank';
          download.rel = 'noopener';
          download.title = getText('download');
          download.setAttribute('aria-label', getText('download') + ': ' + item.name);
          download.append(icon('download'));
          const remove = node('button', '', 'icon-button danger');
          remove.type = 'button';
          remove.id = 'office-delete-' + item.id;
          remove.disabled = busy;
          remove.title = getText('remove');
          remove.setAttribute('aria-label', getText('remove') + ': ' + item.name);
          remove.append(icon('trash'));
          remove.addEventListener('click', () => deleteItem(item, section));
          actions.append(view, download, remove);
          row.append(info, actions);
          return row;
        }),
      );
      if (!rows.length) {
        list.append(
          node(
            'p',
            getText(!loaded ? (busy ? 'loading' : 'loadFailed') : 'empty' + section),
            'section-empty',
          ),
        );
      }
    }
  }
  async function refresh() {
    if (busy) {
      return;
    }
    busy = true;
    render();
    try {
      items = (await request('/api/office/attachments/')).attachments;
      loaded = true;
    } catch (_) {
      message = 'loadFailed';
    } finally {
      busy = false;
      render();
    }
  }
  async function upload(section, files) {
    if (busy || !files.length) {
      return;
    }
    const allowed = section === 'photos' ? /\.(jpe?g|png|webp)$/i : /\.(pdf|txt|docx|xlsx)$/i;
    if (files.some((file) => !allowed.test(file.name) || file.size > 10485760 || file.size === 0)) {
      message = 'invalid';
      render();
      return;
    }
    busy = true;
    message = 'uploading';
    render();
    const categoryId = window.HSpaceCategories?.selectedFor('office-' + section + '-input');
    try {
      for (const file of files) {
        const data = new FormData();
        data.append('file', file);
        if (categoryId) {
          data.append('category_id', categoryId);
        }
        const result = await request('/api/office/attachments/', {
          method: 'POST',
          body: data,
        });
        items.push(result.attachment);
        render();
      }
      message = 'uploaded';
    } catch (_) {
      message = 'failed';
    } finally {
      busy = false;
      render();
      focus('office-add-' + section);
    }
  }
  async function deleteItem(item, section) {
    if (busy || !confirm(getText('confirm') + '\n' + item.name)) {
      return;
    }
    busy = true;
    message = '';
    render();
    try {
      await request(item.manage_url, {
        method: 'DELETE',
      });
      items = items.filter((value) => value.id !== item.id);
      message = 'deleted';
    } catch (_) {
      message = 'failed';
    } finally {
      busy = false;
      render();
      focus('office-add-' + section);
    }
  }
  function openRename(item, id) {
    if (busy) {
      return;
    }
    renameItem = item;
    returnId = id;
    const dot = item.name.lastIndexOf('.'),
      extension = dot >= 0 ? item.name.slice(dot) : '';
    getElement('office-rename-name').value = extension
      ? item.name.slice(0, -extension.length)
      : item.name;
    getElement('office-rename-name').maxLength = 180 - extension.length;
    getElement('office-rename-extension').textContent = extension;
    getElement('office-rename-error').textContent = '';
    getElement('office-rename-name').removeAttribute('aria-invalid');
    getElement('office-rename-dialog').showModal();
    getElement('office-rename-name').focus();
    getElement('office-rename-name').select();
  }
  function closeRename() {
    if (renameBusy) {
      return;
    }
    getElement('office-rename-dialog').close();
    renameItem = null;
    focus(returnId);
  }
  getElement('office-rename-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (busy || !renameItem) {
      return;
    }
    busy = renameBusy = true;
    render();
    for (const id of ['office-rename-save', 'office-rename-cancel', 'office-rename-name'])
      getElement(id).disabled = true;
    try {
      const result = await request(renameItem.manage_url, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: getElement('office-rename-name').value,
          expected_name: renameItem.name,
        }),
      });
      items = items.map((item) => (item.id === result.attachment.id ? result.attachment : item));
      message = 'renamed';
      renameBusy = false;
      closeRename();
    } catch (error) {
      getElement('office-rename-error').textContent = getText(
        error.status === 409 ? 'conflict' : error.status === 400 ? 'badName' : 'failed',
      );
      getElement('office-rename-name').setAttribute('aria-invalid', 'true');
      if (error.status === 409) {
        try {
          items = (await request('/api/office/attachments/')).attachments;
        } catch (_) {
          /* Keep draft and error visible. */
        }
      }
    } finally {
      busy = renameBusy = false;
      for (const id of ['office-rename-save', 'office-rename-cancel', 'office-rename-name'])
        getElement(id).disabled = false;
      render();
      if (getElement('office-rename-dialog').open) {
        getElement('office-rename-name').focus();
      } else {
        focus(returnId);
      }
    }
  });
  getElement('office-rename-cancel').addEventListener('click', closeRename);
  getElement('office-rename-dialog').addEventListener('cancel', (event) => {
    event.preventDefault();
    closeRename();
  });
  for (const section of ['photos', 'files']) {
    getElement('office-add-' + section).addEventListener('click', () => {
      if (!busy) {
        getElement('office-' + section + '-input').click();
      }
    });
    getElement('office-' + section + '-input').addEventListener('change', (event) => {
      const files = Array.from(event.target.files);
      event.target.value = '';
      upload(section, files);
    });
    getElement('office-' + section + '-zip').addEventListener('click', (event) => {
      if (busy || event.currentTarget.getAttribute('aria-disabled') === 'true') {
        event.preventDefault();
      }
    });
  }
  getElement('office-refresh').addEventListener('click', () => {
    message = '';
    refresh();
  });
  function translate() {
    document.title = 'H SPACE | ' + getText('title');
    document.querySelectorAll('[data-office-i18n],[data-i18n]').forEach((el) => {
      const key = el.dataset.officeI18n || el.dataset.i18n;
      if (copy.en[key]) {
        el.textContent = getText(key);
      }
    });
    document
      .querySelectorAll('[data-i18n-aria]')
      .forEach((el) => el.setAttribute('aria-label', getText(el.dataset.i18nAria)));
    render();
  }
  window.addEventListener('hspace:language', translate);
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
      refresh();
    }
  });
  translate();
  refresh();
})();
