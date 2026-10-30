# Plan de implementación

| Fase | Prioridad | Esfuerzo | Riesgo principal | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| 1. Base y acceso | Alta | Hecha | Protección local | Registro, acceso y recuperación seguros y probados |
| 2. Gestión principal | Alta | Medio | Integridad y UX | CRUD de clientes, salones, horarios y emisor, con restricciones |
| 3. Borradores | Alta | Alto | Cálculos y trazabilidad | Líneas con `Decimal`, snapshots y PDF de prueba |
| 4. Adaptación fiscal futura | Fuera de alcance | Alto | Interpretación y cambios normativos | La distribución actual solo compone borradores; un mantenedor deberá revisar y validar su adaptación antes de emitir facturas reales |
| 5. Operación | Media | Medio | Pérdida de datos | Backup/restauración, migraciones, registros y distribución Windows |

La fase 2 incorporará `LegalEntity → Salon`, datos de emisor separados de perfil y clientes por cuenta. La fase 3 asignará números solo al emitir, dentro de transacción. La fase 4 no se trata como una característica visual: bloqueará cualquier salida de producción mientras no esté demostrada.
