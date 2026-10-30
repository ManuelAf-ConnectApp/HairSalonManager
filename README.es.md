# Hair Salon Management

Aplicación nativa local para la futura gestión de peluquerías. Este primer incremento es ejecutable e implementa registro de un gestor, inicio/cierre de sesión, limitación progresiva de intentos y recuperación offline de contraseña con código de un solo uso.

## Estado real

Implementado: SQLite local con cinco migraciones, hash scrypt con sal, auditoría mínima sin secretos, interfaz PySide6, perfil editable y cambio de contraseña con validación de la credencial actual, alta/edición/archivado y listado de clientes, emisores y peluquerías, formularios de horarios, establecimiento activo persistente por cuenta, preferencias operativas, copias de seguridad/restauración local verificadas, exportación CSV y borradores multilínea editables o descartables de prueba con `Decimal`, exportables a PDF no fiscal.

La interfaz utiliza una paleta blanco, azul y rojo con acabados metalizados; el rojo se reserva para avisos, errores y acciones que requieren atención.

Pendiente: validación del paquete en Windows y decisión de licencia antes de publicar. La emisión/numeración fiscal y los cobros de facturas emitidas quedan fuera del alcance de esta distribución.

Propuesto: Argon2id para distribución, adaptador MariaDB cuando haya necesidad multiusuario y una capa fiscal sustituible que un desarrollador pueda implementar y validar para su caso.

La aplicación **no es apta para emitir facturas reales** ni declara conformidad con SIF, VERI*FACTU o NO VERI*FACTU. Consulta el [alcance de documentos de prueba](docs/invoicing-compliance.md) y la [decisión de arquitectura](docs/decisions/0002-alcance-documentos-de-prueba.md).

## Instalación y ejecución

Requiere Python 3.11 o superior y PySide6.

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m hair_salon_management
.venv/bin/python -m unittest discover -s tests
```

La base de datos se crea en la carpeta de datos del usuario (`~/.local/share/hair-salon-management` en plataformas Unix). En Windows se ajustará a la ubicación estándar antes de distribuir.

Para utilizar otra ubicación, por ejemplo en un entorno restringido, define `HAIR_SALON_MANAGER_DATA_DIR` antes de ejecutar la aplicación.

Consulta [arquitectura](docs/architecture.md), [modelo de datos](docs/data-model.md), [plan de implementación](docs/implementation-plan.md) y [guía de uso](docs/user-guide.es.md).

La preparación para empaquetar en Windows y su revisión de licencias está descrita en [la guía de distribución](docs/packaging-windows.es.md).
