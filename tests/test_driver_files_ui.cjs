const assert = require('node:assert/strict'),
  fs = require('node:fs'),
  path = require('node:path'),
  vm = require('node:vm');
const tick = () => new Promise((resolve) => setImmediate(resolve));
async function main() {
  const nodes = new Map(),
    events = {},
    windowEvents = {},
    calls = [],
    emitted = [];
  let redirected = '',
    fail = false,
    nextId = 20,
    hold = null;
  class Node {
    constructor(tag = 'div') {
      this.tagName = tag;
      this.children = [];
      this.handlers = {};
      this.dataset = {};
      this.attributes = {};
      this.value = '';
      this.className = '';
      this._text = '';
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
    setAttribute(
      name,
      value,
    ) {
      this.attributes[name] = value;
      if (name === 'class') {
        this.className = value;
      }
    }
    addEventListener(
      name,
      fn,
    ) {
      this.handlers[name] = fn;
    }
    focus() {
      document.activeElement = this;
    }
    showModal() {
      this.open = true;
    }
    close() {
      this.open = false;
      this.handlers.close?.();
    }
    click() {
      return this.handlers.click?.();
    }
  }
  for (const id of [
    'csrf-token',
    'driver-files-title',
    'driver-files-status',
    'driver-files-add',
    'driver-files-refresh',
    'driver-files-close',
    'driver-files-list',
    'driver-files-empty',
    'driver-files-input',
    'driver-files-dialog',
    'driver-files-name',
  ])
    nodes.set(
      id,
      new Node(),
    );
  const all = () =>
    [...nodes.values()].flatMap(function descend(node) {
      return [node, ...node.children.flatMap(descend)];
    });
  const document = {
    documentElement: { lang: 'en' },
    getElementById: (id) => nodes.get(id),
    createElement: (tag) => new Node(tag),
    createElementNS: (
      _,
      tag,
    ) => new Node(tag),
    querySelectorAll: (selector) =>
      selector.startsWith('.')
        ? all().filter((node) => node.className.split(' ').includes(selector.slice(1)))
        : [],
    addEventListener: (
      name,
      fn,
    ) => {
      events[name] = fn;
    },
    dispatchEvent: (event) => {
      emitted.push(event);
      events[event.type]?.(event);
    },
  };
  nodes.get('csrf-token').value = 'csrf';
  const record = (
    id,
    assignmentId,
    name,
    kind = 'image',
  ) => ({
    id,
    name,
    kind,
    size: 123,
    preview_url: `/api/vehicles/1/drivers/${assignmentId}/attachments/${id}/preview/`,
    download_url: `/api/vehicles/1/drivers/${assignmentId}/attachments/${id}/download/`,
  });
  const data = new Map([
    [5, [record(
      11,
      5,
      'هوية.png',
    )]],
    [6, [record(
      12,
      6,
      'old.txt',
      'file',
    )]],
  ]);
  const context = {
    document,
    location: {
      hash: '#vehicle/1',
      assign: (url) => {
        redirected = url;
      },
    },
    window: {
      confirm: () => true,
      addEventListener: (
        name,
        fn,
      ) => {
        windowEvents[name] = fn;
      },
    },
    CustomEvent: class {
      constructor(
        type,
        options,
      ) {
        this.type = type;
        this.detail = options.detail;
      }
    },
    FormData: class {
      append(
        _,
        file,
      ) {
        this.file = file;
      }
    },
    fetch: async (
      url,
      options,
    ) => {
      calls.push([url, options]);
      if (hold) {
        await hold;
      }
      if (fail) {
        return { status: 503, ok: false };
      }
      const period = Number(url.match(/drivers\/(\d+)/)[1]),
        fileId = Number(url.match(/attachments\/(\d+)/)?.[1]);
      if (options.method === 'POST') {
        const file = record(
          ++nextId,
          period,
          options.body.file.name,
          'file',
        );
        data.get(period).push(file);
        return { ok: true, status: 201, json: async () => ({ attachment: file }) };
      }
      if (options.method === 'DELETE') {
        data.set(
          period,
          data.get(period).filter((file) => file.id !== fileId),
        );
        return { ok: true, status: 204 };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ attachments: JSON.parse(JSON.stringify(data.get(period))) }),
      };
    },
  };
  vm.runInNewContext(
    fs.readFileSync(
      path.join(
        __dirname,
        '../src/limousine/presentation/web/static/web/driver-files.js',
      ),
      'utf8',
    ),
    context,
  );
  const get = (id) => nodes.get(id),
    open = async (
      id,
      current = true,
    ) => {
      events['hspace:open-driver-files']({
        detail: {
          vehicleId: 1,
          assignment: { id, driver_name: id === 5 ? 'Current' : 'Previous', is_current: current },
        },
      });
      await tick();
    };
  await open(5);
  assert.ok(get('driver-files-dialog').open);
  assert.equal(
    get('driver-files-list').children.length,
    1,
  );
  let row = get('driver-files-list').children[0];
  assert.equal(
    row.children[0].children[0].width,
    64,
  );
  assert.equal(
    row.children[1].children[0].textContent,
    'هوية.png',
  );
  assert.equal(
    row.children[2].children[0].href,
    data.get(5)[0].preview_url,
  );
  row.children[1].children[0].children[1].handlers.click();
  assert.ok(
    emitted.some(
      (event) =>
        event.type === 'hspace:rename-driver-file' &&
        event.detail.assignmentId === 5 &&
        event.detail.file.id === 11,
    ),
  );
  events['hspace:driver-file-renamed']({
    detail: { assignmentId: 5, attachment: { ...data.get(5)[0], name: 'New.png' } },
  });
  assert.equal(
    get('driver-files-list').children[0].children[1].children[0].textContent,
    'New.png',
  );
  get('driver-files-input').files = [{ name: 'licence.pdf', size: 25 * 1024 * 1024 }];
  await get('driver-files-input').handlers.change();
  assert.equal(
    get('driver-files-list').children.length,
    2,
  );
  assert.equal(
    get('driver-files-input').value,
    '',
  );
  assert.equal(
    calls.find(([, options]) => options.method === 'POST')[1].headers['X-CSRFToken'],
    'csrf',
  );
  assert.ok(
    emitted.some(
      (event) => event.type === 'hspace:driver-files-changed' && event.detail.count === 2,
    ),
  );
  row = get('driver-files-list').children[1];
  await row.children[2].children[2].handlers.click();
  assert.equal(
    get('driver-files-list').children.length,
    1,
  );
  get('driver-files-close').handlers.click();
  await open(
    6,
    false,
  );
  assert.equal(
    get('driver-files-name').textContent,
    'Previous',
  );
  assert.equal(
    get('driver-files-list').children[0].children[1].children[0].textContent,
    'old.txt',
  );
  get('driver-files-input').files = [{ name: 'licence.pdf', size: 25 * 1024 * 1024 + 1 }];
  const before = calls.length;
  await get('driver-files-input').handlers.change();
  assert.equal(
    calls.length,
    before,
  );
  context.document.documentElement.lang = 'ar';
  windowEvents['hspace:language']();
  assert.match(
    get('driver-files-status').textContent,
    /ميجابايت/,
  );
  let release;
  hold = new Promise((resolve) => {
    release = resolve;
  });
  get('driver-files-refresh').handlers.click();
  windowEvents.hashchange();
  release();
  hold = null;
  await tick();
  assert.equal(
    get('driver-files-list').children.length,
    0,
  );
  fail = true;
  await open(5);
  assert.ok(get('driver-files-add').disabled);
  assert.equal(
    get('driver-files-list').children.length,
    0,
  );
  assert.equal(
    redirected,
    '',
  );
  console.log(
    'Driver attachment dialog passed: period isolation, retained historical access, preview/download, upload/CSRF, delete/count, rename event, size limits, Arabic, stale-response masking and failure gating.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
