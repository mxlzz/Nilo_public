async function refresh(){
 try{
  let response=await fetch('/api/state',{cache:'no-store'});
  if(!response.ok)throw Error('No se pudo consultar el mundo.');
  let current=await response.json();
  if(!current.review_initialized){
   const seed={};
   for(const t of Object.keys(TAB_GROUPS)){
    if(t==='notes'||t==='chat')continue;
    seed[t]=Array.isArray(locallyReviewed[t])?locallyReviewed[t]:
      (t==='proposals'?[]:tabEntries(t,current));
   }
   const init=await fetch('/api/review-bootstrap',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({seen:seed})});
   if(!init.ok)throw Error('No se pudo recuperar la lectura anterior.');
   response=await fetch('/api/state',{cache:'no-store'});
   if(!response.ok)throw Error('No se pudo consultar la lectura migrada.');
   current=await response.json();
  }
  for(const t of Object.keys(current.review_seen||{})){
   locallyReviewed[t]=current.review_seen[t];
  }
  saveLocal('nilo.tabReview.v1',locallyReviewed);
  show(current);
 }catch(error){
  console.error(error);
  el('online').textContent='Sin conexión';
  el('statusdot').className='dot off';
 }
}
async function settings(obj){try{await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});await refresh()}catch(e){console.error(e)}}
document.addEventListener('click',async ev=>{
 const button=ev.target.closest('[data-related-category][data-related-id]');
 if(!button)return;
 ev.preventDefault();ev.stopPropagation();
 const origin=linkedReadOrigin(button);
 const previous=captureRecordLocation();
 try{
  const opened=await openRelatedRecord(button.dataset.relatedCategory,button.dataset.relatedId);
  if(opened)pushRecordLocation(previous);
 }finally{await markLinkedOriginRead(origin)}
});
el('record-dialog-back').onclick=restoreRecordLocation;
el('record-close').onclick=()=>el('record-dialog').close();
document.addEventListener('click',ev=>{
 const k=ev.target.closest('[data-knowledge-jump]');
 if(k&&data){switchTab('findings');const node=[...el('feed').querySelectorAll('[data-knowledge-record]')].find(x=>x.dataset.knowledgeRecord===k.dataset.knowledgeJump);if(node){node.classList.add('record-target');node.scrollIntoView({block:'center',behavior:'smooth'})}return}
 const tool=ev.target.closest('[data-tool-jump]');
 if(tool&&data){openRelatedRecord('tool',tool.dataset.toolJump);return}
});

el('feed').addEventListener('click',ev=>{
 const filter=ev.target.closest('[data-proposal-filter]');
 if(filter){proposalFilter=filter.dataset.proposalFilter;lastFeedSig='';drawFeed();return}
 const activity=ev.target.closest('[data-activity-view]');
 if(activity){activityView=activity.dataset.activityView;lastFeedSig='';drawFeed();return}
 const creation=ev.target.closest('[data-creation-view]');
 if(creation){creationView=creation.dataset.creationView;lastFeedSig='';drawFeed();return}
 const essay=ev.target.closest('[data-essay-view]');
 if(essay){essayView=essay.dataset.essayView;lastFeedSig='';drawFeed();return}
});
el('feed').addEventListener('click',async ev=>{
 const link=ev.target.closest('[data-measurement-id]');
 if(!link)return;
 ev.preventDefault();ev.stopPropagation();
 const origin=linkedReadOrigin(link);
 const previous=captureRecordLocation();
 try{
  const opened=await openMeasurement(link.dataset.measurementId);
  if(opened)pushRecordLocation(previous);
 }finally{await markLinkedOriginRead(origin)}
});
el('feed').addEventListener('click',async ev=>{
 const btn=ev.target.closest('[data-diagnostic]');if(!btn)return;
 ev.preventDefault();ev.stopPropagation();btn.disabled=true;
 try{
  const response=await fetch('/api/diagnostic?id='+encodeURIComponent(btn.dataset.diagnostic),{cache:'no-store'});
  const packet=await response.json();
  if(!response.ok)throw Error(packet.error||'No pude obtener el informe.');
  const blob=new Blob([JSON.stringify(packet,null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const link=document.createElement('a');
  link.href=url;link.download='nilo-informe-'+packet.proposal_id+'.json';
  document.body.appendChild(link);link.click();link.remove();
  URL.revokeObjectURL(url);
 }catch(error){alert(error.message)}
 finally{btn.disabled=false}
});
el('feed').addEventListener('click',async ev=>{let btn=ev.target.closest('[data-review]');if(!btn)return;
 ev.preventDefault();ev.stopPropagation();let reason=el('feed').querySelector(`[data-reason="${btn.dataset.id}"]`)?.value?.trim()||'';
 if(!reason){alert('Escribí el fundamento de la decisión.');return}
 btn.disabled=true;
 try{let r=await fetch('/api/review-rule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:btn.dataset.id,decision:btn.dataset.review,reason})});let j=await r.json();if(!r.ok)throw Error(j.error||'Falló la evaluación');await refresh()}
 catch(e){alert(e.message);btn.disabled=false}
});
async function markRead(category,id,single=false){let res=await fetch('/api/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({category,id,single})});let result=await res.json();if(!res.ok||result.ok!==true)throw Error(result.error||'No se pudo guardar la lectura');await refresh()}
// Un clic sobre una tarjeta pendiente confirma únicamente ese registro.
const readingPending=new Set();
function linkedReadOrigin(element){
 const feed=el('feed');
 if(!feed.contains(element))return null;
 const card=element.closest('[data-entry-id],[data-review-entry-key]');
 if(!card||!feed.contains(card))return null;
 const entryTab=tab,id=card.dataset.entryId;
 if(id&&(entryTab==='notes'||entryTab==='activity')){
  const record=(entryTab==='notes'?data?.journal:data?.news)?.find(x=>String(x.id)===String(id));
  if(record&&!record.read&&!record.writing)
   return {kind:'entry',tab:entryTab,id:String(id),
     category:entryTab==='notes'?'journal':'news'};
 }
 const key=card.dataset.reviewEntryKey;
 return key?{kind:'review',tab:entryTab,key}:null;
}
async function markLinkedOriginRead(origin){
 if(!origin)return;
 if(origin.kind==='review'){
  await markLocalEntryRead(origin.key,origin.tab);
  return;
 }
 const token=origin.tab+':'+origin.id;
 if(readingPending.has(token))return;
 readingPending.add(token);
 try{await markRead(origin.category,origin.id,true)}
 catch(error){alert(error.message)}
 finally{readingPending.delete(token)}
}
function relatedReadKeys(source,keys){
 // Una misma conclusión está visible en Hallazgos y Ensayos.
 const updates={[source]:[...keys]};
 if(source==='findings'||source==='measurements'){
  const target=source==='findings'?'measurements':'findings';
  const shared=new Set((data?.conclusions||[]).map(c=>String(c.id)));
  const aliases=keys.filter(key=>shared.has(key)&&tabEntries(target,data).includes(key));
  if(aliases.length)updates[target]=aliases;
 }
 return updates;
}
async function persistTabRead(tabName,keys){
 if(!keys.length)return;
 const response=await fetch('/api/review-mark',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({tab:tabName,keys})});
 if(!response.ok)throw Error('No se pudo guardar la lectura.');
}
async function markLocalEntryRead(key,entryTab=tab){
 const updates=relatedReadKeys(entryTab,[key]);
 if((locallyReviewed[entryTab]||[]).includes(key))return;
 const backup={};
 for(const [t,keys] of Object.entries(updates)){
  backup[t]=[...(locallyReviewed[t]||[])];
  locallyReviewed[t]=[...new Set([...backup[t],...keys])];
 }
 saveLocal('nilo.tabReview.v1',locallyReviewed);
 el('feed').querySelectorAll('[data-review-entry-key]').forEach(node=>{
  if(node.dataset.reviewEntryKey===key)node.classList.remove('new-record');
 });
 updateTabNotifications();updateReadActions();
 try{await Promise.all(Object.entries(updates).map(([t,keys])=>persistTabRead(t,keys)))}
 catch(error){
  Object.assign(locallyReviewed,backup);
  saveLocal('nilo.tabReview.v1',locallyReviewed);
  lastFeedSig='';drawFeed();updateTabNotifications();updateReadActions();
  alert(error.message);
 }
}
el('feed').addEventListener('click',async ev=>{
 if(ev.target.closest('button,input,select,textarea,a,[contenteditable]'))return;
 const card=ev.target.closest('[data-entry-id],[data-review-entry-key]');
 if(!card||!el('feed').contains(card))return;
 if(tab==='notes'||(tab==='activity'&&card.dataset.entryId)){
  const id=card.dataset.entryId;
  const item=(tab==='notes'?data?.journal:data?.news)?.find(n=>String(n.id)===String(id));
  if(!id||!item||item.read||item.writing||readingPending.has(tab+':'+id))return;
  const token=tab+':'+id;readingPending.add(token);
  try{await markRead(tab==='notes'?'journal':'news',id,true)}
  catch(err){alert(err.message)}finally{readingPending.delete(token)}
  return;
 }
 if(card.dataset.reviewEntryKey)markLocalEntryRead(card.dataset.reviewEntryKey);
});
el('read-tab').onclick=async()=>{
 if(!data||tab==='chat'||!tabHasUpdates(tab,data))return;
 const selected=tab;
 const btn=el('read-tab');btn.disabled=true;
 try{
  if(selected==='notes'||selected==='activity'){
   const category=selected==='notes'?'journal':'news';
   const res=await fetch('/api/read-all',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({categories:[category]})});
   if(!res.ok)throw Error('No se pudo marcar esta solapa como leída');
   if(selected==='activity'){
    const eventKeys=tabEntries('activity',data);
    await persistTabRead('activity',eventKeys);
    locallyReviewed.activity=eventKeys;
    saveLocal('nilo.tabReview.v1',locallyReviewed);
   }
   await refresh();
  }else{
   // Acusar lectura de Propuestas no significa aceptarlas/rechazarlas.
   const keys=tabEntries(selected,data);
   const updates=relatedReadKeys(selected,keys);
   for(const [t,group] of Object.entries(updates))await persistTabRead(t,group);
   for(const [t,group] of Object.entries(updates))
    locallyReviewed[t]=[...new Set([...(locallyReviewed[t]||[]),...group])];
   saveLocal('nilo.tabReview.v1',locallyReviewed);
   lastFeedSig='';
   updateTabNotifications();
   updateReadActions();
   drawFeed();
  }
 }catch(e){alert(e.message);updateReadActions()}
};
el('read-summary').onclick=async()=>{try{let res=await fetch('/api/read-summary',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!res.ok)throw Error('No pude marcar el resumen');await refresh()}catch(e){alert(e.message)}};

function pendingOverview(source,s){
 if(!s)return [];
 if(source!=='notes')tabHasUpdates(source,s);
 const seen=new Set(locallyReviewed[source]||[]),out=[];
 const add=(key,title,detail,kind,id)=>{
  if(key&&!seen.has(key))out.push({key:String(key),title:String(title||'Sin título'),detail:String(detail||''),kind,id:String(id||'')});
 };
 if(source==='notes')return (s.journal||[]).filter(n=>!n.read&&!n.writing).map(n=>({title:n.when+' · Cuaderno',detail:n.visible_text||n.text||'',kind:'note',id:String(n.id)}));
 if(source==='activity'){
  const news=s.news||[];
  for(const n of news)if(!n.read)out.push({title:n.when+' · '+n.title,detail:newsExtra(n),kind:'news',id:String(n.id)});
  for(const e of s.events||[])if(!news.some(n=>e.text===n.title||e.text.startsWith(String(n.title||'').replace(/…$/,''))))add(String(e.id??e.when+':'+e.text),e.when+' · Hecho',e.text,'event',e.id);
 }
 if(source==='research'){
  for(const q of s.research||[])add(String(q.id??q.started+':'+q.question)+':'+String(q.state),q.question,q.hypothesis,'research',q.id);
  for(const p of s.prediction_log||[])add(String(p.id)+':'+p.status,p.hypothesis,p.expected_effect+' · '+p.status,'prediction',p.id);
 }
 if(source==='measurements'){
  for(const m of s.measurements||[])add(String(m.id),measurementActionTitle(m),(m.verified_facts||[]).join('; '),'measurement',m.id);
  for(const c of s.conclusions||[])add(String(c.id),c.text,c.scope,'conclusion',c.id);
 }
 if(source==='findings'){
  for(const c of s.conclusions||[])add(String(c.id),c.text,c.scope,'finding',c.id);
  for(const [k,v] of s.knowledge||[])add(String(k),v,'Conocimiento registrado por el motor','knowledge',k);
 }
 if(source==='creations'){
  for(const d of s.designs||[])add(String(d.id??d.name)+':'+String(d.versions?.at(-1)?.version)+':'+String(d.status),d.name,d.status,'design',d.id);
  for(const o of [...(s.structures||[]),...(s.retired_structures||[]),...(s.items||[])])add(String(o.id??o.name)+':'+String(o.revision||1),o.name,o.purpose||o.status,'plan',o.id||o.name);
 }
 if(source==='projects')for(const p of [...(s.project?[s.project]:[]),...(s.projects||[])])add(String(p.id)+':'+String(p.status),p.title,p.state||p.reason,'project',p.id);
 if(source==='agenda'){
  for(const a of s.agenda||[])add(String(a.id)+':'+a.estado,a.titulo,agendaCondition(a.cuando),'agenda',a.id);
 }
 if(source==='identity')for(const e of s.experience_summary||[])add(String(e.id??e.when+':'+e.fact),e.fact,e.when,'experience',e.when);
 if(source==='habits'){
  for(const h of s.waiting_history||[])add(String(h.id??h.when+':'+h.action),h.fact||h.reason,h.when,'habit',h.when);
  for(const a of s.skills||[])add(String(a.key)+':'+String(a.count),a.target||a.op,a.last_fact,'skill',a.key);
 }
 if(source==='proposals')for(const p of s.proposals||[])if(p.status==='pendiente')add(String(p.id??p.title)+':pendiente',p.title||p.phenomenon,p.rationale,'proposal',p.id);
 return out;
}
let pendingOverviewItems=[],pendingOverviewTab='notes';
let summaryContinuation=null,summaryLoading=false,summaryGeneration=0,summaryViewCache=null;
function syncSummaryActions(){el('catchup-more').hidden=!summaryContinuation||summaryLoading;el('catchup-more').disabled=summaryLoading;}
async function openPendingOverview(){
 if(summaryLoading)return;
 summaryGeneration++;
 summaryContinuation=null;
 summaryViewCache=null;
 el('catchup-history').hidden=false;
 el('catchup-back').hidden=true;
 syncSummaryActions();
 el('catchup-title').textContent='¿Qué me perdí?';
 el('catchup-description').textContent='Síntesis de los acontecimientos más importantes.';
 el('catchup-content').innerHTML='';
 if(!el('catchup-dialog').open)el('catchup-dialog').showModal();
 await renderNextObserverSummary(null,summaryGeneration);
}
async function renderNextObserverSummary(continuation,generation){
 if(summaryLoading)return;
 summaryLoading=true;
 syncSummaryActions();
 const box=el('catchup-content');
 const loading=document.createElement('p');
 loading.className='small';
 loading.textContent=continuation?'Buscando otros acontecimientos relevantes…':'Preparando síntesis narrativa…';
 box.appendChild(loading);
 const candidates=[];
 for(const source of Object.keys(TAB_GROUPS)){
  if(source==='notes'||source==='chat')continue;
  for(const item of pendingOverview(source,data)){
   if(item.key&&item.id)candidates.push({tab:source,key:item.key,kind:item.kind,id:item.id});
  }
 }
 try{
  const response=await fetch('/api/summary-generate',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({candidates,continuation})});
  const packet=await response.json();
  if(!response.ok)throw Error(packet.error||'No se pudo generar el resumen.');
  if(generation!==summaryGeneration)return;
  loading.remove();
  if(packet.empty){
   if(!continuation)box.innerHTML='<p>'+esc(packet.text)+'</p>';
   else{
    const note=document.createElement('p');
    note.className='small';note.textContent=packet.text;
    box.appendChild(note);
   }
   if(packet.id){
    const ack=await fetch('/api/summary-ack',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({id:packet.id})});
    if(!ack.ok)throw Error('El resumen rutinario se conservó, pero no se confirmó su lectura.');
    box.insertAdjacentHTML('beforeend','<p class="summary-review-count">'+esc(packet.reviewed||0)+' registros rutinarios revisados.</p>');
    await refresh();
   }
   summaryContinuation=null;
   syncSummaryActions();
   return;
  }
  let html=(continuation?'<div class="record-summary">':'<div>')+
   '<div class="observer-report">'+esc(packet.text)+'</div>';
  const links=(packet.links||[]);
  if(links.length){
   // Agrupar referencias por categoría; cada enlace conserva su ID real.
   const grouped=new Map();
   for(const item of links){
    const group=RECORD_LABELS[item.category]||item.kind||'Registro';
    if(!grouped.has(group))grouped.set(group,[]);
    if(!grouped.get(group).some(x=>x.category===item.category&&x.id===item.id))grouped.get(group).push(item);
   }
   html+='<details class="summary-references"><summary>Registros destacados ('+esc(links.length)+')</summary>';
   for(const [label,items] of grouped){
    html+='<details class="summary-ref-group"><summary>'+esc(label)+' ('+items.length+')</summary><div class="record-links-items">'+
     items.map(item=>'<button type="button" class="record-link" data-related-category="'+esc(item.category)+
       '" data-related-id="'+esc(item.id)+'">'+esc(String(item.title||item.id).slice(0,95))+'</button>').join('')+'</div></details>';
   }
   html+='</details>';
  }
  const contextual=packet.related_links||[];
  if(contextual.length){
   html+='<details class="summary-references"><summary>Registros vinculados revisados ('+contextual.length+')</summary>'+
      '<div class="record-links-items">'+contextual.map(recordLinkMarkup).join('')+'</div></details>';
  }
  if(packet.omitted)html+='<p class="summary-review-count">'+esc(packet.omitted)+' registros secundarios evaluados y omitidos de la síntesis.</p>';
  if(packet.reviewed)html+='<p class="summary-review-count">'+esc(packet.reviewed)+' marcadores de lectura examinados en esta entrega'+
      (packet.remaining?' · '+esc(packet.remaining)+' acontecimientos destacados para «¿Qué más?»':'')+'.</p>';
  html+='</div>';
  box.insertAdjacentHTML('beforeend',html);
  summaryContinuation=packet.continuation||null;
  // Acreditar primero la página que realmente se mostró; no perder la
  // posibilidad de continuar si durante la respuesta llegan nuevas entradas.
  try{
   const ack=await fetch('/api/summary-ack',{method:'POST',
     headers:{'Content-Type':'application/json'},body:JSON.stringify({id:packet.id})});
   if(!ack.ok)throw Error('No se pudo confirmar la lectura de las fichas incluidas.');
   await refresh();
   if(generation!==summaryGeneration)return;
   syncSummaryActions();
  }catch(error){
   summaryContinuation=null;
   syncSummaryActions();
   const warning=document.createElement('p');
   warning.className='small';
   warning.textContent='El resumen se conservó, pero las fichas siguen pendientes: '+error.message;
   box.appendChild(warning);
  }
 }catch(error){
  if(generation!==summaryGeneration)return;
  loading.remove();
  const errorText=document.createElement('p');
  errorText.className='small';
  errorText.textContent=error.message;
  box.appendChild(errorText);
 }finally{summaryLoading=false;syncSummaryActions()}
}
el('catchup-more').onclick=()=>{if(!summaryLoading&&summaryContinuation)renderNextObserverSummary(summaryContinuation,summaryGeneration)};
async function openObserverHistory(){
 if(summaryLoading)return;
 if(el('catchup-title').textContent!=='Historial de resúmenes'){
  summaryViewCache={title:el('catchup-title').textContent,
    description:el('catchup-description').textContent,html:el('catchup-content').innerHTML};
 }
 el('catchup-more').hidden=true;
 el('catchup-history').hidden=true;
 el('catchup-back').hidden=!summaryViewCache;
 el('catchup-title').textContent='Historial de resúmenes';
 el('catchup-description').textContent='Resúmenes anteriores, conservados con su fecha. Releerlos no modifica las notificaciones.';
 el('catchup-content').innerHTML='<p class="small">Cargando historial…</p>';
 if(!el('catchup-dialog').open)el('catchup-dialog').showModal();
 try{
  const response=await fetch('/api/summary-history',{cache:'no-store'});
  const packet=await response.json();
  if(!response.ok)throw Error(packet.error||'No se pudo consultar el historial.');
  const history=packet.summaries||[];
  el('catchup-content').innerHTML=history.length?history.map(x=>
   '<details class="observer-history-item"><summary>'+
    esc(new Date(x.at*1000).toLocaleString('es-AR',{dateStyle:'medium',timeStyle:'short'}))+
    ' · '+esc(x.count)+' registros</summary><div class="observer-report">'+esc(x.text)+'</div>'+
    ((x.links||[]).length?'<div class="record-links"><div class="record-links-title">Registros originales</div><div class="record-links-items">'+
      x.links.map(recordLinkMarkup).join('')+'</div></div>':'')+'</details>'
  ).join(''):'<p class="small">Todavía no se generaron resúmenes.</p>';
 }catch(error){el('catchup-content').innerHTML='<p class="small">'+esc(error.message)+'</p>'}
}
el('catchup-history').onclick=openObserverHistory;
el('catchup-back').onclick=()=>{
 if(!summaryViewCache)return;
 el('catchup-title').textContent=summaryViewCache.title;
 el('catchup-description').textContent=summaryViewCache.description;
 el('catchup-content').innerHTML=summaryViewCache.html;
 el('catchup-history').hidden=false;
 el('catchup-back').hidden=true;
 summaryViewCache=null;
 syncSummaryActions();
};
el('catchup-shortcut').onclick=openPendingOverview;
el('catchup-close').onclick=()=>el('catchup-dialog').close();
el('catchup-content').addEventListener('click',ev=>{
 const button=ev.target.closest('[data-pending-index]');if(!button)return;
 const item=pendingOverviewItems[Number(button.dataset.pendingIndex)];if(!item)return;
 el('catchup-dialog').close();
 if(item.kind==='news')activityView='featured';
 if(item.kind==='event')activityView='all';
 if(item.kind==='measurement')essayView='all';
 if(item.kind==='plan'||item.kind==='design')creationView='all';
 switchTab(pendingOverviewTab);
 const attr={note:'entry-id',news:'entry-id',event:'event-record',research:'research-record',prediction:'prediction-record',
  measurement:'measurement-record',conclusion:'conclusion-record',finding:'finding-record',knowledge:'knowledge-record',
  plan:'plan-id',design:'design-record',project:'project-record',agenda:'agenda-record',proposal:'proposal-id'}[item.kind];
 const node=attr?[...el('feed').querySelectorAll('[data-'+attr+']')].find(n=>n.getAttribute('data-'+attr)===item.id):null;
 if(node){if(node.tagName==='DETAILS')node.open=true;node.scrollIntoView({block:'center',behavior:'smooth'});}
 else if(item.kind==='note'||item.kind==='news'){
  el('catchup-title').textContent=item.title;
  el('catchup-description').textContent='Registro histórico fuera de la vista reciente.';
  el('catchup-content').innerHTML='<p>'+esc(item.detail)+'</p><button type="button" data-archive-read="'+esc(item.id)+'" data-archive-kind="'+item.kind+'">Marcar este registro como leído</button>';
  el('catchup-dialog').showModal();
 }
});
el('catchup-content').addEventListener('click',async ev=>{
 const btn=ev.target.closest('[data-archive-read]');if(!btn)return;
 btn.disabled=true;
 try{await markRead(btn.dataset.archiveKind==='note'?'journal':'news',btn.dataset.archiveRead,true);el('catchup-dialog').close()}
 catch(error){alert(error.message);btn.disabled=false}
});
let map=el('map');
map.addEventListener('click',ev=>{
 const node=ev.target.closest('[data-x]');
 if(!node||!data)return;
 const layer=mapLayer==='follow'?String(data.position[2]):mapLayer;
 const cell=node.dataset.x+','+node.dataset.y;
 const found=data.structure_cell_lists?.[layer]?.[cell]||[];
 if(!found.length){
  const single=data.structure_layers?.[layer]?.[cell];if(single)openPlanForBuilding(single.id||single.name);
  return;
 }
 if(found.length===1){openPlanForBuilding(found[0].id||found[0].name);return;}
 const options=found.map((b,i)=>(i+1)+'. '+b.name+' · '+(b.id||'sin ID')).join('\n');
 const choice=prompt('Hay varias construcciones en esta casilla. Elegí una:\n'+options);
 if(choice===null)return;
 const index=Number(choice)-1;
 if(Number.isInteger(index)&&found[index])openPlanForBuilding(found[index].id||found[index].name);
});
map.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();ev.target.click()}});
el('buildings').addEventListener('click',ev=>{
 const button=ev.target.closest('.building');
 if(!button||!data)return;
 const building=data.structures.find((b,i)=>(b.id||String(i))===button.dataset.id);
 if(building)openPlanForBuilding(building.id||building.name);
});
function openPlanForBuilding(id){
 creationView='objects';switchTab('creations');
 const target=[...el('feed').querySelectorAll('[data-plan-id]')].find(node=>node.dataset.planId===id);
 if(!target){alert('No encuentro el plano de esta construcción en la vista actual.');return false;}
 target.open=true;
 target.querySelectorAll('details.physical-details').forEach(item=>item.open=true);
 target.scrollIntoView({block:'start',behavior:'smooth'});
 return true;
}
function saveMapView(){saveLocal('nilo.mapView.v1',{view,mapLayer,showTrail})}
el('layerselect').onchange=ev=>{mapLayer=ev.target.value;saveMapView();showMap()};
el('near').onclick=()=>{view='near';saveMapView();showMap()};
el('full').onclick=()=>{view='full';saveMapView();showMap()};
el('trailtoggle').onclick=()=>{showTrail=!showTrail;saveMapView();showMap()};
function adjustZoom(delta){mapZoom[view]=Math.max(10,Math.min(38,mapZoom[view]+delta));saveLocal('nilo.mapZoom.v2',mapZoom);showMap()}
el('zoomin').onclick=()=>adjustZoom(2);el('zoomout').onclick=()=>adjustZoom(-2);
el('map-toggle').onclick=()=>setMapDisplay(mapDisplay==='none'?'both':'none');
document.querySelectorAll('[data-resource-tab]').forEach(button=>{
 button.onclick=()=>setResourceTab(button.dataset.resourceTab);
 button.onkeydown=ev=>{
  if(!['ArrowRight','ArrowLeft','Home','End'].includes(ev.key))return;
  ev.preventDefault();
  const i=RESOURCE_TABS.indexOf(button.dataset.resourceTab);
  const next=ev.key==='Home'?0:ev.key==='End'?RESOURCE_TABS.length-1:
   (i+(ev.key==='ArrowRight'?1:RESOURCE_TABS.length-1))%RESOURCE_TABS.length;
  setResourceTab(RESOURCE_TABS[next]);
  el('resource-tab-'+RESOURCE_TABS[next]).focus();
 };
});
setMapDisplay(mapDisplay);
setResourceTab(resourceTab);
document.querySelectorAll('[data-speed]').forEach(b=>b.onclick=()=>settings({speed:+b.dataset.speed}));el('pause').onclick=()=>settings({paused:!data?.paused});el('autopause').onclick=()=>settings({auto_pause_on_wait:!data?.auto_pause_on_wait});el('retryllm').onclick=async()=>{const btn=el('retryllm');btn.disabled=true;el('retrymsg').textContent='Solicitando reintento…';try{let r=await fetch('/api/retry-llm',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});let j=await r.json();el('retrymsg').textContent=j.reason||'Sin respuesta';await refresh()}catch(e){el('retrymsg').textContent='No se pudo conectar.'}finally{btn.disabled=false}};function recentTabEntry(t){
 if(t==='chat'){
  const pane=el('chatfeed');
  pane.scrollTop=pane.scrollHeight;
  return;
 }
 const feed=el('feed');
 feed.scrollTop=0;
 // En vista apilada el documento también puede desplazarse.
 const panel=feed.closest('.panel.third');
 if(panel&&window.getComputedStyle(feed).overflowY!=='auto'){
  panel.scrollIntoView({block:'start',behavior:'smooth'});
 }
}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{
 switchTab(b.dataset.tab);
 recentTabEntry(b.dataset.tab);
});document.querySelectorAll('[data-group]').forEach(b=>b.onclick=()=>switchTab(GROUP_DEFAULT[b.dataset.group]));refreshGroupNav();
el('chatform').addEventListener('submit',async ev=>{ev.preventDefault();let message=el('chatinput').value.trim();if(!message)return;el('chatsend').disabled=true;el('chaterror').textContent='';try{let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});let j=await r.json();if(!r.ok)throw Error(j.error||'No se pudo enviar.');el('chatinput').value='';await refresh()}catch(e){el('chaterror').textContent=e.message;el('chatsend').disabled=false}});
// Notificaciones nativas de Windows/navegador (solo si la pestaña está en segundo plano).
function processNotifications(state){
 const incoming=[...(state.news||[]).map(n=>({type:'news',id:n.id,seq:n.seq,text:newsExtra(n)||'Abrí Nilo para consultar el hecho registrado.',title:n.title})),
     ...(state.journal||[]).filter(n=>!n.writing).map(n=>({type:'journal',id:n.id,seq:n.seq,title:'Nueva entrada en el cuaderno',text:n.text}))];
 if(!notifyInitialized){for(const n of incoming)seenEntries.add(n.type+':'+n.id);notifyInitialized=true;return}
 let updates=incoming.filter(n=>!seenEntries.has(n.type+':'+n.id));
 for(let n of updates)seenEntries.add(n.type+':'+n.id);
 if(notifyPrefs.mode==='off'||!document.hidden||!('Notification' in window)||Notification.permission!=='granted')return;
 updates=updates.filter(n=>notifyPrefs.source==='both'||notifyPrefs.source===n.type);
 // Se limitan los avisos simultáneos al reanudar la ventana; el resto sigue sin leer.
 for(let n of updates.slice(0,3))sendNotification(n);
 if(updates.length>3)sendNotification({type:'news',title:'Nilo tiene novedades pendientes',text:`${updates.length-3} entradas adicionales sin mostrar individualmente.`,id:null});
}
function sendNotification(item){try{
 const name=notifyPrefs.mode==='brief'?(item.type==='journal'?'Nueva entrada en el cuaderno':'Hay una nueva novedad'):(item.title||'Nilo');
 const body=notifyPrefs.mode==='brief'?'Abrí Nilo para leerla.':String(item.text||'').slice(0,500);
 const alert=new Notification('Nilo · '+name,{body,tag:'nilo-'+item.type+'-'+(item.id||'resumen'),silent:false});
 alert.onclick=()=>{window.focus();switchTab(item.type==='journal'?'notes':'activity');setTimeout(()=>{const entry=[...document.querySelectorAll('[data-entry-id]')].find(e=>e.dataset.entryId===item.id);if(entry){if(entry.tagName==='DETAILS')entry.open=true;entry.scrollIntoView({behavior:'smooth',block:'center'})}},120);alert.close()};
 }catch(e){console.warn('No se pudo mostrar el aviso',e)}}
function populateNotificationSettings(){el('notify-mode').value=notifyPrefs.mode;el('notify-source').value=notifyPrefs.source;el('notify-status').textContent=!('Notification' in window)?'El navegador no admite notificaciones.':`Permiso actual: ${Notification.permission}. Se muestran cuando minimizás el navegador.`}
function showSettingsTab(section){
 const chosen=['alerts','model','versions'].includes(section)?section:'alerts';
 el('settings-alerts').hidden=chosen!=='alerts';
 el('settings-model').hidden=chosen!=='model';
 el('settings-versions').hidden=chosen!=='versions';
 if(chosen==='versions')el('versions-content').innerHTML=data?renderVersions():'Sin datos de la partida.';
 document.querySelectorAll('[data-setting-tab]').forEach(button=>{
  const active=button.dataset.settingTab===chosen;
  button.classList.toggle('active',active);
  button.setAttribute('aria-pressed',String(active));
 });
}
document.querySelectorAll('[data-setting-tab]').forEach(button=>button.onclick=()=>showSettingsTab(button.dataset.settingTab));
el('research-filter').addEventListener('change',ev=>{
 if(tab!=='research'||!RESEARCH_VIEWS.includes(ev.target.value))return;
 researchView=ev.target.value;
 saveLocal('nilo.researchView.v1',researchView);
 lastFeedSig='';drawFeed();
});
el('status-filter').addEventListener('change',ev=>{
 if(!['agenda','projects'].includes(tab)||!STATUS_VIEW_KEYS.includes(ev.target.value))return;
 statusViews[tab]=ev.target.value;
 saveLocal('nilo.statusViews.v1',statusViews);
 lastFeedSig='';drawFeed();
});
el('indicator-inline').addEventListener('change',ev=>{
 if(!Object.hasOwn(TAB_GROUPS,tab)||!['normal','subtle','off'].includes(ev.target.value))return;
 indicatorModes[tab]=ev.target.value;
 saveLocal('nilo.tabIndicators.v1',indicatorModes);
 updateTabNotifications();
});
el('notify-open').onclick=()=>{populateNotificationSettings();showSettingsTab('alerts');el('notify-dialog').showModal()};
for(const [control,key] of [['notify-mode','mode'],['notify-source','source']])el(control).onchange=ev=>{notifyPrefs[key]=ev.target.value;saveLocal('nilo.notifications.v1',notifyPrefs)};
el('notify-activate').onclick=async()=>{if(!('Notification' in window)){populateNotificationSettings();return}await Notification.requestPermission();populateNotificationSettings()};
el('notify-test').onclick=()=>{if('Notification' in window&&Notification.permission==='granted')sendNotification({type:'news',title:'Aviso de prueba',text:'Esta es una notificación de prueba.',id:null});else el('notify-status').textContent='Primero activá y autorizá las notificaciones.'};
bootstrapUIPrefs().finally(()=>refresh());setInterval(refresh,2000);setInterval(animateWriting,130);
