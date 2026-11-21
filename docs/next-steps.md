# Remaining work

- Decide with the owner: local website, desktop launcher/app or server. No hosting provider is selected.
- Check final screens in a native browser: English/Arabic, light/dark, narrow/desktop, keyboard focus, dialogs, artwork and headings. Native Computer Use was blocked during the category update because it could not verify the current browser URL.
- Test real browser downloads and both print modes, including category ZIP selection, preprinted paper and physical printing. ZIP contents/HTTP have automated coverage; native browser download and report printing do not.
- Perform/document a PostgreSQL-plus-media backup restoration drill; automated backups are not scheduled.
- Before wider access, review HTTPS, login rate limiting, monitoring and separate migration/runtime database roles.

Passing automated checks does not establish production readiness. Current commands/results are in [maintenance](maintenance.md).

Media folder organization (schema 9) was applied locally without automated tests at the owner's request. Future verification should cover upload/preview/recovery and ending/correcting driver periods after the named folders update.
