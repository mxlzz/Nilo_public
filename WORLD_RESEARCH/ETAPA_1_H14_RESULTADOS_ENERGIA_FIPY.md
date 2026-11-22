# Etapa 1 — H14. Energía térmica conservada con FiPy

**2026-11-22. Dictamen: H14 APROBADA en laboratorio de conducción 1D cerrada; etapa 1 general ABIERTA.** Ninguna ley térmica codificada en el proyecto; se ejecutó NIST FiPy4.0.3, proveedor de diferencias de volumen finito. No es un motor físico universal ni prueba de evolución del mundo, cambios de fase o energía mecánica.
**Protocolo previo:** [ETAPA_1_H14_PROTOCOLO_ENERGIA_FIPY.md](ETAPA_1_H14_PROTOCOLO_ENERGIA_FIPY.md).
**Código aislado:** [experiments/probe_e1_h14_heat_fipy.py](experiments/probe_e1_h14_heat_fipy.py).
**CI verificada:** https://github.com/mxlzz/Nilo_public/actions/runs/45056513417 — **SUCCESS**, commit workflow `5fa92af3b779ca45d009718b9b7c98e3a3c56e6b`.
**Entorno:** Python3.11.18; FiPy4.0.3, NumPy2.4.6, xarray2026.9.0, GitHub Actions Ubuntu24.04.

## Fenómeno y presupuesto observado

8 celdas consecutivas de 1m³ con 2kg material A cada una, cp=500J/(kg K), conductividad térmica20W/(m K), límites **sin flujo**. Las primeras cuatro celdas a330K y las otras cuatro a270K. FiPy ejecutó 100 pasos de `dt=0.1s` usando `TransientTerm(coeff=1000) == DiffusionTerm(coeff=20)`.

- **Materia**: exactamente16kg antes/después.
- **Energía térmica**: original2.400.000J; final2.399.999,9999999953J. Residuo **−4,656612873077393×10⁻⁹J**. Máximo de desvío absoluto en todos los 100 pasos igual al final: ~4,66×10⁻⁹J; gate fijado antes de correr era0,01J.
- **Transferencia en interfaz**: celda caliente #3 pasó330→**320,94071K**, la fría #4 pasó270→**279,05929K**. El contraste máximo del dominio pasó60→**59,99386K**; las celdas externas apenas cambiaron por el tiempo corto.
- **Sin conductividad (k=0)**: todas las energías individuales exactamente iniciales y flujo0.
- **Sin gradiente térmico (todas300K)**: energías individuales exactamente iniciales y flujo0.
- **Replay** de escenario activo exacto a nivel de arrays; cinco corrupciones rechazadas antes del commit: energía ficticia +1J, energía negativa, masa negativa, unidad J→kJ y cp adulterado.
- **Propiedad:** un `xarray.Dataset` contiene `material_mass_kg(cell)` e `internal_thermal_energy_J(cell)`; FiPy recibe una vista transitoria T(K) derivada del owner, produce un candidato validado y solo entonces se publica el siguiente estado material. No se almacena un campo T como segundo stock. NetCDF768bytes reconstruyó exactamente owner, T derivada y SHA `b2b1d017f669b9f733ef04dcad69152af941229e52012ff65d8fa5ce9aea12ce`.

## Significado científico y límites

**Sí demuestra:** intercambio térmico espontáneo por gradiente con conservación de cantidad de calor en un sistema cerrado, diferenciación por conductividad e integridad del inventario único en cada paso. Se reutilizó el solver establecido FiPy; las propiedades experimentales fueron ficticias y no calibradas.

**No demuestra:** heterogeneidad composicional, intercambio térmico tridimensional, conducción acoplada a deformación, fricción→calor, transporte advectivo por sedimentos, cambio de fase, reacciones, calor latente, contacto térmico entre regiones con ROI H5, meteorología ni validación natural. Aunque el presupuesto total de energía térmica cierra, **no se contabiliza energía mecánica**, que aún falta en el esquema general.

## Gate y dirección

H14 prueba una capacidad central pendiente de la etapa 1 sin desarrollar leyes físicas. **Etapa1 NO cerrada** hasta precisar qué transformaciones materiales, dominios de energía y estados mínimos deben representarse, compatibilidad de propietarios y conservación global cuando se combinan fenómenos. Se recomienda una revisión de criterios de salida antes de nuevas integraciones: demostrar algo nuevo sin inflar complejidad, no continuar indefinidamente con pruebas aisladas ni volver al bucle de dependencias de GeoTaichi. Conservar H13A como bloqueada en imports y H12 como fracaso frente a gate físico. No se modificaron `main` ni NeuroLab.
