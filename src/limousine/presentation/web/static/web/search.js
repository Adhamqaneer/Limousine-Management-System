/* Presentation-only ranking of the already authenticated vehicle list. */
(() => {
  'use strict';
  function normalize(value) {
    return String(value ?? '').normalize('NFKD').replace(/\p{M}/gu, '')
      .replace(/ـ/g, '').replace(/ى/g, 'ي').replace(/[٠-٩]/g, c => String(c.charCodeAt(0) - 1632))
      .replace(/[۰-۹]/g, c => String(c.charCodeAt(0) - 1776)).toLowerCase().trim().replace(/\s+/g, ' ');
  }
  // Adjacent transpositions count as one typo, in addition to insertion/deletion/substitution.
  function distance(a, b) {
    let previous = Array.from({ length: b.length + 1 }, (_, i) => i), beforePrevious;
    for (let i = 1; i <= a.length; i++) {
      const row = [i];
      for (let j = 1; j <= b.length; j++) {
        row[j] = Math.min(row[j - 1] + 1, previous[j] + 1, previous[j - 1] + (a[i - 1] !== b[j - 1]));
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          row[j] = Math.min(row[j], beforePrevious[j - 2] + 1);
        }
      }
      beforePrevious = previous; previous = row;
    }
    return previous[b.length];
  }
  const compactPlate = value => normalize(value).replace(/[\s\-–—]/g, '');
  const cache = new WeakMap();
  function prepared(vehicle) {
    let data = cache.get(vehicle);
    if (!data || data.rawType !== vehicle.vehicle_type || data.rawPlate !== vehicle.plate_number) {
      const type = normalize(vehicle.vehicle_type), plate = normalize(vehicle.plate_number);
      data = {rawType:vehicle.vehicle_type, rawPlate:vehicle.plate_number, type, plate, words:type.match(/[\p{L}\p{N}]+/gu) || []};
      cache.set(vehicle, data);
    }
    return data;
  }
  function search(vehicles, input) {
    const query = normalize(input);
    if (!query) return vehicles.slice();
    if (query.length > 160) return [];
    const tokens = query.match(/[\p{L}\p{N}]+/gu) || [];
    if (!tokens.length) return [];
    const ranked = [];
    vehicles.forEach((vehicle, index) => {
      const {type,plate,words}=prepared(vehicle);
      if (/^[\d\s\-–—]+$/.test(query)) {
        const needle = compactPlate(query), haystack = compactPlate(plate);
        if (needle && haystack.includes(needle)) ranked.push({ vehicle, score: haystack === needle ? -1 : 0, index });
        return;
      }
      let score = 0;
      for (const token of tokens) {
        if (words.includes(token) || plate === token) continue;
        if (type.includes(token) || plate.includes(token)) { score += 1; continue; }
        // Never guess numeric/model/plate tokens, or short words.
        if (/\p{N}/u.test(token) || token.length < 4) { score = Infinity; break; }
        const limit = token.length >= 8 ? 2 : 1;
        const best = Math.min(...words.filter(word => !/\p{N}/u.test(word) && Math.abs(word.length - token.length) <= limit)
          .map(word => distance(token, word)), Infinity);
        if (best > limit) { score = Infinity; break; }
        score += 10 + best;
      }
      if (Number.isFinite(score)) {
        if (type === query || plate === query || compactPlate(plate) === compactPlate(query)) score = -1;
        ranked.push({ vehicle, score, index });
      }
    });
    return ranked.sort((a, b) => a.score - b.score || a.index - b.index).map(item => item.vehicle);
  }
  globalThis.HSpaceSearch = Object.freeze({ search, normalize });
})();
