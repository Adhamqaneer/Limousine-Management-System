// Dependency-free DOM harness: loading/error states, selection, RTL, safe cells and print gating.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
async function main() {
  const nodes = new Map(),
    events = {};
  class Node {
    constructor(tag = 'div') {
      this.tagName = tag;
      this.children = [];
      this.handlers = {};
      this.dataset = {};
      this.classes = new Set();
      this.classList = {
        toggle: (name, on) => (on ? this.classes.add(name) : this.classes.delete(name)),
      };
    }
    set id(value) {
      this._id = value;
      nodes.set(value, this);
    }
    get id() {
      return this._id;
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
    showModal() {
      this.open = true;
    }
    close() {
      this.open = false;
    }
    querySelectorAll() {
      return this.children.flatMap((label) =>
        label.children.filter((node) => node.tagName === 'input'),
      );
    }
  }
  for (const id of [
    'print-style-dialog',
    'print-with-letterhead',
    'print-without-letterhead',
    'cancel-print-style',
    'report-letterhead-cell',
    'report-criteria',
    'report-scope-description',
    'print-all-vehicles',
    'selection-summary',
    'report-status',
    'report-paper',
    'print-report',
    'refresh-report',
    'report-choices',
    'report-head',
    'report-body',
    'report-count',
    'report-date',
    'select-all',
    'clear-fields',
  ]) {
    const node = new Node();
    node.id = id;
  }
  const title = new Node();
  title.dataset.i18n = 'reportTitle';
  title.textContent = 'Print vehicle data';
  const officeNav = new Node();
  officeNav.dataset.i18n = 'navOffice';
  officeNav.textContent = 'Office files';
  const doc = {
    documentElement: { lang: 'ar', dir: 'rtl' },
    getElementById: (id) => nodes.get(id),
    createElement: (tag) => new Node(tag),
    querySelectorAll: (selector) => (selector === '[data-i18n]' ? [title, officeNav] : []),
  };
  let response = {
    ok: true,
    status: 200,
    json: async () => ({
      vehicles: [
        {
          owner_name: '<script>bad()</script>',
          owner_phone: '00123',
          driver_name: '\u0623\u062d\u0645\u062f',
          driver_phone: '0079',
          vehicle_type: 'Camry',
          manufacture_year: '002024',
          chassis_number: 'JT001a',
          plate_number: '050-001',
        },
      ],
    }),
  };
  let printed = 0,
    redirected = '';
  const context = {
    document: doc,
    window: {
      addEventListener: (name, fn) => {
        events[name] = fn;
      },
      print: () => printed++,
    },
    fetch: async () => response,
    location: {
      hash: '',
      assign: (url) => {
        redirected = url;
      },
    },
    Intl,
    Date,
    URLSearchParams,
  };
  const dir = path.join(__dirname, '../src/limousine/presentation/web/static/web');
  vm.runInNewContext(
    ['vehicle-filters.js', 'search.js', 'report-data.js', 'vehicle-report.js']
      .map((file) => fs.readFileSync(path.join(dir, file), 'utf8'))
      .join('\n'),
    context,
  );
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(officeNav.textContent, 'ملفات المكتب');
  doc.documentElement.lang = 'en';
  doc.documentElement.dir = 'ltr';
  events['hspace:language']();
  assert.equal(officeNav.textContent, 'Office files');
  const get = (id) => nodes.get(id);
  assert.equal(get('report-paper').hidden, false);
  assert.equal(get('report-head').children.length, 1);
  assert.equal(get('report-letterhead-cell').colSpan, 1);
  assert.equal(get('report-body').children[0].children[0].children[0].textContent, '050-001');
  get('select-all').handlers.click();
  assert.equal(get('report-head').children.length, 8);
  assert.equal(get('report-letterhead-cell').colSpan, 8);
  assert.ok(get('report-paper').classes.has('landscape'));
  const cells = get('report-body').children[0].children;
  assert.equal(cells[0].children[0].textContent, '<script>bad()</script>');
  assert.equal(cells[0].children[0].tagName, 'bdi');
  assert.equal(cells[1].children[0].textContent, '00123');
  assert.equal(cells[6].children[0].dir, 'ltr');
  get('print-report').handlers.click();
  assert.equal(printed, 0);
  assert.ok(get('print-style-dialog').open);
  get('cancel-print-style').handlers.click();
  assert.equal(printed, 0);
  assert.equal(get('print-style-dialog').open, false);
  get('print-report').handlers.click();
  get('print-without-letterhead').handlers.click();
  assert.equal(printed, 1);
  assert.ok(get('report-paper').classes.has('preprinted-paper'));
  assert.equal(get('print-style-dialog').open, false);
  assert.equal(get('report-body').children[0].children[6].children[0].textContent, 'JT001a');
  get('print-report').handlers.click();
  get('print-with-letterhead').handlers.click();
  assert.equal(printed, 2);
  assert.equal(get('report-paper').classes.has('preprinted-paper'), false);
  get('clear-fields').handlers.click();
  assert.ok(get('print-report').disabled);
  assert.ok(get('report-paper').hidden);
  get('print-report').handlers.click();
  assert.equal(printed, 2);
  get('print-without-letterhead').handlers.click();
  assert.equal(printed, 2);
  doc.documentElement.lang = 'ar';
  doc.documentElement.dir = 'rtl';
  events['hspace:language']();
  assert.equal(officeNav.textContent, 'ملفات المكتب');
  assert.equal(
    get('label-plate_number').textContent,
    '\u0631\u0642\u0645 \u0627\u0644\u0645\u0631\u0643\u0628\u0629',
  );
  get('select-all').handlers.click();
  response = {
    ok: true,
    status: 200,
    json: async () => ({
      vehicles: [
        { owner_name: 'Adham', manufacture_year: '2022', vehicle_type: 'Camry', plate_number: '1' },
        {
          owner_name: 'Adham',
          manufacture_year: '2022',
          vehicle_type: 'Corolla',
          plate_number: '2',
        },
        { owner_name: 'Other', manufacture_year: '2023', vehicle_type: 'Camry', plate_number: '3' },
      ],
    }),
  };
  for (const [hash, count] of [
    ['#results?owner_name=Adham', 2],
    ['#results?manufacture_year=2022', 2],
    ['#results?vehicle_type=Camry', 2],
    ['#results?manufacture_year=2022&vehicle_type=Camry&q=1', 1],
  ]) {
    context.location.hash = hash;
    events.hashchange();
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(get('report-body').children.length, count);
    assert.equal(get('print-all-vehicles').hidden, false);
    assert.ok(get('report-criteria').textContent);
  }
  context.location.hash = '#results?driver_phone=123';
  events.hashchange();
  await new Promise((resolve) => setImmediate(resolve));
  assert.ok(get('print-report').disabled);
  assert.equal(get('report-body').children.length, 0);
  context.location.hash = '';
  events.hashchange();
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(get('report-body').children.length, 3);
  assert.ok(get('print-all-vehicles').hidden);
  response = { ok: false, status: 503 };
  await get('refresh-report').handlers.click();
  assert.ok(get('print-report').disabled);
  assert.equal(get('report-body').children.length, 0);
  response = { ok: true, status: 200, json: async () => ({ vehicles: [] }) };
  await get('refresh-report').handlers.click();
  assert.ok(get('print-report').disabled);
  assert.ok(get('report-paper').hidden);
  response = { ok: false, status: 401 };
  await get('refresh-report').handlers.click();
  assert.equal(redirected, '/login/');
  console.log(
    'Report UI states, eight-column selection, RTL labels, safe cells, leading zeros and print gating passed.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
