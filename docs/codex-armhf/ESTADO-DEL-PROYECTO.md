# Estado del proyecto Codex ARMHF y V8 externo

**Fecha de corte:** 20 de octubre de 2026.

**Destino:** Raspberry Pi Zero 2 W, 512 MB de RAM, Raspberry Pi OS Trixie de 32 bits.

**Estado global:** prototipo funcional bajo emulación; integración completa con Codex Desktop Remote SSH pendiente y con una incompatibilidad confirmada en el lanzador publicado.

## 1. Resultado principal

Se compilaron realmente **Codex CLI y Codex App Server para Linux ARMv7 hard-float de 32 bits**. Ambos ejecutables se enlazaron, se inspeccionaron y se ejecutaron bajo QEMU Cortex-A7. Se publicaron paquetes Debian y tar descargables.

Después se demostró el flujo completo de **Code Mode con V8 oficial x86-64 externo y herramientas ARMHF**: JavaScript se ejecuta en el host x86-64; las llamadas a herramientas regresan al App Server ARMHF, que ejecuta Bash y programas ARMHF y opera sobre archivos del entorno ARMHF.

Estas pruebas no utilizaron inferencia real: un proveedor local de respuestas simuladas emitió las instrucciones de herramientas. **Las herramientas y V8 sí se ejecutaron realmente.** No se afirma haber usado GPT-6.1 Sol con una cuenta real.

**Los paquetes actuales no constituyen una solución completa lista para conectarse desde la aplicación oficial de Windows.** Se encontró que el lanzador `codex-remote-v8` rechaza `app-server proxy`, una ruta utilizada por Remote SSH de Desktop. Las pruebas anteriores usaron un cliente JSON-RPC propio, no la GUI oficial.

## 2. Versiones y procedencia

| Elemento | Versión o referencia |
|---|---|
| Código oficial utilizado | `openai/codex`, etiqueta `rust-v0.163.0` |
| Commit upstream | `83086188ae0614bd882818ff1aa23f3194962012` |
| Destino Rust | `armv7-unknown-linux-gnueabihf` |
| Primera entrega Debian | `0.163.0+armhf1` |
| Entrega con lanzadores V8 remoto | `0.163.0+armhf2.remotev8` |
| Hosts V8 externos | Binarios oficiales OpenAI 0.163.0 para Windows y Linux x86-64 |
| Aplicación Windows indicada por el usuario | `26.1013.40934`, publicada el 16 de octubre de 2026 |

La versión gráfica de Desktop y la versión del motor Codex son identificadores distintos. La versión de la aplicación indicada no fue ejecutada ni inspeccionada directamente en un Windows del usuario.

La segunda entrega conserva los ejecutables ARMHF de la primera, byte por byte. Añade scripts y documentación; no contiene nuevos parches Rust.

## 3. Compilación y entorno

Todo se compiló en Codex Cloud. No hubo conexiones, instalaciones ni compilaciones en una Raspberry.

- Anfitrión Debian Trixie x86-64; límite de tarea de 8 GiB de RAM, dos CPU y sin swap.
- Aproximadamente 30 GB libres al comenzar.
- Contenedor de compilación dedicado, limitado a 7 GiB y dos CPU.
- Rust/Cargo 1.95.0, GCC/G++ ARMHF 14.2, binutils, OpenSSL ARMHF y herramientas Debian.
- Compilación cruzada real mediante `cargo build --release`, no solamente `cargo check`.
- Perfil con optimización por tamaño, sin LTO ni información de depuración y con símbolos eliminados.
- El intento final de Cargo terminó con salida 0 tras 27 min 34 s desde el último relanzamiento. El pico registrado de compilación fue 3.901.852 KiB; no es memoria de ejecución en la Pi.
- Para ejecución se utilizó QEMU user Cortex-A7; posteriormente PRoot 5.4.0 para ejecutar también los descendientes ARMHF.

No se requirieron KVM, un contenedor privilegiado ni registrar binfmt globalmente.

## 4. Cambios respecto al código original

| Cambio | Motivo |
|---|---|
| Ajuste de `Cargo.lock` | La etiqueta tenía versiones internas `0.0.0` incoherentes con el workspace `0.163.0`. |
| Copia local de `pagable 0.4.1` | Corregir una comprobación de tamaño: el layout observado en Linux ARMHF ocupa 40 bytes. |
| Conversiones de números de syscall | Resolver diferencias entre `c_long` de 32 bits y claves `i64` de seccompiler. |
| Copia local de `seccompiler 0.5.0` | Añadir ARM32, `AUDIT_ARCH_ARM = 0x40000028` y tabla de syscalls ARM EABI. |

No se eliminaron los filtros de seguridad para conseguir que compilara. Las otras 1.312 dependencias externas permanecieron idénticas en la comparación final.

El parche completo se conserva como `codex-armhf-source.patch` y se comprobó con `git apply --check` contra las fuentes oficiales fijadas. Los cambios no equivalen a soporte ARMHF oficial de OpenAI.

## 5. Ejecutables ARMHF

| Ejecutable | Tamaño sin comprimir | Identificación |
|---|---:|---|
| `codex` | 166.291.588 bytes | ELF32 ARMv7 EABI5 hard-float, PIE, stripped |
| `codex-app-server` | 125.921.556 bytes | ELF32 ARMv7 EABI5 hard-float, PIE, stripped |

Ambos utilizan `/lib/ld-linux-armhf.so.3`. No son ARM64 ni x86-64.

SHA-256 de los ejecutables, conservado entre las dos entregas:

```text
codex
89c4321eb9dc335b38341050d62189f814c03d030b74deff1fad9722e17f072c

codex-app-server
9a6b46bd3bb5cf724f65fed5971039bb9904c9698ec4b3df9f3f8d3eed1ecfab
```

Dependencias declaradas en el paquete Debian con V8 remoto:

```text
libc6 (>= 2.39), libgcc-s1 (>= 4.3), libssl3t64 (>= 3.0.0),
bubblewrap, ca-certificates, bash, coreutils
```

Recomienda `git` y `ripgrep`; el transporte necesita además un servidor SSH operativo en el equipo ARMHF. El paquete no configura SSH, no instala servicios propios ni inicia Codex automáticamente.

## 6. Lo que funciona y lo que no

| Componente o función | Estado real |
|---|---|
| Compilación y enlace CLI/App Server ARMHF | Verificados en Cloud. |
| Arquitectura y dependencias dinámicas | Verificadas con `file`, `readelf` y cargador ARMHF. |
| Versión, ayuda y funciones básicas CLI | Ejecutadas bajo QEMU. |
| Reglas de ejecución allow/forbidden | Probadas bajo QEMU. |
| App Server: initialize, account/read, config/read y thread/list | Probados bajo QEMU. |
| Turno de texto CLI con proveedor simulado | Completado sin errores con metadatos de gpt-5.5. |
| JavaScript en V8 externo Linux x86-64 | Verificado con el host oficial. |
| Bash, programa ARMHF y archivos mediante callbacks Code Mode | Flujo completo verificado. |
| Code Mode mediante SSH y túnel inverso | Verificado en el banco Cloud. |
| Compartir conexión SSH mediante ControlMaster | Verificado con OpenSSH Linux. |
| Flujo desde `.deb` y tar finales extraídos | Verificado con herramientas reales. |
| Host V8 apagado antes de la celda | Fallo explícito; no se ejecutaron herramientas ni se creó el marcador. |
| V8 en la propia Raspberry | No incluido ni necesario para la arquitectura externa demostrada. |
| Host V8 Windows x86-64 | Descargado, hash verificado y PE32+ inspeccionado; no ejecutado en Windows. |
| Scripts PowerShell | Sintaxis validada con PowerShell real en Linux; uso nativo Windows pendiente. |
| `codex-remote-v8 app-server proxy` | Falla de forma confirmada con código 64. |
| Integración completa con Desktop Windows 26.1013.40934 | No validada; el bloqueo del proxy impide considerarla lista. |
| Daemon gestionado y actualización transparente ARMHF | No soportados por el shim; integración pendiente. |
| Login ChatGPT Plus e inferencia real GPT-6.1 Sol | No probados. |
| Sandbox del kernel ARM, seccomp/namespaces/Landlock/bubblewrap | Pendientes de validación en hardware. |
| Voz y otros auxiliares de la distribución completa | No incluidos en los paquetes ARMHF. |
| TUI interactiva completa, sesiones largas y cargas grandes | No validadas. |
| Raspberry Pi Zero 2 W física con 512 MB | No probada. |

## 7. Qué demostró exactamente Code Mode

```text
Cliente JSON-RPC de prueba
  → canal SSH
  → App Server ARMHF bajo QEMU Cortex-A7
  → gRPC por túnel SSH inverso
  → V8 oficial Linux x86-64 ejecuta JavaScript
  → callback de herramienta al App Server ARMHF
  → Bash y programa ARMHF escriben/leen archivos ARMHF
  → resultado vuelve a V8 y al proveedor simulado
```

El programa de control exigió ARM hard-float al compilar e imprimió punteros de 32 bits. Se verificó Bash ARMHF y `uname -m` como `armv7l`. Los marcadores se crearon dentro del rootfs ARMHF y no en la ruta equivalente del sistema que ejecutaba V8.

Se utilizaron los metadatos de `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-sol` y `gpt-6-luna`, que en el catálogo utilizado son `code_mode_only`. Los ensayos publicados suman **32 llamadas reales a herramientas**: tres pruebas de ocho llamadas y dos pruebas de cuatro desde los paquetes extraídos. El ensayo de host apagado verificó cero llamadas.

La verificación de paquetes realizó además **40 comprobaciones**. Que estas pruebas pasen no demuestra compatibilidad gráfica: incluyen comprobaciones del comportamiento esperado de los scripts, entre ellas sus rechazos de funciones no soportadas.

## 8. Problema pendiente con la aplicación oficial de Windows

La aplicación oficial puede seguir siendo la interfaz prevista. No hay que sustituirla por una aplicación de escritorio creada por este proyecto.

Sin embargo, Remote SSH arranca el motor en el equipo remoto. El App Server ARMHF 0.163.0 necesita `--code-mode-host URL` para usar un V8 externo; activar solamente `features.code_mode_host=true` no selecciona el host de Windows.

Los registros públicos de Desktop muestran la ruta de arranque con socket Unix y `codex app-server proxy`. Existe evidencia de uso del proxy en la versión Desktop 26.1013.40934 sobre macOS; no se extrapola como una ejecución directa del Windows del usuario.

El bloqueo local sí está comprobado: el shim publicado rechaza `app-server proxy` con salida 64. El CLI ARMHF original incluye la implementación upstream del proxy; es el shim añadido el que no la delega. Por ello **conectar la GUI y añadir el shim al PATH no garantiza que la conexión se complete**.

Falta corregir esa delegación y probar el ciclo real: descubrimiento del comando, sonda de versión, arranque, socket, proxy, herramientas, aprobaciones, cancelación y reconexión. También hay que definir cómo se conservará el paquete personalizado ante acciones de actualización o gestión del daemon. El instalador oficial de la versión conservada no selecciona ARMv7 de 32 bits.

No se han corregido ni republicado los binarios o scripts como parte de la investigación posterior de esta incompatibilidad. La entrega `armhf2.remotev8` conserva ese límite.

## 9. Autenticación y ChatGPT Plus

El diseño mantiene el proveedor OpenAI y el login oficial de ChatGPT. No exige una clave API independiente. El host V8 no necesita iniciar sesión en OpenAI: la autenticación del modelo pertenece al App Server.

El CLI conservado dispone de `codex login --device-auth`, y el protocolo ofrece el flujo `chatgptDeviceCode`. Son las rutas previstas para un equipo sin navegador, pero no se ejecutó un login real durante estas pruebas.

La sesión abierta en la aplicación Windows no demuestra por sí sola que el usuario remoto de la Pi esté autenticado. Tampoco disponer de Code Mode concede acceso a un modelo que no esté habilitado para la cuenta. Se deben validar la cuenta, su catálogo y sus límites con un turno real.

## 10. Memoria

Los ensayos funcionales se ejecutaron en contenedores limitados a **512 MiB sin swap**, sin eventos OOM. Incluían también el host V8 externo, el cliente de prueba y procesos SSH del banco; en el despliegue propuesto V8 estará en otro equipo.

| Ensayo | Máximo RSS registrado para App Server con QEMU/PRoot |
|---|---:|
| SSH sin ajustes | 273.176 KiB, aproximadamente 266,8 MiB |
| SSH con un trabajador Tokio y dos arenas malloc | 261.884 KiB, aproximadamente 255,7 MiB |
| Lanzador del staging final | 269.832 KiB, aproximadamente 263,5 MiB |
| Lanzador extraído del tar | 268.984 KiB, aproximadamente 262,7 MiB |
| Lanzador extraído del Debian | 265.324 KiB, aproximadamente 259,1 MiB |

El host V8 x86-64 rondó 25 MiB en estas celdas pequeñas. No es una estimación para programas JavaScript grandes.

La medida procede de GNU time y contiene costes de emulación/trazado; no es la RAM nativa de una Pi ni la suma de todos sus procesos. La contabilidad del cgroup es otra métrica. No es correcto restar una cantidad supuesta de QEMU y presentar el resultado como consumo real ARMHF.

Los lanzadores proponen `TOKIO_WORKER_THREADS=1` y `MALLOC_ARENA_MAX=2`. La muestra también propone salidas cortas y compacción temprana. La variación entre ensayos no permite prometer un porcentaje estable de ahorro.

La viabilidad con el sistema operativo completo, SSH, herramientas y sesiones prolongadas en 512 MB sigue pendiente. Evitar múltiples procesos Codex, contextos enormes, imágenes y comandos de alto consumo. Estas recomendaciones no constituyen un límite duro de memoria.

## 11. Seguridad y errores relevantes

No se eliminaron los mecanismos de seguridad del código para superar la compilación. La generación BPF ARMHF pasó 14 pruebas; instalar un filtro desde QEMU user devolvió `ENOSYS`, por lo que el sandbox del kernel real no queda certificado.

Las pruebas de herramientas utilizaron explícitamente el sandbox externo de un contenedor sin red y sin credenciales. Esa política de ensayo no se instala en los lanzadores de producción.

Los hosts V8 y el túnel se enlazan a loopback. No se debe publicar gRPC en Internet ni tratarlo como un servicio multiusuario autenticado. El equipo x86-64 es de confianza: recibe JavaScript y resultados de herramientas que pueden contener datos del proyecto. No se añadieron tokens ni claves privadas al repositorio.

Además de los errores de compilación ya descritos, se resolvieron incidencias del banco: PRoot 5.1 no gestionaba correctamente metadatos de archivos bajo esta emulación, faltaba montar la CA Cloud en el rootfs y StrictModes rechazó inicialmente la ubicación de claves efímeras. Se usó PRoot 5.4.0, la CA existente de solo lectura y un directorio privado de claves en el contenedor. No se desactivaron TLS ni las comprobaciones SSH para resolverlos.

## 12. Publicaciones y archivos disponibles

Repositorio de entrega: [Rodrigo14090/aeroforge](https://github.com/Rodrigo14090/aeroforge).

- [Primera entrega ARMHF](https://github.com/Rodrigo14090/aeroforge/releases/tag/codex-armhf-v0.163.0-experimental-20261020).
- [Entrega ARMHF con V8 externo](https://github.com/Rodrigo14090/aeroforge/releases/tag/codex-armhf-v0.163.0-remote-v8-20261020).

En la segunda publicación:

| Archivo | Uso |
|---|---|
| `codex-armhf.deb` | Paquete Debian ARMHF con CLI, App Server, lanzadores y documentación. |
| `codex-armhf.tar.gz` | Los mismos ejecutables ARMHF y componentes auxiliares, sin bibliotecas del sistema. |
| `codex-remote-v8-windows-x86_64.zip` | Host oficial V8 Windows x86-64, empaquetado con scripts de arranque y túnel. |
| `codex-remote-v8-linux-x86_64.tar.gz` | Host oficial V8 Linux x86-64, usado en Cloud. |
| `codex-remote-v8-test-details.tar.gz` | Harness, código de pruebas y registros seleccionados. |
| `codex-armhf-source.patch` | Cambios necesarios para compilar ARMHF. |
| `BUILD-MANIFEST.json` | Procedencia, hashes y resultados de pruebas. |
| `PACKAGE-VERIFICATION.json` | Verificación de paquetes extraídos. |
| `SHA256SUMS` | Checksums de los archivos de la publicación. |

GitHub Actions recompuso los archivos probados en Cloud y los publicó sin recompilar los binarios. Se descargaron anónimamente desde GitHub el Debian, el tar ARMHF y el ZIP Windows; sus hashes coincidieron íntegramente con los originales Cloud. Los digests de los once activos coincidieron con los archivos locales en esa verificación.

La primera publicación sigue conservada. La entrega actual continúa marcada como experimental.

## 13. Trabajo necesario para cerrar el proyecto

1. Corregir el shim para delegar el proxy al CLI original y asegurar el arranque del servidor con V8 remoto.
2. Probar el transporte de Desktop con socket Unix y proxy, incluida recuperación de conexiones y manejo de procesos existentes.
3. Validar el host Windows y la GUI oficial 26.1013.40934 sin modificar su aplicación.
4. Autenticar mediante ChatGPT y ejecutar un turno real de GPT-6.1 Sol con una herramienta.
5. Validar ARMHF físico: sandbox, memoria total, estabilidad y comandos habituales en una Pi Zero 2 W.
6. Repetir las verificaciones y publicar una revisión nueva antes de anunciar que Remote SSH está listo para uso completo.

Actualmente están completadas la compilación ARMHF, la publicación verificable y la demostración distribuida de herramientas en Cloud. La integración final de escritorio y la validación en hardware permanecen abiertas.

## Referencias

- [Código oficial utilizado](https://github.com/openai/codex/tree/83086188ae0614bd882818ff1aa23f3194962012).
- [Selección de host remoto en App Server](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/app-server/src/code_mode_host.rs).
- [Remote connections, documentación oficial](https://developers.openai.com/codex/remote-connections).
- [Registros de Remote SSH en Windows Desktop](https://github.com/openai/codex/issues/38055#issuecomment-5294135739).
- [Reporte Desktop 26.1013.40934 en macOS, no prueba Windows](https://github.com/openai/codex/issues/46468#issuecomment-6293548590).
- [Win32 OpenSSH: alcance y ControlMaster](https://github.com/PowerShell/Win32-OpenSSH/wiki/Project-Scope).
- [Guía breve de los paquetes x86-64](GUIA-X86-64.md).
