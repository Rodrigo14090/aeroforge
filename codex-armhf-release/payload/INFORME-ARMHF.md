# Compilación experimental de Codex para Linux ARMHF

Resultado: **Codex CLI y Codex App Server 0.163.0 compilados y enlazados para ARMHF**, con salida 0 de Cargo. Ambos ejecutables pasaron pruebas ARMv7 bajo QEMU y se empaquetaron en `codex-armhf.tar.gz` y `codex-armhf.deb`.

La entrega es experimental y tiene una limitación funcional importante: no contiene el auxiliar V8 `codex-code-mode-host`. Los modelos marcados `code_mode_only`, incluidos los GPT-6 del catálogo de esta versión, necesitan ese auxiliar o un host compatible remoto para sus herramientas. Desactivar la función no transforma esos modelos en modelos de herramientas convencionales. No se certifica el sandbox de un kernel ARM real ni la memoria de sesiones grandes en una Pi física.

## Fuente y objetivo

- Repositorio oficial: https://github.com/openai/codex
- Última versión estable resuelta mediante `releases/latest`: `rust-v0.163.0`.
- Commit: `83086188ae0614bd882818ff1aa23f3194962012` (15 de octubre de 2026).
- Rama local: `work/armhf-rust-v0.163.0`.
- Objetivo Rust: `armv7-unknown-linux-gnueabihf`, GNU EABI hard-float, little endian, punteros de 32 bits.
- Ejecutables solicitados: `codex` (`codex-cli`) y `codex-app-server`.
- Hardware de destino previsto: Pi Zero 2 W con Raspberry Pi OS Trixie **de 32 bits**. No se ha accedido a ninguna Raspberry.

## Entorno Cloud

El anfitrión es Debian 13 Trixie x86_64, kernel 6.18.55. La máquina informa aproximadamente 9,7 GiB de RAM; el cgroup de esta tarea limita la memoria a 8 GiB y la CPU a dos núcleos. No hay swap. Al comenzar había unos 30 GB libres en el almacenamiento de trabajo.

El entorno no traía Rust, Cargo, el compilador cruzado ni QEMU. Se creó únicamente para este trabajo un contenedor `codex-armhf-builder`, basado en `debian:trixie-slim`, limitado a 7 GiB y dos CPU, sin `--privileged`, sin KVM y sin registrar binfmt globalmente. El digest descargado está en `logs/docker-pull.log`. Solo el directorio dedicado del trabajo se monta con escritura; el certificado del proxy se monta de solo lectura. Se mantiene la verificación TLS.

Herramientas instaladas dentro del contenedor: Rust/Cargo 1.95.0, GNU GCC/G++ 14.2 para `arm-linux-gnueabihf`, binutils, Clang/LLD, CMake, Ninja, pkg-config, QEMU user 10.0.13, Python y herramientas Debian. Se instalaron bibliotecas y cabeceras **armhf** de OpenSSL y libcap, además del sysroot GNU ARMHF. El inventario exacto está en `logs/builder-packages.tsv`.

El primer acceso de Git/Curl y del socket Docker dentro del sandbox no funcionó hasta habilitar el permiso de red del comando. No se alteró la política del proxy ni se deshabilitaron certificados.

## Procedimiento

Se clonó el repositorio oficial y se fijó la última etiqueta estable, en vez de una instantánea cambiante de `main`. Los scripts `setup-builder.sh`, `docker-local.sh` y `build-armhf.sh` conservan los comandos utilizados.

Comando de compilación real:

```sh
cargo +1.95.0 build --locked --release \
  --target armv7-unknown-linux-gnueabihf \
  -p codex-cli --bin codex \
  -p codex-app-server --bin codex-app-server
```

Se configura explícitamente GCC/G++/AR ARMHF y el directorio pkg-config multiarch ARMHF. El perfil usa `opt-level=s`, símbolos eliminados, sin información de depuración ni LTO, ocho unidades de generación y dos trabajos simultáneos. Se busca un tamaño razonable y una compilación ajustada a los recursos Cloud. No se ha usado `cargo check` como prueba de éxito.

El comando mostrado con `--locked` es el apropiado después de aplicar el parche entregado, que contiene el lockfile final. Para resolver las versiones locales de la etiqueta y registrar los dos parches se ejecutaron los intentos posteriores con `CODEX_ARMHF_UPDATE_LOCK=1`, que permite actualizar el lockfile. La comparación final confirma que las otras 1.312 dependencias externas permanecen idénticas (`logs/final-dependency-comparison.json`).

El intento final de Cargo terminó con **salida 0**, tras 27 min 34 s desde el relanzamiento con los parches de seccomp. El máximo residente de un proceso de ese intento fue 3.901.852 KiB; no es el consumo de ejecución de Codex. La compilación completa y todos los ensayos se hicieron en Cloud.

## Errores encontrados y modificaciones

1. **Lockfile de la etiqueta incoherente con la versión interna.** `--locked` rechaza el archivo original porque 160 paquetes locales aparecen como `0.0.0`, mientras que el workspace declara `0.163.0`. Se regeneraron esas entradas. La comparación inicial confirma que las 1.314 dependencias externas no cambiaron de versión, fuente ni checksum (`logs/lock-resolution.json`). Las siguientes modificaciones del lockfile reflejan únicamente las dos dependencias locales parcheadas descritas abajo.

2. **`pagable 0.4.1`, E0512.** Una comprobación de tamaño asume que `PagableArcInner<[usize; 4]>` ocupa 12 palabras en toda plataforma de 32 bits. Linux ARMHF produce 40 bytes, es decir, diez palabras. Se conservó una copia local de la dependencia en `codex-rs/vendor/pagable-armhf` y se añadió una comprobación específica de diez palabras para Linux ARM. No se eliminan las comprobaciones de otros destinos ni se cambia la representación de datos o su serialización. El pequeño parche está en `logs/pagable-armhf.patch`; el error original está en `logs/build-02-resolve-lock.log`.

3. **`codex-linux-sandbox`, 25 errores E0308.** Los números de syscall de libc son `c_long`, de 32 bits en ARMHF, mientras que las claves de `seccompiler` son `i64`. Se mantienen ambos tipos y se convierten explícitamente los números al construir el mapa. El código original solo selecciona x86_64 y AArch64 y entra en `unimplemented!` para ARM.

4. **Backend seccomp sin ARM32.** Se conserva una copia local de `seccompiler 0.5.0` en `codex-rs/vendor/seccompiler-armhf`, añadiendo `TargetArch::arm` y el identificador Linux `AUDIT_ARCH_ARM = 0x40000028`. No se utiliza el identificador AArch64 `0xc00000b7`. Las estructuras `seccomp_data` conservan sus campos de argumentos de 64 bits incluso para procesos ARM de 32 bits, por lo que la generación BPF existente sirve con los números y el identificador adecuados. También se genera la tabla ARM EABI para el frontend JSON opcional a partir de las cabeceras Debian ARMHF. Se conservan los filtros y el rechazo de arquitecturas distintas; no se desactiva el aislamiento para hacer que compile.

Registros de intentos sucesivos: `logs/build-01-original.log`, `build-02-resolve-lock.log`, `build-03-pagable.log` y `build-04-seccomp.log`.

5. **Enlace GNU BFD muy lento, sin fallo final.** El enlace de CLI consumió varios minutos. Mientras seguía activo se extrajo la orden de GCC y se repitió solo el enlace con LLD y los mismos objetos producidos por Rust. LLD finalizó en 4,40 s y el binario alternativo ejecutó `--version` en ARMv7. Al ir a detener el enlace lento, GNU ya había terminado: no se interrumpió ningún proceso. **Los artefactos entregados usan los dos ejecutables del build completo de Cargo con GNU**, no el alternativo LLD. Se conservan las órdenes y mediciones de la alternativa en `logs/cli-link-lld*`.

Las advertencias `unused_mut`, importaciones y constantes sin usar provienen del código original y no impidieron el build. No se modificaron para ampliar el alcance del parche.

## Pruebas realizadas

- Programa de control C: enlazado como ELF32 ARM EABI5 hard-float, atributos ARMv7 y VFPv3-D16; ejecutado con `qemu-arm -cpu cortex-a7` y punteros de 32 bits.
- Programa de control Rust: enlazado para el triple solicitado, inspeccionado con `file`/`readelf` y ejecutado en el mismo emulador con punteros de 32 bits.
- Backend de `seccompiler`: 14 pruebas unitarias ARMHF ejecutadas bajo QEMU, todas aprobadas, incluyendo la validación del identificador ARM. Registro: `logs/seccompiler-armhf-unit-tests.log`.

Estos programas de control no son Codex y no se distribuyen bajo sus nombres. `verify-armhf.py` ejecutó 21 comprobaciones sobre los binarios finales: ELF, atributos, dependencias resueltas mediante el cargador ARMHF, versión y ayuda de ambos, listado de funciones de CLI, decisiones de reglas `allow`/`forbidden`, negociación RPC de App Server y cierre limpio. Las reglas verifican en ejecución el parser Starlark y la dependencia `pagable` parcheada.

La tabla ARM EABI del frontend JSON de seccompiler también superó una prueba de mapeo en el anfitrión x86_64 (`logs/seccompiler-json-map-test.log`). Una prueba de instalación de un filtro mínimo desde un programa ARMHF devolvió `ENOSYS` dentro de QEMU (`logs/armhf-seccomp-probe.log`, salida 77), confirmando experimentalmente el límite de la emulación de usuario. No se interpreta ese resultado como un fallo del kernel de la Raspberry, que no se ha probado.

Primer ejecutable enlazado: `codex-app-server`, 121 MiB. Su primera ejecución ARMv7 de `--version` terminó con salida 0 y un máximo residente de 32.484 KiB, incluido QEMU. Pasó después 11 comprobaciones de ELF, cargador, versión, ayuda y RPC (`initialize`, `account/read`, `config/read`, `thread/list`), con cierre limpio. Cloud no tiene `bubblewrap` en PATH: el servidor lo diagnostica con un mensaje genérico que anuncia el helper incorporado. Al investigar el launcher se comprueba que ese helper es un ejecutable externo de la distribución completa, no parte de estos dos binarios. Esta entrega no lo contiene: se necesita `bubblewrap` del sistema para ejecutar comandos con ese sandbox, y el paquete Debian lo declarará como dependencia. La ausencia del helper no impidió las pruebas RPC, que no ejecutan comandos sandboxed.

### Prueba con 512 MiB y turno CLI completo

Tras terminar todos los compiladores, se limitó **el contenedor completo a 536.870.912 bytes, con swap deshabilitada**, y se ejecutaron las 21 comprobaciones anteriores. Todas pasaron. Los contadores `oom` y `oom_kill` permanecieron en cero (`logs/runtime-cgroup-after-tests.txt`). El emulador usó `-cpu cortex-a7`, una CPU ARMv7, no un emulador AArch64.

`mock-turn-armhf.py` ejecutó después `codex exec --ephemeral --skip-git-repo-check --json` contra un servidor HTTP local simulado de Responses. La prueba final usa metadatos de `gpt-5.5`, devuelve `ARMHF_EXECUTION_OK`, emite `turn.completed` y termina con salida 0, sin eventos de error. También se ejecutó con el límite de 512 MiB. Máximo residente: **251.456 KiB (245,6 MiB)**; tiempo: 1,78 s. Incluye el coste de QEMU. No hubo llamadas a un modelo real ni se usaron credenciales.

En un primer ensayo se usó `gpt-5.4`, ausente del catálogo incorporado, y se observó el aviso de metadatos de fallback. Al seleccionar `gpt-6.1-sol` apareció el error explícito de Code Mode no disponible: el modelo declara `tool_mode=code_mode_only` aunque `features.code_mode` esté desactivada. El turno de texto completaba, pero la comprobación adicional rechazó ese evento de error. Esa evidencia se conserva en `logs/validation/mock-code-mode-unavailable/`. Se seleccionó después `gpt-5.5`, que no exige ese modo, y se repitió el ensayo final sin errores. Esto establece una limitación real de la entrega; no se cambió el código para ocultarla.

### Binarios y paquetes finales

| Archivo | Tamaño sin comprimir | Resultado |
| --- | ---: | --- |
| `codex` | 166.291.588 bytes | ELF32 ARMv7 EABI5 hard-float, PIE, stripped |
| `codex-app-server` | 125.921.556 bytes | ELF32 ARMv7 EABI5 hard-float, PIE, stripped |

`file` identifica ambos como `ELF 32-bit LSB pie executable, ARM, EABI5`; `readelf -A` muestra `Tag_CPU_arch: v7` y argumentos VFP. El intérprete es `/lib/ld-linux-armhf.so.3`. Sus bibliotecas se resuelven desde los directorios `arm-linux-gnueabihf`, incluyendo libc, libm, libgcc_s, libssl y libcrypto. OpenSSL añade sus dependencias transitivas zlib/zstd. No se empaquetaron binarios x86_64 ni ARM64 bajo estos nombres.

Paquete Debian: `Package: codex-armhf`, `Version: 0.163.0+armhf1`, `Architecture: armhf`, `Installed-Size: 285417` KiB. Dependencias:

```text
libc6 (>= 2.39), libgcc-s1 (>= 4.3), libssl3t64 (>= 3.0.0), bubblewrap, ca-certificates
```

Recomienda `git`, `bash` y `ripgrep`. No añade servicios ni inicia procesos. La biblioteca libc de Trixie es 2.41; no se promete compatibilidad con sistemas de glibc anteriores al mínimo indicado.

`dpkg-shlibdeps` calculó las dependencias dinámicas. Emitió avisos por la diversión del cargador de Debian con usr-merge y por analizar los ejecutables desde el directorio de compilación. Se contrastaron sus resultados con `readelf`, el cargador ARMHF real y las pruebas de ejecución. Las dependencias declaradas no incluyen paquetes de compilación cruzada ni paquetes `amd64`.

Se extrajeron ambos archivos entregables en un directorio nuevo. **Los cuatro ejecutables extraídos** (dos por formato) tienen SHA-256 idéntico al binario correspondiente del build de Cargo; pasan `file`, `readelf` y `--version` bajo QEMU. `verify-packages.py` terminó con cuatro verificaciones correctas (`logs/package-verification.json`). El `.deb` y el tar contienen README y licencias. El parche completo se comprobó mediante `git apply --check` contra un worktree limpio de la etiqueta oficial.

## Emulación, funciones auxiliares y memoria

QEMU de usuario funciona sin virtualización privilegiada. No hace falta compilar nativamente bajo un sistema ARM emulado mientras la compilación cruzada avance. Cambiar el compilador anfitrión por uno ARM emulado no corregiría por sí mismo errores de tipos o layout del mismo código fuente. La emulación de usuario no permite certificar seccomp, namespaces, Landlock o bubblewrap sobre un kernel ARM real.

Esta compilación solicita dos ejecutables. No incluye `codex-code-mode-host` (V8), `codex-voice-host` ni otros recursos de la distribución completa. Las funciones que necesiten esos auxiliares requieren compilarlos/obtenerlos por separado para ARMHF o un host remoto compatible cuando la aplicación lo admita. No se han convertido archivos ARM64 en ARMHF ni se han sustituido los ejecutables solicitados por versiones x86_64.

No hay una medición de memoria de Codex en una Pi física. Se probó con `TOKIO_WORKER_THREADS=1` y `MALLOC_ARENA_MAX=2`; son las variables recomendadas como punto de partida en 512 MB. Conviene usar un solo proceso Codex y limitar procesos externos. Los stacks de 16 MiB configurados por upstream son reservas virtuales y no equivalen automáticamente a 16 MiB residentes por hilo. No se han reducido sin evidencia, para evitar desbordamientos. Las pruebas acotadas pasaron con 512 MiB, pero las mediciones incluyen QEMU y no garantizan sesiones largas, varias sesiones, herramientas externas o el comportamiento del sistema operativo completo en hardware real.

Quedan sin validar autenticación contra un proveedor real, inferencia real, interacción TUI completa, ejecución de herramientas con sandbox sobre un kernel ARM, el auxiliar V8/Code Mode y voz. Las últimas dos funciones no están incluidas en la entrega. Ninguna Raspberry recibió conexiones, instalaciones o compilaciones durante este trabajo.
