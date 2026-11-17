(() => {
  'use strict';
  const $=id=>document.getElementById(id), globalPage=document.body.dataset.driverHistory==='true';
  const en={skip:'Skip to content',currentDriverHint:'Use the driver actions below to change or correct this value.',driverHistory:'Driver history',changeDriver:'Change driver',correctDriver:'Correct current driver',searchHistory:'Search / print history',corrections:'Correction history',
    name:'Driver name',phone:'Driver phone',start:'Start date',end:'Changed on',current:'Current',unknown:'Unknown',recordedBy:'Recorded by',vehicle:'Vehicle number',type:'Vehicle type',
    startHint:'Changing drivers requires a date. For an older current record, leave an unknown start date empty when correcting.',cancel:'Cancel',save:'Save',searchName:'Driver name',onDate:'Working on date',search:'Search',print:'Print results',
    historyDescription:'Find drivers, their vehicle periods and the phone number recorded for each period.',allVehicles:'All vehicles',periodHint:'The end date is the handover day. Unknown start dates are excluded when searching a specific date.',
    loading:'Loading…',empty:'No driver records match.',failed:'Could not load or save driver history. Try again.',invalid:'Check the name, English phone digits and dates. A start date cannot be in the future or overlap an earlier period.',saved:'Driver history saved.',count:'{count} records',refresh:'Refresh',paperStyle:'Choose paper style',withHeader:'With letterhead and watermark',withoutHeader:'Preprinted paper: no letterhead or watermark',navVehicles:'Vehicles',navReports:'Print data',navTrash:'Deleted items',navDrivers:'Driver history',teamAccess:'Team',brandSub:'Vehicle management',signOut:'Sign out'};
  const ar={skip:'انتقل إلى المحتوى',currentDriverHint:'استخدم أزرار الشوفير بالأسفل للتغيير أو التصحيح.',driverHistory:'سجل الشوفيرين',changeDriver:'تغيير الشوفير',correctDriver:'تصحيح الشوفير الحالي',searchHistory:'بحث / طباعة السجل',corrections:'سجل التصحيحات',name:'اسم الشوفير',phone:'رقم الشوفير',start:'تاريخ البداية',end:'تاريخ التبديل',current:'حالي',unknown:'غير معروف',recordedBy:'سجّله',vehicle:'رقم المركبة',type:'نوع المركبة',
    startHint:'تغيير الشوفير يتطلب تاريخ بداية. عند تصحيح سجل قديم، اترك تاريخ البداية فارغًا إذا كان غير معروف.',cancel:'إلغاء',save:'حفظ',searchName:'اسم الشوفير',onDate:'كان يعمل بتاريخ',search:'بحث',print:'طباعة النتائج',historyDescription:'اعرف الشوفير والسيارات وفترات عمله ورقم تلفونه المسجل بكل فترة.',allVehicles:'كل السيارات',periodHint:'تاريخ النهاية هو يوم التبديل. عند البحث بتاريخ محدد، تُستبعد الفترات التي بدايتها غير معروفة.',loading:'جارٍ التحميل…',empty:'لا توجد فترات مطابقة.',failed:'تعذّر تحميل سجل الشوفيرين أو حفظه. حاول مجددًا.',invalid:'تحقق من الاسم ورقم الهاتف الإنجليزي والتواريخ. البداية لا تكون بالمستقبل ولا تتداخل مع فترة سابقة.',saved:'تم حفظ سجل الشوفيرين.',count:'{count} سجل',refresh:'تحديث',paperStyle:'اختيار نوع الورق',withHeader:'مع الترويسة والعلامة المائية',withoutHeader:'ورق جاهز: بدون ترويسة أو علامة مائية',navVehicles:'السيارات',navReports:'طباعة البيانات',navTrash:'المحذوفات',navDrivers:'سجل الشوفيرين',teamAccess:'إدارة الفريق',brandSub:'إدارة السيارات',signOut:'تسجيل الخروج'};
  const t=key=>(document.documentElement.lang==='ar'?ar[key]:en[key])||en[key]||key;
  const make=(tag,text='',cls='')=>{const node=document.createElement(tag);node.textContent=text;node.className=cls;return node;};
  const stamp=value=>value?new Intl.DateTimeFormat(document.documentElement.lang==='ar'?'ar-JO':'en-GB',{dateStyle:'medium',timeStyle:'short',timeZone:'Asia/Amman'}).format(new Date(value)):t('unknown');
  let rows=[],changes=[],busy=false,vehicleId=null,requestId=0,correcting=false,loaded=false,query='',onDate='',statusKey='';
  async function api(url,options={}){
    const response=await fetch(url,{...options,credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json','X-CSRFToken':$('csrf-token').value}});
    if(response.status===401){location.assign('/login/');throw new Error();}if(!response.ok){const error=new Error();error.status=response.status;throw error;}return response.json();
  }
  const columns=[['driver_name','name'],['driver_phone','phone'],['plate_number','vehicle'],['vehicle_type','type'],['started_on','start'],['ended_on','end']];
  function value(row,key){if(key==='ended_on')return row.is_current?t('current'):row[key]||t('unknown');return row[key]||t('unknown');}
  function render(){
    $('driver-status').textContent=statusKey?t(statusKey):'';
    if(globalPage){
      $('driver-search').disabled=busy;$('print-driver-history').disabled=busy||!loaded||!rows.length;
      $('report-paper').hidden=!loaded||!rows.length;
      const head=columns.map(([,label])=>{const th=make('th',t(label));th.scope='col';return th;});$('driver-report-head').replaceChildren(...head);
      $('driver-report-body').replaceChildren(...rows.map(row=>{const tr=make('tr');columns.forEach(([key])=>{const td=make('td'),bdi=make('bdi',value(row,key));bdi.dir=['driver_phone','plate_number','started_on','ended_on'].includes(key)?'ltr':'auto';td.append(bdi);tr.append(td);});return tr;}));
      $('driver-report-scope').textContent=[t('count').replace('{count}',rows.length),vehicleId?t('vehicle')+': '+(rows[0]?.plate_number||vehicleId):'',query?t('name')+': '+query:'',onDate?t('onDate')+': '+onDate:''].filter(Boolean).join(' · ');
    }else{
      $('change-driver').disabled=busy||!loaded;$('correct-driver').disabled=busy||!loaded||!rows.some(row=>row.is_current);
      $('all-driver-history').href='/drivers/?vehicle_id='+vehicleId;
      $('vehicle-driver-history').replaceChildren(...rows.map(row=>{const line=make('div','','driver-record');const name=make('strong',row.driver_name||t('unknown'));name.dir='auto';line.append(name,make('bdi',row.driver_phone||t('unknown')),make('span',(row.started_on||t('unknown'))+' → '+(row.is_current?t('current'):row.ended_on)),make('span',t('recordedBy')+': '+(row.created_by_name||t('unknown'))));return line;}));
      $('driver-corrections').replaceChildren(...changes.map(change=>{const row=make('div','','driver-record');const before=change.before_data||{},after=change.after_data||{};row.append(make('span',(before.driver_name||t('unknown'))+' / '+(before.driver_phone||t('unknown'))+' / '+(before.started_on||t('unknown'))+' → '+after.driver_name+' / '+(after.driver_phone||t('unknown'))+' / '+(after.started_on||t('unknown'))),make('span',change.actor_name+' · '+stamp(change.created_at)));return row;}));
    }
  }
  function translate(){document.querySelectorAll('[data-driver-i18n]').forEach(node=>{node.textContent=t(node.dataset.driverI18n);});if(globalPage){document.title='H SPACE | '+t('driverHistory');document.querySelectorAll('[data-i18n]').forEach(node=>{if(en[node.dataset.i18n])node.textContent=t(node.dataset.i18n);});document.querySelectorAll('[data-i18n-aria]').forEach(node=>{if(en[node.dataset.i18nAria])node.setAttribute('aria-label',t(node.dataset.i18nAria));});}render();}
  async function load(){
    const id=++requestId;loaded=false;busy=true;rows=[];changes=[];statusKey='loading';render();
    try{
      let url;
      if(globalPage){const params=new URLSearchParams();if(vehicleId)params.set('vehicle_id',vehicleId);if(query)params.set('q',query);if(onDate)params.set('on_date',onDate);url='/api/drivers/?'+params;}
      else {vehicleId=location.hash.match(/^#vehicle\/(\d+)$/)?.[1];if(!vehicleId){busy=false;render();return;}url='/api/vehicles/'+vehicleId+'/drivers/';}
      const payload=await api(url);if(id!==requestId)return;rows=payload.assignments;changes=payload.corrections||[];loaded=true;statusKey=rows.length?'':'empty';
    }catch(_){if(id===requestId)statusKey='failed';}
    finally{if(id===requestId){busy=false;render();}}
  }
  window.addEventListener('hspace:language',translate);
  if(globalPage){
    const param=new URLSearchParams(location.search).get('vehicle_id');if(param&&/^[0-9]+$/.test(param))vehicleId=param;
    $('driver-search-form').addEventListener('submit',event=>{event.preventDefault();query=$('driver-query').value.trim();onDate=$('driver-on-date').value;load();});
    $('print-driver-history').addEventListener('click',()=>{if(!$('print-driver-history').disabled)$('driver-print-dialog').showModal();});
    const print=plain=>{if($('print-driver-history').disabled)return;$('report-paper').classList.toggle('preprinted-paper',plain);$('driver-print-dialog').close();window.print();};
    $('driver-print-with').addEventListener('click',()=>print(false));$('driver-print-without').addEventListener('click',()=>print(true));$('driver-print-cancel').addEventListener('click',()=>$('driver-print-dialog').close());
    translate();load();
  }else{
    function open(correction){if(busy||!loaded)return;correcting=correction;const current=rows.find(row=>row.is_current);$('driver-dialog-title').textContent=t(correction?'correctDriver':'changeDriver');$('new-driver-name').value=correction&&current?current.driver_name:'';$('new-driver-phone').value=correction&&current?current.driver_phone:'';$('driver-start').value=correction&&current?current.started_on||'':'';$('driver-start').required=!correction;$('driver-form-message').textContent='';$('driver-dialog').showModal();}
    $('change-driver').addEventListener('click',()=>open(false));$('correct-driver').addEventListener('click',()=>open(true));$('cancel-driver').addEventListener('click',()=>$('driver-dialog').close());
    const refresh=make('button',t('refresh'),'button secondary small');refresh.type='button';refresh.dataset.driverI18n='refresh';refresh.addEventListener('click',load);$('change-driver').parentElement.append(refresh);
    $('driver-form').addEventListener('submit',async event=>{event.preventDefault();if(busy)return;const target=vehicleId;busy=true;$('save-driver').disabled=true;$('cancel-driver').disabled=true;
      try{const payload=await api('/api/vehicles/'+target+'/drivers/'+(correcting?'current/':''),{method:correcting?'PATCH':'POST',body:JSON.stringify({driver_name:$('new-driver-name').value.trim(),driver_phone:$('new-driver-phone').value.trim(),started_on:$('driver-start').value||null})});$('driver-dialog').close();document.dispatchEvent(new CustomEvent('hspace:driver-updated',{detail:payload}));await load();}
      catch(error){$('driver-form-message').textContent=t(error.status===400?'invalid':'failed');}
      finally{busy=false;$('save-driver').disabled=false;$('cancel-driver').disabled=false;render();}
    });
    document.addEventListener('hspace:detail-ready',load);window.addEventListener('hashchange',()=>{if(!location.hash.startsWith('#vehicle/')){requestId++;rows=[];loaded=false;busy=false;render();}});
    translate();if(location.hash.startsWith('#vehicle/'))load();
  }
})();
