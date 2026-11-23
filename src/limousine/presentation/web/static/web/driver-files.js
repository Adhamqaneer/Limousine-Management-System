/* Documents belong to one driver period, independently of the vehicle gallery. */
(() => {
  'use strict';

  const getElement = (id) => document.getElementById(id);
  const en = {
    title: 'Driver attachments',
    add: 'Add photo / file',
    close: 'Close',
    refresh: 'Refresh',
    empty: 'No attachments for this driver period.',
    loading: 'Loading…',
    failed: 'Could not load or save attachments. Try again.',
    uploading: 'Uploading…',
    saved: 'Attachments updated.',
    view: 'View',
    download: 'Download',
    rename: 'Rename',
    remove: 'Delete',
    confirm: 'Move this driver attachment to deleted items?',
    limit: 'Each file must be 10 MB or smaller.',
    invalid: 'Choose JPG, PNG, WebP, PDF, TXT, DOCX or XLSX.',
    hint: 'Identity, licence and other documents stay with this driver period, including after it ends.',
  };
  const ar = {
    title: 'مرفقات الشوفير',
    add: 'إضافة صورة / ملف',
    close: 'إغلاق',
    refresh: 'تحديث',
    empty: 'لا توجد مرفقات لفترة الشوفير هذه.',
    loading: 'جارٍ التحميل…',
    failed: 'تعذّر تحميل المرفقات أو حفظها. حاول مجددًا.',
    uploading: 'جارٍ الرفع…',
    saved: 'تم تحديث المرفقات.',
    view: 'عرض',
    download: 'تنزيل',
    rename: 'تغيير الاسم',
    remove: 'حذف',
    confirm: 'نقل مرفق الشوفير إلى المحذوفات؟ الاسترجاع للأدمن فقط.',
    limit: 'حجم كل ملف حتى 10 ميجابايت.',
    invalid: 'اختر JPG أو PNG أو WebP أو PDF أو TXT أو DOCX أو XLSX.',
    hint: 'الهوية والرخصة وباقي الأوراق تبقى مرتبطة بفترة الشوفير، حتى بعد انتهائها.',
  };
  const getText = (key) => (document.documentElement.lang === 'ar' ? ar : en)[key];
  const node = (tag, text = '', className = '') => {
    const item = document.createElement(tag);
    item.textContent = text;
    item.className = className;
    return item;
  };
  const icon = (name) => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'icon');
    svg.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', '#' + name);
    svg.append(use);
    return svg;
  };
  let target = null,
    files = [],
    busy = false,
    mutating = false,
    loaded = false,
    requestId = 0,
    status = '';
  const matches = (snapshot) =>
    target &&
    target.vehicleId === snapshot.vehicleId &&
    target.assignment.id === snapshot.assignment.id;
  const base = (snapshot) =>
    `/api/vehicles/${snapshot.vehicleId}/drivers/${snapshot.assignment.id}/attachments/`;
  async function api(url, options = {}) {
    const headers = {
      'X-CSRFToken': getElement('csrf-token').value,
    };
    if (options.body && !(options.body instanceof FormData))
      headers['Content-Type'] = 'application/json';
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'same-origin',
      cache: 'no-store',
    });
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
  function changed() {
    document.dispatchEvent(
      new CustomEvent('hspace:driver-files-changed', {
        detail: {
          vehicleId: target.vehicleId,
          assignmentId: target.assignment.id,
          count: files.length,
        },
      }),
    );
  }
  function render() {
    document.querySelectorAll('[data-driver-file-i18n]').forEach((item) => {
      item.textContent = getText(item.dataset.driverFileI18n);
    });
    getElement('driver-files-status').textContent = status ? getText(status) : '';
    getElement('driver-files-add').disabled = busy || !loaded;
    getElement('driver-files-refresh').disabled = busy;
    getElement('driver-files-close').disabled = mutating;
    getElement('driver-files-list').setAttribute('aria-busy', String(busy));
    getElement('driver-files-empty').hidden = !loaded || !!files.length;
    getElement('driver-files-list').replaceChildren(
      ...files.map((file) => {
        const row = node('div', '', 'file-row'),
          info = node('div', '', 'file-info'),
          nameLine = node('div', '', 'attachment-name');
        const name = node('bdi', file.name, 'filename');
        name.title = file.name;
        const rename = node('button', '', 'icon-button attachment-rename');
        rename.type = 'button';
        rename.disabled = busy;
        rename.dataset.attachmentId = String(file.id);
        rename.title = getText('rename') + ': ' + file.name;
        rename.setAttribute('aria-label', rename.title);
        rename.append(icon('pencil'));
        rename.addEventListener('click', () => {
          if (!busy)
            document.dispatchEvent(
              new CustomEvent('hspace:rename-driver-file', {
                detail: {
                  file,
                  vehicleId: target.vehicleId,
                  assignmentId: target.assignment.id,
                },
              }),
            );
        });
        nameLine.append(name, rename);
        if (window.HSpaceCategories) nameLine.append(HSpaceCategories.createButton(file));
        info.append(
          nameLine,
          node('span', Math.max(1, Math.ceil(file.size / 1024)) + ' KB', 'file-meta'),
        );
        const actions = node('div', '', 'file-actions');
        for (const [label, url] of [
          ['view', file.preview_url],
          ['download', file.download_url],
        ]) {
          const link = node('a', getText(label), 'button secondary small');
          link.href = url;
          link.target = '_blank';
          link.rel = 'noopener';
          link.setAttribute('aria-label', getText(label) + ': ' + file.name);
          actions.append(link);
        }
        const remove = node('button', getText('remove'), 'button ghost small danger');
        remove.type = 'button';
        remove.disabled = busy;
        remove.setAttribute('aria-label', getText('remove') + ': ' + file.name);
        remove.addEventListener('click', () => deleteFile(file));
        actions.append(remove);
        if (file.kind === 'image') {
          const preview = node('a', '', 'photo-link');
          preview.href = file.preview_url;
          preview.target = '_blank';
          preview.rel = 'noopener';
          preview.setAttribute('aria-label', getText('view') + ': ' + file.name);
          const image = document.createElement('img');
          image.src = file.preview_url;
          image.alt = '';
          image.width = 64;
          image.height = 48;
          image.loading = 'lazy';
          preview.append(image);
          row.append(preview);
        } else row.append(icon('file'));
        row.append(info, actions);
        return row;
      }),
    );
  }
  async function load() {
    if (!target || busy) return;
    const snapshot = target,
      request = ++requestId;
    busy = true;
    loaded = false;
    files = [];
    status = 'loading';
    render();
    try {
      const result = await api(base(snapshot));
      if (request !== requestId || !matches(snapshot)) return;
      files = result.attachments;
      loaded = true;
      status = '';
      changed();
    } catch (_) {
      if (request === requestId && matches(snapshot)) status = 'failed';
    } finally {
      if (request === requestId) {
        busy = false;
        render();
      }
    }
  }
  async function deleteFile(file) {
    if (busy || !target || !window.confirm(getText('confirm'))) return;
    const snapshot = target;
    busy = true;
    mutating = true;
    render();
    try {
      await api(base(snapshot) + file.id + '/', {
        method: 'DELETE',
      });
      if (matches(snapshot)) {
        files = files.filter((item) => item.id !== file.id);
        status = 'saved';
        changed();
      }
    } catch (_) {
      if (matches(snapshot)) status = 'failed';
    } finally {
      busy = false;
      mutating = false;
      render();
    }
  }
  getElement('driver-files-add').addEventListener('click', () =>
    getElement('driver-files-input').click(),
  );
  getElement('driver-files-input').addEventListener('change', async () => {
    const input = getElement('driver-files-input'),
      selected = [...input.files];
    input.value = '';
    if (busy || !target || !selected.length) return;
    if (selected.some((file) => file.size > 10 * 1024 * 1024)) {
      status = 'limit';
      render();
      return;
    }
    if (
      selected.some(
        (file) =>
          !['jpg', 'jpeg', 'png', 'webp', 'pdf', 'txt', 'docx', 'xlsx'].includes(
            file.name.split('.').pop().toLowerCase(),
          ),
      )
    ) {
      status = 'invalid';
      render();
      return;
    }
    const snapshot = target;
    busy = true;
    mutating = true;
    status = 'uploading';
    render();
    let failure = '';
    const categoryId = window.HSpaceCategories?.selectedFor(input.id);
    try {
      for (const file of selected) {
        if (!matches(snapshot)) break;
        const body = new FormData();
        body.append('file', file);
        if (categoryId) body.append('category_id', categoryId);
        const result = await api(base(snapshot), {
          method: 'POST',
          body,
        });
        if (matches(snapshot)) {
          files.push(result.attachment);
          changed();
        }
      }
    } catch (error) {
      failure = error.status === 413 ? 'limit' : error.status === 400 ? 'invalid' : 'failed';
    } finally {
      busy = false;
      mutating = false;
      if (matches(snapshot)) {
        status = failure || 'saved';
        render();
      }
    }
  });
  getElement('driver-files-refresh').addEventListener('click', load);
  getElement('driver-files-close').addEventListener('click', () => {
    if (!mutating) getElement('driver-files-dialog').close();
  });
  getElement('driver-files-dialog').addEventListener('cancel', (event) => {
    if (mutating) event.preventDefault();
  });
  getElement('driver-files-dialog').addEventListener('close', () => {
    if (getElement('driver-files-dialog').open) return;
    const previous = target;
    target = null;
    files = [];
    loaded = false;
    requestId++;
    if (!mutating) busy = false;
    if (previous && location.hash === '#vehicle/' + previous.vehicleId)
      Array.from(document.querySelectorAll('.driver-docs-button'))
        .find((button) => button.dataset.assignmentId === String(previous.assignment.id))
        ?.focus();
  });
  document.addEventListener('hspace:open-driver-files', (event) => {
    if (busy) return;
    target = {
      vehicleId: Number(event.detail.vehicleId),
      assignment: event.detail.assignment,
    };
    getElement('driver-files-name').textContent = target.assignment.driver_name;
    getElement('driver-files-dialog').showModal();
    load();
  });
  document.addEventListener('hspace:driver-file-renamed', (event) => {
    if (!target || target.assignment.id !== event.detail.assignmentId) return;
    if (event.detail.attachment) {
      files = files.map((file) =>
        file.id === event.detail.attachment.id ? event.detail.attachment : file,
      );
      render();
    } else load();
  });
  window.addEventListener('hspace:language', render);
  window.addEventListener('hashchange', () => {
    getElement('driver-files-dialog').close();
  });
  render();
})();
