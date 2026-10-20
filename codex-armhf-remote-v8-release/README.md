# Codex ARMHF con Code Mode/V8 externo — experimental

Entrega `0.163.0+armhf2.remotev8`. Conserva los dos ejecutables ARMHF ya
compilados en Cloud y añade lanzadores, scripts Windows y pruebas reproducibles.
La entrega ARMHF anterior permanece disponible en su publicación original.

**Demostrado:** V8 oficial Linux x86-64 ejecuta JavaScript y devuelve callbacks a
App Server ARMHF bajo QEMU Cortex-A7; Bash ARMHF y un programa ARM hard-float de
32 bits escriben/leen archivos dentro del entorno ARMHF. Se verificó el flujo
completo por SSH, incluida una conexión multiplexada Linux, y se repitió con
los archivos extraídos del `.deb` y del `.tar.gz` finales.

Los ensayos usan los metadatos de GPT-6.1 Sol, GPT-6 Astra/Sol/Luna y un proveedor
de respuestas simulado. **La inferencia real y el login Plus no se han probado.**
La solución conserva el login ChatGPT y no requiere una clave API independiente.

## Descargas

- [codex-armhf.deb](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/codex-armhf.deb)
- [codex-armhf.tar.gz](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/codex-armhf.tar.gz)
- [Host y scripts Windows x86-64](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/codex-remote-v8-windows-x86_64.zip)
- [Host Linux x86-64](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/codex-remote-v8-linux-x86_64.tar.gz)
- [Guía de uso y requisitos](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/README.md)
- [Informe técnico](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/INFORME-REMOTE-V8.md)
- [Checksums SHA-256](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/SHA256SUMS)

Los paquetes ARMHF no contienen V8 ni ejecutables de otra arquitectura. Los hosts
x86-64 se entregan aparte y proceden de la publicación oficial 0.163.0.
El host Windows se inspeccionó como PE32+ x86-64 y sus scripts pasaron el parser
real de PowerShell, pero **no se ejecutaron en Windows ni con la GUI oficial**.

La integración admite el arranque directo `codex app-server ...` mediante un
shim opcional en el PATH remoto. Las versiones de la app que usen un daemon
gestionado, otro binario o una ruta absoluta necesitan adaptar su arranque.
Win32 OpenSSH no ofrece ControlMaster: los scripts Windows utilizan un túnel
separado. No se publica ningún puerto de V8 fuera de loopback.

Las pruebas funcionales pasaron bajo 512 MiB sin swap, sin OOM. El máximo RSS de
App Server con QEMU/PRoot rondó 256–267 MiB; son ensayos pequeños, no una garantía
de memoria nativa en una Pi Zero 2 W. El sandbox del kernel ARM, la estabilidad
prolongada y los modelos disponibles para la cuenta real siguen pendientes.

No se cambiaron las políticas de seguridad ni se añadieron tokens. Los lanzadores
deshabilitan el fallback a V8 local y fallan sin ejecutar herramientas si el host
externo no está disponible. El banco de pruebas usó el sandbox externo de un
contenedor aislado; esa política no se instala en producción.

Los archivos de `payload/` son partes de los artefactos ya compilados y probados
en Cloud. `restore.py` recompone los bytes originales, verifica SHA-256 y vuelve
a comprobar `SHA256SUMS`. GitHub Actions publica esos archivos sin recompilarlos.
