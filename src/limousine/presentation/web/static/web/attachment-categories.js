/* Categories for vehicle and driver attachments, including driver uploads. */
(() => {
  const root = document.documentElement;
  const strings = {
    en: {
      category: 'Category',
      categoryInUse:
        'This vehicle already has an attachment in this category, in Photos or Files. Choose another type or delete the existing attachment first.',
      other: 'Other',
      vehicle_license: 'Vehicle license',
      direction_card: 'Direction card',
      customs_declaration: 'Customs declaration',
      save: 'Save category',
      cancel: 'Cancel',
      failed: 'Could not load or save categories. Try again.',
      loading: 'Loading categories…',
      description: 'Choose the document type. Use Other to add a permanent option.',
      newName: 'New document type',
      newHint: 'Enter a name and save. It becomes available for all vehicles; Other stays last.',
      similar:
        'A similar name exists. Choose it above, or confirm this is a different document type.',
      distinct: 'This is a different document type.',
    },
    ar: {
      category: 'التصنيف',
      categoryInUse:
        'هاي السيارة فيها مرفق بنفس التصنيف بالصور أو الملفات. اختار تصنيف ثاني أو احذف المرفق الموجود أولًا.',
      other: 'أخرى',
      vehicle_license: 'رخصة السيارة',
      direction_card: 'كرت الاتجاه',
      customs_declaration: 'البيان الجمركي',
      save: 'حفظ التصنيف',
      cancel: 'إلغاء',
      failed: 'تعذّر تحميل التصنيفات أو حفظها. حاول مجددًا.',
      loading: 'جارٍ تحميل التصنيفات…',
      description: 'اختار نوع المرفق. «أخرى» بتسمح تضيف نوعًا دائمًا.',
      newName: 'اسم النوع الجديد',
      newHint: 'اكتب الاسم واحفظه، بصير خيارًا لكل السيارات وبتضل «أخرى» آخر القائمة.',
      similar: 'في اسم مشابه موجود. اختاره من القائمة أو أكّد إنه نوع مختلف.',
      distinct: 'هذا نوع مرفق مختلف.',
    },
  };
  const text = (key) => strings[root.lang === 'ar' ? 'ar' : 'en'][key] || key;
  const element = (tag, value = '', className = '') => {
    const node = document.createElement(tag);
    node.textContent = value;
    node.className = className;
    return node;
  };
  let categories = [],
    redirects = {},
    pending = null,
    selectedItem = null,
    uploadTarget = null,
    previousUploadCategory = '',
    returnButton = null,
    saving = false;
  const buttons = new Set(),
    uploadSelects = [];
  const dialog = element('dialog', '', 'category-dialog');
  dialog.setAttribute('aria-labelledby', 'attachment-category-title');
  const form = element('form'),
    heading = element('h2');
  heading.id = 'attachment-category-title';
  const description = element('p', '', 'muted');
  description.id = 'attachment-category-description';
  dialog.setAttribute('aria-describedby', description.id);
  const label = element('label');
  label.htmlFor = 'attachment-category-choice';
  const select = element('select');
  select.id = 'attachment-category-choice';
  const newGroup = element('div', '', 'category-new-type'),
    nameLabel = element('label'),
    newName = element('input'),
    hint = element('p', '', 'field-hint');
  newName.id = 'attachment-category-name';
  newName.type = 'text';
  newName.maxLength = 100;
  newName.dir = 'auto';
  newName.autocomplete = 'off';
  nameLabel.htmlFor = newName.id;
  hint.id = 'attachment-category-name-hint';
  newName.setAttribute('aria-describedby', hint.id);
  const distinctLabel = element('label', '', 'category-distinct-confirm'),
    distinct = element('input'),
    distinctText = element('span');
  distinct.type = 'checkbox';
  distinct.id = 'attachment-category-distinct';
  distinctLabel.append(distinct, distinctText);
  distinctLabel.hidden = true;
  newGroup.append(nameLabel, newName, hint, distinctLabel);
  newGroup.hidden = true;
  const status = element('p', '', 'form-message');
  status.setAttribute('role', 'alert');
  const actions = element('div', '', 'dialog-actions'),
    cancel = element('button', '', 'button secondary'),
    save = element('button', '', 'button primary');
  cancel.type = 'button';
  save.type = 'submit';
  actions.append(cancel, save);
  form.append(heading, description, label, select, newGroup, status, actions);
  dialog.append(form);
  document.body.append(dialog);
  function categoryLabel(category) {
    return category.code && strings.en[category.code] ? text(category.code) : category.name;
  }
  function options(control, value) {
    value = redirects[value] || value;
    control.replaceChildren(
      ...categories.map((category) => {
        const option = element('option', categoryLabel(category));
        option.value = String(category.id);
        return option;
      }),
    );
    const other = categories.find((category) => category.is_other);
    control.value = String(value || other?.id || '');
    control.lastCategory = control.value;
    control.disabled = !categories.length || saving;
  }
  function refreshLabels() {
    heading.textContent = text('category');
    label.textContent = text('category');
    description.textContent = text('description');
    nameLabel.textContent = text('newName');
    hint.textContent = text('newHint');
    distinctText.textContent = text('distinct');
    cancel.textContent = text('cancel');
    save.textContent = text('save');
    for (const button of buttons) {
      if (!button.isConnected) {
        buttons.delete(button);
        continue;
      }
      const category =
        categories.find((item) => item.id === button.categoryItem.category_id) ||
        categories.find((item) => item.is_other);
      button.textContent =
        text('category') + ': ' + (category ? categoryLabel(category) : text('other'));
      button.setAttribute('aria-label', button.textContent + ' — ' + button.categoryItem.name);
    }
    uploadSelects.forEach(({ label, select }) => {
      label.firstChild.textContent = text('category');
      options(select, select.value);
    });
    if (dialog.open) {
      options(select, select.value || selectedItem?.category_id);
      updateNewType();
    }
  }
  async function request(url, options = {}) {
    const token = document.getElementById('csrf-token')?.value || '';
    const response = await fetch(url, {
      ...options,
      credentials: 'same-origin',
      cache: 'no-store',
      headers: { 'X-CSRFToken': token, ...options.headers },
    });
    if (response.status === 401) {
      location.assign('/login/');
      throw new Error();
    }
    if (!response.ok) {
      const error = new Error(text('failed'));
      error.code = (await response.json().catch(() => ({}))).error?.code;
      throw error;
    }
    return response.json();
  }
  async function load(force = false) {
    if (pending) {
      return pending;
    }
    if (categories.length && !force) {
      return categories;
    }
    pending = request('/api/attachment-categories/')
      .then((data) => {
        categories = data.categories;
        redirects = data.redirects || {};
        for (const button of buttons)
          button.categoryItem.category_id =
            redirects[button.categoryItem.category_id] || button.categoryItem.category_id;
        refreshLabels();
        return categories;
      })
      .finally(() => {
        pending = null;
      });
    return pending;
  }
  function close(saved = false) {
    if (saving) {
      return;
    }
    if (uploadTarget && !saved) {
      uploadTarget.value = previousUploadCategory;
      uploadTarget.lastCategory = previousUploadCategory;
    }
    dialog.close();
    selectedItem = null;
    uploadTarget = null;
    if (returnButton?.isConnected) {
      returnButton.focus({ preventScroll: true });
    }
  }
  async function open(item, button, uploadControl = null) {
    selectedItem = item;
    uploadTarget = uploadControl;
    previousUploadCategory = uploadControl?.lastCategory || '';
    newName.value = '';
    distinct.checked = false;
    distinctLabel.hidden = true;
    returnButton = button;
    status.textContent = text('loading');
    dialog.showModal();
    save.disabled = true;
    try {
      await load(true);
      if (!dialog.open || selectedItem !== item) {
        return;
      }
      options(
        select,
        uploadControl ? categories.find((category) => category.is_other)?.id : item.category_id,
      );
      updateNewType();
      status.textContent = '';
      save.disabled = false;
      if (uploadControl) {
        newName.focus();
      } else {
        select.focus();
      }
    } catch (_) {
      status.textContent = text('failed');
    }
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (saving || save.disabled || (!selectedItem && !uploadTarget)) {
      return;
    }
    saving = true;
    save.disabled = cancel.disabled = true;
    select.disabled = true;
    newName.disabled = distinct.disabled = true;
    status.textContent = '';
    try {
      let categoryId = Number(select.value);
      if (
        categories.find((category) => category.id === categoryId)?.is_other &&
        newName.value.trim()
      ) {
        const created = await request('/api/attachment-categories/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newName.value.trim(), allow_similar: distinct.checked }),
        });
        categoryId = created.category.id;
        if (pending) {
          await pending;
        }
        await load(true);
        options(select, categoryId);
        updateNewType();
      }
      if (uploadTarget) {
        uploadTarget.value = String(categoryId);
        uploadTarget.lastCategory = uploadTarget.value;
        saving = false;
        close(true);
        return;
      }
      const result = await request(selectedItem.manage_url + 'category/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_id: categoryId }),
      });
      selectedItem.category_id = result.attachment.category_id;
      saving = false;
      refreshLabels();
      close(true);
    } catch (error) {
      if (error.code === 'similar_category') {
        status.textContent = text('similar');
        distinctLabel.hidden = false;
      } else {
        status.textContent = text(error.code === 'category_in_use' ? 'categoryInUse' : 'failed');
      }
    } finally {
      saving = false;
      save.disabled = cancel.disabled = false;
      select.disabled = false;
      newName.disabled = distinct.disabled = false;
    }
  });
  function updateNewType() {
    newGroup.hidden = !categories.find((category) => String(category.id) === select.value)
      ?.is_other;
  }
  select.addEventListener('change', () => {
    updateNewType();
    status.textContent = '';
    if (!newGroup.hidden) {
      newName.focus();
    }
  });
  newName.addEventListener('input', () => {
    distinct.checked = false;
    distinctLabel.hidden = true;
    status.textContent = '';
  });
  cancel.addEventListener('click', () => close());
  dialog.addEventListener('cancel', (event) => {
    event.preventDefault();
    close();
  });
  const uploadPairs = [
    ['driver-files-input', 'driver-files-add'],
  ];
  for (const [inputId, buttonId] of uploadPairs) {
    const input = document.getElementById(inputId),
      button = document.getElementById(buttonId);
    if (!input || !button) {
      continue;
    }
    const wrapper = element('div', '', 'category-upload-choice'),
      caption = element('label', text('category')),
      choice = element('select');
    choice.id = 'category-for-' + inputId;
    caption.htmlFor = choice.id;
    choice.disabled = true;
    choice.addEventListener('change', () => {
      if (categories.find((category) => String(category.id) === choice.value)?.is_other) {
        open(null, choice, choice);
      } else {
        choice.lastCategory = choice.value;
      }
    });
    wrapper.append(caption, choice);
    button.before(wrapper);
    uploadSelects.push({ label: wrapper, select: choice });
  }
  function createButton(item) {
    const button = element('button', '', 'button ghost small attachment-category');
    button.type = 'button';
    button.categoryItem = item;
    button.addEventListener('click', () => open(item, button));
    buttons.add(button);
    button.textContent =
      text('category') +
      ': ' +
      (categories.find((c) => c.id === item.category_id)
        ? categoryLabel(categories.find((c) => c.id === item.category_id))
        : text('other'));
    button.setAttribute('aria-label', button.textContent + ' : ' + item.name);
    return button;
  }
  window.HSpaceCategories = {
    createButton,
    selectedFor: (inputId) => document.getElementById('category-for-' + inputId)?.value || null,
  };
  window.addEventListener('hspace:language', refreshLabels);
  window.addEventListener('focus', () => {
    if (!saving) {
      load(true).catch(() => {});
    }
  });
  refreshLabels();
  load().catch(() => {});
})();
