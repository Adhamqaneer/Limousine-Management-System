const assert = require('node:assert/strict');
require('../src/limousine/presentation/web/static/web/vehicle-filters.js');
require('../src/limousine/presentation/web/static/web/search.js');
const cars = [
  {
    id: 1,
    owner_name: 'Adham',
    manufacture_year: '2024',
    vehicle_type: 'Camry',
    plate_number: '050-001',
  },
  {
    id: 2,
    owner_name: 'Adham',
    manufacture_year: '2023',
    vehicle_type: 'Camry',
    plate_number: '050-002',
  },
  {
    id: 3,
    owner_name: '\u0623\u062d\u0645\u062f',
    manufacture_year: '2024',
    vehicle_type: 'Corolla',
    plate_number: '050-003',
  },
  { id: 4, owner_name: '', manufacture_year: '', vehicle_type: 'Camry', plate_number: '050-004' },
  {
    id: 5,
    owner_name: ' Adham ',
    manufacture_year: '002024',
    vehicle_type: 'Camry',
    plate_number: '050-005',
  },
];
const before = JSON.stringify(cars);
const ids = (selection) => HSpaceVehicleFilters.apply(cars, selection).map((car) => car.id);
assert.deepEqual(ids({}), [1, 2, 3, 4, 5]);
assert.deepEqual(ids({ owner_name: 'Adham' }), [1, 2, 5]);
assert.deepEqual(ids({ manufacture_year: '2024' }), [1, 3]);
assert.deepEqual(ids({ vehicle_type: 'Camry' }), [1, 2, 4, 5]);
assert.deepEqual(ids({ owner_name: 'Adham', manufacture_year: '2024' }), [1]);
assert.deepEqual(
  ids({ owner_name: 'Adham', vehicle_type: 'Camry', manufacture_year: '2023' }),
  [2],
);
assert.deepEqual(ids({ manufacture_year: '002024' }), [5]);
assert.deepEqual(ids({ owner_name: '\u0623\u062d\u0645\u062f' }), [3]);
assert.deepEqual(ids({ owner_name: 'Missing' }), []);
assert.deepEqual(HSpaceVehicleFilters.options(cars, 'owner_name'), [
  'Adham',
  '\u0623\u062d\u0645\u062f',
]);
assert.deepEqual(HSpaceVehicleFilters.options(cars, 'driver_name'), []);
assert.equal(HSpaceVehicleFilters.options(cars, 'vehicle_type').length, 2);
assert.deepEqual(
  HSpaceSearch.search(HSpaceVehicleFilters.apply(cars, { owner_name: 'Adham' }), '050-002').map(
    (car) => car.id,
  ),
  [2],
);
assert.deepEqual(
  HSpaceSearch.search(HSpaceVehicleFilters.apply(cars, { manufacture_year: '2024' }), 'camyr').map(
    (car) => car.id,
  ),
  [1],
);
assert.deepEqual(HSpaceVehicleFilters.apply([], {}), []);
assert.equal(JSON.stringify(cars), before);
for (const selection of [
  { owner_name: 'Adham' },
  { manufacture_year: '2024' },
  { vehicle_type: 'Camry' },
  { owner_name: '\u0623\u062d\u0645\u062f', manufacture_year: '2024', vehicle_type: 'Corolla' },
]) {
  const scope = HSpaceVehicleFilters.reportScope(
    HSpaceVehicleFilters.reportHash(selection, '050-003'),
  );
  assert.ok(scope.valid && scope.filtered);
  assert.deepEqual(
    HSpaceSearch.search(HSpaceVehicleFilters.apply(cars, scope.selected), scope.query).map(
      (car) => car.id,
    ),
    HSpaceSearch.search(HSpaceVehicleFilters.apply(cars, selection), '050-003').map(
      (car) => car.id,
    ),
  );
}
assert.equal(HSpaceVehicleFilters.reportScope('').filtered, false);
assert.ok(HSpaceVehicleFilters.reportScope('#results?').valid);
for (const hash of [
  '#unknown',
  '#results?driver_name=x',
  '#results?__proto__=x',
  '#results?owner_name=a&owner_name=b',
  '#results?manufacture_year=' + '2'.repeat(33),
])
  assert.equal(HSpaceVehicleFilters.reportScope(hash).valid, false);
console.log(
  '16 filter regression checks passed: individual/combined filters, blanks, Arabic, leading zeros, search intersection and unchanged records.',
);
