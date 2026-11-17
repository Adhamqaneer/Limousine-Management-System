/* Presentation validation mirrors domain rules; server validation is authoritative. */
(() => {
  'use strict';
  const limits = {owner_name: 200, owner_phone: 32, driver_name: 200, driver_phone: 32,
    vehicle_type: 120, manufacture_year: 32, chassis_number: 120, plate_number: 64};
  function nameValid(value) {
    let letterSeen = false;
    for (const char of value) {
      const arabic = /[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]/u.test(char);
      if (/[A-Za-z]/u.test(char) || (arabic && /\p{L}/u.test(char))) letterSeen = true;
      else if (char !== ' ' && !(arabic && /\p{M}/u.test(char) && letterSeen)) return false;
    }
    return letterSeen;
  }
  function error(name, value) {
    if (typeof value !== 'string' || !(name in limits)) return 'invalidDetails';
    value = value.trim();
    if (value.length > limits[name] || /\p{Cc}/u.test(value)) return 'invalidDetails';
    if (name === 'plate_number') return /^[0-9]+(?:-[0-9]+)*$/u.test(value) ? '' : 'invalidPlate';
    if (!value) return name === 'vehicle_type' ? 'nameRule' : '';
    if (['owner_name', 'driver_name', 'vehicle_type'].includes(name)) return nameValid(value) ? '' : 'nameRule';
    if (name === 'owner_phone') return /^[0-9\u0660-\u0669\u06f0-\u06f9]+$/u.test(value) ? '' : 'phoneRule';
    if (name === 'chassis_number') return /^[A-Za-z0-9]+$/u.test(value) ? '' : 'chassisRule';
    return /^[0-9]+$/u.test(value) ? '' : 'digitsRule';
  }
  globalThis.HSpaceVehicleValidation = Object.freeze({error});
})();
