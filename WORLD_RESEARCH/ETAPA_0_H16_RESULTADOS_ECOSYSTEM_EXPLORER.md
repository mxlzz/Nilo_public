# Etapa 0 — H16 Ecosystem Explorer: resultado navegador caja negra

**Fecha:** 2026-11-21. **Estado:** H16A APROBADA para accesibilidad de funciones y avance temporal; H16B no ejecutada; la física sigue sin validar.
**Plan previo:** `ETAPA_0_H16_PROTOCOLO_ECOSYSTEM_EXPLORER.md`.
**Fuente pública:** https://www.ethanjhulbert.org/ecosystem-explorer/ y https://www.ethanjhulbert.org/ecosystem-explorer/about/
**Prueba propia:** `experiments/probe_ecosystem_explorer_browser.py`; CI https://github.com/mxlzz/Nilo_public/actions/runs/44958493004 (**SUCCESS**).

## Procedimiento experimental realmente ejecutado
- Una sesión pública con Chromium/Playwright, HTTP200; 6 elementos canvas detectados. Sin descargar, guardar ni reproducir código, JS, imágenes o assets ajenos. Acciones por controles accesibles de UI, no API interna.
- Arranque leído en **Year 1 / Spring**, velocidad 28× pulsada; tras 15s, **Year 3 / Autumn**, año adelantó; prueba de autonomía funcional mientras navegador abierto.
- Se pulsó botón visible accesible «Inspect a tile» y se confirmó activación del modo. Esto **no** implica que se eligiera una celda o se midieran sus propiedades.
- Se abrió «Create a new world» mediante su botón público y quedaron visibles controles **Seed**, **Save in browser**, **Export file**. No se guardó, exportó ni reimportó realmente un mundo; presencia de botones no equivale a comprobar persistencia.

## Fallos conservados
1. https://github.com/mxlzz/Nilo_public/actions/runs/44957981477 : reloj 1→3 y velocidad operaron, pero la sonda buscaba Seed/Export en paneles plegados y concluyó falsamente que no existían.
2. https://github.com/mxlzz/Nilo_public/actions/runs/44958150544 : confundió `✳` (intervenciones) con `⊙` (nuevo mundo). Se corrigió usando `aria-label` semántico de botones visibles, sin inspeccionar la app interna.
3. https://github.com/mxlzz/Nilo_public/actions/runs/44958303795 : se abrió correctamente nuevo mundo y apareció Seed/Export, pero se intentó hacer clic en modo Inspeccionar detrás de un modal sin cerrar. Se reordenó la secuencia: primero activar inspector, luego abrir nuevo mundo, sin modificar criterios.
4. https://github.com/mxlzz/Nilo_public/actions/runs/44958493004 : **PASS** controles+reloj 28×. Se registraron nombres accesibles y fallos históricos como parte del arnés.

## Relevancia y límites
Ecosystem Explorer combina en su documentación generación por semilla, geoformas, agua, erosión, sedimentos, humedad, vegetación, incendios, nieve, volcanes y evolución visible. El autor expresa explícitamente que son reglas simplificadas y **no física calibrada**. H16A verifica **la interfaz y el avance de calendario** por uso público; **NO** ha cuantificado erosión, balances, transición de biomas, causalidad de agua ni reproducibilidad de semillas. Tampoco acredita evolución offline mientras el navegador está cerrado.

**No se identificó licencia pública de código reutilizable.** Los términos del sitio reservan copyright salvo licencias específicas; no copiar fuente ni inferir API utilizable. Esto no disminuye su valor como benchmark funcional del producto.

## Dictamen
H16A ACEPTADA como referencia funcional de un mundo generativo con tiempo visible, creación, observación y guardado accesibles. Ecosystem Explorer **no** puede elegirse como módulo open source sin autorización/contrato de código. H16B futuro, si conviene: intervención puntual + export/reimport + lectura de una celda con mismo estado; no asumir éxito ni iniciar copiando JS.

La etapa 0 puede usar H16 para **comparar visión y affordances** con Landlab, Sandspiel, Powder Toy, WorldEngine y motores de emergencia, sin mezclar NeuroLab.
