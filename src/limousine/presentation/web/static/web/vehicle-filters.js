/* Exact facets of the authenticated list; no business data is persisted here. */
(() => {
  'use strict';

  const fields = Object.freeze(['owner_name', 'manufacture_year', 'vehicle_type']);
  const value = (input) => (typeof input === 'string' ? input.trim() : '');
  function options(vehicles, field, language = 'en') {
    if (!fields.includes(field)) return [];
    return [...new Set(vehicles.map((vehicle) => value(vehicle[field])).filter(Boolean))].sort(
      (a, b) => a.localeCompare(b, language),
    );
  }
  function apply(vehicles, selected) {
    return vehicles.filter((vehicle) =>
      fields.every(
        (field) => !value(selected[field]) || value(vehicle[field]) === value(selected[field]),
      ),
    );
  }
  function reportHash(selected, query = '') {
    const params = new URLSearchParams();
    fields.forEach((field) => {
      if (value(selected[field])) params.set(field, value(selected[field]));
    });
    if (query) params.set('q', query);
    return '#results?' + params.toString();
  }
  function reportScope(hash) {
    if (!hash)
      return {
        filtered: false,
        valid: true,
        selected: {},
        query: '',
      };
    const invalid = {
      filtered: true,
      valid: false,
      selected: {},
      query: '',
    };
    if (!hash.startsWith('#results?') || hash.length > 16000) return invalid;
    const params = new URLSearchParams(hash.slice(9));
    const limits = {
      owner_name: 200,
      manufacture_year: 32,
      vehicle_type: 120,
      q: 2048,
    };
    for (const [key, val] of params) {
      if (
        !Object.hasOwn(limits, key) ||
        params.getAll(key).length !== 1 ||
        val.length > limits[key]
      )
        return invalid;
    }
    return {
      filtered: true,
      valid: true,
      selected: Object.fromEntries(fields.map((field) => [field, params.get(field) || ''])),
      query: params.get('q') || '',
    };
  }
  globalThis.HSpaceVehicleFilters = Object.freeze({
    fields,
    options,
    apply,
    reportHash,
    reportScope,
  });
})();
