function renderActivity(){
 const controls='<div class="activity-filters" aria-label="Filtrar la cronología"><button type="button" data-activity-view="featured" class="'+(activityView==='featured'?'active':'')+'">Destacados</button><button type="button" data-activity-view="all" class="'+(activityView==='all'?'active':'')+'">Todos los hechos</button></div>';
 return controls+(activityView==='featured'
  ?renderNews()
  :(data.events||[]).map(e=>`<article class="feedentry" data-event-record="${esc(e.id||'')}"><div class="date"><span>${esc(e.when)}</span><span>${esc(e.kind)}</span></div><div class="journaltext">${renderEvidenceText(e.text)}</div>${recordLinks('event',e.id)}</article>`).join('')||'<div class="empty">Sin hechos registrados.</div>');
}
function renderFindings(){
 const conclusions=data.conclusions||[],knowledge=data.knowledge||[];
 return '<div class="research explainer"><h3>Hallazgos documentados</h3><p>Las conclusiones se muestran con el alcance de las pruebas que las respaldan. Los demás conocimientos se identifican como registros del motor, sin atribuirles una demostración causal.</p></div>'+
  conclusions.map(c=>`<div class="research" data-finding-record="${esc(c.id||'')}"><div class="date"><span>${esc(c.when)}</span><span>${esc(c.status||'Conclusión registrada')}</span></div><strong>${renderEvidenceText(c.text)}</strong><p class="small">Alcance: ${esc(c.scope||'No especificado')}</p><p class="small">Mediciones: ${(c.evidence_ids||[]).map(id=>measurementLink(id)).join(' · ')||'Sin mediciones vinculadas'}</p>${recordLinks('conclusion',c.id)}</div>`).join('')+
  '<div class="research explainer"><h3>Propiedades recientes registradas por el motor</h3><p class="small">Estos registros describen interacciones observadas; no todas son generalizaciones demostradas.</p></div>'+
  (knowledge.map(([k,v])=>`<div class="research" data-knowledge-record="${esc(k)}"><strong>${renderEvidenceText(v)}</strong></div>`).join('')||'<div class="empty">Todavía no hay propiedades registradas.</div>');
}
function renderCreations(){
 const controls='<div class="creation-filters" aria-label="Filtrar creaciones"><button type="button" data-creation-view="all" class="'+(creationView==='all'?'active':'')+'">Todas</button><button type="button" data-creation-view="designs" class="'+(creationView==='designs'?'active':'')+'">Diseños</button><button type="button" data-creation-view="objects" class="'+(creationView==='objects'?'active':'')+'">Objetos físicos</button></div>';
 return controls+(creationView==='objects'?'':'<div class="research explainer"><h3>Diseños documentados</h3><p>Propuestas de Nilo; un diseño no implica que el objeto haya sido construido ni que funcione.</p></div>'+renderDesigns())+(creationView==='designs'?'':renderPlans());
}

const RECORD_LABELS={news:'Novedad',journal:'Cuaderno',research:'Investigación',prediction:'Hipótesis',measurement:'Ensayo',conclusion:'Hallazgo',proposal:'Propuesta',project:'Proyecto',design:'Diseño',construction:'Construcción',tool:'Herramienta',material:'Material',diagnostic:'Resultado',event:'Hecho'};
const RECORD_GLYPHS={project:'▣',research:'⌕',measurement:'⚗',conclusion:'✦',journal:'✎',prediction:'◇',design:'◇',construction:'▤',tool:'⚒',material:'▦',proposal:'↗',diagnostic:'!',news:'•',event:'•'};
function recordLinkMarkup(r){
 const category=String(r.category||'');
 if(category==='material'){
  // Un movimiento de inventario no tiene un ID de objeto ni una ficha
  // individual. Mostrarlo como saldo comprobado, nunca como enlace falso.
  return '<span class="record-link record-material" title="Variación medida del inventario">'+
   '<span class="record-link-icon" aria-hidden="true">▦</span>'+
   '<span class="record-link-label">Material · '+esc(r.title||r.id)+'</span></span>';
 }
 const phase=['new','updated'].includes(r.phase)?r.phase:'related';
 const marker=phase==='new'?'Nuevo':phase==='updated'?'Actualizado':'';
 return '<button type="button" class="record-link" data-related-category="'+esc(category)+
  '" data-related-id="'+esc(r.id)+'" data-link-category="'+esc(category)+
  '" data-link-phase="'+esc(phase)+'" title="'+esc(r.relation==='evidencia'?'Evidencia por ID':'Vínculo documentado')+'">'+
  '<span class="record-link-icon" aria-hidden="true">'+esc(RECORD_GLYPHS[category]||'·')+'</span>'+
  '<span class="record-link-label">'+esc(RECORD_LABELS[category]||category)+' · '+esc(String(r.title||r.id).slice(0,72))+'</span>'+
  (marker?'<span class="record-link-phase">'+marker+'</span>':'')+'</button>';
}
const RECORD_TAB={news:'activity',journal:'notes',research:'research',prediction:'research',measurement:'measurements',conclusion:'findings',proposal:'proposals',project:'projects',design:'creations',construction:'creations',tool:'creations',event:'activity',diagnostic:'activity'};
// Familias contiguas, sin subtítulos ni separadores artificiales.
const RELATED_FAMILY_ORDER=['measurement','material','research','prediction','conclusion',
 'project','design','tool','construction','proposal','diagnostic','journal','event','news'];
function orderedRecordLinks(rows){
 const family=category=>{const index=RELATED_FAMILY_ORDER.indexOf(category);return index<0?RELATED_FAMILY_ORDER.length:index};
 const phase={new:0,updated:1,related:2};
 return [...rows].sort((a,b)=>family(a.category)-family(b.category)||
   (phase[a.phase||'related']??2)-(phase[b.phase||'related']??2)||
   (Number(b.seq)||0)-(Number(a.seq)||0)||
   String(a.id||'').localeCompare(String(b.id||'')));
}
function recordLinks(category,id,overridden){
 const all=overridden??data?.record_relations?.[category+':'+id]??[];
 if(!Array.isArray(all)||!all.length)return '';
 const items=orderedRecordLinks(all).map(recordLinkMarkup);
 return '<div class="record-links"><div class="record-links-title">Registros relacionados · vínculos documentados ('+all.length+')</div>'+
  '<div class="record-links-items">'+items.join('')+'</div></div>';
}
// Solo Proyectos: un registro reciente visible y los anteriores por familia.
function projectRecordLinks(id,overridden){
 const all=overridden??data?.record_relations?.['project:'+id]??[];
 if(!Array.isArray(all)||!all.length)return '';
 const families=new Map();
 for(const r of all){
  const category=String(r.category||'');
  if(!families.has(category))families.set(category,[]);
  families.get(category).push(r);
 }
 const order=category=>{const at=RELATED_FAMILY_ORDER.indexOf(category);return at<0?RELATED_FAMILY_ORDER.length:at};
 const html=[...families].sort((a,b)=>order(a[0])-order(b[0])||a[0].localeCompare(b[0])).map(([category,records])=>{
  // La fase de alta/actualización no reemplaza al orden histórico del índice.
  const latest=[...records].sort((a,b)=>(Number(b.seq)||0)-(Number(a.seq)||0)||
   String(b.when||'').localeCompare(String(a.when||''))||
   String(a.id||'').localeCompare(String(b.id||'')));
  const top=recordLinkMarkup(latest[0]);
  const older=latest.slice(1);
  const toggle=older.length?'<details class="project-related-older" data-project-related-family="'+esc(category)+
   '"><summary>Ver anteriores ('+older.length+')</summary><div class="record-links-items">'+
   older.map(recordLinkMarkup).join('')+'</div></details>':'';
  return '<div class="project-related-family"><div class="record-links-items">'+top+'</div>'+toggle+'</div>';
 }).join('');
 return '<div class="record-links project-record-links"><div class="record-links-title">Registros relacionados · vínculos documentados ('+
  all.length+')</div>'+html+'</div>';
}
function recordDescription(category,record){
 if(category==='journal')return record.text||'';
 if(category==='research')return [record.question,record.hypothesis,record.conclusion].filter(Boolean).join('\n\n');
 if(category==='prediction')return [record.hypothesis,record.expected_effect,record.scope].filter(Boolean).join('\n\n');
 if(category==='measurement')return [measurementActionTitle(record),...(record.verified_facts||[])].join('\n\n');
 if(category==='proposal')return [record.title||record.phenomenon,record.rationale,record.experiment].filter(Boolean).join('\n\n');
 if(category==='conclusion')return [record.text,record.scope].filter(Boolean).join('\n\n');
 if(category==='project')return [record.title,record.reason,record.state].filter(Boolean).join('\n\n');
 if(category==='design')return [record.name,record.versions?.at(-1)?.purpose,record.versions?.at(-1)?.principle].filter(Boolean).join('\n\n');
 if(category==='diagnostic')return [record.op,...(record.facts||[])].filter(Boolean).join('\n\n');
 return [record.name||record.title||record.text,record.purpose].filter(Boolean).join('\n\n');
}
// Historial exclusivamente de navegación; no altera el estado ni el cuaderno.
const recordNavigationHistory=[];
function captureRecordLocation(){
 const dialog=el('record-dialog'),catchup=el('catchup-dialog');
 return {tab,feedScroll:el('feed').scrollTop,
   creationView,activityView,essayView,focusedMeasurement,
   archiveDialog:dialog.open?{
     title:el('record-title').textContent,meta:el('record-meta').textContent,
     text:el('record-text').textContent,links:el('record-relations').innerHTML,
     scroll:dialog.scrollTop}:null,
   summaryDialog:catchup.open?{scroll:catchup.scrollTop}:null};
}
function updateRecordBack(){
 const enabled=recordNavigationHistory.length>0;
 el('record-dialog-back').hidden=!enabled;
}
function pushRecordLocation(previous){
 recordNavigationHistory.push(previous);
 if(recordNavigationHistory.length>30)recordNavigationHistory.shift();
 updateRecordBack();
}
function restoreRecordLocation(){
 const previous=recordNavigationHistory.pop();
 if(!previous)return;
 el('record-dialog').close();
 if(el('catchup-dialog').open)el('catchup-dialog').close();
 creationView=previous.creationView;
 activityView=previous.activityView;
 essayView=previous.essayView;
 focusedMeasurement=previous.focusedMeasurement;
 switchTab(previous.tab);
 // La posición debe restaurarse después de volver a dibujar la solapa.
 el('feed').scrollTop=previous.feedScroll;
 if(previous.archiveDialog){
  el('record-title').textContent=previous.archiveDialog.title;
  el('record-meta').textContent=previous.archiveDialog.meta;
  el('record-text').textContent=previous.archiveDialog.text;
  el('record-relations').innerHTML=previous.archiveDialog.links;
  el('record-dialog').showModal();
  el('record-dialog').scrollTop=previous.archiveDialog.scroll;
 }else if(previous.summaryDialog){
  el('catchup-dialog').showModal();
  el('catchup-dialog').scrollTop=previous.summaryDialog.scroll;
 }
 updateRecordBack();
}
async function openRelatedRecord(category,id){
 if(!RECORD_LABELS[category]||typeof id!=='string'||!id)return;
 if(category==='measurement')return await openMeasurement(id);
 try{
  const response=await fetch('/api/record?category='+encodeURIComponent(category)+'&id='+encodeURIComponent(id),{cache:'no-store'});
  const result=await response.json();
  if(!response.ok)throw Error(result.error||'No se pudo consultar el registro relacionado.');
  if(category==='design')creationView='designs';
  if(category==='tool'||category==='construction')creationView='objects';
  if(category==='event')activityView='all';
   if(category==='news')activityView='featured';
  if(el('record-dialog').open)el('record-dialog').close();
  if(el('catchup-dialog').open)el('catchup-dialog').close();
  if(RECORD_TAB[category])switchTab(RECORD_TAB[category]);
  const attr={news:'entry-id',journal:'entry-id',research:'research-record',prediction:'prediction-record',conclusion:'finding-record',proposal:'proposal-id',project:'project-record',design:'design-record',construction:'plan-id',tool:'plan-id',event:'event-record'}[category];
  const node=attr?[...el('feed').querySelectorAll('[data-'+attr+']')].find(n=>n.getAttribute('data-'+attr)===id):null;
  if(node){
   if(node.tagName==='DETAILS')node.open=true;
   node.classList.add('record-target');
   node.scrollIntoView({block:'center',behavior:'smooth'});
   return true;
  }
  el('record-title').textContent=RECORD_LABELS[category]+' · registro archivado';
  el('record-meta').textContent=result.record.when||result.record.started||'';
  el('record-text').textContent=recordDescription(category,result.record);
  el('record-relations').innerHTML=recordLinks(category,id,result.relations);
  el('record-dialog').showModal();
  return true;
 }catch(error){alert(error.message);return false}
}
function renderNotes(){return data.journal.map(e=>`<article class="feedentry ${!e.read?'unread':''}" data-entry-id="${esc(e.id)}"><div class="date"><span>${esc(e.when)}</span><span>${e.writing?'ESCRIBIENDO…':e.origin==='llm'?'NILO':'DEMO'}</span></div><div class="journaltext" data-note="${esc(e.id)}">${esc(e.visible_text)}${e.writing?'<i class="cursor"></i>':''}</div>${recordLinks('journal',e.id)}</article>`).join('')}
function renderDesigns(){return (data.designs||[]).map(d=>{
 const latest=d.versions?.at(-1)||{};
 return `<details class="research" data-design-record="${esc(d.id||'')}"><summary><div class="date"><span>${esc(d.created)}</span><span>${esc(d.status)}</span></div><strong>${esc(d.name)}</strong> · <span class="muted">Versión ${latest.version||1}</span></summary><div class="details"><p><strong>Propósito:</strong> ${esc(latest.purpose)}</p><p><strong>Fundamento:</strong> ${esc(latest.principle)}</p><p><strong>Predicción:</strong> ${esc(latest.prediction)}</p><p><strong>Procedimiento:</strong> ${esc(latest.procedure)}</p><p><strong>Requisitos:</strong> ${esc(latest.requirements)}</p><p><strong>Componentes:</strong></p>${(latest.components||[]).map(c=>`<p>${esc(c.name)} · ${esc(c.material)} · ${esc(c.function)} · unión: ${esc(c.connection)}</p>`).join('')}<p><strong>Funciones comprobadas:</strong> ${(d.verified_functions||[]).filter(v=>v.design_version===latest.version).map(v=>esc(v.name)+(v.measurement_id?' · '+measurementLink(v.measurement_id):'')).join(' · ')||'Ninguna función comprobada para esta versión.'}</p><p class="small">Una fabricación satisfactoria no demuestra funcionalidad. Una recuperación dentro del refugio no prueba mayor seguridad ni ventaja causal respecto del exterior.</p><p><strong>Ensayos y fabricación (${d.tests?.length||0}):</strong></p>${(d.tests||[]).slice(-15).map(t=>`<p>${esc(t.when)} · ${esc(t.success?'Éxito':'Falló')} · ${esc(t.evidence)}</p>`).join('')||'<p>Sin pruebas físicas.</p>'}${recordLinks('design',d.id)}</div></details>`;
 }).join('')}
function historicMaterials(revision){
 const materials=Array.isArray(revision.materials)?revision.materials:
  (revision.components||[]).map(c=>c.material).filter(Boolean);
 const counts=new Map();
 for(const item of materials){const material=String(typeof item==='string'?item:item?.material||'').trim();if(material)counts.set(material,(counts.get(material)||0)+1)}
 return counts;
}
function historicMaterialText(counts){
 return [...counts].map(([material,count])=>esc(material)+' ×'+count).join(' · ')||'Sin materiales históricos identificables';
}
function historicMaterialDiff(current,previous){
 if(!previous)return 'Versión inicial';
 const changes=[];
 for(const material of new Set([...current.keys(),...previous.keys()])){
  const diff=(current.get(material)||0)-(previous.get(material)||0);
  if(diff)changes.push(esc(material)+(diff>0?' +':' ')+diff);
 }
 return changes.join(' · ')||'Sin cambios en cantidad por material';
}
function renderStructuralEvidence(o){
 const cargo=Object.entries(o.cargas_almacenadas||{}).map(([name,qty])=>esc(name)+' ×'+esc(qty)).join(' · ');
 const trials=(o.ensayos_de_carga||[]).slice(-6);
 if(!cargo&&!trials.length)return '';
 return '<div class="physical-details"><p><strong>Material almacenado:</strong> '+(cargo||'Sin carga actual')+'</p>'+
  (trials.length?'<p><strong>Ensayos de carga:</strong></p>'+trials.map(t=>
   '<p class="small">Versión '+esc(t.revision)+' · '+esc(t.material)+' ×'+esc(t.quantity)+
   ' · '+(t.supported?'Soportó':'No soportó')+' · carga ensayada '+esc(t.load)+
   ' / límite '+esc(t.limit)+' (unidades abstractas)</p>').join(''):'')+
  '<p class="small">Estos ensayos modelan soporte estático, no estabilidad dinámica, abrigo ni seguridad climática.</p></div>';
}
function renderPlans(){
 const buildings=[...(data.structures||[]),...(data.retired_structures||[])];
 const tools=[...(data.items||[])];
 const all=[...buildings.map(o=>({o,type:'obra'})),...tools.map(o=>({o,type:'herramienta'}))];
 return `<div class="research"><h3>Cuaderno técnico · Planos y revisiones</h3><p>Las construcciones muestran esquemas y huellas aproximadas. En herramientas portátiles solo se conoce el listado de componentes: su tamaño, su forma detallada y sus uniones todavía no están modelados. Las modificaciones conservan historial; cada mejora funcional necesita nuevas pruebas.</p></div>`+
 (all.length?all.map(({o,type})=>{
   const history=o.revisions||[],latest=history.at(-1)||{};
   return `<details class="research" data-plan-id="${esc(o.id||o.name||'')}"><summary><div class="date"><span>${type==='obra'?'Construcción':'Herramienta portátil'}</span><span>v${esc(o.revision||1)} · ${esc(o.status||'En uso')}</span></div><strong>${esc(o.name||'Sin nombre')}</strong> · ${type==='obra'?esc(o.space?.area_m2||'—')+' m²':'forma y superficie sin modelar'}</summary><div class="details"><p><strong>Propósito:</strong> ${esc(o.purpose||'—')}</p><p><strong>Componentes actuales (${(o.components||[]).length}):</strong></p>${(o.components||[]).map(c=>`<p class="small">${esc(c.material)} · estado ${(100*(c.condition??1)).toFixed(0)}%</p>`).join('')||'<p>Sin componentes actuales.</p>'}${type==='obra'?renderStructuralEvidence(o):''}
<p><strong>Historial de planos y cambios (${history.length}):</strong></p>${[...history].reverse().map((v,index,reverse)=>{const current=historicMaterials(v);const previous=historicMaterials(reverse[index+1]||{});return `<details class="physical-details"><summary>Versión ${esc(v.revision)} · ${esc(v.operation)} · ${[...current.values()].reduce((a,b)=>a+b,0)} lotes</summary><p class="small"><strong>Materiales de esta versión:</strong> ${historicMaterialText(current)}</p><p class="small"><strong>Variación:</strong> ${historicMaterialDiff(current,index+1<reverse.length?previous:null)}</p>${(v.components||[]).length?'<p class="small"><strong>Piezas:</strong> '+v.components.map(c=>esc(c.material||'desconocido')+(c.condition==null?'':' · estado '+Math.round(100*c.condition)+'%')).join(' · ')+'</p>':''}<pre class="schematic">${esc(type==='herramienta'?String(v.schematic||'Sin dibujo').replace(/\s*\/\s*cmp-[a-z0-9-]+/g,''):v.schematic||'Sin dibujo')}</pre><p class="small">${esc(type==='herramienta'&&v.observation==='Geometría estimada a partir de recursos reales.'?'Registro de componentes; forma y dimensiones todavía no comprobadas.':v.observation||'')}</p></details>`}).join('')||'<p>No hay revisiones históricas.</p>'}<p class="small">${type==='obra'?'Los espacios son usos declarados, no subdivisiones construidas salvo que el motor compruebe sus componentes.':'El esquema indica cantidad y material de las piezas; no representa tamaño, huella ni uniones verificadas.'}</p>${recordLinks(type==='obra'?'construction':'tool',o.id||o.name)}</div></details>`;
 }).join(''):'<div class="empty">Nilo todavía no documentó obras ni herramientas.</div>');
}
function renderProposals(){
 const all=data.proposals||[];
 const proposals=all.filter(p=>proposalFilter==='all'||(proposalFilter==='debug'?p.type==='debug':p.type!=='debug'));
 const counts={all:all.length,debug:all.filter(p=>p.type==='debug').length,physics:all.filter(p=>p.type!=='debug').length};
 const filters=[['all','Todas'],['debug','Diagnósticos'],['physics','Ampliaciones']];
 return `<div class="research"><h3>Solicitudes de ampliación y revisión</h3><p class="small">Los diagnósticos distinguen uso incorrecto, limitaciones y posibles errores. Las ampliaciones proponen física todavía no representada. Ninguna evaluación cambia el motor automáticamente.</p><div class="controls">${filters.map(([id,label])=>`<button type="button" data-proposal-filter="${id}" class="${proposalFilter===id?'active':''}">${label} (${counts[id]})</button>`).join('')}</div></div>`+
 (proposals.length?proposals.map(p=>{
   const debug=p.type==='debug';
   const origin=p.origin==='motor'?' · DETECTADO POR EL MOTOR':'';
   const subject=esc(debug?p.title:p.phenomenon);
   const details=debug?`<p><strong>Resultado esperado:</strong> ${esc(p.expected)}</p><p><strong>Resultado observado (según Nilo):</strong> ${esc(p.observed)}</p><p><strong>Motivo:</strong> ${esc(p.rationale)}</p><p><strong>Operación:</strong> ${esc(p.related_action||'Sin especificar')}</p><p><strong>Tipo informado:</strong> ${esc(({uso:'Duda sobre uso',limitacion:'Limitación de capacidad',error:'Posible error'})[p.issue_kind]||'Sin clasificar')}</p><p><strong>Contrato operativo:</strong> ${esc(p.manual_reference||'No consultado')}</p><p><strong>Resultados físicos adjuntos (${(p.evidence||[]).length}):</strong></p>${(p.evidence||[]).map(e=>`<p class="small">${e.id?.startsWith('med-')?measurementLink(e.id,e.op):'<strong>Resultado registrado</strong>'} · ${esc(e.when)} · ${esc(actionName({op:e.op,target:e.target}))} ${esc(e.target||'')} · ${e.success?'Acción exitosa':'Acción fallida'} · ${esc((e.facts||[]).join(' / '))}</p>`).join('')||'<p class="small">Sin registros de ejecución adjuntos. Se puede solicitar mayor evidencia.</p>'}`:
     `<p><strong>Motivo:</strong> ${esc(p.rationale)}</p><p><strong>Qué falta:</strong> ${esc(p.missing_capability)}</p><p><strong>Prueba propuesta:</strong> ${esc(p.experiment)}</p>${(p.evidence||[]).length?`<p><strong>Ensayos sin física vinculados (${p.evidence.length}):</strong> ${p.evidence.map(e=>e.id?.startsWith('med-')?measurementLink(e.id,e.op):esc(actionName({op:e.op,target:e.target}))).join(' · ')}</p>`:""}`;
   const decisions=debug?[['bug','Confirmar error'],['limite','Limitación válida'],['capacidad','Falta capacidad'],['interpretacion','Interpretación equivocada'],['ampliar','Pedir más evidencias']]:[['aprobar','Aprobar estudio'],['ampliar','Pedir detalles'],['rechazar','Rechazar']];
   return `<details class="research" data-proposal-id="${esc(p.id||'')}"><summary><div class="date"><span>${esc(p.when)} · ${debug?(p.issue_kind==='limitacion'?'LIMITACIÓN':p.issue_kind==='uso'?'REVISAR USO':'POSIBLE ERROR'):'AMPLIACIÓN FÍSICA'}${origin}</span><span>${esc(p.status)}</span></div><strong>${subject}</strong></summary><div class="details">${details}<div class="proposal-actions"><button type="button" data-diagnostic="${esc(p.id)}" title="Exportar paquete de revisión con evidencias verificadas">Exportar informe JSON</button></div>${p.review?`<p><strong>Evaluación:</strong> ${esc(p.review.decision)} · ${esc(p.review.reason)}</p>`:''}${p.status==='pendiente'?`<textarea class="review-reason" maxlength="700" rows="3" data-reason="${esc(p.id)}" placeholder="Fundamento de tu evaluación (obligatorio)"></textarea><div class="proposal-actions">${decisions.map(([value,label])=>`<button type="button" data-review="${value}" data-id="${esc(p.id)}">${label}</button>`).join('')}</div><p class="small">La decisión se registra y Nilo la recibe; ninguna clasificación instala automáticamente una corrección.</p>`:''}${recordLinks('proposal',p.id)}</div></details>`;
 }).join(''):'<div class="empty">No hay solicitudes en este filtro.</div>');
}

function renderBehavior(){
  const b=data.behavior||{};
  if(!b.acciones_registradas)return '<div class="research"><h3>Conducta observada</h3><p class="small">Sin datos desde la instrumentación actual. El historial anterior no se reconstruye con estimaciones.</p></div>';
  const counts=Object.entries(b.acciones_por_clase||{}).map(([k,v])=>esc(k)+': '+esc(v)).join(' · ');
  const origins=Object.entries(b.acciones_por_origen||{}).map(([k,v])=>esc(k)+': '+esc(v)).join(' · ');
  const times=Object.entries(b.minutos_medidos_por_clase||{}).map(([k,v])=>esc(k)+': '+esc(v)+' min').join(' · ');
  return '<div class="research"><h3>Conducta observada</h3>'+
    '<p class="small">Desde el minuto simulado '+esc(b.desde_minuto_simulado)+' · '+esc(b.acciones_registradas)+' acciones completadas.</p>'+
    '<p class="small"><strong>Tipos:</strong> '+counts+'</p>'+
    '<p class="small"><strong>Origen:</strong> '+origins+'</p>'+
    '<p class="small"><strong>Tiempo medido:</strong> '+(times||'Sin duración medida')+' ('+esc(b.acciones_con_duracion_medida)+' acciones)</p>'+
    '<p class="small"><strong>Novedad observada:</strong> '+esc(b.acciones_con_novedad_observable)+' acciones ('+esc(Math.round(100*b.proporcion_con_novedad_observable))+'%). '+
    'Casillas descubiertas: '+esc(b.casillas_nuevas_reveladas)+'. Materiales distintos obtenidos: '+esc(b.materiales_distintos_obtenidos)+'.</p>'+
    '<p class="small">Destinos distintos de desplazamiento: '+esc(b.destinos_distintos_al_moverse)+
    ' · regresos registrados: '+esc(b.regresos_a_destinos_ya_visitados)+
    ' · cambios de proyecto: '+esc(b.cambios_entre_proyectos_activos)+'.</p>'+
    '<p class="small">Indicadores descriptivos de acciones verificadas, no rasgos psicológicos ni pruebas de creatividad. La cobertura comienza con esta versión.</p></div>';
}
function renderHabits(){
 const skills=(data.skills||[]), prefs=(data.waiting_preferences||[]), history=(data.waiting_history||[]), waiting=data.waiting_state||{};
 const name=op=>({forage:'Recolectar alimento',gather:'Recolectar materiales',drink:'Beber',rest:'Descansar',craft:'Fabricar un objeto'})[op]||op;
 return renderBehavior()+`<div class="research"><h3>Actividad actual sin LLM</h3><p>${esc(waiting.reason||'No se han necesitado actividades autónomas todavía.')}</p><p class="small">${esc(waiting.when||'')}</p></div>`+
 `<div class="research"><h3>Actividades previstas por Nilo</h3>${prefs.length?prefs.map(v=>`<p><strong>${esc(name(v.op))}</strong>${v.target?' · '+esc(v.target):''} · hasta ${esc(v.hasta)} · radio ${esc(v.radio)} · ${esc(v.motivo||'')}</p>`).join(''):'<p>Sin encargos explícitos. Puede abastecerse de lo necesario mediante habilidades ya comprobadas.</p>'}</div>`+
 `<div class="research"><h3>Trabajo de mantenimiento reciente</h3><p>${esc(data.maintenance?.observacion||'Aún no hay suficientes acciones registradas.')}</p><p class="small">Últimos ${esc(data.maintenance?.periodo_dias_simulados||3)} días simulados · ${esc(data.maintenance?.minutos_de_mantenimiento_aprox||0)} minutos estimados en tareas · ${Object.entries(data.maintenance?.actividades||{}).map(([k,v])=>esc(name(k))+': '+esc(v)).join(' · ')||'sin tareas repetidas'}</p><p class="small">Es un registro para que Nilo decida si quiere investigar alternativas; no lo obliga a automatizar nada.</p></div>`+
 `<div class="research"><h3>Habilidades comprobadas</h3>${skills.length?skills.map((v,i)=>`<p data-skill-index="${i}"><strong>${esc(name(v.op))}</strong> · ${esc(v.target||'')} · ${esc(v.count||0)} veces · ${esc(v.last_fact||'')}</p>`).join(''):'<p>Todavía no hay procedimientos verificados que pueda repetir sin deliberar.</p>'}</div>`+
 `<div class="research"><h3>Acciones sin nueva deliberación</h3><p class="small">${esc(data.autonomy_stats?.routine_actions||0)} acciones por hábitos · ${esc(data.autonomy_stats?.deliberated_actions||0)} acciones deliberadas · ${Math.round(100*(data.autonomy_stats?.routine_actions||0)/Math.max(1,(data.autonomy_stats?.routine_actions||0)+(data.autonomy_stats?.deliberated_actions||0)))}% por rutina, agenda o motor</p><p class="small">No incluye comer, beber o recuperarse automáticamente.</p></div>`+
 `<div class="research"><h3>Registro de actividades autónomas</h3><p class="small">Acciones ejecutadas por el motor, no decisiones nuevas del LLM.</p></div>`+
 (history.length?history.map(h=>`<div class="feedentry"><div class="date"><span>${esc(h.when)}</span><span>${h.success?'Comprobado':'Fallido'}</span></div><strong>${esc(name(h.op))}</strong><p class="small">${esc(h.origin==='rutina'?'Rutina cotidiana · ':h.origin==='motor'?'Seguimiento del motor · ':'Espera de LLM · ')}${esc(h.reason||'')}</p><p>${esc(h.fact||'')}</p></div>`).join(''):'<div class="empty">Todavía no realizó acciones autónomas durante una espera.</div>');
}
function agendaCondition(when){
 const c=when&&typeof when==='object'?when:{};
 const kind=c.tipo||'ahora';
 if(kind==='despues_de_minutos'){
  const mins=Number(c.minutos);
  return Number.isFinite(mins)?'Activar después de '+mins.toLocaleString('es-AR')+
   ' min simulados desde que se programó (no implica descansar ese tiempo)':'Tiempo de espera no definido';
 }
 if(kind==='cuando_haya_material')
  return 'Activar cuando haya al menos '+(c.cantidad??1)+' unidades de '+(c.material||'material');
 if(kind==='cuando_necesidad'){
  const need={energia:'energía',hidratacion:'hidratación',nutricion:'alimentación'};
  return 'Activar cuando '+(need[c.necesidad]||c.necesidad||'una necesidad')+' esté por debajo de '+(c.menor_que??'?');
 }
 if(kind==='ahora')return 'Activar en cuanto el motor permita ejecutar la tarea';
 return 'Condición no reconocida ('+kind+')';
}
function agendaEvidenceNote(t){
 const txt=String(t.titulo||'')+' '+String(t.motivo||'');
 if(!/descans|repos|dormir|sueño|recuperaci[oó]n/i.test(txt))return '';
 const steps=t.pasos||[];
 const doesRest=steps.some(s=>s.op==='rest');
 const doesCompare=steps.some(s=>s.op==='compare');
 if(doesRest||doesCompare)return '';
 const claimsConclude=steps.some(s=>s.op==='conclude');
 if(!claimsConclude)return '';
 const refs=steps.flatMap(s=>Array.isArray(s.evidence_ids)?s.evidence_ids:[]);
 const found=(data.measurements||[]).filter(m=>refs.includes(m.id));
 const crossCheck=found.length&&!found.some(m=>m.op==='rest')
  ?' Las mediciones vinculadas disponibles tampoco corresponden a descansos.':'';
 return 'Esta tarea solamente programa el registro de una conclusión: no incluye descansar ni comparar mediciones. Que figure como completada confirma la ejecución de sus pasos, no que se haya demostrado una recuperación energética.'+crossCheck;
}
function renderAgenda(){
 const history=data.agenda_history||[],priority={lista_para_revisar:0,en_curso:1,pendiente:2,pospuesta:3,bloqueada:4,completada:5,cancelada:6},tasks=[...(data.agenda||[])].filter(t=>typeof matchesStatusView==='function'?matchesStatusView(t,'agenda'):true).sort((a,b)=>(priority[a.estado]??9)-(priority[b.estado]??9));
 const taskLabel=t=>t.modo==='recordatorio'?({pendiente:'Esperando condición',lista_para_revisar:'Condición cumplida',completada:'Recordatorio atendido',cancelada:'Cancelado',pospuesta:'Pospuesto'}[t.estado]||t.estado):({pendiente:'Pendiente',en_curso:'En curso',completada:'Secuencia completada',bloqueada:'Bloqueada',cancelada:'Cancelada',pospuesta:'Pospuesta'}[t.estado]||t.estado||'Sin estado');
 return `<div class="research"><h3>Agenda y recordatorios</h3><p>Las tareas delegadas se ejecutan si cumplen sus requisitos. Los recordatorios solo avisan que corresponde reconsiderar un proyecto; no ejecutan acciones. «Secuencia completada» no prueba el objetivo.</p></div>`+
 (tasks.length?tasks.map(t=>{
  const steps=t.pasos||[],warning=agendaEvidenceNote(t);
  const recorded=t.resultados||[],full=Number(t.indice)||0;
  return `<details class="research" data-agenda-record="${esc(t.id||'')}" ${t.estado==='en_curso'?'open':''}>
   <summary><div class="date"><span>${esc(taskLabel(t))}</span><span>${t.modo==='recordatorio'?'Recordatorio':esc(Math.min(full,steps.length))+'/'+esc(steps.length)+' pasos'}</span></div>
    <strong>${esc(t.titulo||'Tarea sin título')}</strong>
    <div class="measurement-key">${esc(agendaCondition(t.cuando))}</div>
   </summary>
   <div class="details">
    <p><strong>Objetivo declarado:</strong> ${esc(t.motivo||t.titulo||'Sin motivo declarado')}</p>
    ${t.modo==='recordatorio'?'<p class="small">No tiene acciones físicas programadas. Nilo decidirá cuándo y si retomar el proyecto.</p>':'<p><strong>Pasos programados:</strong></p>'}
    <ol class="agenda-steps" ${t.modo==='recordatorio'?'hidden':''}>${steps.map((s,i)=>`<li>${i<full?'✓ Realizado · ':''}${esc(actionName(s))}</li>`).join('')||'<li>Sin pasos</li>'}</ol>
    <p class="agenda-status">${esc(t.ultimo_motivo||'')}</p>
    ${t.cumplimiento_objetivo?.estado==='no_verificado_por_ejecucion'?'<p class="agenda-caveat">Los pasos se ejecutaron; el cumplimiento del objetivo declarado no fue verificado automáticamente.</p>':''}
    ${warning?`<p class="agenda-caveat">${esc(warning)}</p>`:''}
    ${t.modo==='recordatorio'?'<p><strong>Estado de la condición:</strong> '+esc(t.condicion_cumplida||'Pendiente')+'</p>':'<p><strong>Qué registró el motor:</strong></p>'}
    ${recorded.length?recorded.map(r=>`<p class="small"><strong>${esc(r.exito?'Paso ejecutado':'Paso fallido')}</strong> · ${esc(r.when||'Sin fecha')} · ${esc(actionName({op:r.op||steps[(r.paso||1)-1]?.op||''}))}<br>${renderEvidenceText(r.hecho||'Sin descripción registrada')}</p>`).join(''):'<p class="small">Todavía no se ejecutó ningún paso.</p>'}
   </div>
  </details>`;
 }).join(''):'<div class="empty">No hay registros para este filtro.</div>')+
 `<details class="research explainer"><summary>Archivo de ejecuciones recientes</summary><p class="small">Registro cronológico de los pasos que ya figuran en las tareas.</p>${history.slice(0,20).map(e=>`<p class="small">${esc(e.when)} · ${esc(e.titulo)} · ${renderEvidenceText(e.hecho)}</p>`).join('')||'<p class="small">Sin ejecuciones todavía.</p>'}</details>`;
}
function renderIdentity(){return `<div class="research"><h3>Etapas de vida (30 días simulados)</h3>${Object.entries(data.life_chapters||{}).map(([n,c])=>`<details class="physical-details"><summary>Etapa ${esc(n)} · desde día ${esc(c.desde_dia)} · ${esc(c.exitos)} éxitos / ${esc(c.fallos)} fallos</summary>${(c.hitos||[]).map(e=>`<p class="small">${esc(e.when)} · ${esc(e.fact)}</p>`).join('')||'<p class="small">Sin hitos destacados.</p>'}</details>`).join('')||'<p>Sin etapas documentadas todavía.</p>'}</div><div class="research"><h3>Tendencias de acción calculadas</h3><p class="small">Estos valores se ajustan mediante reglas de éxito y fallo. No representan preferencias declaradas ni rasgos psicológicos medidos.</p>${Object.entries(data.preferences||{}).map(([k,v])=>`<p>${esc(k)} · ${Math.round(v*100)}%</p>`).join('')}</div>${(data.experience_summary||[]).map(e=>`<div class="feedentry"><div class="date">${esc(e.when)} · ${esc(e.action)}</div>${esc(e.fact)}</div>`).join('')}`}
function renderVersions(){
 const sessions=data.engine_sessions||[],identity=data.engine_identity||{};
 const local=stamp=>{if(!stamp)return '—';const date=new Date(stamp);return Number.isNaN(date.getTime())?esc(stamp):esc(date.toLocaleString('es-AR',{dateStyle:'short',timeStyle:'medium'}))};
 const sim=minutes=>{if(typeof minutes!=='number')return '—';let d=Math.floor(minutes/1440)+1,m=Math.floor(minutes%1440);return 'Día '+d+' · '+String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')};
 const status=s=>s.state==='en_curso'?'En curso':s.state==='cerrada'?'Cerrada':'Sin cierre registrado';
 return `<div class="research"><h3>Historial de versiones de esta partida</h3><p>Registro técnico de las sesiones desde Nilo 0.5.9.1. Las horas anteriores no se reconstruyen. El historial describe con qué programa se ejecutó el mundo; no es conocimiento de Nilo.</p><p class="small">Versión actual: ${esc(identity.engine_version||'Desconocida')} · Commit: ${esc(identity.code_commit||'No disponible (por ejemplo, copia ZIP)')}</p></div>`+
 (sessions.length?sessions.map(s=>`<details class="research"><summary><div class="date"><span>Sesión ${esc(s.id)} · ${esc(status(s))}</span><span>v${esc(s.engine_version)}</span></div><strong>${local(s.started_utc)}</strong> · ${esc(sim(s.simulated_start_min))} → ${esc(sim(s.simulated_end_min))}</summary><div class="details"><p><strong>Inicio real:</strong> ${local(s.started_utc)}</p><p><strong>Fin real:</strong> ${s.ended_utc?local(s.ended_utc):'No registrado'}</p><p><strong>Último guardado:</strong> ${local(s.last_seen_utc)}</p><p><strong>Tiempo simulado:</strong> ${esc(sim(s.simulated_start_min))} → ${esc(sim(s.simulated_end_min))}</p><p><strong>Versión:</strong> ${esc(s.engine_version)} · ${esc(s.scenario_id)} / ${esc(s.environment_id)}</p><p><strong>Commit Git:</strong> ${esc(s.code_commit||'No disponible')}</p><p class="small">Huella del manifiesto: ${esc(s.manifest_sha256||'No disponible')}</p><p><strong>Modelo configurado al iniciar:</strong> ${esc(s.configured_provider||'—')} / ${esc(s.configured_model||'—')}</p><p><strong>Modelos realmente utilizados:</strong></p>${(s.models_used||[]).map(x=>`<p class="small">${esc(x.provider)} / ${esc(x.model)} · ${x.purpose==='chat'?'Chat':'Deliberaciones'}: ${esc(x.calls)}</p>`).join('')||'<p class="small">Todavía sin consultas registradas en esta sesión.</p>'}<p class="small">«Sin cierre registrado» puede indicar cierre imprevisto; no atribuye automáticamente un fallo al programa.</p></div></details>`).join(''):'<div class="empty">Todavía no se registraron sesiones.</div>');
}
function renderResearch(){
 const selection=(data.research||[]).filter(q=>typeof matchesResearchView!=='function'||matchesResearchView(q));
 return (selection.length?selection.map(q=>{
 const change=q.project_retirement||null;
 const project=change?[...(data.projects||[]),...(data.project?[data.project]:[])].find(p=>p.id===change.project_id):null;
 const retired=['pausada','archivada_sin_resolver','archivada_con_proyecto','integrada'].includes(q.state);
 const projectLink=project?'<button type="button" class="record-link" data-related-category="project" data-related-id="'+esc(project.id)+'">Ver proyecto vinculado</button>':'';
 const transitionHtml=retired?'<p class="small"><strong>Estado de investigación:</strong> '+esc(q.state||'—')+
  (change?.when?' · '+esc(change.when):'')+
  (change?.status?' · proyecto '+esc(change.status):'')+'</p>'+
  '<p class="small"><strong>Motivo registrado en el proyecto:</strong> '+esc(project?.closure_reason||'Motivo no registrado')+'</p>'+projectLink+
  (q.merged_into?'<p class="small"><strong>Integrada en:</strong> '+esc(q.merged_into)+'</p>':''):
  ['documentada','concluida'].includes(q.state)?'<p class="small"><strong>Documentada:</strong> '+esc(q.closed||q.updated||'Fecha no registrada')+'</p>':'';

 const linked=Array.isArray(q.evidence)?q.evidence:[];
 const refs=Array.isArray(q.evidence_ids)?q.evidence_ids:[];
 const linkedList=linked.length?`<details class="research-evidence"><summary>Ver los ${linked.length} registros asociados</summary><ol>${linked.map(e=>`<li><span class="muted">${esc(e.when||'Fecha no registrada')}</span>${(e.facts||[]).map(f=>`<div>${renderEvidenceText(f)}</div>`).join('')||'<div>Sin descripción disponible.</div>'}</li>`).join('')}</ol></details>`:'<p class="small">Sin resultados asociados registrados.</p>';
 const measurements=refs.map(id=>{const m=(data.measurements||[]).find(x=>x.id===id);return measurementLink(id,m?.op||'')});
 return `<div class="research" data-research-record="${esc(q.id||'')}"><div class="date"><span>${esc(q.started)}</span><span>${esc(q.state||'abierta')}</span></div><h3>${esc(q.question)}</h3><p><span class="muted">Hipótesis:</span> ${esc(q.hypothesis||'Todavía no tengo una.')}</p>${q.conclusion?`<p><strong>Conclusión registrada:</strong> ${renderEvidenceText(q.conclusion)}</p>${refs.length?`<p class="small"><strong>Mediciones citadas:</strong> ${measurements.join(' · ')}</p>`:''}`:''}<p class="small">${linked.length} registros de acciones asociados mientras Nilo investigaba este tema. No todos acreditan la hipótesis.</p>${linkedList}${transitionHtml}${recordLinks('research',q.id)}</div>`;
 }).join(''):'<div class="empty">No hay investigaciones para este filtro.</div>')+renderPredictions();}
function renderPredictions(){
 const all=data.prediction_log||[];
 const labels={pendiente:'Pendiente de ejecutar',prediccion_coincide:'Coincidió la métrica',prediccion_no_coincide:'No coincidió la métrica',variable_no_medida:'Variable no medida',sin_modelo_evaluable:'Sin evaluación física',criterio_incompleto:'Sin criterio numérico completo',prediccion_cualitativa:'Predicción cualitativa'};
 const criterion=p=>p.metric&&p.operator&&p.threshold!=null?(p.metric+' '+({gte:'≥',gt:'>',lte:'≤',lt:'<',eq:'='}[p.operator]||p.operator)+' '+p.threshold):p.metric?(p.metric+' · sin umbral comprobable'):'Sin variable cuantificada';
 return '<div class="research"><h3>Predicciones registradas antes de actuar</h3><p>Estas predicciones fueron registradas antes de ejecutar cada ensayo. Solo se contrastan las variables físicas realmente medidas: coincidir no demuestra toda la hipótesis ni propiedades que el motor desconoce.</p></div>'+
 (all.length?all.map(p=>`<details class="research" data-prediction-record="${esc(p.id||'')}"><summary><div class="date"><span>${esc(p.when)} · ${esc(actionName({op:p.operation,target:p.target}))}</span><span>${esc(labels[p.status]||p.status)}</span></div><strong>${esc(p.hypothesis)}</strong></summary><div class="details"><p><strong>Efecto esperado:</strong> ${esc(p.expected_effect)}</p><p><strong>Predicción comprobable:</strong> ${esc(criterion(p))}</p><p><strong>Resultado de la acción:</strong> ${esc(p.evaluation_status||'Pendiente')}</p><p><strong>Variable observada:</strong> ${p.measured_value==null?'Sin dato disponible':esc(p.measured_value)}</p><p><strong>Otras variables medidas:</strong> ${esc((p.available_metrics||[]).join(', ')||'Ninguna')}</p><p><strong>Prueba:</strong> ${p.measurement_id?measurementLink(p.measurement_id,p.operation):'Todavía no registrada'}</p><p class="small">${esc(p.scope||'El contraste aún no acredita una propiedad física.')}</p>${recordLinks('prediction',p.id)}</div></details>`).join(''):'<div class="empty">Nilo todavía no formuló predicciones para ensayos concretos.</div>');
}
function measurementActionTitle(m){
 const op=String(m.op||'');
 if(op==='go'){
  const position=m.end?.position;
  const original=m.start?.position;
  if(Array.isArray(position)&&position.length>=2&&position.every((n,i)=>i>=2||Number.isFinite(Number(n)))){
   const loc='('+position[0]+', '+position[1]+')';
   const moved=!Array.isArray(original)||position[0]!==original[0]||position[1]!==original[1];
   return moved?'Desplazamiento hasta '+loc:'Intento de desplazamiento en '+loc;
  }
  return 'Desplazamiento registrado';
 }
 if(op==='rest')return 'Descanso '+(m.condition==='refugio'?'en refugio':m.condition==='intemperie'?'a la intemperie':'registrado');
 const title=actionName({op:m.op,target:m.target});
 return title==='Acción sin especificar'?'Acción registrada':title;
}
function measurementSummary(m){
 const facts=Array.isArray(m.verified_facts)?m.verified_facts:[];
 const mins=Number.isFinite(m.duration_minutes)?m.duration_minutes.toLocaleString('es-AR',{maximumFractionDigits:2}):'—';
 const walk=m.op==='go'?facts.join(' ').match(/Avanc[eé] (\d+) tramos?/i):null;
 return (walk?walk[1]+' tramos recorridos · ':'')+mins+' min'+
   (m.op==='rest'&&m.condition?' · '+m.condition:'');
}
function measurementLink(id,op=''){
 const found=[...(data?.measurements||[]),...(focusedMeasurement?[focusedMeasurement]:[])].find(m=>m.id===id);
 const description=found?measurementActionTitle(found):op?actionName({op}):'Medición archivada';
 return `<button type="button" class="measurement-link" data-measurement-id="${esc(id)}">Ver ensayo · ${esc(description)}</button>`;
}
function renderEvidenceText(raw){
 const str=String(raw??''),pattern=/\b([a-z_]+)\s*\((med-[a-z0-9-]+);\s*([^)]+)\)|\b(med-[a-z0-9-]+)\b/gi;
 let html='',last=0,match;
 while((match=pattern.exec(str))!==null){
  html+=esc(str.slice(last,match.index));
  html+=match[2]?measurementLink(match[2],match[1])+' · '+esc(match[3]):measurementLink(match[4]);
  last=pattern.lastIndex;
 }
 return html+esc(str.slice(last));
}
async function openMeasurement(id){
 if(!/^med-[a-z0-9-]{1,56}$/i.test(id))return false;
 const existing=(data?.measurements||[]).find(m=>m.id===id);
 if(!existing&&focusedMeasurement?.id!==id){
  try{
   const response=await fetch('/api/measurement?id='+encodeURIComponent(id),{cache:'no-store'});
   const record=await response.json();
   if(!response.ok||record.id!==id)throw Error(record.error||'La medición no está disponible en el archivo.');
   focusedMeasurement=record;
  }catch(error){alert(error.message);return false;}
 }
 if(el('record-dialog').open)el('record-dialog').close();
 if(el('catchup-dialog').open)el('catchup-dialog').close();
 essayView='all';switchTab('measurements');
 const node=[...el('feed').querySelectorAll('[data-measurement-record]')].find(element=>element.dataset.measurementRecord===id);
 if(!node){alert('No se pudo mostrar la medición seleccionada.');return false;}
 node.open=true;node.classList.add('record-target');
 node.scrollIntoView({block:'start',behavior:'smooth'});
 return true;
}
function isDeliberateTest(m){return ['experiment','compare','use','excavate'].includes(m.op)||(m.op==='rest'&&m.rest_comparable)||(data?.prediction_log||[]).some(p=>p.measurement_id===m.id)}
function renderMeasurements(){
 const recent=data.measurements||[],all=[...recent,...(focusedMeasurement&&!recent.some(m=>m.id===focusedMeasurement.id)?[focusedMeasurement]:[])],ms=essayView==='tests'?all.filter(m=>isDeliberateTest(m)):all,cs=data.conclusions||[],status=data.experiment_status||{};
 const number=v=>typeof v==='number'?v.toFixed(2):'—';
 return `<div class="essay-filters" aria-label="Filtrar ensayos"><button type="button" data-essay-view="tests" class="${essayView==='tests'?'active':''}">Pruebas</button><button type="button" data-essay-view="all" class="${essayView==='all'?'active':''}">Todas las mediciones</button></div><div class="research"><h3>Mediciones y resultados de acciones</h3><p class="small">Las pruebas se distinguen de las mediciones rutinarias mediante el filtro. Completar una acción no equivale a comprobar una hipótesis; los detalles físicos están en cada ficha.</p><p class="small"><strong>Comparación de descansos:</strong> ${esc(status.conclusion||status.message||status.status||'Sin ensayos comparables')}</p></div>`+
 (cs.map(c=>`<div class="research" data-conclusion-record="${esc(c.id||'')}"><div class="date"><span>${esc(c.when)}</span><span>CONCLUSIÓN REGISTRADA</span></div><h3>${renderEvidenceText(c.text)}</h3><p class="small">Evidencias: ${(c.evidence_ids||[]).map(id=>measurementLink(id)).join(' · ')}. ${esc(c.scope||'')}</p></div>`).join(''))+
 (ms.map(m=>`<details class="research" data-measurement-record="${esc(m.id||'')}">
  <summary><div class="date"><span>${esc(m.when)}</span><span>${m.evaluation_status==='no_evaluable'?'SIN MODELO FÍSICO':(m.success?'ACCIÓN COMPLETADA':'ACCIÓN FALLIDA')}</span></div>
  <strong>${esc(measurementActionTitle(m))}</strong>
  <div class="measurement-key">${esc(measurementSummary(m))}</div></summary>
  <div class="details">
   ${m.op==='go'?`<p><strong>Recorrido:</strong> ${esc(Array.isArray(m.start?.position)?'('+m.start.position.slice(0,2).join(', ')+')':'—')} → ${esc(Array.isArray(m.end?.position)?'('+m.end.position.slice(0,2).join(', ')+')':'—')}</p>`:''}
   <p><strong>Cambio de energía:</strong> ${number(m.start?.needs?.energia)} → ${number(m.end?.needs?.energia)} (${number(m.needs_delta?.energia)} puntos)${m.energy_per_hour!==undefined?` · ${number(m.energy_per_hour)} puntos/h`:''}</p>
   ${m.physical?`<p><strong>Variable física medida:</strong> ${Object.entries(m.physical.metrics||{}).map(([k,v])=>`${esc(k)}: ${number(v)}`).join(' · ')||'Sin métricas cuantitativas adicionales'}</p><p class="small">${esc(m.physical.kind)} · ${esc(m.physical.method)} · ${esc(m.physical.subject)} · ${esc(m.physical.precision||'')}</p>`:''}
   ${m.op==='rest'?`<p class="small">${m.rest_comparable?'Descanso apto para comparación':'Descanso no comparable con los criterios actuales (saturación u otras condiciones)'}</p>`:''}
   ${Object.entries(m.inventory_delta||{}).map(([k,v])=>`<p class="small">Inventario ${esc(k)}: ${v>0?'+':''}${esc(v)}</p>`).join('')}
   <p><strong>Resultado registrado:</strong> ${renderEvidenceText((m.verified_facts||[]).join(' · ')||'Sin descripción verificable disponible.')}</p>
   <details class="technical-details"><summary>Información técnica</summary>
    <p>ID de medición: ${esc(m.id||'Sin ID')} · Operación: ${esc(m.op||'Sin código')}${m.target?' · Objetivo: '+esc(m.target):''}</p>
    <p>Estado de evaluación: ${esc(m.evaluation_status||'Sin estado')}</p>
   </details>
  ${recordLinks('measurement',m.id)}</div>
 </details>`).join('')||'<div class="empty">Todavía no hay mediciones.</div>');
}
function oneProject(p){
 const status=String(p.status||'');
 const reasonHtml=['pausado','abandonado'].includes(status)?
  '<p class="small"><strong>Motivo de '+(status==='pausado'?'pausa':'abandono')+':</strong> '+esc(p.closure_reason||'Motivo no registrado')+'</p>':'';
 const evidence=p.closure_evidence;
 const closureHtml=status==='terminado'?
  '<p class="small"><strong>Cierre verificado:</strong> '+esc(evidence?.summary||'Evidencia no registrada')+'</p>'+
  (Array.isArray(evidence?.evidence_ids)&&evidence.evidence_ids.length?
   '<p class="small"><strong>Mediciones de cierre:</strong> '+evidence.evidence_ids.map(id=>measurementLink(id)).join(' · ')+'</p>':''):'';
 return `<div class="projectcard" data-project-record="${esc(p.id||'')}"><div class="date"><span>${esc(p.started||'—')}</span><span>${esc(p.status||'—').toUpperCase()}</span></div><h3>${esc(p.title||'Proyecto sin nombre')}</h3><p class="state">${esc(p.state||p.reason||'Sin detalle')}</p>${(p.subgoals||[]).length?`<div class="small" style="margin:7px 0">Próximos problemas: ${p.subgoals.map(v=>esc(v)).join(' · ')}</div>`:''}<div class="meter"><i style="width:${Math.max(0,Math.min(100,p.progress||0))}%"></i></div><div class="small">${p.progress||0}% estimado · ${p.steps_done||0} acciones · ${(p.verified_results||[]).length} últimos resultados conservados · ${p.failed_actions||0} fallos${p.last_result?` · Último resultado: ${renderEvidenceText(p.last_result)}`:''}</div><details class="physical-details"><summary>Trayectoria y evidencias</summary><p><strong>Motivo:</strong> ${esc(p.reason||'No registrado')}</p>${p.reconsideration_required?'<p class="agenda-caveat">Nilo necesita reconsiderar el método actual.</p>':''}<p><strong>Subobjetivos:</strong> ${esc((p.subgoals||[]).join(' · ')||'No documentados')}</p><p><strong>Hitos comprobados:</strong></p>${(p.verified_milestones||[]).slice(-12).reverse().map(h=>`<p class="small">${esc(h.when)} · ${renderEvidenceText(h.fact)}</p>`).join('')||'<p class="small">Sin hitos conservados.</p>'}<p><strong>Resultados recientes:</strong></p>${(p.verified_results||[]).slice(-15).reverse().map(v=>`<p class="small">${esc(v.when)} · ${renderEvidenceText(v.result)}</p>`).join('')||'<p class="small">Sin resultados comprobados.</p>'}</details>${reasonHtml}${closureHtml}${projectRecordLinks(p.id)}</div>`}
function newsReading(){return data?.unread?.news||0}
// Una novedad puede tener un único hecho: en ese caso no mostramos un desplegable vacío.
// Compatibilidad: las versiones antiguas guardaban el título repetido al principio del detalle.
function newsExtra(n){
 const title=String(n.title||'').trim();let detail=String(n.detail||'').trim();
 if(!detail||detail.replace(/[\s.·;:!…]+$/g,'').toLocaleLowerCase()===title.replace(/[\s.·;:!…]+$/g,'').toLocaleLowerCase())return '';
 if(detail.toLocaleLowerCase().startsWith(title.toLocaleLowerCase())){
   detail=detail.slice(title.length).replace(/^[\s.·;:!…-]+/,'').trim();
 }
 return detail;
}
function renderNews(){return (data.news||[]).map(n=>{
 const unread=!n.read,additional=newsExtra(n);
 const heading=`<div class="news-info"><span class="date">${esc(n.when)} · ${esc(n.kind)}${unread?' · NUEVO':''}</span><strong>${esc(n.title)}</strong></div>`;
 if(!additional)return `<article class="news-entry ${unread?'unread':'read'}" data-entry-id="${esc(n.id)}"><div class="news-heading">${heading}</div></article>`;
 return `<details class="news-entry ${unread?'unread':'read'}" data-entry-id="${esc(n.id)}"><summary>${heading}<span class="muted">⌄</span></summary><div class="news-more">${esc(additional)}</div></details>`;
 }).join('')}
function decorateRecords(){
 const box=el('feed'),keys=new Set(tabEntries(tab,data)),seen=new Set(locallyReviewed[tab]||[]);
 const mark=(selector,getKey)=>box.querySelectorAll(selector).forEach((node,i)=>{
  const key=getKey(node,i);
  if(!key||!keys.has(key))return;
  node.dataset.reviewEntryKey=key;
  if(!seen.has(key))node.classList.add('new-record');
 });
 const keyOf=(record,fall='')=>record?String(record.id??fall):'';
 if(tab==='activity'&&activityView==='all')mark('[data-event-record]',node=>{
  const e=(data.events||[]).find(r=>r.id===node.dataset.eventRecord);
  return keyOf(e,e?.when+':'+e?.text);
 });
 if(tab==='research'){
  mark('[data-research-record]',node=>{
   const q=(data.research||[]).find(r=>r.id===node.dataset.researchRecord);
   return q?keyOf(q,q.started+':'+q.question)+':'+(q.state||''):'';
  });
  mark('[data-prediction-record]',node=>{
   const p=(data.prediction_log||[]).find(r=>r.id===node.dataset.predictionRecord);
   return p?keyOf(p)+':'+(p.status||''):'';
  });
 }
 if(tab==='measurements'){
  mark('[data-measurement-record]',node=>node.dataset.measurementRecord);
  mark('[data-conclusion-record]',node=>node.dataset.conclusionRecord);
 }
 if(tab==='findings'){
  mark('[data-finding-record]',node=>node.dataset.findingRecord);
  mark('[data-knowledge-record]',node=>node.dataset.knowledgeRecord);
 }
 if(tab==='creations'){
  mark('[data-design-record]',node=>{
   const d=(data.designs||[]).find(r=>r.id===node.dataset.designRecord);
   return d?keyOf(d,d.name)+':'+(d.versions?.at(-1)?.version??'')+':'+(d.status||''):'';
  });
  mark('[data-plan-id]',node=>{
   const objects=[...(data.structures||[]),...(data.retired_structures||[]),...(data.items||[])];
   const o=objects.find(r=>(r.id||r.name)===node.dataset.planId);
   return o?keyOf(o,o.name)+':'+(o.revision||1):'';
  });
 }
 if(tab==='proposals')mark('details.research[data-proposal-id]',node=>{
  const p=(data.proposals||[]).find(item=>item.id===node.dataset.proposalId);
  return p?.status==='pendiente'?(p.id||p.title)+':pendiente':'';
 });
 if(tab==='projects')mark('[data-project-record]',node=>{
  const p=[...(data.projects||[]),...(data.project?[data.project]:[])].find(r=>r.id===node.dataset.projectRecord);
  return p?keyOf(p)+':'+p.status:'';
 });
 if(tab==='agenda')mark('[data-agenda-record]',node=>{
  const t=(data.agenda||[]).find(r=>r.id===node.dataset.agendaRecord);
  return t?keyOf(t)+':'+t.estado:'';
 });
 if(tab==='identity')mark('.feedentry',(_,i)=>{
  const e=(data.experience_summary||[])[i];return e?String(e.id??e.when+':'+e.fact):'';
 });
 if(tab==='habits'){
  mark('.feedentry',(_,i)=>{
   const h=(data.waiting_history||[])[i];return h?String(h.id??h.when+':'+h.action):'';
  });
  mark('[data-skill-index]',node=>{
   const a=(data.skills||[])[Number(node.dataset.skillIndex)];
   return a?String(a.key)+':'+String(a.count):'';
  });
 }
}
let floatingHelp=null;
function closeSectionHelp(returnFocus=false){
 if(!floatingHelp)return;
 const trigger=floatingHelp.trigger;
 floatingHelp.panel.remove();
 floatingHelp=null;
 trigger.setAttribute('aria-expanded','false');
 if(returnFocus&&trigger.isConnected)trigger.focus();
}
function openSectionHelp(trigger){
 if(floatingHelp?.trigger===trigger){closeSectionHelp();return;}
 closeSectionHelp();
 const panel=document.createElement('div');
 panel.className='section-help-popover';
 panel.setAttribute('role','dialog');
 panel.setAttribute('aria-label','Información: '+trigger.dataset.helpTitle);
 panel.innerHTML='<strong>'+esc(trigger.dataset.helpTitle)+'</strong>'+trigger.helpHtml;
 document.body.appendChild(panel);
 const bounds=trigger.getBoundingClientRect();
 const width=panel.getBoundingClientRect().width;
 const height=panel.getBoundingClientRect().height;
 const left=Math.max(8,Math.min(window.innerWidth-width-8,bounds.right-width));
 const top=bounds.bottom+8+height<=window.innerHeight-8?bounds.bottom+8:
   Math.max(8,bounds.top-height-8);
 panel.style.left=left+'px';
 panel.style.top=top+'px';
 trigger.setAttribute('aria-expanded','true');
 floatingHelp={trigger,panel};
}
function helpButton(title,html){
 const button=document.createElement('button');
 button.type='button';
 button.className='section-help';
 button.dataset.helpTitle=title;
 button.helpHtml=html;
 button.setAttribute('aria-label','Información: '+title);
 button.setAttribute('aria-expanded','false');
 button.title='Información sobre '+title;
 button.textContent='?';
 return button;
}
function relocateExplainer(){
 const feed=el('feed');
 const cards=[...feed.children].filter(node=>node.classList?.contains('research')
   &&node.tagName!=='DETAILS'&&node.querySelector(':scope > h3'));
 const allowed={
  measurements:['Mediciones y resultados de acciones'],
  creations:['Diseños documentados'],
  findings:['Hallazgos documentados','Propiedades recientes registradas por el motor'],
  research:['Predicciones registradas antes de actuar'],
  proposals:['Solicitudes de ampliación y revisión'],
  agenda:['Agenda y recordatorios']
 };
 for(const card of cards){
  const heading=card.querySelector(':scope > h3');
  const title=heading?.textContent?.trim();
  if(!allowed[tab]?.includes(title))continue;
  const body=[...card.children].filter(el=>el.tagName==='P')
     .map(p=>p.outerHTML).join('');
  const help=helpButton(title,body);
  const filters=tab==='measurements'?feed.querySelector('.essay-filters'):
    tab==='creations'?feed.querySelector('.creation-filters'):null;
  if(filters){
   filters.appendChild(help);
   card.remove();
  }else if(tab==='proposals'){
   const controls=card.querySelector('.controls');
   const bar=document.createElement('div');
   bar.className='section-info-line proposal-controls';
   if(controls)bar.appendChild(controls);
   bar.appendChild(help);
   card.replaceWith(bar);
  }else{
   const bar=document.createElement('div');
   bar.className='section-info-line';
   const label=document.createElement('span');
   label.textContent=title;
   bar.append(label,help);
   card.replaceWith(bar);
  }
 }
}

// La apertura de las fichas pertenece a la vista humana, no al estado de Nilo.
const FEED_RECORD_ATTRIBUTES=['data-entry-id','data-research-record','data-prediction-record',
 'data-measurement-record','data-conclusion-record','data-finding-record','data-knowledge-record',
 'data-design-record','data-plan-id','data-proposal-id','data-project-record','data-agenda-record',
 'data-event-record','data-skill-index','data-review-entry-key'];
let renderedFeedTab=null;
function feedDetailIdentity(node){
 if(node.classList?.contains('section-help'))return tab+'|ayuda|'+node.dataset.helpTitle;
 const root=node.closest(FEED_RECORD_ATTRIBUTES.map(x=>'['+x+']').join(','));
 if(root){
  const attr=FEED_RECORD_ATTRIBUTES.find(x=>root.hasAttribute(x));
  const nested=root===node?'root':Array.from(root.querySelectorAll('details')).indexOf(node);
  return tab+'|'+attr+'|'+root.getAttribute(attr)+'|'+nested;
 }
 const titles=[];
 for(let current=node;current&&current.id!=='feed';current=current.parentElement)
  if(current.tagName==='DETAILS')
   titles.unshift((current.querySelector(':scope > summary')?.textContent||'').trim().slice(0,160));
 return tab+'|unkeyed|'+titles.join('|');
}
function feedExpandedDetails(){
 return new Set([...el('feed').querySelectorAll('details[open]')].map(feedDetailIdentity));
}
function restoreFeedExpandedDetails(keys){
 for(const node of el('feed').querySelectorAll('details')){
  if(keys.has(feedDetailIdentity(node)))node.open=true;
 }
}
function assignAccordionGroups(){
 const selectors=[
  ['measurementRecord','ensayos'],['predictionRecord','predicciones'],
  ['designRecord','disenos'],['planId','objetos'],
  ['proposalId','propuestas'],['agendaRecord','agenda'],
  ['projectRecord','proyectos']
 ];
 const opened=new Map();
 for(const node of el('feed').children){
  if(node.tagName!=='DETAILS')continue;
  const match=selectors.find(([attr])=>node.dataset[attr]!==undefined);
  // Las secciones físicas y las predicciones no se excluyen entre sí.
  const group=tab+':'+(match?match[1]:'archivo');
  node.dataset.accordionGroup=group;
  if(node.open){
   if(opened.has(group))opened.get(group).open=false;
   opened.set(group,node);
  }
 }
}
function enforceAccordionGroup(node){
 if(node?.tagName!=='DETAILS'||!node.open||node.parentElement!==el('feed'))return;
 const group=node.dataset.accordionGroup;
 if(!group)return;
 for(const peer of el('feed').children){
  if(peer!==node&&peer.tagName==='DETAILS'&&peer.open
      &&peer.dataset.accordionGroup===group)peer.open=false;
 }
}

