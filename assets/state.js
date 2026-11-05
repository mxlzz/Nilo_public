
let focusedMeasurement=null;
let activityView='featured',creationView='all',essayView='tests',proposalFilter='all';
let data=null,tab='notes',activeGroup='diario',view='near',mapLayer='follow',showTrail=true,lastFeedSig='',lastChatSig='',gotAt=0,lastNeedsSig='';
const stored=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const RESEARCH_VIEWS=['abiertas','pausadas','documentadas','archivadas','todas'];
let researchView=stored('nilo.researchView.v1','todas');
if(!RESEARCH_VIEWS.includes(researchView))researchView='todas';
function matchesResearchView(q){
 if(researchView==='todas')return true;
 const state=String(q.state||'abierta').toLowerCase();
 if(researchView==='abiertas')return state==='abierta';
 if(researchView==='pausadas')return state==='pausada';
 if(researchView==='documentadas')return ['documentada','concluida'].includes(state);
 return ['archivada_sin_resolver','archivada_con_proyecto','integrada'].includes(state);
}
const statusViews=stored('nilo.statusViews.v1',{agenda:'vigentes',projects:'vigentes'});
const STATUS_VIEW_KEYS=['vigentes','agendados','finalizados','bloqueados','todos'];
function selectedStatusView(section){
 const value=statusViews?.[section];
 return STATUS_VIEW_KEYS.includes(value)?value:'vigentes';
}
function matchesStatusView(record,section){
 const view=selectedStatusView(section);
 if(view==='todos')return true;
 const status=String(record?.estado||record?.status||'').toLowerCase();
 if(section==='agenda'){
  if(view==='vigentes')return ['en_curso','lista_para_revisar'].includes(status);
  if(view==='agendados')return ['pendiente','pospuesta'].includes(status);
  if(view==='finalizados')return ['completada','cancelada'].includes(status);
  return status==='bloqueada';
 }
 if(view==='vigentes')return status==='activo';
 if(view==='agendados')return status==='pausado' && (data?.agenda||[]).some(t=>t.proyecto_id===record.id && t.modo==='recordatorio' && ['pendiente','lista_para_revisar'].includes(t.estado));
 if(view==='finalizados')return ['terminado','abandonado'].includes(status);
 return status==='pausado';
}
const UI_PREF_KEYS={theme:'nilo.theme.v1',mapDisplay:'nilo.mapDisplay.v2',resources:'nilo.resourceTab.v1',
                   mapZoom:'nilo.mapZoom.v2',mapView:'nilo.mapView.v1',
                   notifications:'nilo.notifications.v1',indicators:'nilo.tabIndicators.v1'};
const originalLocalPrefs=Object.fromEntries(Object.entries(UI_PREF_KEYS)
 .filter(([,key])=>localStorage.getItem(key)!==null)
 .map(([field,key])=>[field,stored(key,null)]));
let uiPrefsReady=false,prefsTimer=null;
function prefsSnapshot(){return Object.fromEntries(Object.entries(UI_PREF_KEYS).map(([field,key])=>[field,stored(key,null)]).filter(([,v])=>v!==null))}
async function sendUIPrefs(){
 const r=await fetch('/api/ui-preferences',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify(prefsSnapshot())});
 if(!r.ok)throw Error('No se pudo conservar la configuración visual en disco.');
}
async function bootstrapUIPrefs(){
 try{
  const response=await fetch('/api/ui-preferences',{cache:'no-store'});
  if(!response.ok)throw Error('No se pudo leer la configuración visual');
  const saved=await response.json();
  const combined={...saved,...originalLocalPrefs};
  // Las preferencias ya existentes en este navegador prevalecen; el resto se
  // recupera de la carpeta antigua si allí ya se había guardado este archivo.
  for(const [field,key] of Object.entries(UI_PREF_KEYS)){
   if(combined[field]!==undefined)localStorage.setItem(key,JSON.stringify(combined[field]));
  }
  theme=themes.includes(combined.theme)?combined.theme:theme;
  document.documentElement.dataset.theme=theme;
  el('theme-select').value=theme;
  if(['both','map','none'].includes(combined.mapDisplay))setMapDisplay(combined.mapDisplay);
  if(['materials','tools','buildings'].includes(combined.resources))setResourceTab(combined.resources);
  if(combined.mapZoom&&['near','full'].every(k=>Number.isFinite(combined.mapZoom[k])&&combined.mapZoom[k]>=10&&combined.mapZoom[k]<=38)){
   mapZoom=combined.mapZoom;
  }
  const prefs=combined.mapView;
  if(prefs&&typeof prefs==='object'){
   view=['near','full'].includes(prefs.view)?prefs.view:view;
   mapLayer=['follow','0','-1'].includes(prefs.mapLayer)?prefs.mapLayer:mapLayer;
   showTrail=typeof prefs.showTrail==='boolean'?prefs.showTrail:showTrail;
   el('layerselect').value=mapLayer;
  }
  if(combined.notifications&&typeof combined.notifications==='object')notifyPrefs=combined.notifications;
  if(combined.indicators&&typeof combined.indicators==='object'){
   for(const key of Object.keys(indicatorModes))delete indicatorModes[key];
   Object.assign(indicatorModes,combined.indicators);
   migrateIndicatorModes();
  }
  uiPrefsReady=true;
  if(Object.keys(originalLocalPrefs).length)await sendUIPrefs();
  if(data){showMap();updateTabNotifications();updateReadActions()}
 }catch(error){uiPrefsReady=true;console.warn('Se conservan los ajustes de este navegador:',error)}
}

const themes=['bosque','grafito','terracota','grises-oscuros','grises-claros'];
let theme=stored('nilo.theme.v1','bosque');
if(!themes.includes(theme))theme='bosque';
document.documentElement.dataset.theme=theme;
document.getElementById('theme-select').value=theme;
document.getElementById('theme-select').addEventListener('change',ev=>{
  const next=ev.target.value;
  if(!themes.includes(next))return;
  theme=next;
  document.documentElement.dataset.theme=theme;
  saveLocal('nilo.theme.v1',theme);
});
const savedMapDisplay=stored('nilo.mapDisplay.v2',null);
let mapDisplay=['both','map'].includes(savedMapDisplay)?'both':
  savedMapDisplay==='none'?'none':
  (stored('nilo.mapVisible.v1',true)===false?'none':'both');
function setMapDisplay(mode){
 // Migración: "Solo mapa" equivale a mapa con referencias plegadas.
 if(mode==='map')mode='both';
 if(!['both','none'].includes(mode))return;
 mapDisplay=mode;
 const visible=mode==='both';
 el('map-content').hidden=!visible;
 el('map-toggle').textContent=visible?'Ocultar mapa':'Mostrar mapa';
 el('map-toggle').setAttribute('aria-pressed',String(visible));
 saveLocal('nilo.mapDisplay.v2',mode);
 if(visible)showMap();
}
const RESOURCE_TABS=['materials','tools','buildings'];
let resourceTab=stored('nilo.resourceTab.v1','materials');
if(!RESOURCE_TABS.includes(resourceTab))resourceTab='materials';
function setResourceTab(next){
 if(!RESOURCE_TABS.includes(next))return;
 resourceTab=next;
 document.querySelectorAll('[data-resource-tab]').forEach(button=>{
  const selected=button.dataset.resourceTab===next;
  button.classList.toggle('active',selected);
  button.setAttribute('aria-selected',String(selected));
  button.tabIndex=selected?0:-1;
  el('resource-panel-'+button.dataset.resourceTab).hidden=!selected;
 });
 saveLocal('nilo.resourceTab.v1',next);
}
let mapZoom=stored('nilo.mapZoom.v2',{near:22,full:16});
for(const key of ['near','full'])if(!Number.isFinite(mapZoom[key])||mapZoom[key]<10||mapZoom[key]>38)mapZoom[key]=key==='near'?22:16;
let notifyPrefs=stored('nilo.notifications.v1',{mode:'brief',source:'both'});
let notifyInitialized=false,seenEntries=new Set();
const saveLocal=(key,val)=>{
 try{localStorage.setItem(key,JSON.stringify(val))}
 catch(e){console.warn('No se pudieron guardar los ajustes locales',e);return}
 if(uiPrefsReady&&Object.values(UI_PREF_KEYS).includes(key)){
  clearTimeout(prefsTimer);
  prefsTimer=setTimeout(()=>sendUIPrefs().catch(e=>console.warn(e)),350);
 }
};
const el=id=>document.getElementById(id), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const CH={'@':['t-at','Nilo'],'T':['t-tree','arboleda'],'c':['t-cave','entrada a cueva'],'o':['t-mineral','mineral'],'~':['t-water','agua'],'^':['t-rock','roca'],'#':['t-wall','pared'],'.':['t-plain','suelo'],',':['t-grass','hierba'],'s':['t-sand','arena'],'r':['t-ruin','ruinas'],'h':['t-home','refugio'],'=':['t-road','sendero'],':':['t-gallery','galería'],'e':['t-exit','salida a superficie'],'v':['t-vent','ventilación'],'M':['t-mech','mecanismo'],'E':['t-struct','estructura'],'H':['t-home','habitáculo'],'?':['t-proto','prototipo'],' ':['','desconocido']};
function displayMinutes(v){if(v===null||v===undefined)return '—';let ss=Math.max(0,Math.round(v*60));return ss>=3600?`${Math.floor(ss/3600)} h ${Math.floor(ss%3600/60)} min`:ss>=60?`${Math.floor(ss/60)} min ${ss%60} s`:`${ss} s`}
function displaySeconds(v){if(v===null||v===undefined)return '—';let ss=Math.max(0,Math.round(v));return ss>=3600?`${Math.floor(ss/3600)} h ${Math.floor(ss%3600/60)} min`:ss>=60?`${Math.floor(ss/60)} min ${ss%60} s`:`${ss} s`}
function showNeeds(){let needs=data.needs?.valores||{},sens=data.needs?.sensaciones||{};
 const sig=Object.entries(needs).map(([k,v])=>k+':'+v).join('|')+'|'+JSON.stringify(sens);
 if(sig===lastNeedsSig)return;
 lastNeedsSig=sig;
 const titles={hidratacion:'Hidratación',nutricion:'Alimentación',energia:'Energía',abrigo:'Abrigo',seguridad:'Seguridad'};
 const help={
   hidratacion:'La reserva cae 0,55 puntos/h simulada. Sed: 90–100 bien hidratado; 60–<90 sin sed; 30–<60 algo de sed; 15–<30 mucha sed; <15 sed extrema y tensión corporal. Nilo decide cuándo beber. Preparar reservas futuras es una decisión diferente de tener sed.',
   nutricion:'La reserva cae 0,32 puntos/h simulada. Hambre: 90–100 completamente saciado; 60–<90 sin hambre; 30–<60 algo de hambre; 15–<30 mucha hambre; <15 hambre extrema. La tensión corporal física aparece bajo 12. Nilo decide cuándo comer: por acción explícita o delegación finita, nunca por un umbral automático.',
   energia:'La actividad reduce aproximadamente 1,15 puntos/h; la inactividad recupera 0,8 puntos/h y descansar recupera 6,6 puntos/h al aire libre o 10,6 bajo refugio (netos). Cansancio: ≥90 con mucha energía; 60–<90 descansado; 30–<60 algo cansado; 12–<30 muy cansado; <12 agotamiento severo y tensión corporal; ≤5 inconsciencia; recupera la conciencia al alcanzar 40. Nilo decide cuánto descansar (1–1440 min; 30 por defecto).',
   abrigo:'Indicador sin variación activa: todavía no se simulan cambios de temperatura ambiental ni exposición climática.',
   seguridad:'Indicador sin variación activa: el mundo todavía no modela amenazas ambientales que modifiquen esta reserva.'
 };
 const labels={hidratacion:{ninguna:'Bien hidratado',normal_sin_urgencia:'Sin sed',progresiva:'Algo de sed',intensa:'Mucha sed',critica:'Sed extrema'},nutricion:{ninguna:'Completamente saciado',normal_sin_urgencia:'Sin hambre',progresiva:'Algo de hambre',intensa:'Mucha hambre',critica:'Hambre extrema'},energia:{ninguna:'Con mucha energía',normal_sin_urgencia:'Descansado',progresiva:'Algo cansado',intensa:'Muy cansado',tension_corporal:'Agotamiento severo',inconsciente:'Inconsciente'}};
 const kind={hidratacion:'sed',nutricion:'hambre',energia:'cansancio'};
 el('needs').innerHTML=Object.entries(needs).map(([k,v])=>{
   const level=sens[kind[k]],description=level?(labels[k]?.[level]||level):'';
   return `<div class="needline ${k==='abrigo'||k==='seguridad'?'need-inactive':''}"><div class="pair small"><span>${esc(titles[k]||k)}</span><strong>${Math.round(v)}%</strong><button class="needinfo" type="button" aria-label="Información sobre ${esc(titles[k]||k)}" aria-describedby="need-tip-${esc(k)}">?</button><div class="needtip" id="need-tip-${esc(k)}" role="tooltip"><strong>${esc(titles[k]||k)} · ${Math.round(v)}%</strong>${description?'Sensación actual: '+esc(description)+'. ':''}${esc(help[k]||'Indicador corporal observado.')}</div></div><div class="meter"><i class="${v<30?'low':''}" style="width:${Math.max(0,Math.min(100,v))}%"></i></div>${description?'<div class="small">'+esc(description)+'</div>':''}</div>`;
 }).join('');
}
const ACTION_LABELS={
 compare:'Comparar mediciones',modify:'Modificar objeto',dismantle:'Desmontar objeto',
 write:'Escribir en el cuaderno',explore:'Explorar el entorno',inspect:'Inspeccionar',
 gather:'Recolectar',experiment:'Realizar experimento',combine:'Combinar materiales',
 build:'Construir',craft:'Fabricar herramienta',use:'Probar herramienta',
 excavate:'Excavar',descend:'Descender',ascend:'Ascender',rest:'Descansar',
 forage:'Buscar alimento',drink:'Beber agua',eat:'Comer',
 conclude:'Registrar conclusión',go:'Desplazarse',design:'Diseñar',
 propose:'Presentar propuesta',assemble:'Ensamblar',report_issue:'Informar un problema'
};
function actionName(s){
 if(!s)return 'Acción sin especificar';
 const op=String(s.op||'');
 if(op==='go'){
  if(s.target==='agua')return 'Desplazarse hacia el agua';
  if(Number.isFinite(Number(s.x))&&Number.isFinite(Number(s.y))&&s.x!=null&&s.y!=null)
   return 'Desplazarse hacia ('+s.x+', '+s.y+')';
  return 'Desplazarse';
 }
 const name=ACTION_LABELS[op]||'Operación '+op;
 const rawSubject=s.item||s.target||s.name||'';
 // El ID es una referencia de ejecución, no una etiqueta legible.
 const known=(data?.items||[]).find(tool=>tool.id===rawSubject);
 const subject=known?.name||rawSubject;
 return name+(subject?' · '+subject:'');
}
function showMap(){
 if(!data||mapDisplay==='none')return;
 let activeLayer=mapLayer==='follow'?String(data.position[2]):mapLayer;
 let rows=data.maps?.[activeLayer]||data.map,beginX=0,beginY=0;
 const positionOnLayer=activeLayer===String(data.position[2]);
 el('layerselect').value=mapLayer;
 if(view==='near'){
   let [x,y]=positionOnLayer?data.position:[Math.floor(data.w/2),Math.floor(data.h/2)];
   beginX=Math.max(0,Math.min(data.w-17,x-8));
   beginY=Math.max(0,Math.min(data.h-11,y-5));
   rows=rows.slice(beginY,beginY+11).map(r=>r.slice(beginX,beginX+17));
 }
 const font=mapZoom[view];
 el('map').style.setProperty('--font-size',font+'px');
 el('zoomlabel').textContent=font+' px';
 el('near').classList.toggle('active',view==='near');
 el('full').classList.toggle('active',view==='full');
 el('trailtoggle').classList.toggle('active',showTrail);
 const ongoing=data.active_intervention;
 const marker=(ongoing&&String(ongoing.z)===activeLayer&&Number.isInteger(ongoing.x)&&Number.isInteger(ongoing.y))?ongoing:null;
 let trailAge={};
 if(showTrail){for(let s of data.trail_layers?.[activeLayer]||[]){if(s.age>=25)continue;let key=s.x+','+s.y;if(!(key in trailAge))trailAge[key]=s.age}}
 const coord=(n,corner=false)=>corner?'<span class="coord-cell corner" aria-hidden="true"></span>':`<span class="coord-cell ${n>=10?'two':''}" title="${n}"><span>${n}</span></span>`;
 const cols=rows[0]?.length||0;
 let top=coord(0,true);
 for(let i=0;i<cols;i++)top+=coord(i+beginX);
 const body=rows.map((row,j)=>{
   const yy=j+beginY;
   let line=coord(yy);
   for(let i=0;i<row.length;i++){
     let xx=i+beginX,ch=row[i],b=data.structure_layers?.[activeLayer]?.[xx+','+yy];
     let cl=CH[ch]?.[0]||'t-plain',bs=data.structure_cell_lists?.[activeLayer]?.[xx+','+yy]||[],title=bs.length?bs.map(q=>q.name).join(' / '):CH[ch]?.[1]||'';
     const age=trailAge[xx+','+yy];
     let trail='';
     if(ch!=='@'&&age!=null){const band=age<3?5:age<7?4:age<12?3:age<18?2:1;trail=' trail-'+band}
     const intervened=(marker&&marker.x===xx&&marker.y===yy&&ch!==' ')?' intervened':'';
     line+=`<span class="tile ${cl}${trail}${b?' structure has-structure':''}${intervened}" ${b?`data-x="${xx}" data-y="${yy}" tabindex="0" role="button"`:''} title="${esc(title)} (${xx}, ${yy})">${ch===' '?'&nbsp;':(['t-plain','t-grass','t-sand','t-road','t-gallery'].includes(cl)?'<span class="terrain-glyph">'+esc(ch)+'</span>':esc(ch))}</span>`;
   }
   return line;
 }).join('\n');
 el('map').innerHTML=top+'\n'+body;
}

function show(data2){data=data2;gotAt=Date.now();el('online').textContent=data.paused?'En pausa':data.auto_wait_frozen?'Tiempo detenido · API':'Viviendo';el('statusdot').className='dot'+((data.paused||data.auto_wait_frozen)?' off':'');el('clock').textContent=data.time;el('effective-speed-label').textContent='Ritmo ×'+data.effective_speed+(data.planning?' · LLM':data.auto_wait_frozen?' · espera':data.paused?' · pausa':'');el('coords').textContent=`${data.level} · x ${data.position[0]} · y ${data.position[1]}${Number(data.position[2])===0?'':' · z '+data.position[2]}`;showMap();showNeeds();
 el('legend').innerHTML=Object.entries(CH).map(([sym,v])=>`<span><b class="${v[0]}">${sym===' '?'□':esc(sym)}</b> ${esc(v[1])}</span>`).join('');
 document.querySelectorAll('[data-speed]').forEach(b=>b.classList.toggle('active',+b.dataset.speed===data.speed));el('pause').textContent=data.paused?'Reanudar':'Pausar';el('autopause').textContent='Pausa auto: '+(data.auto_pause_on_wait?'activada':'desactivada');el('autopause').classList.toggle('active',data.auto_pause_on_wait);
 el('activity').textContent=data.activity;el('progressblock').style.display=data.progress==null?'none':'block';if(data.progress!=null){el('activitybar').style.width=Math.min(100,Math.max(0,data.progress))+'%';el('pct').textContent=data.progress+'%';el('remainingworld').textContent=displayMinutes(data.remaining_world_minutes);el('remainingreal').textContent=displaySeconds(data.remaining_real_seconds)}
 el('projectname').textContent=data.project?.title||'Entre proyectos';el('projectstate').textContent=data.project?.state||'Nilo está reconsiderando qué quiere investigar.';el('projectprogress').style.display=data.project?'block':'none';if(data.project){el('projectbar').style.width=(data.project.progress||0)+'%';el('projectpct').textContent=`Avance estimado por Nilo: ${data.project.progress||0}% · ${data.project.steps_done||0} acciones ejecutadas. No implica objetivo verificado.`}
 el('steps').innerHTML=data.plan.length?data.plan.map((x,i)=>`<div class="listrow"><span class="muted">${i+1}.</span> ${esc(actionName(x))}</div>`).join(''):'<p class="small">Sin pasos pendientes. Puede estar escribiendo o deliberando.</p>';
 el('inventory').innerHTML=Object.entries(data.inventory).length?Object.entries(data.inventory).map(([k,v])=>`<div class="listrow">${esc(k)} <span class="muted">× ${v}</span></div>`).join(''):'<span class="small">Sin materiales</span>';
 el('tools').innerHTML=(data.items||[]).length?data.items.map(i=>`<button type="button" class="listrow summary-jump" data-tool-jump="${esc(i.id||i.name)}" title="Abrir la ficha de la herramienta"><strong>${esc(i.name)}</strong> <span class="muted">· ${esc(i.form)} · ${i.durability}% durabilidad</span><div class="small">Materiales: ${esc((i.materials||[]).join(', '))} · ${esc(i.geometry?.shape||'sin geometría registrada')} · Pruebas: ${(i.tests||[]).length}${i.contents?.material?` · Contenido: ${esc(i.contents.material)} (${i.contents.quantity})`:''}</div>${(i.tests||[]).length?`<div class="small">Última prueba: ${esc(i.tests.at(-1).result)}</div>`:'<div class="small">Aún sin probar</div>'}</button>`).join(''):'<span class="small">Todavía no llevo herramientas.</span>';
 el('resource-tab-materials').textContent='Materiales · '+Object.keys(data.inventory||{}).length;
 el('resource-tab-tools').textContent='Herramientas · '+(data.items||[]).length;
 el('resource-tab-buildings').textContent='Obras · '+(data.structures||[]).length;
 el('buildings').innerHTML=data.structures.length?data.structures.map((b,i)=>`<div class="listrow"><button type="button" class="building" data-id="${esc(b.id||String(i))}" style="border:0;padding:0;text-align:left;color:var(--accent)">${esc(b.name)}</button> <span class="muted">(${b.pos?.slice(0,2).join(', ')}) · ${esc(b.category||'prototipo')}</span></div>`).join(''):'<span class="small">Todavía no construí nada.</span>';
 el('knowledge').innerHTML=data.knowledge.length?data.knowledge.slice(0,7).map(([k,v])=>`<button type="button" class="listrow summary-jump" data-knowledge-jump="${esc(k)}" title="Abrir este conocimiento en Hallazgos">${esc(v)}</button>`).join(''):'<span class="small">Todavía no comprobé propiedades.</span>';
 let ai=data.ai, routing=ai.routing||{}, provs=routing.providers||[];
 let waiting=ai.mode==='espera', backup=routing.last_provider==='groq';
 el('mode').textContent=!ai.configured?'Modo demostración':ai.mode==='limite'?'Límite diario':waiting?'Esperando API':backup?'Respaldo: Groq':'LLM conectado';
 el('mode').className='pill'+((!ai.configured||waiting||ai.mode==='limite')?' warn':'');
 el('apierror').innerHTML=!ai.configured?'<div class="warning">No hay clave API: Nilo usa planes de demostración. Agregá GEMINI_API_KEY o GROQ_API_KEY en config.env.</div>':ai.error?`<div class="warning">${esc(ai.error)}${ai.next_try_seconds?`<br>Próximo intento en aproximadamente ${displaySeconds(ai.next_try_seconds)}.`:''}</div>`:'';
 let providerLines=provs.map(p=>`${p.name==='groq'?'Groq':p.name==='gemini'?'Gemini':p.name} (${p.model}) · ${p.status}${p.retry_seconds?' · reintento en '+displaySeconds(p.retry_seconds):''}\n  Hoy: ${p.successes} respuestas · ${p.attempts} intentos · ${p.failures} errores${p.last_error?'\n  Último fallo: '+p.last_error:''}`);
 el('aiinfo').textContent=`Último modelo usado: ${routing.last_provider||'—'}${routing.last_model?' · '+routing.last_model:''}\nRespaldo: ${routing.fallback_enabled?'habilitado':'no configurado'}\nIntervalo mínimo real: ${ai.min_interval_seconds??60} s entre deliberaciones exitosas\nDeliberaciones exitosas: ${ai.daily_calls}/${ai.daily_limit} hoy\nRespuestas de chat exitosas: ${ai.chat_calls}/${ai.chat_limit} hoy\nÚltima deliberación: ${ai.tokens.entrada||0} entrada / ${ai.tokens.salida||0} salida\n\n${providerLines.join('\n\n')}`;
 updateTabNotifications();
 const newsCount=data.unread?.news||0, notesCount=data.unread?.journal||0;
 updateReadActions();
 processNotifications(data);
 if(tab==='chat')drawChat();else drawFeed();
}

