# Codex ARMHF con V8 externo — 0.163.0+armhf2.remotev8

Esta entrega conserva los ejecutables ARMHF anteriores y añade lanzadores y
scripts para usar el Code Mode Host oficial en otro equipo x86-64. No instala V8
en la Raspberry. Es una compilación experimental, sin soporte oficial ARMHF.

**Demostrado en Cloud:** App Server ARMHF bajo QEMU Cortex-A7 → gRPC por túnel
SSH inverso → V8 oficial Linux x86-64 → callback gRPC → Bash y herramientas ARMHF
→ escritura/lectura de archivos ARMHF → resultado devuelto al proveedor simulado.
Las pruebas usan respuestas de modelo deterministas; no se ha probado una sesión
autenticada real con ChatGPT Plus ni la interfaz gráfica de Windows.

## Archivos y requisitos

- `codex-armhf.deb`: arquitectura Debian `armhf`, para Raspberry Pi OS Trixie de
  32 bits. Ejecutables ELF32 ARMv7 EABI5 hard-float, cargador
  `/lib/ld-linux-armhf.so.3`. No contiene ejecutables x86-64 ni ARM64.
- `codex-armhf.tar.gz`: los mismos `codex` y `codex-app-server`, dos lanzadores,
  documentación y scripts de Windows. No contiene bibliotecas del sistema.
- `codex-remote-v8-windows-x86_64.zip`: scripts, licencia y ZIP oficial verificado
  del host Windows x86-64. Se utiliza en el PC, nunca en la Raspberry.
- `codex-remote-v8-linux-x86_64.tar.gz`: host oficial Linux x86-64 y lanzador;
  es el utilizado en las pruebas Cloud.

Dependencias ARMHF: `libc6 (>= 2.39)`, `libgcc-s1 (>= 4.3)`,
`libssl3t64 (>= 3.0.0)`, `bubblewrap`, `ca-certificates`, `bash`, `coreutils`.
Se recomienda `git` y `ripgrep`. Para el transporte se necesita SSH funcionando
en la Pi con reenvío TCP inverso permitido. No se necesita un servidor SSH en el
PC Windows: el PC abre la conexión hacia la Pi.

El paquete no configura SSH, no cambia el PATH, no añade servicios y no inicia
procesos. No se ha instalado nada en una Raspberry ni se ha conectado con ella.

## Inicio en Windows x86-64

Usar el host **0.163.0**, compatible con el App Server conservado. Mantener ambos
terminales abiertos. En PowerShell, dentro del ZIP de Windows extraído:

```powershell
.\Start-CodexArmhfCodeModeHost.ps1
```

Escucha exclusivamente en `grpc://127.0.0.1:46730`. El script verifica SHA-256 del
ZIP oficial antes de extraer el EXE; descarga desde la publicación oficial si no
dispone del ZIP adjunto. No utiliza claves API ni tokens ChatGPT.

En otro terminal, utilizando un alias de SSH **ya configurado y de confianza**:

```powershell
.\Start-CodexArmhfTunnel.ps1 -SshHost pi-zero
```

Equivale a:

```powershell
ssh.exe -N -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R 127.0.0.1:46731:127.0.0.1:46730 pi-zero
```

Usa claves o el agente SSH existente. Conserva la comprobación de la clave del
servidor y aborta si no puede crear el túnel. En la configuración del servidor
SSH de la Pi deben permitirse reenvíos remotos; por ejemplo, un administrador
puede restringirlos al puerto con `PermitListen 127.0.0.1:46731`. Nunca se debe
publicar el puerto gRPC en `0.0.0.0` ni habilitar `GatewayPorts yes` para este uso.

## Inicio de App Server ARMHF

Una vez instalado el `.deb`, el comando es:

```sh
codex-app-server-remote-v8 --listen stdio://
```

Es un servicio JSON-RPC, no una interfaz de chat para escribir a mano. El cliente
selecciona el transporte; para un cliente que utilice un socket Unix:

```sh
codex-app-server-remote-v8 --listen unix://
```

Con el tar extraído, los comandos equivalentes empiezan por
`./codex-app-server-remote-v8`. El lanzador encuentra el ejecutable que está a su
lado y termina con `exec`, sin mantener un intérprete residente adicional.

El endpoint predeterminado es `http://127.0.0.1:46731`. Se puede cambiar mediante
`CODEX_ARMHF_CODE_MODE_HOST` o un archivo de una sola línea
`~/.config/codex-armhf/code-mode-host.url`. Solo se aceptan endpoints de loopback
para usarlos con un túnel SSH. No se ejecuta el contenido del archivo.

El lanzador activa Code Mode y su host, desactiva el fallback a V8 local y el
precalentamiento, y establece por defecto:

```sh
TOKIO_WORKER_THREADS=1
MALLOC_ARENA_MAX=2
```

Respeta valores de estas dos variables que el usuario ya haya configurado.
No cambia las políticas de aprobación, sandbox, acceso a archivos o autenticación.
Si el host externo no responde, la ejecución de Code Mode falla; no migra V8 a ARMHF.

## ChatGPT Plus, sin clave API independiente

Se mantiene el proveedor OpenAI normal y el inicio de sesión oficial con ChatGPT.
La muestra `armhf-config.example.toml` **no configura un proveedor alternativo**.
El proveedor simulado solo existe en el banco de pruebas y no debe copiarse al
perfil de uso real.

Para un entorno sin navegador se puede autenticar el CLI conservado con:

```sh
codex login --device-auth
codex login status
```

El cliente App Server también dispone de `account/login/start` con tipo
`chatgptDeviceCode`. Los tokens se mantienen en el almacenamiento de autenticación
del usuario que ejecuta App Server; el host V8 no necesita recibirlos. No se deben
copiar tokens a los scripts ni al repositorio. Usar la misma cuenta de sistema y
`CODEX_HOME` para el login y el proceso remoto.

La cuenta debe tener acceso al modelo elegido. El soporte del protocolo
`code_mode_only` no concede acceso a GPT-6.1 Sol ni evita límites de Plus.

## Aplicación gráfica oficial para Windows

La documentación oficial indica que Remote SSH lanza `codex` mediante el shell de
login remoto. Se incluye `codex-remote-v8`, un shim opcional que conserva
`codex --version` y `codex login`, y redirige **`codex app-server ...` directo** al
App Server con V8 externo.

Para seleccionar ese shim, el usuario puede crear en su propio entorno remoto
un enlace llamado `codex` que apunte a `codex-remote-v8` y colocar su directorio
antes de `/usr/bin` en el PATH del shell de login. El paquete no lo hace
automáticamente. Si la app permite especificar el comando de App Server, se puede
seleccionar directamente `codex-app-server-remote-v8`.

**Límite importante:** no se dispone aquí de Windows ni de la app gráfica para
validar su arranque y actualización. Un cliente que descargue otro ejecutable,
use una ruta absoluta, arranque un daemon gestionado o reutilice un backend ya
existente puede omitir el shim. Este shim rechaza los subcomandos daemon/proxy;
no aparenta configurar un daemon que upstream arranca sin propagar
`--code-mode-host`. En ese caso hacen falta una opción de comando/argumentos en
el cliente o cambios documentados en el arranque del daemon. No se ha modificado
la aplicación gráfica ni se promete integración automática con todas sus versiones.

## Reutilizar la conexión SSH

En Linux se ha probado una única conexión con `ControlMaster`: el canal de App
Server y el reenvío inverso funcionan sobre el mismo transporte autenticado.
Win32 OpenSSH documenta `Client ControlMaster` como no soportado; el script de
Windows utiliza un túnel separado y persistente, compatible con la conexión de
la app. Reutilizar exactamente la conexión privada de la app requeriría que ella
añadiese el reenvío al establecerla o expusiera un mecanismo de control.

Un `RemoteForward` en el alias de `~/.ssh/config` podría añadirlo a la conexión
de la app si esa versión conserva los reenvíos. No se configura como valor por
defecto: las conexiones auxiliares de sondeo pueden intentar reservar el mismo
puerto, y algunos clientes limpian los reenvíos. No combinarlo con el túnel
separado que ya usa ese puerto.

## Memoria y compatibilidad

Prueba con cuatro hilos de conversación secuenciales y ocho herramientas reales,
sin inferencia remota, dentro de un contenedor limitado a 512 MiB sin swap:

| Configuración | Máximo RSS App Server + QEMU/PRoot | Host V8 x86-64 |
|---|---:|---:|
| Sin ajustes de hilos/arenas | 266,8 MiB | 24,8 MiB |
| Un trabajador Tokio y dos arenas malloc | 255,7 MiB | 25,1 MiB |
| Lanzador final con esos ajustes | 263,5 MiB | 24,8 MiB |

Son mediciones del emulador; no son una predicción exacta del consumo nativo de
la Pi. El RSS máximo de GNU time y la contabilidad del cgroup son métricas
distintas. La variación entre ejecuciones impide atribuir una reducción estable
a esos ajustes con esta muestra. Ninguna prueba provocó OOM. El informe incluye
ambas mediciones.

Recomendaciones: un solo App Server, pocas conversaciones cargadas, ninguna
compilación en la Pi, salidas de herramientas cortas, compacción temprana y
evitar herramientas que lancen procesos grandes. La muestra propone 2048 tokens
de salida y compacción a 24000 tokens: son ajustes de rendimiento, no límites
duros de memoria. No se garantiza que repositorios grandes, imágenes, numerosas
sesiones o payloads gRPC grandes quepan en 512 MB.

QEMU de usuario no permite validar seccomp/namespaces/Landlock ARM del kernel.
Las pruebas de herramientas usan el sandbox externo del contenedor sin red,
sin credenciales, mediante la política explícita `externalSandbox`. Eso **no se
añade a los lanzadores de producción**. El sandbox Linux normal permanece sin
alteraciones y requiere validación en hardware real antes de confiar en él.

No se incluyen voz ni otros auxiliares de la distribución completa. Los hooks,
MCP y comandos que dependan de programas no instalados en ARMHF seguirán
necesitando esos programas en la Pi. El host V8 externo es una máquina de
confianza: recibe JavaScript y los resultados de herramientas, que pueden
contener código y datos del proyecto.

Véase `INFORME-REMOTE-V8.md` para detalles técnicos, errores, evidencias y fuentes.
