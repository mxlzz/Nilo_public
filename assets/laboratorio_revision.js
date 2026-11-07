/* Auditoría humana de solicitudes: nunca altera el LLM, el motor ni SQLite.
   El archivo se arma SOLO en el navegador, a partir de una solicitud original
   archivada o calculada; las marcas son propuestas, no cambios aplicados. */
(function(global){
"use strict";
const SCHEMA="nilo.lab.context_review.v1";
const MAX_NOTE=1600;
const MAX_OVERVIEW=5000;
const MAX_BODY=4*1024*1024;

function utf8(value){return new TextEncoder().encode(value)}
function cpSlice(value,start,end){return Array.from(value).slice(start,end).join("")}
async function sha256(value){
 const api=global.crypto?.subtle;
 if(!api)throw Error("Este navegador no permite verificar SHA-256. Usá localhost o un entorno seguro.");
 const digest=await api.digest("SHA-256",utf8(value));
 return Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,"0")).join("");
}
function key(path,block){
 return String(path)+"|"+block.start+":"+block.end+"|"+String(block.literal_sha256);
}
function normNote(text,max){
 if(typeof text!=="string"||text.length>max)throw Error("La observación supera el límite permitido.");
 return text;
}
function inferRoot(pointer){
 if(typeof pointer!=="string"||!pointer.startsWith("/"))return null;
 return pointer.split("/")[1].replace(/~1/g,"/").replace(/~0/g,"~");
}
function snapshotModel(value){
 if(!value||typeof value!=="object"||!Array.isArray(value.messages)
    ||typeof value.body_utf8!=="string")throw Error("No hay una solicitud literal verificable.");
 if(!["captured_http","calculated_preview"].includes(value.kind))
    throw Error("Origen del contexto no reconocido.");
 if(value.kind==="captured_http"&&value.sent_to_llm!==true)
    throw Error("La captura real está mal identificada.");
 if(value.kind==="calculated_preview"&&value.sent_to_llm!==false)
    throw Error("La previsualización no puede identificarse como envío real.");
 return value;
}
function getBlocks(model){
 const map=new Map();
 for(const m of model.messages){
   if(typeof m.path!=="string"||typeof m.text!=="string"
      ||!Array.isArray(m.segments)||!Array.isArray(m.blocks))
      throw Error("Mensaje incompleto: faltan los segmentos originales.");
   for(const b of m.blocks){
     if(!["text","field"].includes(b.kind))throw Error("Bloque sin tipo conocido.");
     const id=key(m.path,b);
     if(map.has(id))throw Error("Dos bloques comparten el mismo identificador.");
     map.set(id,{message:m,block:b});
   }
 }
 return map;
}
async function validate(model,selected){
 snapshotModel(model);
 if(utf8(model.body_utf8).length>MAX_BODY)throw Error("La solicitud excede el límite de exportación.");
 const originalHash=await sha256(model.body_utf8);
 if(originalHash!==model.body_sha256)throw Error("El SHA-256 de la solicitud no coincide con el cuerpo original.");
 if(model.body_bytes!==undefined&&model.body_bytes!==utf8(model.body_utf8).length)
    throw Error("Los bytes de la solicitud no coinciden con el cuerpo original.");
 // Además de los SHA, comprobar que cada texto del índice provenga de
 // exactamente esa ruta del cuerpo HTTP (evita una ficha falsa o desfasada).
 let payload;
 try{payload=JSON.parse(model.body_utf8)}
 catch(_){throw Error("El cuerpo original no contiene una solicitud JSON válida.")}
 const at=(pointer)=>{
   let value=payload;
   for(const token of pointer.split("/").slice(1)){
     const name=token.replace(/~1/g,"/").replace(/~0/g,"~");
     if(value===null||typeof value!=="object"||!(name in value))
       throw Error("Ruta de mensaje ajena al cuerpo original: "+pointer);
     value=value[name];
   }
   return value;
 };
 const catalog=getBlocks(model),seenMessages=new Set();
 for(const message of model.messages){
   if(seenMessages.has(message.path))throw Error("Mensajes duplicados en el índice");
   seenMessages.add(message.path);
   if(at(message.path)!==message.text)
     throw Error("Mensaje no coincide con el texto HTTP: "+message.path);
   const pieces=message.path.split("/");
   if(pieces[1]==="messages"&&Array.isArray(payload.messages)){
      if(payload.messages[Number(pieces[2])]?.role!==message.role)
         throw Error("Rol incompatible con el cuerpo HTTP.");
   }
   if(pieces[1]==="contents"&&Array.isArray(payload.contents)){
      if(payload.contents[Number(pieces[2])]?.role!==message.role)
         throw Error("Rol Gemini incompatible con el cuerpo HTTP.");
   }
   if(pieces[1]==="systemInstruction"&&message.role!=="system")
      throw Error("El rol de instrucciones del sistema no coincide.");
   if((await sha256(message.text))!==message.text_sha256)
      throw Error("El texto del rol no supera su SHA-256: "+message.path);
   let offset=0,joined="";
   for(const s of message.segments){
     if(s.start!==offset||!Number.isInteger(s.start)||!Number.isInteger(s.end)
        ||s.end<s.start||cpSlice(message.text,s.start,s.end)!==s.literal)
        throw Error("Los segmentos originales no son consecutivos: "+message.path);
     joined+=s.literal;offset=s.end;
   }
   if(joined!==message.text||offset!==Array.from(message.text).length)
      throw Error("La reconstrucción del mensaje no coincide: "+message.path);
   for(const block of message.blocks){
     if(!message.segments.some(segment=>
          segment.kind===block.kind &&
          segment.start===block.start&&segment.end===block.end &&
          segment.literal_sha256===block.literal_sha256))
        throw Error("Bloque ajeno a los segmentos originales: "+message.path);
     if(cpSlice(message.text,block.start,block.end)!==block.literal
        ||(await sha256(block.literal))!==block.literal_sha256)
        throw Error("Un bloque cambió desde su captura: "+message.path);
   }
 }
 for(const [id,selection] of selected){
   if(!catalog.has(id))throw Error("Selección ajena a esta solicitud.");
   normNote(selection.note,MAX_NOTE);
 }
 return catalog;
}
async function buildReview(model,selected,overview,policy){
 const catalog=await validate(model,selected);
 const notes=normNote(overview||"",MAX_OVERVIEW);
 const options=new Set(Array.isArray(policy?.optional_context)?policy.optional_context:[]);
 const proposals=[];
 for(const [id,marked] of selected){
   const {message,block}=catalog.get(id);
   const root=inferRoot(block.json_pointer);
   const profileEligible=message.role==="user"&&block.kind==="field"&&options.has(root);
   proposals.push({
     action:"propose_exclusion_only",
     message_path:message.path,role:message.role,
     json_pointer:block.json_pointer||null,root_field:root,
     start_codepoint:block.start,end_codepoint:block.end,
     field_title:block.title||null,display_group:block.display_group||"otros",
     original_literal:block.literal,original_literal_sha256:block.literal_sha256,
     observation:marked.note,
     existing_profile_optional_field:profileEligible,
     requires_manual_review:true,
     applied_to_engine:false
   });
 }
 return {
   schema:SCHEMA,
   created_utc:new Date().toISOString(),
   review_status:"human_proposal_not_applied",
   source:{
     kind:model.kind,sent_to_llm:model.sent_to_llm,
     provider:model.provider,model:model.model,purpose:model.purpose,
     attempt_id:model.attempt_id||null,call_id:model.call_id||null,
     status:model.status||null,simulated_at:model.simulated_at||null,
     stage:model.stage||null,scenario:model.scenario||null,
     seed:model.seed??null,profile:model.profile||null,
     installed_engine_version:policy?.engine_version||null,
     installed_commit:policy?.commit||null,
     captured_engine_version:model.captured_engine_version||null,
     version_caveat:"La versión instalada puede diferir de la que generó una captura histórica."
   },
   original:{
     body_utf8:model.body_utf8,body_sha256:model.body_sha256,
     body_bytes:utf8(model.body_utf8).length,
     messages:model.messages.map(m=>({
       path:m.path,role:m.role,text:m.text,text_sha256:m.text_sha256,
       blocks:m.blocks.map(b=>({
         kind:b.kind,title:b.title||null,json_pointer:b.json_pointer||null,
         start_codepoint:b.start,end_codepoint:b.end,
         literal_sha256:b.literal_sha256,display_group:b.display_group||"otros"
       }))
     })),
     provenance:model.provenance??null,
     related_episode:model.related_episode??null
   },
   proposals,
   general_observation:notes,
   integrity:{
     original_http_or_preview_sha256_verified:true,
     message_and_segment_sha256_verified:true,
     offsets_checked_as_unicode_codepoints:true,
     proposed_count:proposals.length,
     no_modified_prompt_generated:true,
     no_network_request_to_llm:true,
     no_motor_or_world_changes:true
   },
   caveats:[
     "Proponer excluir un bloque no elimina automáticamente campos de la simulación ni modifica el prompt.",
     "Algunos campos e instrucciones no son opcionales y requieren examen del funcionamiento antes de considerar cambios.",
     "El archivo incluye la solicitud literal y puede contener información privada. Revisarlo antes de adjuntarlo.",
     "Las secciones y títulos son editoriales; el texto original es la referencia.",
     "Una solicitud capturada en el límite de transporte no prueba que el proveedor remoto la haya recibido si hubo error de red."
   ]
 };
}
function node(tag,className,text){
 const e=document.createElement(tag);
 if(className)e.className=className;
 if(text!==undefined)e.textContent=String(text);
 return e;
}
function download(name,payload){
 if(!global.Blob||!global.URL?.createObjectURL)throw Error("No se puede guardar el archivo en este navegador.");
 const blob=new Blob([JSON.stringify(payload,null,2)+"\n"],{type:"application/json;charset=utf-8"});
 const objectUrl=global.URL.createObjectURL(blob);
 try{
   const link=node("a");link.href=objectUrl;link.download=name;
   document.body.appendChild(link);link.click();link.remove();
 }finally{
   // Safari puede iniciar la descarga después del siguiente ciclo del UI;
   // revocar inmediatamente puede cancelar la exportación del archivo.
   if(typeof global.setTimeout==="function")
     global.setTimeout(()=>global.URL.revokeObjectURL(objectUrl),15000);
   else global.URL.revokeObjectURL(objectUrl);
 }
}
function controller(model,policy){
 const source=snapshotModel(model),selected=new Map(),controls=new Map(),groupControls=[];
 let overview="",counts=[],busy=false;
 const all=getBlocks(source);
 function refresh(){
   for(const [id,boxes] of controls)for(const box of boxes)box.checked=selected.has(id);
   for(const group of groupControls){
     const on=group.ids.filter(id=>selected.has(id)).length;
     group.box.checked=on===group.ids.length&&on>0;
     group.box.indeterminate=on>0&&on<group.ids.length;
   }
   for(const label of counts)label.textContent=selected.size+" bloques marcados para revisión";
 }
 function set(id,checked){
   if(!all.has(id))throw Error("Bloque ajeno a esta consulta");
   if(checked){if(!selected.has(id))selected.set(id,{note:""})}
   else selected.delete(id);
   refresh();
 }
 function addBlock(container,message,block){
   const id=key(message.path,block);
   if(!all.has(id))throw Error("Bloque inválido");
   const wrap=node("div","nilo-review-item");
   const label=node("label","nilo-review-check");
   const input=node("input");input.type="checkbox";
   const text=node("span","", "Proponer excluir este bloque");
   label.append(input,text);wrap.appendChild(label);
   const optional=(message.role==="user"&&block.kind==="field"&&
      Array.isArray(policy?.optional_context)&&
      policy.optional_context.includes(inferRoot(block.json_pointer)));
   wrap.appendChild(node("span","nilo-review-hint",
     optional?"Campo opcional del perfil; requiere revisión antes de aplicar.":
              "Campo o instrucción fuera de las omisiones del perfil; revisión obligatoria."));
   const note=node("textarea","nilo-review-note");
   note.rows=2;note.maxLength=MAX_NOTE;
   note.placeholder="Observación opcional: por qué te parece innecesario o problemático";
   note.setAttribute("aria-label","Observación sobre el bloque "+(block.title||"texto"));
   note.hidden=!selected.has(id);
   note.value=selected.get(id)?.note||"";
   input.checked=selected.has(id);
   input.addEventListener("change",()=>{
     set(id,input.checked);note.hidden=!input.checked;
     if(input.checked)note.value=selected.get(id)?.note||"";
   });
   note.addEventListener("input",()=>{if(selected.has(id))selected.get(id).note=note.value});
   if(!controls.has(id))controls.set(id,[]);
   controls.get(id).push(input);
   wrap.appendChild(note);container.appendChild(wrap);
   return wrap;
 }
 function addGroup(container,message,blocks){
   const ids=blocks.map(b=>key(message.path,b)).filter(id=>all.has(id));
   if(!ids.length)return null;
   const label=node("label","nilo-review-check nilo-review-group");
   const box=node("input");box.type="checkbox";
   label.append(box,node("span","","Proponer excluir todos los bloques de esta sección"));
   box.addEventListener("change",()=>{
     const checked=box.checked;
     ids.forEach(id=>set(id,checked));
     // Las notas se despliegan incluso cuando el grupo cambia su selección.
     for(const field of container.parentElement?.querySelectorAll(".nilo-review-item")||[]){
       const inp=field.querySelector("input"),note=field.querySelector("textarea");
       if(inp&&note)note.hidden=!inp.checked;
     }
   });
   container.prepend(label);
   groupControls.push({box,ids});refresh();
   return label;
 }
 function addHeader(container,{title="Revisión para exportar"}={}){
   const box=node("div","nilo-review-toolbar");
   box.append(node("strong","",title),
     node("p","nilo-review-hint","Marcá bloques como propuestas de exclusión. No cambia el prompt ni el motor. El archivo contiene la solicitud literal; revisalo antes de compartir."));
   const status=node("span","nilo-review-count");counts.push(status);
   const notes=node("textarea","nilo-review-overview");notes.rows=2;notes.maxLength=MAX_OVERVIEW;
   notes.placeholder="Observaciones generales (opcional)";
   notes.setAttribute("aria-label","Observaciones generales para la revisión exportada");
   notes.value=overview;notes.addEventListener("input",()=>{overview=notes.value});
   const row=node("div","nilo-review-actions");
   const button=node("button","nilo-review-export","Exportar revisión (.json)");
   button.type="button";
   const feedback=node("span","nilo-review-feedback");
   button.addEventListener("click",async()=>{
     if(busy)return;
     busy=true;button.disabled=true;feedback.textContent="Verificando integridad…";
     try{
       const report=await buildReview(source,selected,overview,policy||{});
       const prefix=source.kind==="captured_http"?"captura":"simulacion";
       const safeId=String(source.attempt_id||source.scenario||source.profile||"contexto")
         .replace(/[^a-zA-Z0-9_-]/g,"").slice(0,40)||"contexto";
       download("nilo_revision_"+prefix+"_"+safeId+".json",report);
       feedback.textContent="Archivo exportado localmente; no se aplicó ningún cambio.";
     }catch(e){feedback.textContent="Error de exportación: "+e.message}
     finally{busy=false;button.disabled=false}
   });
   row.append(button,status);
   box.append(notes,row,feedback);
   container.prepend(box);refresh();
   return box;
 }
 function resetControls(){controls.clear();groupControls.length=0;counts.length=0}
 function count(){return selected.size}
 return {addBlock,addGroup,addHeader,resetControls,count,selected,
         async build(){return buildReview(source,selected,overview,policy||{})}};
}
async function readPolicy(){
 const response=await fetch("/api/lab/audit/info",{cache:"no-store",credentials:"same-origin"});
 if(!response.ok)throw Error("No se pudo leer la versión del motor");
 return response.json();
}
global.NiloReview={SCHEMA,controller,buildReview,key,sha256,readPolicy};
if(typeof module!=="undefined"&&module.exports)module.exports=global.NiloReview;
})(typeof window!=="undefined"?window:globalThis);
