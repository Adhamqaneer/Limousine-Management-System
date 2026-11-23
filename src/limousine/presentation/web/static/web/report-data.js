/* Selection is presentation state only; records come from the authenticated API. */
(() => {
  'use strict';

  const fields = Object.freeze([
    'owner_name',
    'owner_phone',
    'driver_name',
    'driver_phone',
    'vehicle_type',
    'manufacture_year',
    'chassis_number',
    'plate_number',
  ]);
  function columns(selected) {
    const validFields = selected.filter((name) => fields.includes(name));
    return [...new Set(validFields)];
  }
  function rows(vehicles, selected) {
    const names = columns(selected);
    return vehicles.map((vehicle) =>
      names.map((name) =>
        typeof vehicle[name] === 'string' && vehicle[name] !== '' ? vehicle[name] : '—',
      ),
    );
  }
  globalThis.HSpaceReport = Object.freeze({
    fields,
    columns,
    rows,
    landscape: (selected) => columns(selected).length > 4,
  });
})();
