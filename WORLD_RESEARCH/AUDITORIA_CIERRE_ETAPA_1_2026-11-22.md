# Auditoría formal de gate — Etapa 1 («materia compartida, sin paisaje»)

**Fecha:** 2026-11-22. **Dictamen:** **CERRAR PROVISIONALMENTE solo el gate de laboratorio mínimo de etapa1**, con alcance y limitaciones expresos. Autoriza investigar etapa2 **sin** declarar validado un motor de mundo 3D ni acoplamientos físicos completos.

**Fuentes rectoras:** [hoja de ruta](BASES_Y_HOJA_DE_RUTA.md) §6 y [procedimiento](PROCEDIMIENTO_Y_AUDITORIA.md), no reformulados para que los ensayos pasen. [Estado previo y brechas](AUDITORIA_GATE_ETAPA_1_POST_H14_2026-11-22.md). Evidencia decisiva [H15](ETAPA_1_H15_RESULTADOS_FASE_ENTALPIA.md) y [H16](ETAPA_1_H16_RESULTADOS_DOS_MATERIALES.md), además de H1/H3/H5/H6.

## A. Hipótesis y esquema de datos

**Requisito literal E1:** «un esquema pequeño representa materiales distintos sin definir objetos finales», con espacio cerrado, cantidad/masa/volumen/energía y transformaciones trazables.

**Evidencia:** H1 representó A/B y estado volumétrico; H5/H6 demostraron propiedad material y exclusividad de superficie/ROI, cavidades y cambios reversibles de representación. [H16 CI SUCCESS](https://github.com/mxlzz/Nilo_public/actions/runs/45059387895) demostró, **en un único `xarray.Dataset` 1D**, matrices `material_mass_kg(material,cell)` e `internal_energy_J(material,cell)`; masa16kg, volumen ocupado8m³, dos tipos A/B de diferente respuesta térmica y fase A derivada sin un tercer inventario. Las celdas no codifican «roca», «casa», «río» ni forma final. **Resultado: requisito mínimo CUMPLIDO en laboratorio**, no esquema volumétrico universal.

## B. Cuatro pruebas de aceptación expresas

1. **Conservación:** H16 mantuvo A8kg/B8kg y 16kg totales, y la energía térmica total3.896.000J con máximo error absoluto de4,5635×10⁻⁸J en sistema cerrado (tolerancia preregistrada0,02J). H9 corroboró independientemente salida sedimentaria explícita; H15 corroboró masa+energía/latente con una sola clase. **CUMPLIDA** para mecanismos ensayados, NO para acoplamiento global mecánico/termoquímico.
2. **Estados imposibles:** H16 rechazó nueve corrupciones: masa negativa, sobrecapacidad, doble material en celda llena, fuentes energéticas no declaradas, unidades, identidad, propiedades y variable redundante. H5 rechazó doble propietario ROI/campo exterior y un vacío de cueva oculto no reconstructible desde altura. **CUMPLIDA** en dominios/controladores de laboratorio. No existe verificador general de geometrías arbitrarias.
3. **Mismas condiciones→mismo estado:** H1/H5/H6 tenían hash/roundtrip; H15 y H16 tuvieron replay exacto bit a bit en misma CPU y checkpoint NetCDF que preserva todos los inventarios, unidades, parámetros y campos derivados. No hay RNG en H16. **CUMPLIDA en alcance local**, sin afirmación determinista de solvers múltiples/otros sistemas.
4. **Cambio de composición causa efecto solo cuando ley lo justifica:** H16 comparó AB (A:cp500+latente, B:cp1000) con BB manteniendo masa total16kg, campo inicial T y conductividad. En celda3, enfriamiento AB3,374935K frente BB5,293564K, diferencia1,918629K >0,25K preregistrado; sin conducción o sin gradiente, ninguna variación. Es consecuencia del coeficiente volumétrico de `TransientTerm`, no una plantilla de cambio de forma. **CUMPLIDA**.
   
## C. Condiciones de cierre y de reapertura

**Aprobación estrictamente relativa a etapa1:** pequeño territorio discreto 1D/contratos de ROI, dos materiales separados por celda, estado térmico, masa/volumen y transformación idealizada dentro de rango. No confundir con motor, biome, planeta ni emergencia. El mecanismo de latente de H15/H16 solo se comprobó **dentro** de franja lineal290–310K, con materiales ficticios y constantes: no demuestra frentes de fase, cristalización ni transporte de líquidos.

**No requisitos para E1, sí para siguientes etapas:** flujo de materia por gradiente, movimiento bajo gravedad con estado persistente, mezcla de especies en mismo voxel, interacción sedimentación/energía, estabilidad de estructuras (H12 falló), uso CPU de GeoTaichi (H13A bloqueado), física 3D y reanudación real con memoria cinemática. No retrasar E1 exigiendo etapas3–8 retrospectivamente; **tampoco usar cierre E1 para declarar cubiertos estos pendientes**.

**Disparadores de reapertura:** al integrar etapa2, una incompatibilidad sustantiva de owner o unidades invalida los tests E1; un solver necesita fuentes/sumideros imposibles de conciliar; simultaneidad de fases requiere estado adicional no derivable; doble ocupación o restauración no controladas. Reabrir E1 y registrar evidencia, no parchear con inventarios paralelos.

## D. Decisión y próximo trabajo permitido

**Etapa0:** cerrada provisionalmente en gate reutilización, ADR-0003.
**Etapa1:** **CERRADA PROVISIONALMENTE en gate mínimo** con el resultado H16 y esta auditoría.
**Etapa2:** **ABIERTA, todavía no satisfecha**, solo autorizar nueva prueba local mediante protocolo previo. Priorizar **movimiento de materia gobernado por gravedad en espacios libres/bloqueados**, que deposite un cuerpo existente y publique posiciones/velocidades de su owner. Los ensayos Bullet H7/H8/H10 mostraron física de contacto pero no demostraron publicación de **estado cinemático** en el inventario. Debe justificarse ese hueco frente a la repetición de H7.
**Etapas3–8:** sin gate formal.

**Registro relacionado de decisión:** [ADR-0009](DECISIONES/ADR-0009_GATE_ETAPA_1_MINIMO.md) (a crear inmediatamente tras esta auditoría). No se cambia rama main ni NeuroLab; criterios del plan original siguen intactos.
