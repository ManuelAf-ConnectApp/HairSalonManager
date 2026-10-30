# PROMPT MAESTRO — HAIR SALON MANAGEMENT

> **Destinatario:** Claude / OpenAI Codex, actuando como Principal Software Engineer, arquitecto Python y especialista en aplicaciones de escritorio PySide6.
>
> **Finalidad:** analizar, diseñar e implementar una aplicación de escritorio profesional para la gestión de una o varias peluquerías, con persistencia local, seguridad, arquitectura limpia y facturación extensible.
>
> **Idioma de interfaz y documentación funcional:** español (España). Los identificadores internos del código podrán utilizar inglés coherente. No se debe afirmar cumplimiento legal sin verificarlo y probarlo.

## 0. Rol, misión y reglas de trabajo

Actúa como un **Ingeniero Principal de Software y Arquitecto de Aplicaciones Desktop** con experiencia demostrable en Python, PySide6/Qt, SQLAlchemy, bases de datos relacionales, Clean Architecture, DDD pragmático, SOLID, testing automatizado, UX y aplicaciones de facturación para pequeñas empresas.

Construye **Hair Salon Management**, aplicación de escritorio destinada a un responsable que administra una o varias peluquerías. La implementación debe ser funcional, mantenible y preparada para crecimiento gradual, sin introducir capas o servicios distribuidos innecesarios.

**Reglas imperativas:**

1. Antes de modificar código, inspecciona el repositorio existente, sus dependencias, esquemas, pruebas y convenciones. No asumas que empieza de cero.
2. Documenta claramente **implementado / pendiente / propuesto**. No presentes un boceto o un mock como funcionalidad completa.
3. Si falta una decisión, adopta la opción más sencilla y segura, explica el supuesto y registra la decisión en `docs/decisions/`.
4. Evita cambios destructivos y conserva datos mediante migraciones. No incorpores credenciales o datos de clientes reales al repositorio.
5. Entrega incrementos ejecutables con pruebas; no generes únicamente pseudocódigo, pantallas estáticas o un plan sin código cuando el entorno permita desarrollar.
6. Distingue **operadores del sistema**, **clientes** y **entidades fiscales emisoras**: no son el mismo concepto.
7. Da prioridad a la integridad de datos, la seguridad de los usuarios y la trazabilidad de la facturación sobre el aspecto visual.
8. Usa licencias compatibles para dependencias y recursos (comprobar las condiciones de PySide6/Qt y el modo de distribución elegido).

## 1. Alcance del producto

- **Nombre:** Hair Salon Management.
- **Plataforma:** aplicación nativa de escritorio; objetivo principal Windows, con diseño portable a macOS y Linux.
- **Interfaz:** PySide6 (Qt Widgets), responsiva al redimensionado de ventanas y compatible con HiDPI.
- **Lenguaje:** Python moderno compatible con la versión estable seleccionada y dependencias verificadas.
- **Persistencia:** base de datos relacional local. **Preferir SQLite** para instalación monousuario offline, con claves foráneas, transacciones, WAL cuando proceda, backups y migraciones. Mantener la capa de persistencia desacoplada para permitir un adaptador MySQL/MariaDB cuando exista necesidad real de acceso concurrente multiusuario. No instalar un servidor MySQL local como requisito del MVP sin justificarlo.
- **Arquitectura:** Clean Architecture + separación por responsabilidades, SOLID, tipado y Clean Code.
- **Moneda MVP:** EUR. **Ámbito fiscal inicial:** España, con parametrización de impuestos y textos.
- **Múltiples peluquerías:** una misma cuenta de gestión podrá administrar establecimientos distintos; permitir seleccionar establecimiento activo.
- **Fuera del MVP salvo aprobación:** reservas online, TPV completo, inventario de productos, nóminas, sincronización cloud, agenda de citas, fidelización, marketing, integración bancaria y multiusuario en red.

## 2. Diseño de arquitectura

Aplicar dependencia unidireccional: **presentación → casos de uso → dominio**, con infraestructura implementando los puertos del dominio/aplicación.

### 2.1 Capas

- **Domain:** entidades y value objects (`Email`, `TaxIdentifier`, `Money`, `BusinessHours`, `InvoiceNumber`), políticas de negocio, invariantes y errores de dominio. Sin imports de Qt ni SQLAlchemy.
- **Application:** casos de uso (`RegisterOperator`, `Authenticate`, `CreateCustomer`, `UpdateSalon`, `IssueInvoice`, etc.), DTO, interfaces/repositorios, control de transacciones.
- **Infrastructure:** SQLite / SQLAlchemy, Alembic u otra migración definida, adaptadores de hash de contraseñas, PDF, almacenamiento, auditoría, clock, ID generation y backups.
- **Presentation:** widgets PySide6, modelos de tabla `QAbstractTableModel`, validadores, controladores/presenters y navegación. No realizar consultas SQL desde widgets.
- **Composition root:** construcción de dependencias al iniciar la aplicación; sin singletons globales para acceso a base de datos.

### 2.2 Convenciones

- Tipado explícito (`typing`, dataclasses donde tenga sentido), `Decimal` para todos los importes monetarios, formato y redondeo definidos; **no utilizar `float` para dinero**.
- Manejo de errores tipados, logging estructurado sin datos confidenciales, transacciones atómicas y mensajes localizados.
- Emplear señales/slots de Qt y workers para tareas que puedan bloquear la interfaz (exportaciones, backups, importaciones, consultas lentas). Respetar la afinidad de hilo de Qt y no compartir sesiones SQLAlchemy entre hilos.
- No multiplicar abstracciones sin beneficios claros; justificar patrones y librerías.

## 3. Experiencia de usuario y navegación

Proponer una aplicación moderna y profesional, intuitiva para personal sin conocimientos técnicos. Usar barra lateral o navegación superior persistente tras autenticación, con acceso a **Inicio, Clientes, Peluquerías, Facturas, Perfil, Ajustes** y **Cerrar sesión**. Mostrar nombre y peluquería activa. Añadir estados vacíos, confirmaciones contextuales, filtros, feedback tras guardar y accesibilidad con teclado.

**Autenticación:** pantalla de **Iniciar sesión** como contenedor padre de la navegación a **Registro** y **Recuperar contraseña**, mediante rutas/páginas Qt sin abrir ventanas modales innecesarias. Al autenticar, abrir la shell principal y cerrar la vista de acceso. No permitir entrar a vistas protegidas sin sesión.

**Dashboard (Inicio):** bienvenida, establecimiento activo, accesos rápidos (`Nuevo cliente`, `Nueva factura`, `Nueva peluquería`), indicadores útiles (clientes registrados, facturas emitidas, facturas pendientes de cobro) y actividad reciente si ya existe información. Evitar gráficos de relleno.

**Diseño:** paleta sobria y corporativa, tipografía legible, componentes reutilizables, jerarquía visual, tooltips, contraste adecuado, foco visible, tablas con ordenación y buscador, diseño compatible con pantallas habituales de escritorio. Preparar para internacionalización mediante Qt translation.

## 4. Módulo de registro, sesión y recuperación

### 4.1 Iniciar sesión

- Campos: **email** y **contraseña**; validación de formato, obligatoriedad y mensajes seguros.
- Verificar hash almacenado mediante biblioteca reconocida (Argon2id preferido, o alternativa justificada); nunca guardar contraseñas en texto claro.
- Implementar cierre de sesión y expiración/bloqueo razonable de la sesión local; evitar enumeración de cuentas mediante respuestas detalladas.
- Medidas de mitigación de fuerza bruta: retardo progresivo o límites prudentes, sin impedir indefinidamente el uso legítimo.

### 4.2 Registro del responsable/operador

Campos indicados por el solicitante: **email, nombre, apellidos, CIF/NIF, dirección, código postal y país**. **Añadir de forma obligatoria contraseña y confirmación de contraseña**, ya que no se puede crear una cuenta utilizable sin credencial. Incluir teléfono como opcional y validar unicidad normalizada del email.

Los datos fiscales introducidos en el registro **no deben mezclarse de manera irreversible** con el perfil personal: crear un **emisor fiscal** asociado al responsable, editable después en Perfil, y utilizar sus datos en facturas. Si la peluquería tiene una razón social distinta, asignar el emisor correspondiente a cada establecimiento.

### 4.3 Recuperar contraseña (offline)

No permitir restablecer la contraseña **solo por conocer el email**. Exigir un **código de recuperación previamente generado y entregado al usuario durante el registro/activación**, guardando únicamente su hash (o verificador apropiado). Especificar longitud y entropía suficiente, un solo uso si procede, revocación y renovación controlada; ofrecer confirmación de nueva contraseña. En ausencia de código, definir un procedimiento de soporte/recuperación administrativa local que no permita tomar una cuenta sin prueba de posesión. Si se diseña integración de correo en el futuro, marcarla como opcional con conectividad y requisitos adicionales.

## 5. Clientes (etiqueta visual «Clientes», no «Usuarios»)

Pantalla dividida en **dos paneles** adaptables (formularios y tabla). Si la ventana es estrecha, usar pestañas o layout apilado.

### 5.1 Alta/edición

Campos:
- Nombre (obligatorio)
- Apellidos (obligatorio)
- Dirección (opcional en ficha general; puede ser necesaria para determinada factura)
- Email (opcional, validado si existe)
- Teléfono (**obligatorio**)

Añadir ID interno inmutable, fechas creación/actualización y campo opcional de notas **sin introducir datos sensibles de salud por defecto**. Normalizar datos de contacto sin perder información relevante (prefijo internacional telefónico); definir deduplicación no agresiva: evitar bloquear clientes distintos que comparten teléfono.

### 5.2 Tabla y acciones

- Mostrar nombre completo, teléfono, email y acciones **Editar / Archivar o Eliminar**.
- Buscar por nombre, apellidos, teléfono y email; ordenar y paginar/virtualizar según volumen.
- Antes de borrar, mostrar confirmación y el impacto. **No eliminar físicamente clientes referenciados por facturas emitidas**; preferir archivado o anonimización únicamente cuando sea legalmente posible.
- Mostrar validación inmediata y mensajes de éxito/error. Pruebas CRUD y de integridad referencial.

## 6. Peluquerías / establecimientos

Pantalla en dos mitades: formulario de alta/edición y tabla de peluquerías con filtros y acciones. Una cuenta puede tener una o más peluquerías.

### 6.1 Datos

- Nombre comercial (obligatorio)
- Dirección completa, código postal, localidad, provincia, país
- **Emisor fiscal asociado / CIF-NIF**: usar un selector entre entidades fiscales registradas; no suponer que cada peluquería dispone de un CIF distinto.
- Teléfono y email (validados)
- Estado activa/inactiva
- **Horario por día de lunes a domingo**; día cerrado, tramo de mañana y tarde, o jornada ininterrumpida. Admitir horarios distintos cada día, intervalos sin solapamientos y cruces de medianoche solamente si se especifica una política compatible.

### 6.2 Operaciones

- Crear, consultar, editar y desactivar/archivar.
- Tabla con nombre, dirección resumida, estado, teléfono y horario general.
- Evitar eliminar una peluquería con facturas vinculadas.
- Permitir establecer una peluquería activa y conservar esa selección durante la sesión.
- Preparar vínculo `Salon → LegalEntity` con posibilidad de varios salones compartiendo entidad fiscal.

## 7. Facturación y generación PDF

### 7.1 Flujo funcional

1. Seleccionar peluquería o usar la activa.
2. Cargar automáticamente el emisor fiscal asociado al establecimiento (selector solo si hay emisores fiscalmente válidos para la cuenta).
3. Buscar cliente con autocompletado por nombre, teléfono o email; persistir ID del cliente.
4. Incluir al menos **una línea de servicio**: descripción, cantidad, precio unitario sin IVA, descuento aplicable y tipo impositivo. Se permite una línea por defecto «Servicio de peluquería», pero modelar múltiples líneas.
5. Mostrar base imponible, descuentos, tipo(s) de IVA, cuota(s), total, fecha de emisión y fecha de operación si difiere.
6. Crear **borrador**, revisar y **emitir** con numeración transaccional correlativa por serie. Ofrecer **Exportar a PDF** y **Guardar copia** del documento emitido.
7. Registrar estado de cobro (pendiente, parcial, cobrado), fecha y método opcional. Separar **estado fiscal de la factura** y **estado de pago**.
8. Consultar facturas emitidas por fecha, número, establecimiento, cliente y estado; visualización del PDF y reexportación controlada.

### 7.2 Reglas monetarias

- El **21 % de IVA** será el valor **inicial configurable** en el supuesto estándar español, no una constante inmutable ni aplicable automáticamente a todos los supuestos.
- Descuentos en porcentaje, aplicados sobre la base antes del cálculo del impuesto, con reglas de redondeo y precisión explícitas; mostrar subtotal y desglose.
- Usar `Decimal` y reglas documentadas para cantidades, descuentos, cuotas e importes totales; impedir importes no válidos y errores de redondeo.
- Diseñar el PDF con datos completos del emisor y destinatario cuando corresponda, serie/número, fechas, descripción, bases, tipos, cuotas y total.
- Reproducir de manera fiel las cifras guardadas; nunca recalcular con reglas actuales una factura emitida históricamente.

### 7.3 Integridad fiscal y cumplimiento

**Requisito crítico:** una aplicación que expide facturas en España debe diseñarse con la normativa vigente, no solo con la capacidad de imprimir PDFs. El código de un MVP **no puede anunciarse como conforme a VERI*FACTU / reglamento SIF** por el mero hecho de generar numeración o PDF.

- Numeración **correlativa por serie**, con asignación atómica al emitir y controles de concurrencia; permitir series por establecimiento y otros supuestos legales.
- Una factura **emitida no debe borrarse ni editarse silenciosamente**. Definir anulación/rectificación conforme a las reglas vigentes, con registro auditable y relaciones a documentos originales.
- Establecer registros de auditoría, conservación, exportación de datos y controles anti-manipulación. Separar la lógica fiscal en un módulo sustituible.
- Investigar y documentar qué exigencias del **Reglamento de Sistemas Informáticos de Facturación (SIF)**, **VERI*FACTU/no VERI*FACTU**, registros de facturación, encadenamiento/huellas, QR, firma cuando proceda, remisión y trazabilidad **aplican al caso concreto**, con fechas verificadas en la AEAT antes de comercializar o usar para facturación real.
- La aplicación debe incluir una **advertencia explícita de alcance legal** si todavía no implementa completamente los requisitos aplicables: no emitir facturas reales como solución legalmente conforme hasta que haya validación.
- Estudiar diferenciación de **facturas completas y simplificadas** cuando corresponda, sin asumir que toda operación requiere el mismo conjunto de datos.

**Referencias oficiales a consultar y citar en la documentación técnica:**
- [AEAT — Contenido de las facturas](https://www3.agenciatributaria.gob.es/Sede/iva/facturacion-registro/facturacion-iva/contenido-facturas.html)
- [AEAT — Sistemas Informáticos de Facturación y VERI*FACTU](https://www3.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html)
- [BOE — Reglamento de facturación, RD 1619/2012](https://www.boe.es/buscar/act.php?id=BOE-A-2012-14696)

## 8. Perfil del gestor y datos fiscales

Pantalla con las secciones:

- **Datos personales:** nombre, apellidos, email y cambio de contraseña con validación de credenciales actuales.
- **Datos fiscales:** NIF/CIF, razón social o nombre completo del titular, nombre comercial si procede, dirección fiscal completa, código postal, localidad, provincia y país, email y teléfono.
- **Entidades fiscales vinculadas:** opción de crear/editar diferentes emisores cuando una cuenta administre peluquerías de titulares distintos, evitando asumir que el perfil del gestor es siempre el emisor.
- **Preferencias:** establecimiento por defecto y configuración fiscal inicial (solo usuarios autorizados).

Conservar en cada factura emitida una **instantánea inmutable** de datos del emisor, cliente y conceptos para que los cambios posteriores de perfil no reescriban documentos históricos.

## 9. Ajustes y operación

Incluir en el MVP o en una fase inmediatamente posterior:

- Idioma, tema visual, ruta de exportación de PDFs, formato de fechas, establecimiento predeterminado.
- Copias de seguridad locales versionadas y restauración guiada; indicar si es necesario cerrar conexiones o usar API de backup consistente.
- Selección de ubicación de base de datos en carpeta de datos del sistema operativo con permisos apropiados; nunca usar el directorio del ejecutable para datos modificables.
- Registros de incidencias sin contraseñas, tokens ni datos personales completos.
- Exportación de clientes y facturas con controles de autorización/privacidad.
- Política de actualización y migraciones de esquema; no instalar actualizaciones ni transmitir datos sin informar al usuario.

## 10. Modelo de datos y relaciones mínimas

Define un esquema relacional con migraciones y restricciones reales. Entidades iniciales:

| Entidad | Responsabilidad / relaciones |
|---|---|
| `OperatorAccount` | Autenticación local del gestor, hash de contraseña, estado |
| `OperatorProfile` | Datos personales del operador, 1:1 con cuenta |
| `RecoveryCredential` | Verificador de código y control de revocación/uso |
| `LegalEntity` | Emisor fiscal, identificado por NIF/CIF cuando aplique |
| `Salon` | Establecimiento, relación con `LegalEntity` y gestor |
| `OpeningInterval` | Día de la semana, inicio/fin, múltiples tramos por día |
| `Customer` | Cliente registrado, activo/archivado |
| `Invoice` | Cabecera, numeración/serie, fechas, snapshots, estado fiscal y de cobro |
| `InvoiceLine` | Cantidad, precio, descuento, impuesto, totales por línea |
| `InvoiceSeries` | Serie, último número y reglas de asignación por emisor/ejercicio |
| `Payment` | Cobros parciales o completos relacionados con factura |
| `AuditEvent` | Registro de eventos sensibles sin filtrar secretos |

Añadir claves foráneas, unicidad, índices de búsqueda y restricciones CHECK. Establecer si la titularidad de clientes es global a la cuenta o por establecimiento; preferir alcance por cuenta y asociación opcional a peluquerías, documentando la decisión. Introducir soft-delete solo donde aporte valor y no contradiga integridad fiscal ni RGPD.

Incluir diagrama entidad-relación en Mermaid y un inventario de índices, restricciones y migraciones.

## 11. Seguridad, privacidad y robustez

- Hash de contraseñas con salt y parámetros documentados; no usar SHA-256 simple ni «cifrado reversible» para passwords.
- Consultas parametrizadas/ORM, validación de entradas y sanitización de rutas/nombres de PDF.
- Almacenamiento local protegido mediante permisos, copias de seguridad seguras y, si se incluyen datos especialmente sensibles o hay riesgo material, estudiar cifrado en reposo y custodia de claves.
- Gestión de roles: MVP con rol de gestor; diseñar interfaces listas para introducir empleado/administrador en el futuro, pero sin sobreconstrucción.
- Privacidad conforme al RGPD: minimización, deber de información, plazos de conservación, acceso/exportación de información y supresión cuando proceda; conservar datos fiscales en los plazos obligatorios.
- Recuperación frente a fallos en mitad de transacciones; pruebas ante apagados inesperados y escrituras concurrentes si se permiten varias instancias.
- Mensajes de error orientados al usuario, telemetría desactivada por defecto, ningún envío automático de datos a terceros.

## 12. Estructura de carpetas sugerida

```text
hair-salon-management/
├── README.md
├── README.es.md
├── CHANGELOG.md
├── LICENSE
├── NOTICE
├── pyproject.toml
├── .gitignore
├── .env.example                  # solo si existen variables necesarias; sin secretos
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   ├── invoicing-compliance.md
│   ├── user-guide.es.md
│   └── decisions/
├── src/hair_salon_management/
│   ├── __main__.py
│   ├── domain/
│   │   ├── entities/
│   │   ├── value_objects/
│   │   └── services/
│   ├── application/
│   │   ├── use_cases/
│   │   ├── dto/
│   │   └── ports/
│   ├── infrastructure/
│   │   ├── persistence/
│   │   ├── security/
│   │   ├── pdf/
│   │   └── backups/
│   ├── presentation/
│   │   ├── windows/
│   │   ├── pages/
│   │   ├── widgets/
│   │   ├── models/
│   │   └── resources/
│   └── bootstrap.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── ui/
└── packaging/
```

El árbol es orientativo; adapta módulos y nombres al repositorio real. No introduzcas rutas vacías que no tengan responsabilidad clara.

## 13. Dependencias y distribución

- Preferir: PySide6, SQLAlchemy 2.x, Alembic, Argon2-cffi, pytest, Ruff y mypy/pyright según compatibilidad; seleccionar una herramienta de generación PDF confiable (p. ej. ReportLab) tras comprobar licencias y necesidades de maquetación.
- Fijar dependencias reproducibles, señalar licencias y evitar paquetes abandonados o con vulnerabilidades conocidas.
- Proporcionar `pyproject.toml`, configuración de lint/format, scripts de desarrollo y comandos claros para crear entorno virtual, migrar y ejecutar.
- Preparar empaquetado para Windows (PyInstaller o alternativa justificada) y explicar requisitos para macOS/Linux, recursos Qt, plugins y ubicación de datos.
- Ejecutar tests en CI para al menos una plataforma principal, añadiendo otras cuando esté disponible. No afirmar compatibilidad no probada.

## 14. Pruebas y criterios de aceptación

Implementar pruebas unitarias, de integración y UI cuando sean razonables. Como mínimo:

1. Registro con contraseña confirmada; rechazo de email duplicado y de contraseñas débiles.
2. Login correcto/incorrecto; no exposición de secretos; logout.
3. Recuperación offline con código válido, inválido, revocado y reutilizado.
4. CRUD de cliente con teléfono obligatorio y email opcional.
5. Edición y archivado de clientes; imposibilidad de borrar registros vinculados a facturas emitidas.
6. Alta de dos peluquerías con horarios distintos y días cerrados; comprobar solapamientos.
7. Una entidad fiscal compartida por varias peluquerías y otra distinta, sin mezclar datos.
8. Autocompletado de cliente sin confundir personas con el mismo nombre.
9. Cálculo con `Decimal` para base, IVA 21 % por defecto, descuentos y redondeos; test de valores límite.
10. Numeración correlativa y transaccional sin duplicados, incluso con reintentos.
11. Emisión de factura y generación de PDF con datos fiscales, serie, fechas, líneas e importes; snapshots estables tras cambios de cliente/emisor.
12. Facturas emitidas inmutables; proceso controlado de rectificación y auditoría (cuando se implemente conformidad fiscal).
13. Copia de seguridad, restauración, migraciones y recuperación tras errores.
14. Inexistencia de SQL en widgets y de dependencias de Qt en el dominio.
15. Fluidez UI y ausencia de congelación durante generación de PDFs o backups.
16. Arranque sin configuración manual de servidor MySQL en instalación local SQLite.

**No declarar el módulo de facturación apto para uso real** hasta comprobar los requisitos legales aplicables, implementar los mecanismos necesarios y validarlos.

## 15. Roadmap de implementación

### Fase 0 — Diagnóstico y diseño
- Inspección del repositorio y dependencias.
- Matriz de requisitos (existente/faltante), riesgos, decisiones de tecnología y arquitectura.
- ERD, navegación, wireframes y estrategia de facturación conforme al ámbito español.

### Fase 1 — Base operativa
- Esqueleto Clean Architecture, configuración, SQLite, migraciones, arranque PySide6.
- Registro, login, recuperación local segura, perfil y navegación.
- Tests de dominio y persistencia iniciales.

### Fase 2 — Gestión principal
- CRUD Clientes, Peluquerías, horarios, entidades fiscales y establecimiento activo.
- Búsqueda y tablas editables, validación, archivado, auditoría básica.

### Fase 3 — Facturación
- Borradores, líneas de factura, cálculo monetario, numeración, PDF y consulta.
- Diseñar la conformidad SIF/VERI*FACTU como un **bloqueador de salida a producción** y no como tarea cosmética opcional.
- Implementación y validación fiscal completa conforme al alcance y normativa aplicable antes de habilitar facturación real.

### Fase 4 — Calidad y distribución
- Tests completos, revisión de rendimiento, backups, manejo de fallos y seguridad.
- Packaging, guías, documentación, CI, verificación de licencias y checklist de release.

## 16. Documentación obligatoria

Genera o actualiza de forma veraz:

- `README.md`: propósito del producto, alcance, funcionalidades **reales**, capturas solo si existen, arquitectura, instalación, ejecución, pruebas, packaging, seguridad, limitaciones legales y contribuciones.
- `README.es.md`: equivalente completo en español, enlazado desde README principal.
- `CHANGELOG.md`: historial de cambios con entradas reales, siguiendo Keep a Changelog si es conveniente.
- `LICENSE`: licencia a elegir por el propietario del proyecto; **no inventes una licencia como decisión ya aprobada**. Proponer Apache 2.0 si es compatible con todas las dependencias y derechos de terceros, y solicitar validación antes de publicar.
- `NOTICE`: información de copyright y atribuciones requeridas, no inventar autores/organizaciones.
- `docs/architecture.md`, `docs/data-model.md`, `docs/invoicing-compliance.md` y guía de uso en español.

## 17. Formato obligatorio de la respuesta y ejecución

Trabaja en este orden:

1. **Auditoría inicial**: qué existe, qué falta, dependencias, problemas identificados y decisiones pendientes.
2. **Arquitectura propuesta**: esquema por capas, dependencias, diagrama Mermaid de navegación y ERD.
3. **Modelo de datos**: entidades y relaciones, migraciones, reglas de integridad.
4. **Plan de archivos y tareas por fases**, con prioridades, riesgo, esfuerzo relativo y criterios de aceptación.
5. **Implementación real** del primer incremento razonable sobre el repositorio cuando tengas acceso a sus archivos; código coherente, no plantillas vacías.
6. **Validación**: comandos ejecutados, resultado de tests, errores observados y correcciones.
7. **Informe de entrega**: lista de archivos añadidos/modificados, funcionalidades verificadas, limitaciones conocidas y siguientes pasos.

No solicites aprobación para cada detalle menor: adopta supuestos técnicos seguros y explícitalos. Sí señala decisiones de negocio y legales que no puedas resolver por cuenta propia (titular fiscal, licencia, obligaciones SIF). No afirmes haber ejecutado pruebas, consultado registros, compilado o validado leyes si no lo has hecho.

## 18. Condición de éxito

El MVP será satisfactorio cuando un gestor pueda instalar e iniciar la aplicación, registrar su cuenta de forma segura, gestionar una o varias peluquerías y sus horarios, administrar clientes, configurar correctamente emisores fiscales, crear **borradores** de facturas con importes exactos y generar PDFs de prueba; y cuando exista una ruta clara, verificable y completa para habilitar la **facturación real conforme a la normativa española**. Las funciones que no estén conformes deberán estar claramente marcadas como demostrativas o bloqueadas para uso real.

---

**Instrucción final para Claude/Codex:** prioriza una solución sobria, estable y verificable. Construye fundamentos correctos antes de ampliar funcionalidades. La implementación, la documentación y las pruebas deben describir exactamente el mismo estado del producto.
