(() => {
  'use strict';
  const $ = id => document.getElementById(id), en = {};
  document.querySelectorAll('[data-i18n]').forEach(el => { en[el.dataset.i18n] = el.textContent; });
  Object.assign(en, {restore:'Restore', unknown:'Unknown (older record)', createdBy:'Added by', deletedBy:'Deleted by',
    vehicle:'Vehicle', attachment:'Attachment', cover:'Card photo', empty:'No deleted items.', noHistory:'No recorded activity yet.',
    failed:'Could not complete the request. Refresh and try again.', saved:'Item restored.', parentDeleted:'Restore the vehicle first.',
    confirmRestore:'Restore {label}?', CREATE:'Added', DELETE:'Deleted', RESTORE:'Restored', replaced:'Replaced card photo',
    removeCurrentPhoto:'Remove current card photo', confirmCurrentPhoto:'Move the current card photo for {plate} to deleted items? You can then restore an older photo.', currentPhotoRemoved:'Current card photo moved to deleted items.',
    coverConflict:'Remove the current card photo before restoring an older photo.', loading:'Loading…', signOut:'Sign out'});
  const ar = {navDrivers:'سجل الشوفيرين', navTrash:'المحذوفات', navReports:'طباعة البيانات', navVehicles:'السيارات', teamAccess:'إدارة الفريق', brandSub:'إدارة السيارات', skip:'انتقل إلى المحتوى', signOut:'تسجيل الخروج',
    trashTitle:'المحذوفات', trashDescription:'الملفات محفوظة. الاسترجاع للأدمن فقط.', refreshTrash:'تحديث', deletedTitle:'الاسترجاع',
    restoreNote:'استرجع السيارة أولًا. الملفات المحذوفة بشكل منفصل تظل محذوفة. لاسترجاع صورة كارد قديمة، احذف الصورة الحالية أولًا.',
    activityTitle:'سجل العمليات', historyNote:'تُسجل الإضافات والحذف والاسترجاع الجديدة. هوية من أضاف السجلات القديمة غير معروفة.', olderActivity:'تحميل عمليات أقدم',
    restore:'استرجاع', unknown:'غير معروف (سجل قديم)', createdBy:'أضافه', deletedBy:'حذفه', vehicle:'سيارة', attachment:'مرفق', cover:'صورة الكارد',
    empty:'لا توجد محذوفات.', noHistory:'لا توجد عمليات مسجلة بعد.', failed:'تعذّر إكمال الطلب. حدّث الصفحة وحاول مجددًا.', saved:'تم الاسترجاع.', parentDeleted:'استرجع السيارة أولًا.',
    removeCurrentPhoto:'حذف صورة الكارد الحالية', confirmCurrentPhoto:'نقل صورة الكارد الحالية للسيارة {plate} إلى المحذوفات؟ بعدها بتقدر تسترجع صورة قديمة.', currentPhotoRemoved:'تم نقل صورة الكارد الحالية إلى المحذوفات.',
    confirmRestore:'استرجاع {label}؟', CREATE:'إضافة', DELETE:'حذف', RESTORE:'استرجاع', replaced:'استبدال صورة الكارد', coverConflict:'احذف صورة الكارد الحالية قبل استرجاع صورة قديمة.', loading:'جارٍ التحميل…'};
  let items = [], events = [], busy = false, more = false, messageKey = '';
  const t = key => (document.documentElement.lang === 'ar' ? ar[key] : en[key]) ?? en[key] ?? key;
  const make = (tag, text, cls='') => { const node = document.createElement(tag); node.textContent=text; node.className=cls; return node; };
  const date = value => value ? new Intl.DateTimeFormat(document.documentElement.lang === 'ar' ? 'ar-JO' : 'en-GB', {dateStyle:'medium',timeStyle:'short',timeZone:'Asia/Amman'}).format(new Date(value)) : t('unknown');
  async function request(url, options={}) {
    const response = await fetch(url,{...options,credentials:'same-origin',cache:'no-store',headers:{'X-CSRFToken':$('csrf-token').value}});
    if(response.status===401){location.assign('/login/');throw new Error();}
    if(!response.ok){const error=new Error();error.status=response.status;throw error;}
    return response.status===204 ? null : response.json();
  }
  function render() {
    $('trash-message').textContent=messageKey?t(messageKey):'';
    $('refresh-trash').disabled=busy; $('older-activity').disabled=busy; $('older-activity').hidden=!more;
    $('deleted-list').setAttribute('aria-busy',String(busy));
    $('deleted-list').replaceChildren(...(items.length?items.map(item=>{
      const card=make('article','','panel recycle-card'), info=make('div');
      const title=make('h3',item.label);title.dir='auto';
      info.append(make('p',t(item.kind)+' · '+item.plate_number,'muted'),title,
        make('p',t('createdBy')+': '+(item.created_by||t('unknown'))+' · '+date(item.created_at),'muted'),
        make('p',t('deletedBy')+': '+(item.deleted_by||t('unknown'))+' · '+date(item.deleted_at),'muted'));
      const button=make('button',t(item.kind!=='vehicle'&&item.parent_deleted?'parentDeleted':'restore'),'button secondary');button.type='button';button.disabled=busy||(item.kind!=='vehicle'&&item.parent_deleted);
      button.addEventListener('click',()=>restore(item));card.append(info,button);
      if(item.kind==='cover'&&item.has_current_cover&&!item.parent_deleted){
        const remove=make('button',t('removeCurrentPhoto'),'button secondary danger');remove.type='button';remove.disabled=busy;
        remove.addEventListener('click',()=>removeCurrentPhoto(item));card.append(remove);
      }
      return card;
    }):[make('p',t(busy?'loading':'empty'),'section-empty')]));
    $('activity-list').replaceChildren(...(events.length?events.map(event=>{
      const card=make('article','','panel activity-card'), label=make('strong',event.label);label.dir='auto';
      card.append(make('p',t(event.action)+' · '+t(event.entity_kind)+' · '+event.plate_number),label,
        make('p',event.actor_name+' · '+date(event.created_at),'muted'));
      if(event.reason==='replaced')card.append(make('p',t('replaced'),'muted'));
      return card;
    }):[make('p',t('noHistory'),'section-empty')]));
  }
  async function load(older=false) {
    if(busy)return;busy=true;render();
    try {
      if(older){const result=await request('/api/activity/?before='+events[events.length-1].id);events.push(...result.events);more=result.events.length===100;}
      else {const [deleted,history]=await Promise.all([request('/api/recycle-bin/'),request('/api/activity/')]);items=deleted.items;events=history.events;more=events.length===100;}
    } catch(_){messageKey='failed';}
    finally{busy=false;render();}
  }
  async function restore(item) {
    if(busy||!window.confirm(t('confirmRestore').replace('{label}',item.label)))return;
    busy=true;messageKey='';render();
    try {await request('/api/recycle-bin/'+item.kind+'/'+item.id+'/restore/',{method:'POST'});messageKey='saved';}
    catch(error){messageKey=error.status===400&&item.kind==='cover'?'coverConflict':'failed';}
    finally{busy=false;await load();}
  }
  async function removeCurrentPhoto(item) {
    if(busy||!window.confirm(t('confirmCurrentPhoto').replace('{plate}',item.plate_number)))return;
    busy=true;messageKey='';render();
    try {await request('/api/vehicles/'+item.vehicle_id+'/cover/',{method:'DELETE'});messageKey='currentPhotoRemoved';}
    catch(_){messageKey='failed';}
    finally{busy=false;await load();}
  }
  function translate(){document.title='H SPACE | '+t('trashTitle');document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});document.querySelectorAll('[data-i18n-aria]').forEach(el=>{el.setAttribute('aria-label',t(el.dataset.i18nAria));});render();}
  $('refresh-trash').addEventListener('click',()=>{messageKey='';load();});$('older-activity').addEventListener('click',()=>load(true));
  window.addEventListener('hspace:language',translate);window.addEventListener('pageshow',event=>{if(event.persisted)load();});
  translate();load();
})();
