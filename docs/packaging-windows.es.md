# Empaquetado para Windows

El script `scripts/build-windows.ps1` crea una distribución de prueba con PyInstaller. Debe ejecutarse **en Windows**: PyInstaller no genera de forma fiable un ejecutable Windows desde macOS o Linux.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build-windows.ps1
```

El resultado se sitúa en `dist\HairSalonManagement\`. Antes de publicar una distribución se debe probar en un equipo Windows limpio, comprobar creación de base de datos, copia/restauración y PDF de composición, y firmar el ejecutable si se dispone de certificado.

El flujo [`.github/workflows/windows.yml`](../.github/workflows/windows.yml) ejecuta en GitHub Actions las pruebas, construye el ejecutable y adjunta el resultado durante 14 días. Su primera ejecución requiere publicar estos cambios en un repositorio GitHub; el artefacto no es una versión publicada ni firmada.

## Revisión de licencias antes de distribuir

Este repositorio aún no declara una licencia propia: su propietario debe elegirla y añadir `LICENSE` y `NOTICE` antes de publicar binarios o código.

- PySide6/Qt dispone de modalidades LGPL/GPL y comercial. Una distribución bajo LGPL debe cumplir sus obligaciones, incluida la información y mecanismos exigidos por esa licencia; si no se pueden cumplir, debe evaluarse una licencia comercial. Consulta la [documentación oficial de Qt](https://doc.qt.io/QT-6/licensing.html).
- PyInstaller ofrece una excepción a GPL que permite distribuir los binarios generados bajo una licencia compatible con las dependencias; esto no sustituye la revisión de licencias de esas dependencias. Consulta su [licencia oficial](https://www.pyinstaller.org/en/stable/license.html).
- También deben revisarse los derechos de imágenes, tipografías y cualquier dependencia que se añada posteriormente.

No se ha generado ni validado un `.exe` Windows en este entorno macOS.
