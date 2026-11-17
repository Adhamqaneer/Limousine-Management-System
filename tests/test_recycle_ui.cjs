// Minimal DOM contract checks; native layout/accessibility still need browser review.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
async function main(){
  const nodes=new Map(),events={},calls=[];
  class Node{
    constructor(tag='div'){this.tagName=tag;this.children=[];this.handlers={};this.dataset={};}
    append(...items){this.children.push(...items);}
    replaceChildren(...items){this.children=items;}
    addEventListener(name,fn){this.handlers[name]=fn;}
    setAttribute(name,value){this[name]=value;}
  }
  for(const id of ['csrf-token','trash-message','refresh-trash','older-activity','deleted-list','activity-list'])nodes.set(id,new Node());
  nodes.get('csrf-token').value='csrf';
  const stamp='2026-01-01T10:00:00Z';
  let items=[{kind:'vehicle',id:1,vehicle_id:1,plate_number:'050-001',label:'050-001',parent_deleted:true,created_by:null,deleted_by:'Member',created_at:stamp,deleted_at:stamp},
    {kind:'attachment',id:2,vehicle_id:1,plate_number:'050-001',label:'<script>file</script>',parent_deleted:true,created_by:'Member',deleted_by:'Admin',created_at:stamp,deleted_at:stamp}];
  const history=Array.from({length:100},(_,index)=>({id:200-index,vehicle_id:1,entity_kind:'attachment',action:'DELETE',plate_number:'050-001',label:'<script>file</script>',actor_name:'Member',created_at:stamp,reason:''}));
  const document={documentElement:{lang:'en'},getElementById:id=>nodes.get(id),createElement:tag=>new Node(tag),querySelectorAll:()=>[]};
  const context={document,Intl,Date,window:{confirm:()=>true,addEventListener:(name,fn)=>{events[name]=fn;}},location:{assign:()=>{}},fetch:async(url,options)=>{
    calls.push([url,options]);
    if(options.method==='DELETE'){items=items.map(item=>({...item,has_current_cover:false}));return {ok:true,status:204};}
    if(options.method==='POST'){items=items.filter(item=>item.kind!=='vehicle').map(item=>({...item,parent_deleted:false}));return {ok:true,status:204};}
    return {ok:true,status:200,json:async()=>url.startsWith('/api/recycle-bin')?{items}:{events:url.includes('before=')?[]:history}};
  }};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/limousine/presentation/web/static/web/recycle-bin.js'),'utf8'),context);
  await new Promise(resolve=>setImmediate(resolve));
  const list=nodes.get('deleted-list');
  assert.equal(list.children.length,2);
  assert.equal(list.children[0].children[1].disabled,false);
  assert.equal(list.children[1].children[1].disabled,true);
  assert.equal(list.children[1].children[0].children[1].textContent,'<script>file</script>');
  assert.equal(nodes.get('activity-list').children.length,100);
  assert.equal(nodes.get('older-activity').hidden,false);
  await nodes.get('older-activity').handlers.click();
  assert.ok(calls.some(([url])=>url.includes('before=101')));
  assert.equal(nodes.get('older-activity').hidden,true);
  await list.children[0].children[1].handlers.click();
  assert.ok(calls.some(([url,options])=>url==='/api/recycle-bin/vehicle/1/restore/'&&options.method==='POST'&&options.headers['X-CSRFToken']==='csrf'));
  assert.equal(list.children.length,1);assert.equal(list.children[0].children[1].disabled,false);
  document.documentElement.lang='ar';events['hspace:language']();
  assert.equal(list.children[0].children[1].textContent,'\u0627\u0633\u062a\u0631\u062c\u0627\u0639');
  items.push({kind:'cover',id:3,vehicle_id:1,plate_number:'050-001',label:'old.png',parent_deleted:false,has_current_cover:true,created_at:stamp,deleted_at:stamp});
  await nodes.get('refresh-trash').handlers.click();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(list.children[1].children.length,3);
  await list.children[1].children[2].handlers.click();
  assert.ok(calls.some(([url,options])=>url==='/api/vehicles/1/cover/'&&options.method==='DELETE'&&options.headers['X-CSRFToken']==='csrf'));
  assert.equal(list.children[1].children.length,2);
  console.log('Recycle UI parent-first gating, actor history, safe labels, cursor pagination, CSRF restoration and Arabic passed.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
