/* Optional frontend unit checks: node tests/test_search.cjs */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = {};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../src/limousine/presentation/web/static/web/search.js'), 'utf8'), context);
const cars = [
  { id: 1, vehicle_type: 'تويوتا كامري', plate_number: '50-76523' },
  { id: 2, vehicle_type: 'Toyota Camry', plate_number: '001-235' },
  { id: 3, vehicle_type: 'كامري', plate_number: '50-76524' },
  { id: 4, vehicle_type: 'Honda Civic', plate_number: '900' }
];
const original = JSON.stringify(cars);
const cases = [
  ['تيوتا', [1]], ['كامير', [1, 3]], ['كامري', [3, 1]], ['تُويوتا', [1]],
  ['TOYOTA CAMRY', [2]], ['Toyta', [2]], ['٥٠٧٦٥٢٣', [1]], ['۰۰۱۲۳۵', [2]],
  ['76524', [3]], ['76525', []], ['76523-50', []], ['تيوتا 76523', [1]],
  ['تيوتا 76524', []], ['xyz', []], ['   ', [1, 2, 3, 4]], ['---', []], ['a'.repeat(161), []]
];
for (const [query, expected] of cases) assert.deepEqual(Array.from(context.HSpaceSearch.search(cars, query), car => car.id), expected, query);
assert.equal(JSON.stringify(cars), original);
// Cached comparisons must not hide later edits to the same record object.
const updated = {id:5,vehicle_type:'Camry',plate_number:'000-123'};
assert.equal(context.HSpaceSearch.search([updated], 'Camry').length, 1);
updated.vehicle_type = 'Accord'; updated.plate_number = '000-456';
assert.equal(context.HSpaceSearch.search([updated], 'Camry').length, 0);
assert.equal(context.HSpaceSearch.search([updated], 'Accord 456').length, 1);
module.exports = { passed: cases.length, nonmutating: true };
