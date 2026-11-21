// The batch flow chooses categories and saves one original-file ZIP, with no printing.
const assert = require('node:assert/strict'),
  fs = require('node:fs'),
  path = require('node:path'),
  vm = require('node:vm');
async function main() {
  const nodes = new Map(),
    events = {},
    requests = [],
    downloads = [];
  class Node {
    constructor(tag = 'div') {
      this.tagName = tag;
      this.children = [];
      this.handlers = {};
      this.dataset = {};
    }
    append(...items) {
      this.children.push(...items);
    }
    replaceChildren(...items) {
      this.children = items;
    }
    addEventListener(name, fn) {
      this.handlers[name] = fn;
    }
    setAttribute(name, value) {
      this[name] = value;
    }
    querySelectorAll(selector) {
      const inputs = this.children.flatMap((child) =>
        child.children.filter((item) => item.tagName === 'input'),
      );
      return selector === 'input:checked' ? inputs.filter((item) => item.checked) : inputs;
    }
    click() {
      downloads.push({ href: this.href, name: this.download });
    }
    remove() {}
  }
  for (const id of [
    'download-availability',
    'availability-status',
    'availability-refresh',
    'availability-head',
    'availability-body',
    'download-types',
    'download-selected',
    'download-status',
    'download-scope',
    'attachment-download-form',
    'csrf-token',
  ])
    nodes.set(id, new Node());
  const get = (id) => nodes.get(id);
  get('csrf-token').value = 'signed-csrf';
  const document = {
    documentElement: { lang: 'ar', dir: 'rtl' },
    body: new Node('body'),
    getElementById: get,
    createElement: (tag) => new Node(tag),
    querySelectorAll: () => [],
  };
  let status = 200,
    blobCalls = 0;
  class BrowserURL extends URL {}
  BrowserURL.createObjectURL = () => {
    blobCalls++;
    return 'blob:local-archive';
  };
  BrowserURL.revokeObjectURL = () => {};
  const context = {
    document,
    window: { addEventListener: (name, fn) => (events[name] = fn) },
    location: { hash: '#results?vehicle_type=Camry', assign: () => {} },
    URL: BrowserURL,
    URLSearchParams,
    setTimeout: () => 0,
    fetch: async (url, options = {}) => {
      requests.push({ url, options });
      const payload = url.includes('/availability/')
        ? {
            vehicles: [
              { id: 10, plate_number: '050-001', documents: [{ category_id: 1, count: 2 }] },
              { id: 12, plate_number: '050-002', documents: [{ category_id: 1, count: 0 }] },
            ],
            file_count: 2,
          }
        : url.includes('attachment-categories')
          ? {
              categories: [
                { id: 1, name: 'License', code: 'vehicle_license' },
                { id: 2, name: 'Other', code: 'other' },
              ],
            }
          : {
              vehicles: [
                { id: 10, vehicle_type: 'Camry' },
                { id: 12, vehicle_type: 'Camry' },
                { id: 11, vehicle_type: 'Accord' },
              ],
            };
      return {
        ok: status === 200,
        status,
        json: async () => payload,
        blob: async () => ({ type: 'application/zip' }),
        headers: { get: (key) => (key === 'X-HSpace-File-Count' ? '4' : '1') },
      };
    },
  };
  const folder = path.join(__dirname, '../src/limousine/presentation/web/static/web');
  vm.runInNewContext(
    ['search.js', 'vehicle-filters.js', 'attachment-download.js']
      .map((file) => fs.readFileSync(path.join(folder, file), 'utf8'))
      .join('\n'),
    context,
  );
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(get('download-selected').disabled, true);
  const license = get('download-types').querySelectorAll('input')[0];
  license.checked = true;
  await license.handlers.change();
  assert.equal(get('download-selected').disabled, false);
  assert.equal(get('availability-body').children.length, 2);
  assert.equal(get('availability-body').children[0].children[0].children[0].dir, 'ltr');
  assert.equal(get('availability-body').children[0].children[0].children[0].textContent, '050-001');
  assert.equal(get('download-types').children[0].children[1].textContent, 'رخصة السيارة');
  await get('attachment-download-form').handlers.submit({ preventDefault() {} });
  const request = requests.find((item) => item.url === '/api/attachment-download/');
  assert.deepEqual(JSON.parse(request.options.body), { vehicle_ids: [10, 12], category_ids: [1] });
  assert.equal(request.options.headers['X-CSRFToken'], 'signed-csrf');
  assert.deepEqual(downloads, [{ href: 'blob:local-archive', name: 'HSPACE-attachments.zip' }]);
  assert.equal(blobCalls, 1);
  assert.match(get('download-status').textContent, /_missing-documents.txt/);
  document.documentElement.lang = 'en';
  events['hspace:language']();
  assert.equal(get('download-types').children[0].children[1].textContent, 'Vehicle license');
  assert.equal(get('download-types').querySelectorAll('input:checked').length, 1);
  status = 404;
  await get('attachment-download-form').handlers.submit({ preventDefault() {} });
  assert.equal(downloads.length, 1);
  assert.match(get('download-status').textContent, /No matching attachments/);
  status = 500;
  await get('attachment-download-form').handlers.submit({ preventDefault() {} });
  assert.equal(downloads.length, 1);
  assert.match(get('download-status').textContent, /Could not download/);
  console.log(
    'Category download UI passed: type selection, filtered vehicles, CSRF, one ZIP save, Arabic/English and empty/failure gating.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
