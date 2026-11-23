/* Keep the first three attachment rows visible, even when their names or actions wrap. */
(() => {
  'use strict';

  const visibleRows = 3;

  for (const list of document.querySelectorAll('.scroll-region--attachments')) {
    let observedRows = [];
    function updateHeight() {
      if (!observedRows[0]?.getClientRects().length) {
        return;
      }
      // Use layout heights so the driver dialog's opening animation cannot shrink the limit.
      let height = parseFloat(getComputedStyle(list).paddingBlockStart);
      for (const row of observedRows) {
        height += parseFloat(getComputedStyle(row).blockSize);
      }
      list.style.setProperty(
        '--attachment-list-limit',
        `${Math.ceil(height)}px`,
      );
    }

    const resizeObserver = new ResizeObserver(updateHeight);
    function updateRows() {
      resizeObserver.disconnect();
      const scrollable = list.children.length > visibleRows;
      list.tabIndex = scrollable ? 0 : -1;
      observedRows = scrollable ? Array.from(list.children).slice(
        0,
        visibleRows,
      ) : [];
      if (!scrollable) {
        list.style.removeProperty('--attachment-list-limit');
        return;
      }
      for (const row of observedRows) {
        resizeObserver.observe(
          row,
          { box: 'border-box' },
        );
      }
      updateHeight();
    }

    new MutationObserver(updateRows).observe(
      list,
      { childList: true },
    );
    updateRows();
  }
})();
