function drawFeed(){
 closeSectionHelp();
 let content='';
 if(tab==='notes')content=renderNotes();
 else if(tab==='activity')content=renderActivity();
 else if(tab==='research')content=renderResearch();
 else if(tab==='measurements')content=renderMeasurements();
 else if(tab==='findings')content=renderFindings();
 else if(tab==='creations')content=renderCreations();
 else if(tab==='identity')content=renderIdentity();
 else if(tab==='proposals')content=renderProposals();
 else if(tab==='habits')content=renderHabits();
 else if(tab==='agenda')content=renderAgenda();
 else if(tab==='projects')content=[...(data.project?[data.project]:[]),...(data.projects||[])].filter(p=>matchesStatusView(p,'projects')).map(oneProject).join('');
 const sig=tab+':'+(tab==='proposals'?proposalFilter:'')+':'+(tab==='notes'?JSON.stringify(data.journal.map(j=>[j.id,j.visible_text,j.read])):tab==='activity'?JSON.stringify([activityView,data.news,data.events]):tab==='research'?JSON.stringify([researchView,data.research,data.prediction_log]):tab==='measurements'?JSON.stringify([essayView,data.measurements,data.conclusions,data.experiment_status,focusedMeasurement?.id]):tab==='findings'?JSON.stringify([data.conclusions,data.knowledge]):tab==='creations'?JSON.stringify([creationView,data.designs,data.structures,data.retired_structures,data.items]):tab==='projects'?JSON.stringify([selectedStatusView('projects'),data.project,data.projects,data.agenda]):tab==='identity'?JSON.stringify([data.preferences,data.experience_summary,data.life_chapters]):tab==='habits'?JSON.stringify([data.skills,data.waiting_preferences,data.waiting_history,data.waiting_state,data.maintenance,data.behavior]):tab==='agenda'?JSON.stringify([selectedStatusView('agenda'),data.agenda,data.agenda_history]):JSON.stringify(data.proposals));
 const fullSig=sig+JSON.stringify(data.record_relations||{});
 if(fullSig===lastFeedSig)return;
 const expanded=renderedFeedTab===tab?feedExpandedDetails():new Set();
 lastFeedSig=fullSig;
 el('feed').innerHTML=content||'<div class="empty">Todavía no hay registros.</div>';
 relocateExplainer();
 if(!['notes','chat'].includes(tab))decorateRecords();
 restoreFeedExpandedDetails(expanded);
 assignAccordionGroups();
 renderedFeedTab=tab;
}
document.addEventListener('click',event=>{
 const trigger=event.target.closest('button.section-help');
 if(trigger){event.preventDefault();openSectionHelp(trigger);return;}
 if(floatingHelp&&!floatingHelp.panel.contains(event.target))closeSectionHelp();
});
document.addEventListener('keydown',event=>{
 if(event.key==='Escape'&&floatingHelp){event.preventDefault();closeSectionHelp(true);}
});
el('feed').addEventListener('scroll',()=>closeSectionHelp(),{passive:true});
window.addEventListener('resize',()=>closeSectionHelp());
el('feed').addEventListener('toggle',event=>enforceAccordionGroup(event.target),true);
function writtenCharacters(text,elapsed){let t=0;for(let i=0;i<text.length;i++){let ch=text[i];t+=(ch===' '||ch==='\t')?.11:.17;if(t>elapsed+0.000001)return i;if(i<text.length-1){if('.!?…'.includes(ch))t+=.38;else if(',;:'.includes(ch))t+=.20;else if(ch==='\n')t+=.42}}return text.length}
function animateWriting(){if(!data||tab!=='notes'||data.speed>=300)return;let entry=data.journal.find(j=>j.writing);if(!entry)return;let node=el('feed').querySelector(`[data-note="${entry.id}"]`);if(!node)return;let since=(data.paused||data.auto_wait_frozen)?0:(Date.now()-gotAt)/1000;let remain=Math.max(0,(data.remaining_write_base_seconds??0)-since*(data.effective_speed||1));let elapsed=Math.max(0,(entry.duration_seconds||1)-remain);let content=entry.text.slice(0,writtenCharacters(entry.text,elapsed));let old=node.firstChild?.nodeValue||'';if(old!==content){if(node.firstChild&&node.firstChild.nodeType===3)node.firstChild.nodeValue=content;else node.insertBefore(document.createTextNode(content),node.firstChild)}}
function drawChat(){el('summary-actions').hidden=!data.summary_markable;let sig=JSON.stringify(data.chat)+data.chatting+data.chat_error;if(sig===lastChatSig)return;lastChatSig=sig;let box=el('chatfeed');let bottom=box.scrollHeight-box.scrollTop-box.clientHeight<65;box.innerHTML=data.chat.map(c=>`<div class="bubble ${c.role==='user'?'user':'nilo'}"><div class="date">${c.role==='user'?'VOS':'NILO'}</div>${esc(c.text)}</div>`).join('')+(data.chatting?'<p class="small">Nilo está pensando una respuesta…</p>':'');if(bottom||data.chatting)box.scrollTop=box.scrollHeight;el('chaterror').textContent=data.chat_error||'';el('chatsend').disabled=data.chatting||!data.ai.configured}
const TAB_GROUPS={notes:'diario',activity:'diario',identity:'diario',
 research:'laboratorio',measurements:'laboratorio',findings:'laboratorio',creations:'laboratorio',
 projects:'autonomia',agenda:'autonomia',habits:'autonomia',
 chat:'vinculo',proposals:'vinculo'};
const GROUP_DEFAULT={diario:'notes',laboratorio:'research',autonomia:'projects',vinculo:'chat'};

/* Señales discretas por actividad nueva. Las lecturas de Cuaderno/Novedades
   continúan siendo registradas por el servidor, no por localStorage. */
const TAB_LABELS=Object.fromEntries([...document.querySelectorAll('[data-tab]')].map(b=>[b.dataset.tab,b.textContent]));
const GROUP_LABELS=Object.fromEntries([...document.querySelectorAll('[data-group]')].map(b=>[b.dataset.group,b.textContent]));
const locallyReviewed=stored('nilo.tabReview.v1',{});
if(!locallyReviewed.activity&&Array.isArray(locallyReviewed.events))locallyReviewed.activity=locallyReviewed.events;
if(!locallyReviewed.creations&&(locallyReviewed.designs||locallyReviewed.plans))locallyReviewed.creations=[...(locallyReviewed.designs||[]),...(locallyReviewed.plans||[])];
const indicatorModes=stored('nilo.tabIndicators.v1',{});
function migrateIndicatorModes(){
 if(indicatorModes.activity===undefined&&indicatorModes.news!==undefined)indicatorModes.activity=indicatorModes.news;
 if(indicatorModes.creations===undefined)indicatorModes.creations=indicatorModes.designs??indicatorModes.plans??'normal';
 if(indicatorModes.findings===undefined&&indicatorModes.measurements!==undefined)indicatorModes.findings=indicatorModes.measurements;
}
migrateIndicatorModes();
const INDICATOR_OPTIONS={normal:'Normal · rojo y pestaña madre',subtle:'Discreto · solo esta solapa',off:'Oculto · sin indicador'};
function indicatorMode(t){return ['normal','subtle','off'].includes(indicatorModes[t])?indicatorModes[t]:'normal'}
function tabEntries(t,s){
 const x=(v,f)=>String(v??f??''),arr=v=>Array.isArray(v)?v:[];
 const signature=(items,get)=>items.filter(Boolean).map(get).filter(Boolean);
 if(t==='activity')return signature(arr(s.events),r=>x(r.id,r.when+':'+r.text));
 if(t==='research')return [...signature(arr(s.research),r=>x(r.id,r.started+':'+r.question)+':'+x(r.state)),
   ...signature(arr(s.prediction_log),r=>x(r.id)+':'+x(r.status))];
 if(t==='measurements')return [...signature(arr(s.measurements),r=>x(r.id)),
   ...(focusedMeasurement&&!arr(s.measurements).some(m=>m.id===focusedMeasurement.id)?[focusedMeasurement.id]:[]),
   ...signature(arr(s.conclusions),r=>x(r.id))];
 if(t==='findings')return [...signature(arr(s.conclusions),r=>x(r.id)),
   ...signature(arr(s.knowledge),r=>x(r[0],r[1]))];
 if(t==='creations')return [...signature(arr(s.designs),r=>x(r.id,r.name)+':'+x(r.versions?.at(-1)?.version)+':'+x(r.status)),
   ...signature([...arr(s.structures),...arr(s.retired_structures),...arr(s.items)],r=>x(r.id,r.name)+':'+x(r.revision,1))];
 if(t==='proposals')return signature(arr(s.proposals).filter(r=>r.status==='pendiente'),r=>x(r.id,r.title)+':pendiente');
 if(t==='identity')return signature(arr(s.experience_summary),r=>x(r.id,r.when+':'+r.fact));
 if(t==='habits')return [...signature(arr(s.waiting_history),r=>x(r.id,r.when+':'+r.action)),
   ...signature(arr(s.skills),r=>x(r.key)+':'+x(r.count))];
 if(t==='agenda')return signature(arr(s.agenda),r=>x(r.id)+':'+x(r.estado));
 if(t==='projects')return signature([...arr(s.projects),...(s.project?[s.project]:[])],r=>x(r.id)+':'+x(r.status));
 return [];
}
function tabHasUpdates(t,s){
 if(t==='notes')return (s.unread?.journal||0)>0;
 if(t==='activity'&&(s.unread?.news||0)>0)return true;
 const current=tabEntries(t,s);
 if(!Array.isArray(locallyReviewed[t])){
  if(t==='proposals')return current.length>0; // Las propuestas pendientes siguen visibles hasta revisarlas.
  locallyReviewed[t]=current;
  saveLocal('nilo.tabReview.v1',locallyReviewed);
  return false; // No inventar registros anteriores a la instalación.
 }
 const reviewed=new Set(locallyReviewed[t]);
 return current.some(id=>!reviewed.has(id));
}
function setDot(button,label,active,mode='normal'){
 button.replaceChildren(document.createTextNode(label));
 const visible=active&&mode!=='off';
 if(visible){
  const dot=document.createElement('span');
  dot.className=mode==='subtle'?'nav-dot nav-dot-muted':'nav-dot';
  dot.setAttribute('aria-hidden','true');
  button.appendChild(dot);
 }
 button.setAttribute('aria-label',label+(visible?' · tiene novedades pendientes':''));
}
function updateTabNotifications(){
 if(!data)return;
 const active={};
 for(const t of Object.keys(TAB_GROUPS))active[t]=tabHasUpdates(t,data);
 document.querySelectorAll('[data-tab]').forEach(button=>{
  const id=button.dataset.tab;
  setDot(button,TAB_LABELS[id],Boolean(active[id]),indicatorMode(id));
 });
 document.querySelectorAll('[data-group]').forEach(button=>{
  const group=button.dataset.group;
  const needsAttention=Object.keys(TAB_GROUPS).some(t=>TAB_GROUPS[t]===group&&active[t]&&indicatorMode(t)==='normal');
  setDot(button,GROUP_LABELS[group],needsAttention);
 });
}
function updateReadActions(){
 el('read-actions').hidden=tab==='chat';
 if(tab==='chat'||!data)return;
 const hasUpdates=tabHasUpdates(tab,data);
 el('indicator-inline').value=indicatorMode(tab);
 let filterWrap=null;
 try{filterWrap=el('status-filter-wrap')}catch{}
 if(filterWrap){
  filterWrap.hidden=!['agenda','projects'].includes(tab);
  if(!filterWrap.hidden)el('status-filter').value=selectedStatusView(tab);
 }
 let researchFilter=null;
 try{researchFilter=el('research-filter-wrap')}catch{}
 if(researchFilter){
  researchFilter.hidden=tab!=='research';
  if(tab==='research')el('research-filter').value=researchView;
 }
 el('read-tab').disabled=!hasUpdates;
}
function refreshGroupNav(){
 document.querySelectorAll('[data-group]').forEach(b=>b.classList.toggle('active',b.dataset.group===activeGroup));
 document.querySelectorAll('[data-tab]').forEach(b=>b.hidden=TAB_GROUPS[b.dataset.tab]!==activeGroup);
}
function switchTab(t){closeSectionHelp();activeGroup=TAB_GROUPS[t]||'diario';tab=t;refreshGroupNav();updateTabNotifications();updateReadActions();lastFeedSig='';document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));el('feed').hidden=tab==='chat';el('chatwrap').hidden=tab!=='chat';if(data){if(tab==='chat')drawChat();else drawFeed()}}
