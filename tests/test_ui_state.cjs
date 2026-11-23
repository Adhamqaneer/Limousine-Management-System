const assert = require('node:assert/strict');
require('../src/limousine/presentation/web/static/web/ui-state.js');
const original = {
  owner_name: 'Old',
  owner_phone: '00123',
  driver_name: 'A',
  driver_phone: '0079',
  vehicle_type: 'Camry',
};
const draft = {
  owner_name: ' New owner ',
  owner_phone: '00123',
  driver_name: 'A',
  driver_phone: '0079',
  vehicle_type: 'Camry',
};
const saved = { ...original, owner_phone: '00456', driver_name: 'B', driver_phone: '0088' };
const merged = HSpaceDraft.merge(
  original,
  draft,
  saved,
);
assert.equal(
  merged.owner_name,
  ' New owner ',
);
assert.equal(
  merged.owner_phone,
  '00456',
);
assert.equal(
  merged.driver_name,
  'B',
);
assert.equal(
  merged.driver_phone,
  '0088',
);
assert.equal(
  original.owner_name,
  'Old',
);
assert.equal(
  draft.driver_name,
  'A',
);
assert.equal(
  HSpaceDraft.merge(
    original,
    { ...draft, owner_name: '' },
    saved,
  ).owner_name,
  '',
);
console.log(
  'Draft merging preserves dirty inputs/clears/leading zeros and synchronizes pristine and driver fields.',
);
