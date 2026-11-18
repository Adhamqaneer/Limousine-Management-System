/* Pure draft merging; no browser persistence of business data. */
(() => {
  function merge(original, draft, saved) {
    return Object.fromEntries(
      Object.entries(draft).map(([key, value]) => [
        key,
        !['driver_name', 'driver_phone'].includes(key) && value.trim() !== (original[key] || '')
          ? value
          : saved[key] || '',
      ]),
    );
  }
  globalThis.HSpaceDraft = Object.freeze({
    merge,
  });
})();
