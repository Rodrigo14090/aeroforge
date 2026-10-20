# Codex 0.163.0 ARMHF — entrega experimental

Los ejecutables `codex` y `codex-app-server` se compilaron íntegramente en Codex Cloud desde `openai/codex`, etiqueta `rust-v0.163.0`, commit `83086188ae0614bd882818ff1aa23f3194962012`, con los parches ARM32 documentados. Este flujo **no compila**: reconstruye los archivos originales a partir de fragmentos y verifica sus SHA-256 antes de publicarlos.

Descargas:

- [codex-armhf.tar.gz](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-experimental-20261020/codex-armhf.tar.gz)
- [codex-armhf.deb](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-experimental-20261020/codex-armhf.deb)
- [Informe completo](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-experimental-20261020/INFORME-ARMHF.md)
- [Parches, scripts y registros](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-experimental-20261020/codex-armhf-build-details.tar.gz)
- [SHA256SUMS](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-experimental-20261020/SHA256SUMS)

Destino: Linux ARMv7 de 32 bits, GNU EABI hard-float (`armv7-unknown-linux-gnueabihf`), previsto para Raspberry Pi OS Trixie de 32 bits. No son binarios ARM64.

Ambos binarios se verificaron con `file`, `readelf`, el cargador ARMHF y QEMU con CPU Cortex-A7. Pasaron 21 comprobaciones y un turno CLI con un servidor Responses simulado, con el contenedor limitado a 512 MiB y sin swap. El turno usó aproximadamente 246 MiB residentes, incluido QEMU. Las cuatro copias extraídas del tar y del Debian coinciden con los binarios de Cargo y ejecutan `--version` bajo ARMv7.

## Limitaciones

- No incluye V8/Code Mode ni el auxiliar de voz. Los modelos `code_mode_only`, incluidos los GPT-6 del catálogo de esta versión, requieren un `codex-code-mode-host` compatible o remoto para sus herramientas. Desactivar Code Mode no elimina ese requisito.
- El turno simulado final usó metadatos de `gpt-5.5`; no se probaron credenciales ni inferencia real.
- El sandbox sobre un kernel ARM físico y la interfaz TUI completa quedan pendientes de prueba. El paquete requiere `bubblewrap` y soporte del kernel para namespaces/seccomp.
- Las pruebas limitadas a 512 MiB no garantizan sesiones largas o herramientas externas en una Pi con 512 MB.
- No se accedió a ninguna Raspberry ni se compiló o instaló nada en ella.

Dependencias del Debian: `libc6 (>= 2.39)`, `libgcc-s1 (>= 4.3)`, `libssl3t64 (>= 3.0.0)`, `bubblewrap`, `ca-certificates`. Recomienda `git`, `bash` y `ripgrep`.

Se necesitan parches de `pagable`, `seccompiler`/seccomp y la actualización de las versiones internas del lockfile. Las otras 1.312 dependencias externas conservaron sus versiones y fuentes. No es una distribución oficial con soporte ARMHF.

Los fragmentos de `payload/` evitan superar el límite de tamaño de archivos Git. `restore.py` los concatena sin transformar ni recompilar los ejecutables. Se conservan el manifiesto, los checksums y el informe originales de Cloud. El código original de Codex y sus licencias se identifican en los paquetes; la licencia MIT del repositorio de entrega no cambia las licencias de Codex ni de sus dependencias.
