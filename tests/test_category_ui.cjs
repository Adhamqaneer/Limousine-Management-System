// Shared labels must reach upload pickers and scoped classification requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

async function main() {
  const nodes = new Map(),
    events = {},
    requests = [];
  class Node {
    constructor(tag = 'div') {
      this.tagName = tag;
      this.children = [];
      this.handlers = {};
      this.isConnected = true;
      this.textContent = '';
    }
    set id(value) {
      this._id = value;
      nodes.set(value, this);
    }
    get id() {
      return this._id;
    }
    get firstChild() {
      return this.children[0];
    }
    append(...items) {
      this.children.push(...items);
    }
    before(item) {
      this.beforeNode = item;
    }
    replaceChildren(...items) {
      this.children = items;
    }
    setAttribute(name, value) {
      this[name] = value;
    }
    addEventListener(name, handler) {
      this.handlers[name] = handler;
    }
    querySelector(tag) {
      return this.children.find((item) => item.tagName === tag);
    }
    cloneNode() {
      const result = new Node(this.tagName);
      Object.assign(result, { href: this.href, target: this.target, rel: this.rel });
      return result;
    }
    showModal() {
      this.open = true;
    }
    close() {
      this.open = false;
    }
    focus() {
      this.focused = true;
    }
  }
  for (const id of [
    'photo-input',
    'add-photos',
    'file-input',
    'add-files',
    'office-photos-input',
    'office-add-photos',
    'office-files-input',
    'office-add-files',
    'driver-files-input',
    'driver-files-add',
    'csrf-token',
  ]) {
    const node = new Node();
    node.id = id;
  }
  nodes.get('csrf-token').value = 'csrf';
  const body = new Node('body'),
    root = { lang: 'ar' };
  let fail = false,
    added = false,
    conflict = false;
  const context = {
    document: {
      documentElement: root,
      body,
      createElement: (tag) => new Node(tag),
      getElementById: (id) => nodes.get(id),
    },
    location: { assign: () => {} },
    Event: class {
      constructor(type) {
        this.type = type;
      }
    },
    CustomEvent: class {
      constructor(type, options) {
        this.type = type;
        this.detail = options.detail;
      }
    },
    window: {
      addEventListener: (name, handler) => (events[name] = handler),
      dispatchEvent: () => {},
    },
    fetch: async (url, options = {}) => {
      requests.push({ url, options });
      if (fail) return { status: 500, ok: false };
      if (conflict && options.method === 'PATCH')
        return {
          status: 409,
          ok: false,
          json: async () => ({ error: { code: 'category_in_use' } }),
        };
      if (options.method === 'POST') {
        added = true;
        return {
          status: 200,
          ok: true,
          json: async () => ({ category: { id: 8, name: 'Insurance' } }),
        };
      }
      return {
        status: 200,
        ok: true,
        json: async () =>
          options.method === 'PATCH'
            ? { attachment: { category_id: JSON.parse(options.body).category_id } }
            : {
                categories: [
                  { id: 1, name: 'رخصة السيارة', code: 'vehicle_license' },
                  ...(added ? [{ id: 8, name: 'Insurance' }] : []),
                  { id: 99, name: 'أخرى', code: 'other', is_other: true },
                ],
                redirects: { 5: 1 },
              },
      };
    },
  };
  context.HSpaceCategories = undefined;
  vm.runInNewContext(
    fs.readFileSync(
      path.join(__dirname, '../src/limousine/presentation/web/static/web/attachment-categories.js'),
      'utf8',
    ),
    context,
  );
  context.HSpaceCategories = context.window.HSpaceCategories;
  const item = {
    id: 7,
    name: 'License.png',
    category_id: 5,
    manage_url: '/api/vehicles/10/attachments/7/',
  };
  const button = context.HSpaceCategories.createButton(item);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(item.category_id, 1);
  assert.match(button.textContent, /رخصة السيارة/);
  for (const [inputId, buttonId] of [
    ['photo-input', 'add-photos'],
    ['file-input', 'add-files'],
    ['office-photos-input', 'office-add-photos'],
    ['office-files-input', 'office-add-files'],
  ]) {
    assert.equal(context.HSpaceCategories.selectedFor(inputId), null);
    assert.equal(nodes.get(buttonId).beforeNode, undefined);
  }
  const choice = nodes.get('category-for-driver-files-input');
  assert.equal(choice.value, '99');
  choice.value = '1';
  assert.equal(context.HSpaceCategories.selectedFor('driver-files-input'), '1');
  assert.equal(nodes.get('driver-files-add').beforeNode.querySelector('a'), undefined);
  await button.handlers.click();
  const dialog = body.children[0],
    form = dialog.children[0],
    select = nodes.get('attachment-category-choice');
  assert.ok(dialog.open);
  assert.equal(select.value, '1');
  select.value = '99';
  await form.handlers.submit({ preventDefault() {} });
  const request = requests.find((item) => item.options.method === 'PATCH');
  assert.equal(request.url, item.manage_url + 'category/');
  assert.equal(request.options.headers['X-CSRFToken'], 'csrf');
  assert.deepEqual(JSON.parse(request.options.body), { category_id: 99 });
  assert.equal(item.category_id, 99);
  assert.equal(dialog.open, false);
  assert.ok(button.focused);
  root.lang = 'en';
  events['hspace:language']();
  assert.equal(button.textContent, 'Category: Other');
  await button.handlers.click();
  select.value = '99';
  select.handlers.change();
  assert.equal(nodes.get('attachment-category-name').disabled, false);
  nodes.get('attachment-category-name').value = 'Insurance';
  await form.handlers.submit({ preventDefault() {} });
  assert.equal(item.category_id, 8);
  assert.equal(choice.children.at(-1).value, '99');
  assert.ok(choice.children.some((option) => option.value === '8'));
  const create = requests.find((item) => item.options.method === 'POST');
  assert.deepEqual(JSON.parse(create.options.body), { name: 'Insurance', allow_similar: false });
  const previousPatches = requests.filter((item) => item.options.method === 'PATCH').length;
  choice.value = '99';
  choice.handlers.change();
  await new Promise((resolve) => setImmediate(resolve));
  nodes.get('attachment-category-name').value = 'Insurance';
  await form.handlers.submit({ preventDefault() {} });
  assert.equal(choice.value, '8');
  assert.equal(requests.filter((item) => item.options.method === 'PATCH').length, previousPatches);
  await button.handlers.click();
  select.value = '1';
  conflict = true;
  await form.handlers.submit({ preventDefault() {} });
  assert.equal(item.category_id, 8);
  assert.equal(dialog.open, true);
  assert.match(form.children.at(-2).textContent, /already has an attachment/);
  conflict = false;
  form.children.at(-1).children[0].handlers.click();
  fail = true;
  await button.handlers.click();
  assert.ok(dialog.open);
  assert.equal(form.children.at(-1).children.at(-1).disabled, true);
  console.log(
    'Category UI passed: vehicle classification, driver upload choices, no office pickers, redirects, CSRF and focus.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
