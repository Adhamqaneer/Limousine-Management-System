const assert = require('node:assert/strict');
require('../src/limousine/presentation/web/static/web/report-data.js');
const fields = HSpaceReport.fields;
const vehicles = [{owner_name:'<img src=x onerror=alert(1)>', owner_phone:'00123', driver_name:'\u0623\u062d\u0645\u062f',
  driver_phone:'0079', vehicle_type:'Camry', manufacture_year:'002024', chassis_number:'JT001a', plate_number:'050-001'},
  {plate_number:'50-1746', owner_name:''}];
const snapshot = JSON.stringify(vehicles);
// Every possible non-empty combination: fixed column order, exact values, blank cells and orientation.
for (let mask = 1; mask < 256; mask++) {
  const wanted = fields.filter((_, index) => mask & (1 << index));
  const selected = [...wanted].reverse().concat('password_hash', wanted[0]);
  assert.deepEqual(HSpaceReport.columns(selected), wanted);
  const rows = HSpaceReport.rows(vehicles, selected);
  assert.equal(rows.length, 2);
  assert.deepEqual(rows[0], wanted.map(name => vehicles[0][name]));
  assert.deepEqual(rows[1], wanted.map(name => vehicles[1][name] || '—'));
  assert.equal(HSpaceReport.landscape(selected), wanted.length > 4);
}
assert.deepEqual(HSpaceReport.columns([]), []);
assert.deepEqual(HSpaceReport.rows([], fields), []);
assert.equal(JSON.stringify(vehicles), snapshot);
assert.ok(Object.isFrozen(fields));
console.log('255 report combinations passed; leading zeros, Arabic, blank cells and source records preserved.');
