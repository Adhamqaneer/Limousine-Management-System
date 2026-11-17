/* Dependency-free workflow regressions: node tests/test_vehicle_ui.cjs */
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const staticDir = path.join(__dirname, '../src/limousine/presentation/web/static/web');
const tick = () => new Promise(resolve => setImmediate(resolve));

function page() {
  const nodes = new Map(), events = {}, windowEvents = {}, frames = new Map(), calls = [];
  let frameId = 0, mutationWait = null;
  const document = {cookie:'', addEventListener:(name, fn) => { events[name] = fn; }, dispatchEvent:event => events[event.type]?.(event)};
  class Node {
    constructor(tag = 'div') {
      this.tagName = tag; this.children = []; this.dataset = {}; this.handlers = {}; this.attributes = {};
      this.value = ''; this.className = ''; this._text = '';
      this.classList = {add:name => { this.className += ' ' + name; }};
    }
    get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
    set textContent(value) { this._text = String(value); this.replaceChildren(); }
    append(...children) { for (const child of children) { child.parentElement = this; this.children.push(child); } }
    prepend(child) { child.parentElement = this; this.children.unshift(child); }
    replaceChildren(...children) {
      if (this !== document.body && this.contains(document.activeElement)) document.activeElement = document.body;
      for (const child of this.children) child.parentElement = null;
      this.children = []; this.append(...children);
    }
    matches(selector) {
      if (selector.startsWith('.')) return this.className.split(' ').includes(selector.slice(1));
      if (selector.startsWith('[data-action=')) return this.dataset.action === selector.match(/"([^"]+)"/)[1];
      return this.tagName === selector;
    }
    closest(selector) { return this.matches(selector) ? this : this.parentElement?.closest(selector); }
    querySelectorAll(selector) { return this.children.flatMap(child => [...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector)]); }
    querySelector(selector) { return this.querySelectorAll(selector)[0]; }
    contains(node) { return !!node && (node === this || this.children.some(child => child.contains(node))); }
    addEventListener(name, fn) { this.handlers[name] = fn; }
    setAttribute(name, value) { this.attributes[name] = value; }
    getAttribute(name) { return this.attributes[name]; }
    removeAttribute(name) { delete this.attributes[name]; if (name === 'href') delete this.href; }
    setCustomValidity(value) { this.validityMessage = value; }
    reportValidity() { return true; }
    focus() { document.activeElement = this; }
    showModal() { this.open = true; }
    close() { this.open = false; }
  }
  document.body = new Node('body'); document.activeElement = document.body;
  document.documentElement = new Node('html'); document.documentElement.dataset.theme = 'dark';
  for (const name of ['home.html', '_header.html']) {
    const html = fs.readFileSync(path.join(staticDir, '../../templates/web', name), 'utf8');
    for (const match of html.matchAll(/\bid="([^"]+)"/g)) {
      const node = new Node(); node.id = match[1]; nodes.set(node.id, node); document.body.append(node);
    }
  }
  nodes.set('language-label', new Node()); nodes.set('theme-toggle', new Node()); nodes.set('language-toggle', new Node());
  const meta = new Node();
  Object.assign(document, {
    getElementById:id => nodes.get(id), createElement:tag => new Node(tag), createElementNS:(_, tag) => new Node(tag),
    createTextNode:text => { const node = new Node('#text'); node.textContent = text; return node; },
    querySelector:() => meta, querySelectorAll:selector => document.body.querySelectorAll(selector)
  });
  const vehicle = (id, plate) => ({id, plate_number:plate, vehicle_type:'Camry', owner_name:'Old Owner', owner_phone:'00123', driver_name:'Old Driver', driver_phone:'0079', chassis_number:'VIN001', manufacture_year:'2022', created_at:'2026-01-01T10:00:00Z', attachment_count:0, attachments:[]});
  const records = new Map([[1, vehicle(1, '050-001')], [2, vehicle(2, '050-002')]]);
  records.get(1).attachments = [
    {id:7,kind:'image',name:'صورة Camry.png',size:9000000,uploaded_at:'2026-01-01T10:00:00Z',preview_url:'/private/photo/7',download_url:'/private/photo/7/download'},
    {id:8,kind:'image',name:'Portrait.jpg',size:12000,uploaded_at:'2026-01-01T10:00:00Z',preview_url:'/private/photo/8',download_url:'/private/photo/8/download'}
  ];
  records.get(1).attachment_count = 2;
  const location = {hash:'#vehicles', assign:() => {}};
  const window = {location, scrollY:0, scrollTo:(_, y) => { window.scrollY = y; }, addEventListener:(name, fn) => { windowEvents[name] = fn; }, dispatchEvent:event => windowEvents[event.type]?.(event), confirm:() => true};
  const context = {document, window, location, localStorage:{getItem:() => null, setItem:() => {}}, Intl, Date,
    Headers:class {set() {}}, FormData:class {append() {}},
    Event:class {constructor(type) { this.type = type; }}, CustomEvent:class {constructor(type, options) { this.type = type; this.detail = options.detail; }},
    requestAnimationFrame:fn => { frames.set(++frameId, fn); return frameId; }, cancelAnimationFrame:id => frames.delete(id),
    fetch:async(url, options) => {
      calls.push({url, options});
      if (options.method && mutationWait) await mutationWait;
      const id = Number(url.match(/vehicles\/(\d+)/)?.[1]);
      if (options.method === 'PATCH' && url.includes('/attachments/')) {
        const attachmentId=Number(url.match(/attachments\/(\d+)/)[1]), body=JSON.parse(options.body);
        const old=records.get(id).attachments.find(file=>file.id===attachmentId), dot=old.name.lastIndexOf('.');
        if(body.expected_name!==old.name)return {ok:false,status:409,json:async()=>({error:{code:'attachment_name_conflict'}})};
        const updated={...old,name:body.name+old.name.slice(dot)};
        records.set(id,{...records.get(id),attachments:records.get(id).attachments.map(file=>file.id===attachmentId?updated:file)});
        return {ok:true,status:200,json:async()=>({attachment:JSON.parse(JSON.stringify(updated))})};
      }
      if (options.method === 'PATCH') records.set(id, {...records.get(id), ...JSON.parse(options.body)});
      if (options.method === 'DELETE') records.delete(id);
      if (url.endsWith('/cover/')) records.set(id, {...records.get(id), cover_url:'/private/photo'});
      const payload = id ? {vehicle:records.get(id)} : {vehicles:[...records.values()]};
      return {ok:true, status:200, json:async() => JSON.parse(JSON.stringify(payload))};
    }
  };
  vm.createContext(context);
  for (const name of ['search.js', 'vehicle-filters.js', 'vehicle-validation.js', 'ui-state.js', 'app.js']) vm.runInContext(fs.readFileSync(path.join(staticDir, name), 'utf8'), context);
  return {nodes, calls, records, document, window, events, windowEvents,
    pauseMutation() { let release; mutationWait = new Promise(resolve => { release = resolve; }); return () => { mutationWait = null; release(); }; },
    search(value) { nodes.get('vehicle-search').value = value; nodes.get('vehicle-search').focus(); nodes.get('vehicle-search').handlers.input(); for (const fn of frames.values()) fn(); frames.clear(); },
    async route(hash) { location.hash = hash; windowEvents.hashchange(); await tick(); },
    hasUnsaved() { let warned = false; windowEvents.beforeunload({preventDefault() { warned = true; }}); return warned; }
  };
}

async function main() {
  const p = page(), get = id => p.nodes.get(id); await tick();
  const first = get('vehicle-grid').children[0];
  p.search('٠٠١');
  assert.equal(get('vehicle-grid').children.length, 1);
  assert.equal(get('vehicle-grid').children[0], first, 'typing should retain unchanged card nodes');
  assert.equal(first.querySelector('mark').textContent, '001');
  assert.equal(first.querySelector('h2').querySelector('bdi').dir, 'ltr');
  p.window.scrollY = 320; await p.route('#vehicle/1');
  assert.equal(get('detail-plate').value, '050-001');
  assert.equal(get('download-photos').href, '/api/vehicles/1/attachments/archive/photos/');
  assert.equal(get('download-photos').attributes['aria-disabled'], 'false');
  assert.equal(get('download-files').attributes['aria-disabled'], 'true');
  assert.equal(get('download-files').href, undefined);
  assert.equal(get('detail-title').children[2].dir, 'ltr');
  assert.equal(get('photo-grid').children.length, 2);
  for (const [index, row] of get('photo-grid').children.entries()) {
    const file = p.records.get(1).attachments[index], thumbnail = row.children[0], image = thumbnail.children[0], actions = row.children[2];
    assert.equal(image.width, 64); assert.equal(image.height, 48);
    assert.equal(thumbnail.href, file.preview_url); assert.equal(thumbnail.target, '_blank');
    assert.equal(row.children[1].children[0].textContent, file.name);
    assert.equal(actions.children[0].href, file.preview_url); assert.equal(actions.children[1].href, file.download_url);
    assert.ok(actions.children[2].attributes['aria-label'].includes(file.name));
  }
  get('detail-owner').value = 'New Owner'; get('detail-owner').handlers.input();
  let edit=get('photo-grid').children[0].querySelector('button');edit.handlers.click();
  assert.ok(get('rename-dialog').open);assert.equal(get('rename-extension').textContent,'.png');
  get('rename-name').value='صورة جديدة';await get('rename-form').handlers.submit({preventDefault(){}});
  assert.equal(get('detail-owner').value,'New Owner');assert.equal(get('rename-dialog').open,false);
  assert.equal(get('photo-grid').children[0].children[1].children[0].textContent,'صورة جديدة.png');
  assert.equal(p.document.activeElement.dataset.attachmentId,'7');
  edit=get('photo-grid').children[0].querySelector('button');edit.handlers.click();
  p.records.get(1).attachments[0].name='Other name.png';get('rename-name').value='Keep my input';
  await get('rename-form').handlers.submit({preventDefault(){}});
  assert.ok(get('rename-dialog').open);assert.equal(get('rename-name').value,'Keep my input');
  assert.equal(get('detail-owner').value,'New Owner');assert.equal(p.document.activeElement,get('rename-name'));
  get('cancel-rename').handlers.click();
  p.records.set(1, {...p.records.get(1), driver_name:'New Driver', driver_phone:'0088'});
  p.events['hspace:driver-updated']({detail:{vehicle:{...p.records.get(1)}}});
  assert.equal(get('detail-owner').value, 'New Owner');
  assert.equal(get('detail-driver').value, 'New Driver'); assert.equal(get('detail-driver-phone').value, '0088');
  assert.equal(get('save-information').disabled, false);
  await p.route('#vehicles'); assert.equal(p.window.scrollY, 320); assert.equal(p.document.activeElement, get('vehicle-search'));
  assert.equal(get('vehicle-search').value, '٠٠١'); assert.ok(p.hasUnsaved());
  await p.route('#vehicle/2'); assert.equal(get('detail-owner').value, 'Old Owner');
  assert.equal(get('download-photos').attributes['aria-disabled'], 'true');
  assert.equal(get('download-photos').href, undefined);
  await p.route('#vehicle/1'); assert.equal(get('detail-owner').value, 'New Owner');
  get('detail-owner').value = 'Old Owner'; get('detail-owner').handlers.input(); assert.equal(p.hasUnsaved(), false, 'reverting the active draft should clear the warning');
  get('detail-owner').value = 'Saved Owner'; get('detail-owner').handlers.input();
  await get('vehicle-information-form').handlers.submit({preventDefault() {}});
  const patch = p.calls.find(call => call.options.method === 'PATCH' && !call.url.includes('/attachments/'));
  assert.deepEqual(JSON.parse(patch.options.body), {owner_name:'Saved Owner'});
  assert.equal(p.hasUnsaved(), false);
  await p.route('#vehicles'); p.search('');
  const card = get('vehicle-grid').children[0], photo = card.querySelector('[data-action="photo"]'), input = card.querySelector('input');
  photo.focus(); input.files = [{name:'car.jpg',size:100}]; input.value = 'car.jpg'; input.handlers.change(); await tick();
  assert.equal(input.value, ''); assert.equal(p.document.activeElement.dataset.action, 'photo');
  let replacement = get('vehicle-grid').children[0]; assert.notEqual(replacement, card);
  const release = p.pauseMutation(), nextInput = replacement.querySelector('input');
  replacement.querySelector('[data-action="photo"]').focus();
  nextInput.files = [{name:'car.jpg',size:100}]; nextInput.handlers.change();
  get('vehicle-search').focus(); release(); await tick();
  assert.equal(p.document.activeElement, get('vehicle-search'), 'upload completion must not take focus from search');
  replacement = get('vehicle-grid').children[0];
  replacement.querySelector('[data-action="delete"]').focus();
  await replacement.querySelector('[data-action="delete"]').handlers.click();
  assert.equal(get('vehicle-grid').children.length, 1); assert.equal(p.document.activeElement.dataset.action, 'delete');
  assert.equal(p.document.activeElement.closest('.vehicle-card').dataset.vehicleId, '2');
  console.log('Vehicle workflow passed: Arabic plate lookup/open, stable cards/highlighting, unsaved driver merge, cross-vehicle drafts, save payload, return position, cover focus and neighbor focus after deletion.');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
