(() => {
  'use strict';
  const en = {};
  document.querySelectorAll('[data-i18n]').forEach(el => { en[el.dataset.i18n] = el.textContent; });
  Object.assign(en, { active:'Active', disabled:'Disabled', deleted:'Deleted', admin:'Administrator', member:'Member',
    disable:'Disable access', enable:'Enable access', remove:'Soft delete', restore:'Restore account',
    failed:'Could not load or update the team. Try again.', retry:'Try again', saved:'Account updated.', protected:'Administrator account', signOut:'Sign out' });
  const ar = { back:'العودة للسيارات', team:'إدارة الفريق', description:'إدارة دخول الحسابات الأربعة. صلاحيات السيارات مشتركة.',
    note:'تعطيل الحساب أو حذفه ينهي جلساته. الحساب المحذوف يبقى محفوظًا ويمكن استعادته. حساب الأدمن محمي.',
    active:'مفعّل', disabled:'معطّل', deleted:'محذوف', admin:'أدمن', member:'عضو', disable:'تعطيل الدخول', enable:'تفعيل الدخول',
    remove:'حذف منطقي', restore:'استعادة الحساب', failed:'تعذّر تحميل الفريق أو تحديث الحساب. أعد المحاولة.', retry:'إعادة المحاولة', saved:'تم تحديث الحساب.', protected:'حساب الإدارة',
    navDrivers:'سجل الشوفيرين', navTrash:'المحذوفات', navReports:'طباعة البيانات', navVehicles: 'السيارات', teamAccess:'الفريق', brandSub:'إدارة السيارات', skip:'انتقل إلى المحتوى', memberAccess:'فريق مكتبك', loading:'جارٍ تحميل الفريق…', signOut:'تسجيل الخروج' };
  const make = (tag,value,cls) => { const el=document.createElement(tag); el.textContent=value; if(cls)el.className=cls; return el; };
  const message=document.getElementById('team-message'), list=document.getElementById('team-list');
  let busy=false, users=[], messageKey='';
  const t = key => (document.documentElement.lang === 'ar' ? ar[key] : en[key]) ?? en[key] ?? key;
  function apply() {
    document.title = document.documentElement.lang === 'ar' ? 'H SPACE | الفريق' : 'H SPACE | Team';
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent=t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label',t(el.dataset.i18nAria)); });
    message.textContent=messageKey?t(messageKey):''; if(users.length)render();
    else if(messageKey==='failed')renderRetry();
  }
  async function request(url,options={}) {
    const response=await fetch(url,{...options,credentials:'same-origin',cache:'no-store',
      headers:{'Content-Type':'application/json','X-CSRFToken':document.getElementById('csrf-token').value}});
    if(response.status===401){location.assign('/login/');throw new Error();}
    if(!response.ok)throw new Error(); return response.json();
  }
  function render() {
    list.replaceChildren(...users.map(user => {
      const card=make('section','','panel team-card'), person=make('div','','team-person');
      const avatar=make('span',user.username.slice(0,1).toUpperCase(),'team-avatar'); avatar.setAttribute('aria-hidden','true');
      const info=make('div','','team-info'), name=make('h2',user.username); name.dir='auto';
      info.append(name,make('p',t(user.role==='ADMIN'?'admin':'member'),'team-role'));
      const status=make('span',t(user.is_deleted?'deleted':user.is_active?'active':'disabled'),'status-badge'+(user.is_active&&!user.is_deleted?' active':''));
      person.append(avatar,info,status); card.append(person);
      const actions=make('div','','team-actions');
      if(user.role==='ADMIN')actions.append(make('span',t('protected'),'muted'));
      else {
        const button=make('button',t(user.is_deleted?'restore':user.is_active?'disable':'enable'),'button secondary');
        button.type='button'; button.disabled=busy;
        button.addEventListener('click',()=>update(user,user.is_deleted?{is_deleted:false,is_active:false}:{is_active:!user.is_active}));
        actions.append(button);
        if(!user.is_deleted){const remove=make('button',t('remove'),'button ghost danger');remove.type='button';remove.disabled=busy;remove.addEventListener('click',()=>update(user,{is_deleted:true}));actions.append(remove);}
      }
      card.append(actions);return card;
    }));
  }
  async function load() {
    list.setAttribute('aria-busy','true');
    try { ({users}=await request('/api/users/')); render(); }
    finally { list.setAttribute('aria-busy','false'); }
  }
  function renderRetry() {
    const retry=make('button',t('retry'),'button secondary'); retry.type='button';
    retry.addEventListener('click',()=>{messageKey='';message.textContent='';load().catch(showFailure);});
    list.replaceChildren(retry);
  }
  function showFailure() { messageKey='failed';apply(); }
  async function update(user,changes) {
    if(busy)return;busy=true;render();
    try { await request('/api/users/'+user.id+'/',{method:'PATCH',body:JSON.stringify(changes)});await load();messageKey='saved'; }
    catch(_){messageKey='failed';}
    finally {busy=false;apply();}
  }
  window.addEventListener('hspace:language',apply);
  apply();load().catch(showFailure);
})();
