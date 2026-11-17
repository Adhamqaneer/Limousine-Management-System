// Run with Node.js; no packages required.
const assert = require('node:assert/strict');
require('../src/limousine/presentation/web/static/web/vehicle-validation.js');
const cases = [
  ['chassis_number', 'ABC', true], ['chassis_number', '00123', true],
  ['chassis_number', 'JT001a', true], ['chassis_number', 'JT-123', false],
  ['chassis_number', '\u0634123', false], ['chassis_number', '\u0661\u0662', false],
  ['owner_name', '\u0623\u062d\u0645\u062f Adham', true],
  ['owner_name', '\u0645\u064f\u062d\u064e\u0645\u064e\u0651\u062f', true],
  ['owner_name', 'John1', false], ['owner_name', '\u0301', false],
  ['owner_phone', '\u0660\u0667\u0669', true], ['owner_phone', '+123', false],
  ['driver_phone', '\u0660\u0667\u0669', false], ['driver_phone', '0079', true],
  ['manufacture_year', '002024', true], ['manufacture_year', '\u0662\u0660\u0662\u0664', false],
  ['plate_number', '50-1746', true], ['plate_number', '1--2', false],
  ['plate_number', '-12', false], ['plate_number', '12-', false],
  ['vehicle_type', 'Camry 2024', false], ['vehicle_type', 'Camry', true],
  ['vehicle_type', '', false], ['owner_phone', '', true], ['chassis_number', '', true],
  ['driver_phone', '0'.repeat(33), false], ['plate_number', '0'.repeat(65), false]
];
for (const [name, value, valid] of cases) {
  assert.equal(!HSpaceVehicleValidation.error(name, value), valid, `${name}: ${value}`);
}
console.log(`${cases.length} vehicle validation cases passed.`);
