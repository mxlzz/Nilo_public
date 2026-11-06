/* Nilo · Tema compartido del laboratorio.
   Almacena solo preferencia visual; no toca mundos, configuraciones del motor
   ni solicitudes LLM. Opera sin red ni bibliotecas de terceros. */
(() => {
  "use strict";
  const KEY = "nilo.lab.theme.v1";
  const CHOICES = ["system", "light", "dark"];
  const LABELS = {system:"Tema: sistema",light:"Tema: claro",dark:"Tema: oscuro"};
  function storageRead() {
    try { return window.localStorage.getItem(KEY); } catch (_) { return null; }
  }
  function storageWrite(value) {
    try { window.localStorage.setItem(KEY,value); } catch (_) { /* sin persistencia */ }
  }
  function normalize(value) {
    return CHOICES.includes(value) ? value : "system";
  }
  function apply(value) {
    const mode = normalize(value);
    if (mode === "system") document.documentElement.removeAttribute("data-lab-theme");
    else document.documentElement.setAttribute("data-lab-theme",mode);
    const button = document.getElementById("lab-theme-toggle");
    if (button) {
      button.textContent = LABELS[mode];
      button.setAttribute("aria-label","Cambiar tema de color. Actual: "+mode);
      button.setAttribute("title","Alternar tema: sistema, claro u oscuro");
    }
    return mode;
  }
  let selected = apply(storageRead());
  function ready() {
    const button = document.getElementById("lab-theme-toggle");
    if (!button) return;
    apply(selected);
    button.addEventListener("click", () => {
      selected = apply(CHOICES[(CHOICES.indexOf(selected)+1)%CHOICES.length]);
      storageWrite(selected);
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded",ready,{once:true});
  } else ready();
})();