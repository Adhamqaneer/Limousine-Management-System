(() => {
  'use strict';
  let arabic = false;
  try { arabic = localStorage.getItem('limousine.language') === 'ar'; } catch (_) {}
  const text = arabic ? { back: 'العودة للسيارات', team: 'إدارة الفريق',
    description: 'إدارة دخول الحسابات الأربعة. صلاحيات السيارات مشتركة.',
    note: 'تعطيل الحساب أو حذفه ينهي جلساته. الحساب المحذوف يبقى محفوظًا ويمكن استعادته. حساب الأدمن محمي.',
    active: 'مفعّل', disabled: 'معطّل', deleted: 'محذوف', admin: 'أدمن', member: 'عضو',
    disable: 'تعطيل الدخول', enable: 'تفعيل الدخول', remove: 'حذف منطقي', restore: 'استعادة الحساب',
    failed: 'تعذّر تحديث الحساب. أعد المحاولة.', saved: 'تم تحديث الحساب.', protected: 'حساب الإدارة' }
    : { back: 'Back to vehicles', team: 'Team access', description: 'Manage access for your four accounts. Vehicle permissions remain shared.',
    note: 'Disabling or deleting an account ends its sessions. Deleted accounts remain stored and can be restored. The administrator is protected.',
    active: 'Active', disabled: 'Disabled', deleted: 'Deleted', admin: 'Admin', member: 'Member',
    disable: 'Disable access', enable: 'Enable access', remove: 'Soft delete', restore: 'Restore account',
    failed: 'Could not update the account. Try again.', saved: 'Account updated.', protected: 'Administrator account' };
  document.documentElement.lang = arabic ? 'ar' : 'en'; document.documentElement.dir = arabic ? 'rtl' : 'ltr';
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = text[el.dataset.i18n]; });
  const message = document.getElementById('team-message');
  const make = (tag, value, cls) => { const el = document.createElement(tag); el.textContent = value; if (cls) el.className = cls; return el; };
  let busy = false;
  async function request(url, options = {}) {
    const response = await fetch(url, { ...options, credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.getElementById('csrf-token').value } });
    if (response.status === 401) { location.assign('/login/'); throw new Error(); }
    if (!response.ok) throw new Error();
    return response.json();
  }
  async function update(user, changes) {
    if (busy) return;
    busy = true; document.querySelectorAll('#team-list button').forEach(button => { button.disabled = true; });
    try { await request('/api/users/' + user.id + '/', { method: 'PATCH', body: JSON.stringify(changes) }); await load(); message.textContent = text.saved; }
    catch (_) { message.textContent = text.failed; document.querySelectorAll('#team-list button').forEach(button => { button.disabled = false; }); }
    finally { busy = false; }
  }
  async function load() {
    const { users } = await request('/api/users/');
    document.getElementById('team-list').replaceChildren(...users.map(user => {
      const card = make('section', '', 'panel team-card'); const info = make('div', '');
      info.append(make('h2', user.username), make('p', text[user.role === 'ADMIN' ? 'admin' : 'member'] + ' · ' + text[user.is_deleted ? 'deleted' : user.is_active ? 'active' : 'disabled'], 'muted'));
      card.append(info); const actions = make('div', '', 'team-actions');
      if (user.role === 'ADMIN') actions.append(make('span', text.protected, 'muted'));
      else {
        const button = make('button', text[user.is_deleted ? 'restore' : user.is_active ? 'disable' : 'enable'], 'button secondary');
        button.type = 'button'; button.addEventListener('click', () => update(user, user.is_deleted ? { is_deleted: false, is_active: false } : { is_active: !user.is_active }));
        actions.append(button);
        if (!user.is_deleted) { const remove = make('button', text.remove, 'button secondary'); remove.type = 'button'; remove.addEventListener('click', () => update(user, { is_deleted: true })); actions.append(remove); }
      }
      card.append(actions); return card;
    }));
  }
  load().catch(() => { message.textContent = text.failed; });
})();
