const assert = require('node:assert/strict'),
  fs = require('node:fs'),
  path = require('node:path'),
  vm = require('node:vm');
const tick = () => new Promise((resolve) => setImmediate(resolve));
async function main() {
  const nodes = new Map(),
    events = {},
    calls = [];
  let data = [],
    next = 10,
    fail = false,
    conflict = false;
  class Node {
    constructor(tag = 'div') {
      this.tagName = tag;
      this.children = [];
      this.handlers = {};
      this.dataset = {};
      this.attributes = {};
      this._text = '';
      this.value = '';
      this.className = '';
      this.classList = {
        add: (value) => {
          this.className += ' ' + value;
        },
      };
    }
    get textContent() {
      return this._text + this.children.map((child) => child.textContent).join('');
    }
    set textContent(value) {
      this._text = String(value);
      this.children = [];
    }
    append(...children) {
      this.children.push(...children);
    }
    replaceChildren(...children) {
      this.children = children;
    }
    setAttribute(name, value) {
      this.attributes[name] = String(value);
    }
    getAttribute(name) {
      return this.attributes[name];
    }
    removeAttribute(name) {
      delete this.attributes[name];
      if (name === 'href') delete this.href;
    }
    addEventListener(name, fn) {
      this.handlers[name] = fn;
    }
    focus() {
      document.activeElement = this;
    }
    select() {}
    showModal() {
      this.open = true;
    }
    close() {
      this.open = false;
    }
    click() {
      return this.handlers.click?.({ currentTarget: this, preventDefault() {} });
    }
  }
  const ids = [
    'csrf-token',
    'office-sections',
    'office-refresh',
    'office-message',
    'office-rename-dialog',
    'office-rename-form',
    'office-rename-name',
    'office-rename-extension',
    'office-rename-error',
    'office-rename-save',
    'office-rename-cancel',
  ];
  for (const section of ['photos', 'files'])
    ids.push(
      'office-add-' + section,
      'office-' + section + '-zip',
      'office-' + section + '-list',
      'office-' + section + '-input',
    );
  ids.forEach((id) => {
    const el = new Node();
    el.id = id;
    nodes.set(id, el);
  });
  const all = () =>
    [...nodes.values()].flatMap(function walk(el) {
      return [el, ...el.children.flatMap(walk)];
    });
  const document = {
    documentElement: { lang: 'en' },
    getElementById: (id) => nodes.get(id) || all().find((el) => el.id === id),
    createElement: (tag) => new Node(tag),
    createElementNS: (_, tag) => new Node(tag),
    querySelectorAll: () => [],
  };
  nodes.get('csrf-token').value = 'csrf';
  const record = (id, name, kind) => ({
    id,
    name,
    kind,
    size: 123,
    uploaded_at: '2026-01-01T12:00:00Z',
    manage_url: `/api/office/attachments/${id}/`,
    preview_url: `/api/office/attachments/${id}/preview/`,
    download_url: `/api/office/attachments/${id}/download/`,
  });
  const context = {
    document,
    Intl,
    Date,
    location: { assign() {} },
    confirm: () => true,
    window: {
      addEventListener: (name, fn) => {
        events[name] = fn;
      },
    },
    FormData: class {
      append(_, file) {
        this.file = file;
      }
    },
    fetch: async (url, options) => {
      calls.push([url, options]);
      if (fail) return { ok: false, status: 503 };
      const id = Number(url.match(/attachments\/(\d+)/)?.[1]);
      if (options.method === 'POST') {
        const file = options.body.file,
          item = record(++next, file.name, /png$/i.test(file.name) ? 'image' : 'file');
        data.push(item);
        return { ok: true, status: 201, json: async () => ({ attachment: item }) };
      }
      if (options.method === 'DELETE') {
        data = data.filter((item) => item.id !== id);
        return { ok: true, status: 204 };
      }
      if (options.method === 'PATCH') {
        if (conflict) return { ok: false, status: 409 };
        const payload = JSON.parse(options.body),
          item = data.find((item) => item.id === id);
        item.name = payload.name + item.name.slice(item.name.lastIndexOf('.'));
        return { ok: true, status: 200, json: async () => ({ attachment: { ...item } }) };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ attachments: data.map((item) => ({ ...item })) }),
      };
    },
  };
  vm.runInNewContext(
    fs.readFileSync(
      path.join(__dirname, '../src/limousine/presentation/web/static/web/office-files.js'),
      'utf8',
    ),
    context,
  );
  const get = (id) => document.getElementById(id),
    wait = async () => {
      await tick();
      await tick();
    };
  await wait();
  assert.equal(get('office-files-zip').getAttribute('aria-disabled'), 'true');
  assert.ok(!get('office-files-zip').href);
  async function upload(section, files) {
    const input = get('office-' + section + '-input');
    input.handlers.change({ target: { files, value: 'selected' } });
    await wait();
  }
  await upload('photos', [{ name: 'هوية المكتب.png', size: 100 }]);
  await upload('files', [{ name: 'office.txt', size: 100 }]);
  assert.equal(get('office-photos-list').children.length, 1);
  assert.equal(get('office-files-list').children.length, 1);
  assert.equal(get('office-photos-zip').href, '/api/office/attachments/archive/photos/');
  assert.equal(get('office-files-zip').href, '/api/office/attachments/archive/files/');
  const photoRow = get('office-photos-list').children[0];
  assert.equal(photoRow.children[0].children[0].children[0].width, 64);
  assert.equal(photoRow.children[0].children[0].href, data[0].preview_url);
  assert.equal(photoRow.children[1].children[0].href, data[0].preview_url);
  assert.equal(photoRow.children[1].children[1].href, data[0].download_url);
  get('office-rename-11').click();
  assert.ok(get('office-rename-dialog').open);
  assert.equal(get('office-rename-extension').textContent, '.png');
  get('office-rename-name').value = 'New';
  await get('office-rename-form').handlers.submit({ preventDefault() {} });
  assert.equal(data[0].name, 'New.png');
  assert.equal(document.activeElement.id, 'office-rename-11');
  const renameCall = calls.find(([, options]) => options.method === 'PATCH');
  assert.equal(renameCall[1].headers['X-CSRFToken'], 'csrf');
  assert.equal(JSON.parse(renameCall[1].body).expected_name, 'هوية المكتب.png');
  get('office-rename-11').click();
  get('office-rename-name').value = 'Draft';
  conflict = true;
  await get('office-rename-form').handlers.submit({ preventDefault() {} });
  assert.equal(get('office-rename-name').value, 'Draft');
  assert.ok(get('office-rename-error').textContent.includes('Someone changed'));
  assert.ok(get('office-rename-dialog').open);
  get('office-rename-cancel').click();
  conflict = false;
  document.documentElement.lang = 'ar';
  events['hspace:language']();
  assert.equal(get('office-photos-list').children[0].children[1].children[0].textContent, 'عرض');
  get('office-delete-11').click();
  await wait();
  assert.equal(get('office-photos-zip').getAttribute('aria-disabled'), 'true');
  assert.equal(data.length, 1);
  assert.equal(document.activeElement.id, 'office-add-photos');
  const count = calls.length;
  await upload('files', [{ name: 'bad.exe', size: 20 }]);
  assert.equal(calls.length, count);
  assert.ok(get('office-message').textContent.includes('10 MB'));
  fail = true;
  get('office-refresh').click();
  await wait();
  assert.equal(get('office-message').getAttribute('role'), 'alert');
  assert.ok(!get('office-refresh').disabled);
  console.log(
    'PASS: office empty/busy/error states, scoped upload/ZIP targets, compact preview, CSRF, fixed-extension rename/conflict/draft/focus, deletion and Arabic labels.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
