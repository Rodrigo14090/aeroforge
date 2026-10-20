# Informe: Code Mode externo para Codex ARMHF

Fecha: 20 de octubre de 2026. Revisión de entrega: `0.163.0+armhf2.remotev8`.
Se conserva la etiqueta upstream `rust-v0.163.0`, commit
`83086188ae0614bd882818ff1aa23f3194962012`, y todos los parches de la primera
compilación ARMHF. No se han realizado nuevos cambios Rust ni recompilado los
dos ejecutables para esta revisión.

## Resultado y alcance

La separación funciona de extremo a extremo en el banco de pruebas Cloud:

```text
Cliente JSON-RPC de prueba
        | SSH: canal de sesión sobre conexión ControlMaster
        v
App Server ELF32 ARMHF, QEMU Cortex-A7 + PRoot
        | --code-mode-host http://127.0.0.1:PUERTO_EN_ARMHF
        | gRPC HTTP/2, reenvío SSH -R hacia el equipo x86-64
        v
Code Mode Host oficial 0.163.0, Linux x86-64, V8 real
        | ejecuta JavaScript; tools.exec_command(...) produce un callback
        v
App Server ARMHF -> Bash ELF32 ARMHF -> programa ARM hard-float y archivos ARMHF
        | CompleteToolCall -> V8 -> salida de celda -> siguiente petición al modelo
        v
Proveedor de respuestas determinista local, sin API ni cuenta real
```

No se está sustituyendo V8 por Node ni implementando una imitación de gRPC.
El host utilizado es el binario oficial de la misma versión que el protocolo.
El modelo simulado ordena ejecutar celdas; las celdas y herramientas sí se
ejecutan realmente. Esto prueba el motor, los callbacks, Bash y las operaciones
de archivos, no la disponibilidad comercial ni la inferencia de un modelo real.

Se probaron los slugs `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-sol` y `gpt-6-luna`.
Los cuatro tienen `tool_mode: code_mode_only` en el catálogo de esta versión.
Se verificó también que las peticiones sucesivas conservaban el slug seleccionado.

**Pendiente:** autenticación real con Plus, inferencia con esos modelos, ejecución
del host en Windows, cliente gráfico oficial Windows, kernel ARM físico y
sesiones prolongadas con una Pi de 512 MB. No se declara éxito en esos puntos.

## Implementación upstream examinada

Las rutas siguientes se refieren al commit indicado arriba.

- `codex-rs/app-server/src/code_mode_host.rs`: define el argumento de proceso
  `--code-mode-host URL`, valida HTTP/HTTPS, rechaza credenciales, ruta, query y
  fragmento, y selecciona `CodeModeHostTransport::Grpc`.
- `codex-rs/app-server/src/lib.rs`: crea un
  `GrpcCodeModeSessionProvider::with_http_client_factory` compartido. Exige
  `features.code_mode_host` habilitado. No exige un host local para esa ruta.
- `codex-rs/code-mode/src/grpc_session/transport.rs`: conexión HTTP/2 compartida
  y consciente de la política de red, sin redirecciones. Admite HTTP o HTTPS
  para el cliente y usa el almacén de CA configurado.
- `codex-rs/code-mode-protocol/src/grpc/codex.code_mode.v1.proto`: `OpenSession`,
  `Execute`, `Wait`, `SubscribeToToolCalls`, `CompleteToolCall`, cancelación,
  notificaciones y cierre. El cliente se suscribe a los callbacks por su conexión
  existente: no se necesita abrir otra conexión entrante desde el host V8 a la Pi.
- `codex-rs/code-mode/src/grpc_session/callbacks.rs`: comprueba sesión, celda,
  secuencias y admisión, invoca `delegate.invoke_tool` en el proceso cliente y
  devuelve el resultado por `CompleteToolCall`. Por eso la localización de V8 no
  traslada Bash ni el acceso normal a archivos al equipo Windows.
- `codex-rs/code-mode-host/src/grpc_transport.rs`: el host escucha
  `--listen grpc://IP:PORT`, publica su endpoint HTTP y requiere HTTP/2 para
  gRPC. `/healthz` es únicamente una comprobación básica, no una prueba funcional.
- `codex-rs/code-mode-host/src/main.rs`: ejecutable independiente multiplataforma.
- `codex-rs/core/src/code_mode_host.rs`: ruta local predeterminada con
  `--listen grpc+stdio://`. Es distinta de la selección remota de App Server.
- `codex-rs/app-server/tests/suite/v2/code_mode_host.rs`: pruebas upstream del
  host seleccionado por argumento, reutilización entre conversaciones y tiempos.
- `codex-rs/features/src/feature_configs.rs`: permite
  `features.code_mode_host.disable_in_process_fallback`, usado por los lanzadores
  para que no intenten alojar V8 local si falla la ruta remota.

No es un endpoint persistente de `config.toml` en esta versión: la URL es un
argumento del proceso. Activar `code_mode_host_grpc` por sí solo no proporciona
el endpoint remoto. El flag pertenece a App Server; no debe suponerse que
`codex exec --code-mode-host ...` sea un comando válido.

## Qué se ejecutó realmente

Primero se ejecutaron los binarios originales ARMHF y el host x86-64 mediante
gRPC de loopback. Después se introdujeron un servidor SSH de prueba y claves
efímeras, limitados a loopback dentro de un contenedor sin red externa.

Un único proceso SSH maestro creó el túnel inverso; otra sesión sobre ese mismo
maestro arrancó App Server mediante SSH. `ssh -O check` confirmó la reutilización.
La conexión SSH nunca apuntó a una Raspberry ni a una máquina del usuario.

Cada celda JavaScript:

1. Calculó `2n ** 80n` en V8, obteniendo `1208925819614629174706176`, e imprimió
   que `process` y `require` no existen. El código usa el entorno aislado de Codex.
2. Invocó `tools.exec_command` para ejecutar Bash, consultar `$BASH_VERSION`,
   ejecutar `uname -m` y un pequeño programa compilado para ARMv7 hard-float.
3. Ese programa exigía en compilación `__arm__` y `__ARM_PCS_VFP` e imprimió
   `ARMHF_NATIVE_TOOL pointer_bits=32 ... hard_float=1`.
4. Bash escribió un marcador en `/evidence/turnN.txt`, dentro del rootfs ARMHF.
5. Una segunda llamada real a `tools.exec_command` leyó el marcador.
6. Se comprobó que el archivo existía en el rootfs ARMHF y que no existía en
   `/evidence` del sistema que ejecutaba V8. No era un volumen de trabajo común
   usado para fingir la localización de las operaciones.
7. Se inspeccionó la siguiente petición al proveedor: incluía la salida real de
   la celda y de ambas herramientas, y el turno terminaba correctamente.

La arquitectura del host Linux es ELF64 x86-64, static PIE. Bash, BusyBox,
el programa de prueba y App Server son ELF32 ARM. PRoot aplica QEMU a los
descendientes, de forma que no se utiliza Bash x86-64 para ejecutar herramientas.
V8 corre fuera de ese rootfs, en un PID separado x86-64.

Las ejecuciones `ssh-optimized`, `ssh-baseline` y `packaged-launcher` completaron
cuatro conversaciones secuenciales y ocho llamadas reales cada una. La última
usó el lanzador instalado en el staging final del paquete, con fallback local
deshabilitado. En `host-unavailable` se terminó el host antes de ejecutar la
celda: gRPC devolvió un fallo explícito y no se ejecutó ninguna herramienta ni
se creó el marcador. La prueba no confunde un turno de texto completado con una
llamada a herramienta exitosa.

Las evidencias publicadas son `result.json`, `tool-evidence.json`, tiempos y
registros SSH. Se omiten cuerpos completos de peticiones y perfiles de usuario.
No se incluyen claves privadas ni tokens; las claves SSH de prueba se crearon
en `/run` del contenedor efímero.

## Windows x86-64 y SSH

Upstream publica `codex-code-mode-host-x86_64-pc-windows-msvc.exe.zip` para
0.163.0. Se descargó el ZIP, se verificó su SHA-256 contra el digest publicado
en GitHub y se inspeccionó el ejecutable como PE32+ x86-64. Sus imports observados
son DLL de Windows; no se observó una DLL de runtime MSVC redistribuible externa.
Esto no sustituye una prueba de arranque en Windows.

El mismo servidor gRPC usa Tokio/Tonic, con transporte TCP independiente del
sistema operativo. Ejecutarlo nativamente en Windows es, por tanto, una opción
respaldada por el binario oficial y la implementación común. La ejecución
funcional demostrada aquí corresponde al binario oficial Linux x86-64.

El script Windows verifica el ZIP oficial antes de extraerlo, fija la versión y
enlaza solamente a `127.0.0.1`. No solicita autenticación OpenAI. El segundo
script usa el alias SSH existente, verificación estricta del host, modo batch y
`ExitOnForwardFailure`. No necesita permisos de administrador, reglas entrantes
de firewall Windows ni servidor SSH local.

**Reutilización:** el banco de pruebas demuestra ControlMaster en Linux. El
proyecto Win32 OpenSSH enumera `Client ControlMaster` fuera de su soporte; no
se debe copiar esa receta sin más al `ssh.exe` nativo. El túnel separado es la
opción reproducible del paquete. Para compartir exactamente el transporte de
la app Windows haría falta que la app añadiese `-R` a su conexión inicial, que
respetase un `RemoteForward` configurado y tuviese un ciclo de vida compatible,
o que expusiera una interfaz de multiplexación. Esto no se ha comprobado.

Un túnel separado permite mantener la configuración SSH de la app sin reenviar
el mismo puerto en cada conexión de sondeo. La penalización es otra conexión
SSH y sus procesos en la Pi; su consumo ARMHF no se ha medido aquí.

## Integración con la aplicación oficial

La documentación actual de Remote connections describe la detección de aliases
OpenSSH y el arranque del `codex` remoto mediante el shell de login. Un shim
seleccionado expresamente en ese PATH puede interceptar el arranque directo
`codex app-server --listen ...` y añadir la ruta al host externo. Se conserva
la negociación, el transporte que pide el cliente y los comandos de login.

El código abierto también incluye `codex app-server daemon start/bootstrap` y
`proxy`. Esos comandos gestionan otra copia del paquete y un daemon persistente;
el dispatcher de esta versión no propaga automáticamente el flag de host remoto
al arranque gestionado. Por ello el shim no trata esos subcomandos como si fueran
el arranque directo y los rechaza con explicación.

Si una versión de la app utiliza ese flujo, son necesarios cambios en su selector
de ejecutable/argumentos o en la propagación de la configuración del daemon. Una
configuración futura debería persistir el endpoint por instalación del daemon,
validar loopback y usarlo al construir `AppServerRuntimeOptions`, manteniendo la
misma autenticación y el control de seguridad. No se ha aplicado un parche a
ciegas ni modificado la aplicación propietaria. La actualización automática de
la app o del daemon podría reemplazar los binarios ARMHF o eludir el shim.

No se ha probado la GUI Windows: se entrega una integración para arranque
directo con límites explícitos, no una afirmación de compatibilidad integral
con cualquier build de la aplicación.

## Autenticación Plus

La autenticación de modelo sigue perteneciendo a App Server, separada del canal
V8. No se añade proxy de API, clave independiente, proveedor de pago distinto
ni servicio de inferencia al equipo Windows. Para uso real se conserva el
proveedor OpenAI y el login oficial de ChatGPT.

El protocolo admite `account/login/start` de tipo `chatgptDeviceCode`, y el CLI
conservado admite `login --device-auth`. Se recomienda ese mecanismo para una
Pi sin navegador; el cliente gráfico puede utilizar su flujo oficial compatible.
No se recomienda copiar manualmente tokens del PC. El modo interno
`chatgptAuthTokens` está marcado como interno/inestable en el código, por lo que
no se usa como solución pública.

Cloud no tenía una sesión Plus disponible para el App Server de prueba y la
política de red no incluía los endpoints de inferencia/autenticación. No se
intentó extraer la sesión del chat ni saltarse la política de red. El mock
permite probar las herramientas sin esas credenciales. Una cuenta real debe
confirmar mediante su catálogo que GPT-6.1 Sol está disponible.

## Memoria

Cada contenedor funcional se limitó a 512 MiB, sin swap y con dos CPU. También
contenía el host V8 x86-64, el cliente Python y los procesos SSH del ensayo;
en el despliegue propuesto V8 no residirá en la Pi.

| Ensayo | RSS máximo App Server/QEMU/PRoot | V8 x86-64 observado | Pico cgroup completo |
|---|---:|---:|---:|
| SSH, sin ajustes | 273176 KiB | 25396 KiB | 243191808 bytes |
| SSH, Tokio=1 y arenas=2 | 261884 KiB | 25716 KiB | 230326272 bytes |
| Lanzador empaquetado | 269832 KiB | 25360 KiB | 290676736 bytes |
| Host apagado, sin herramientas | 247228 KiB | 10668 KiB | 195743744 bytes |

No hubo OOM ni uso de swap en estos ensayos. El RSS procede de GNU time/wait4
para el árbol que arranca App Server y excluye el host V8, que es un proceso
independiente. Incluye traducción QEMU y PRoot. El cgroup usa otra contabilidad
y mide el contenedor completo; sus números no deben sumarse al RSS ni
interpretarse como una medición física de la Pi. El muestreo adicional por
`/proc/PID/exe` no identificó consistentemente el proceso trazado, por lo que
no se usa para afirmar un pico exacto del proceso nativo.

El cambio de arenas/trabajadores produjo una reducción en la comparación
inicial, pero el lanzador repitió con un pico diferente. Es una muestra pequeña:
se recomiendan esos ajustes razonables, sin prometer un porcentaje estable.
No se ha realizado una prueba de carga prolongada ni una medida nativa ARMHF.

Se añaden valores orientativos para salida corta y compacción temprana a la
muestra de configuración. La solución más importante es retirar V8 del equipo
ARMHF. Siguen en la Pi el historial, el estado de sesiones, serialización gRPC,
SQLite y procesos de herramientas. Hay un límite de mensajes del protocolo de
64 MiB, que puede implicar copias y picos relevantes: no es una garantía de que
cualquier payload quepa en 512 MB. Evitar imágenes grandes, salidas sin límite,
numerosos hilos y compilaciones locales.

## Seguridad y errores encontrados

No se han eliminado sandbox, comprobaciones de callbacks ni políticas de red.
No se han añadido credenciales al repositorio. El host TCP no implementa login
ChatGPT ni TLS de escucha propio; debe usarse con SSH y loopback en ambos extremos.
No es un servicio multiusuario autenticado para exponer en una LAN o Internet.
Los identificadores de sesión del protocolo no sustituyen la autenticación SSH.

QEMU de usuario no valida seccomp, namespaces o Landlock del kernel ARM. El banco
de pruebas usó la política explícita `externalSandbox` porque el contenedor
aislado, sin red y sin credenciales era el sandbox externo. Esa selección solo
está en el harness, nunca en los lanzadores ni en la configuración de producción.
El sandbox Linux nativo permanece pendiente de pruebas en la Pi.

Incidencias resueltas del banco de pruebas:

- **PRoot Debian 5.1:** abrir archivos funcionaba, pero consultar sus metadatos
  fallaba y Codex decía que CODEX_HOME no existía. Se compiló PRoot upstream
  v5.4.0 para el banco de pruebas. No hubo cambios en Codex por ello.
- **CA Cloud ausente en rootfs:** la conexión gRPC falló al crear el cliente
  porque `SSL_CERT_FILE` apuntaba a una ruta no montada. Se montó el bundle
  existente como solo lectura y se conservó la verificación TLS.
- **Claves SSH temporales bajo /tmp:** StrictModes rechazó los permisos de un
  padre de la ruta. Se trasladaron a un directorio privado bajo `/run` del
  contenedor. No se desactivó StrictModes ni la comprobación del host.
- **Aserción del harness sobre `tools`:** el formato de petición de estos modelos
  no incluía ese campo. Se corrigió la aserción, manteniendo comprobaciones de
  salida efectiva, arquitectura, archivos y llamada de retorno.
- **Imagen PowerShell de MCR:** la descarga de capas fue rechazada por la política
  del entorno. Para analizar sintaxis se utilizó la distribución oficial Linux
  de PowerShell desde GitHub, en un directorio del trabajo. No se desactivó TLS.

La distribución Windows se inspeccionó, y los scripts se analizan con el parser
real de PowerShell. Esto no equivale a ejecutarlos en Windows ni a probar la GUI.

## Reproducción

El archivo `codex-remote-v8-test-details.tar.gz` contiene el harness, la fixture
SSH, el programa de prueba ARM y los registros publicados. Requiere los
ejecutables ARMHF de la entrega anterior y un contenedor Debian Trixie x86-64.
La compilación ARMHF original y sus parches siguen en la publicación anterior.

En el contenedor preparar QEMU user, OpenSSH client/server, PRoot, time, Python3,
compilador `arm-linux-gnueabihf-gcc`, cabeceras y bibliotecas ARMHF de libc6,
libgcc-s1 y OpenSSL. Descargar los paquetes ARMHF de Bash, BusyBox-static y
libtinfo6 sin instalarlos en el anfitrión x86-64. Compilar PRoot v5.4.0 con
`libtalloc-dev` y `make`, sin parches. El helper `setup-arm-root.sh` prepara el
rootfs y aplica QEMU a Bash y sus descendientes.

Descargar el host oficial y verificar:

```text
Linux x86-64 tar.gz:
314263128ba6592e7e807c265deeaf928a692b72dcbfeb5e0b20c9423b703529
Windows x86-64 exe.zip:
bc82fa6d8f449c818292eac35bd7400c4f7dae08908fc9bc67bfbad8c4a3de68
```

El harness espera `/work/validated-binaries`, `/work/remote-code-mode/arm-root`,
el host en `hosts/`, y PRoot en `proot-source/src/proot`. Ejecutar
`python3 /work/remote-code-mode/test-flow.py` con `TEST_SSH=1`, etiquetas
distintas y `TEST_MODELS=gpt-6.1-sol,gpt-6-astra,gpt-6-sol,gpt-6-luna`. Para comparar
memoria usar `TEST_OPTIMIZED=0` y `1`. Para probar el lanzador se usa
`TEST_LAUNCHER=/work/remote-code-mode/package-stage/usr/bin/codex-app-server-remote-v8`.
`TEST_HOST_FAIL=1` ejecuta la comprobación de fallo cerrado.

El contenedor debe ejecutarse con `--network none --memory 512m --memory-swap 512m`.
Se necesita loopback, no virtualización privilegiada, dispositivos KVM ni binfmt
global. El bundle de CA del entorno se monta solo lectura en la ruta indicada
por su variable existente. No se monta ningún perfil de autenticación del usuario.

`package-remote-v8.py stage` conserva los binarios y prepara los lanzadores;
`pack` exige los resultados funcionales y compara SHA-256 de ambos ejecutables
antes de generar los paquetes. El control Debian declara `Architecture: armhf`.
El ZIP Windows y el tar Linux x86-64 están separados y nombrados como tales.
La verificación final vuelve a extraer ambos formatos ARMHF, compara ejecutables,
usa `file`/`readelf` y ejecuta versiones y el flujo de herramientas desde lo extraído.

## Fuentes

- [Fuentes oficiales fijadas a 0.163.0](https://github.com/openai/codex/tree/83086188ae0614bd882818ff1aa23f3194962012).
- [Publicación oficial y hosts Linux/Windows](https://github.com/openai/codex/releases/tag/rust-v0.163.0).
- [Remote connections, documentación oficial actual](https://developers.openai.com/codex/remote-connections).
- [Codex con el plan ChatGPT](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan).
- [Win32 OpenSSH: alcance y ControlMaster](https://github.com/PowerShell/Win32-OpenSSH/wiki/Project-Scope).
- [Seguimiento oficial de ControlMaster en Windows](https://github.com/PowerShell/Win32-OpenSSH/issues/1328).
- [PRoot v5.4.0](https://github.com/proot-me/proot/tree/v5.4.0).
