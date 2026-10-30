# Guía de uso — incremento base

1. Instala el proyecto y ejecútalo con `python -m hair_salon_management`.
2. Selecciona **Crear cuenta** e introduce los campos obligatorios. La contraseña requiere 12 caracteres y tres clases de caracteres.
3. Guarda el código de recuperación mostrado en una ubicación segura: no vuelve a mostrarse ni se puede recuperar desde la aplicación.
4. Inicia sesión. El panel Inicio confirma la sesión y permite cerrarla.
5. Para recuperar una contraseña, usa el email y el código guardado. El código se consume al restablecerla.
6. Tras iniciar sesión, usa **Clientes** para crear, modificar (indicando su ID) o archivar fichas. El listado muestra los IDs.
7. Usa **Peluquerías y emisores** para registrar primero el emisor fiscal y después sus establecimientos. En la pestaña Horarios, selecciona establecimiento y día para consultar los tramos actuales; una lista vacía marca el día como cerrado. Los tramos se separan por comas (`09:00-14:00, 16:00-20:00`).
8. Selecciona un establecimiento activo y abre **Facturas**. Introduce el ID de cliente y añade una o varias líneas de servicio. El resultado es un borrador de prueba: puedes editarlo, descartarlo o usar **Exportar PDF de prueba**. No tiene número fiscal ni valor de factura emitida.
9. En **Peluquerías**, introduce un ID existente para editar o archivar un emisor o establecimiento. No es posible archivar un emisor mientras conserve peluquerías activas asociadas.
10. En **Ajustes**, usa **Crear copia de seguridad** para elegir un archivo `.db`. Para restaurar, selecciona una copia de Hair Salon Management válida y confirma la operación; se comprueba su integridad y esquema antes de reemplazar los datos locales y cerrar la sesión.
11. En **Ajustes**, puedes guardar el formato de fecha y una carpeta predeterminada para exportaciones CSV; las preferencias se conservan por cuenta.
12. En **Ajustes**, exporta clientes o borradores a CSV. Los archivos incluyen únicamente los registros de la cuenta con sesión iniciada y no contienen contraseñas ni códigos de recuperación.

La facturación aún no está disponible. No introduzcas ni emitas facturas reales con esta versión.
