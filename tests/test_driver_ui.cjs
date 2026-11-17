const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../src/limousine/presentation/web/static/web/drivers.js'),'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function page(globalPage){
  const nodes=new Map(),events={},calls=[],dispatched=[];
  class Node{
    constructor(tag='div'){this.tagName=tag;this.children=[];this.handlers={};this.dataset={};this.value='';this.classes=new Set();this.classList={toggle:(name,on)=>on?this.classes.add(name):this.classes.delete(name)};}
    append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
    addEventListener(name,fn){this.handlers[name]=fn;}setAttribute(name,value){this[name]=value;}showModal(){this.open=true;}close(){this.open=false;}
  }
  for(const id of ['csrf-token','driver-status','driver-search','print-driver-history','report-paper','driver-report-head','driver-report-body','driver-report-scope','driver-search-form','driver-query','driver-on-date','driver-print-dialog','driver-print-with','driver-print-without','driver-print-cancel','change-driver','correct-driver','all-driver-history','vehicle-driver-history','driver-corrections','driver-dialog-title','new-driver-name','new-driver-phone','driver-start','driver-form-message','driver-dialog','cancel-driver','driver-form','save-driver'])nodes.set(id,new Node());
  nodes.get('csrf-token').value='csrf';nodes.get('change-driver').parentElement=new Node();
  const original={id:1,vehicle_id:1,driver_name:'Old Driver',driver_phone:'00123',started_on:null,ended_on:null,is_current:true,plate_number:'050-001',vehicle_type:'Camry',created_by_name:'Member',created_at:'2026-01-01T10:00:00Z'};
  let rows=[original],printed=0,fail=false;
  const document={body:{dataset:globalPage?{driverHistory:'true'}:{}},documentElement:{lang:'en'},getElementById:id=>nodes.get(id),createElement:tag=>new Node(tag),querySelectorAll:()=>[],addEventListener:(name,fn)=>{events[name]=fn;},dispatchEvent:event=>{dispatched.push(event);}};
  const context={document,Intl,Date,URLSearchParams,location:{hash:globalPage?'':'#vehicle/1',search:'',assign:()=>{}},window:{addEventListener:(name,fn)=>{events[name]=fn;},print:()=>printed++},CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail;}},fetch:async(url,options)=>{
    calls.push([url,options]);if(fail)return {ok:false,status:503};
    if(options.method){const payload=JSON.parse(options.body);if(options.method==='POST'){rows=rows.map(row=>({...row,is_current:false,ended_on:payload.started_on}));rows.unshift({...original,...payload,id:2});}else rows=rows.map(row=>row.is_current?{...row,...payload}:row);return {ok:true,status:200,json:async()=>({vehicle:{id:1,...payload}})};}
    return {ok:true,status:200,json:async()=>({assignments:rows,corrections:[]})};
  }};
  vm.runInNewContext(source,context);
  return {nodes,events,calls,dispatched,document,setFail:value=>{fail=value;},printed:()=>printed};
}
async function main(){
  const g=page(true),get=id=>g.nodes.get(id);await tick();
  assert.equal(get('driver-report-head').children.length,6);
  assert.equal(get('driver-report-body').children[0].children[1].children[0].textContent,'00123');
  get('driver-query').value='Old';get('driver-on-date').value='2022-01-01';await get('driver-search-form').handlers.submit({preventDefault(){}});
  await tick();
  assert.ok(g.calls.some(([url])=>url.includes('q=Old')&&url.includes('on_date=2022-01-01')));
  get('print-driver-history').handlers.click();assert.ok(get('driver-print-dialog').open);
  get('driver-print-without').handlers.click();assert.equal(g.printed(),1);assert.ok(get('report-paper').classes.has('preprinted-paper'));
  get('print-driver-history').handlers.click();get('driver-print-with').handlers.click();assert.equal(g.printed(),2);assert.equal(get('report-paper').classes.has('preprinted-paper'),false);
  g.document.documentElement.lang='ar';g.events['hspace:language']();assert.equal(get('driver-report-head').children[0].textContent,'\u0627\u0633\u0645 \u0627\u0644\u0634\u0648\u0641\u064a\u0631');
  g.setFail(true);await get('driver-search-form').handlers.submit({preventDefault(){}});await tick();assert.ok(get('print-driver-history').disabled);assert.ok(get('report-paper').hidden);
  const h=page(false),input=id=>h.nodes.get(id);await tick();
  assert.equal(input('vehicle-driver-history').children.length,1);
  input('correct-driver').handlers.click();assert.equal(input('new-driver-name').value,'Old Driver');assert.equal(input('driver-start').required,false);
  input('new-driver-phone').value='00124';await input('driver-form').handlers.submit({preventDefault(){}});
  assert.ok(h.calls.some(([url,options])=>url.endsWith('/drivers/current/')&&options.method==='PATCH'&&options.headers['X-CSRFToken']==='csrf'));
  assert.equal(input('vehicle-driver-history').children.length,1);assert.ok(h.dispatched.some(event=>event.type==='hspace:driver-updated'));
  input('change-driver').handlers.click();assert.equal(input('driver-start').required,true);
  input('new-driver-name').value='New Driver';input('new-driver-phone').value='0079';input('driver-start').value='2022-01-01';await input('driver-form').handlers.submit({preventDefault(){}});
  assert.equal(input('vehicle-driver-history').children.length,2);assert.ok(h.calls.some(([url,options])=>url.endsWith('/drivers/')&&options.method==='POST'));
  console.log('Driver UI correction/assignment, CSRF, current synchronization, name/date search, both print modes, RTL and error gating passed.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
