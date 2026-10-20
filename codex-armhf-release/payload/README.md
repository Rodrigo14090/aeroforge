# Codex 0.163.0: compilación experimental ARMHF

Contiene `codex` y `codex-app-server` compilados desde las fuentes oficiales:
https://github.com/openai/codex/tree/83086188ae0614bd882818ff1aa23f3194962012

Limitación funcional: esta entrega no incluye V8/Code Mode. Los modelos cuyo
catálogo indica `code_mode_only` (incluidos los gpt-6 de esta versión) requieren
un `codex-code-mode-host` compatible o remoto para sus herramientas; no basta
con desactivar esa función. La prueba de turno local usa metadatos de `gpt-5.5`,
que no exige ese modo. La disponibilidad de modelos en una cuenta real no se
ha comprobado. No es la distribución completa oficial de Codex.

Destino: `armv7-unknown-linux-gnueabihf`, ELF32 ARMv7 EABI5 hard-float,
little endian. Sistema previsto: Raspberry Pi OS de 32 bits, Debian Trixie.
Cargador: `/lib/ld-linux-armhf.so.3`. No son binarios ARM64 ni x86_64.
El sandbox requiere soporte del kernel para seccomp y namespaces, y permisos
para crear los namespaces necesarios. Estos requisitos dependen del kernel
y de la configuración de Raspberry Pi OS, además de las bibliotecas Debian.

Dependencias Debian calculadas mediante dpkg-shlibdeps:

    libc6 (>= 2.39), libgcc-s1 (>= 4.3), libssl3t64 (>= 3.0.0), bubblewrap, ca-certificates

Se recomienda disponer de `git`, `bash` y `ripgrep` para tareas de desarrollo.
Para usar el sandbox es obligatorio disponer de `bwrap` de la dependencia
`bubblewrap`: esta entrega no contiene el helper externo de la distribución
completa. Un mensaje de startup que anuncia un helper incorporado no demuestra
que ese helper exista junto a una compilación personalizada de dos binarios.
El archivo tar no contiene las bibliotecas del sistema; el paquete Debian
declara las dependencias anteriores para que APT las resuelva.

## Uso

Tras extraer el tar, ejecutar `./codex --version` o `./codex-app-server --help`.
Se pueden copiar ambos ejecutables a un directorio del PATH. Para el paquete:

    sudo apt install ./codex-armhf.deb

No se han ejecutado estas instrucciones ni instalado nada en una Raspberry.
El paquete no añade servicios ni inicia procesos automáticamente.
Codex necesita conexión a un proveedor y autenticación válida para inferencia.
La autenticación y las llamadas a modelos reales no se probaron en este trabajo.

## Cambios necesarios respecto a upstream

- Actualización de versiones internas del Cargo.lock de la etiqueta.
- `pagable 0.4.1`: comprobación del layout de 40 bytes específica de Linux ARM32.
- `codex-linux-sandbox`: conversiones de números de syscall de c_long a i64.
- `seccompiler 0.5.0`: arquitectura ARM32 y AUDIT_ARCH_ARM 0x40000028;
  tabla de syscalls ARM EABI para el frontend JSON opcional.

El informe, los parches y los registros del trabajo acompañan la entrega.
Es una compilación local experimental, sin soporte oficial de ARMHF.

## Pruebas y límites

Los dos ejecutables se han inspeccionado con file/readelf y ejecutado bajo
QEMU `-cpu cortex-a7`: versión, ayuda, reglas allow/forbidden y negociación
RPC de App Server (initialize, account/read, config/read, thread/list).
Las pruebas verifican ejecutables reales, no solamente cargo check.

El backend BPF pasó 14 pruebas ARMHF bajo QEMU. Instalar seccomp dentro de
QEMU de usuario devuelve ENOSYS: el aislamiento del kernel, bubblewrap,
namespaces y Landlock quedan pendientes de validación en hardware ARM.
No se ha desactivado el sandbox en el código para evitar estos límites.

No se incluyen los auxiliares `codex-code-mode-host` (V8), `codex-voice-host`
ni otros recursos de la distribución completa. Las funciones que los necesitan
no están disponibles en esta entrega de dos ejecutables. Para evitar intentar
usar el host local de code mode, se puede configurar en ~/.codex/config.toml:

    [features]
    code_mode = false
    code_mode_host = false

## Raspberry Pi de 512 MB

La compilación se hizo íntegramente en Codex Cloud. No hay mediciones en la Pi
ni garantía de que sesiones grandes, varias sesiones simultáneas o procesos
externos de desarrollo quepan en 512 MB. Ejecutar un solo proceso Codex,
limitar procesos externos y comenzar con:

    TOKIO_WORKER_THREADS=1 MALLOC_ARENA_MAX=2 ./codex

Para App Server se pueden usar las mismas variables. No hace falta ejecutar
CLI y App Server simultáneamente para utilizar cada uno por separado.
Los números de memoria medidos bajo QEMU incluyen el emulador.
