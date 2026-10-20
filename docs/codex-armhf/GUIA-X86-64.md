# Guía breve: paquetes x86-64 del proyecto

Los dos paquetes x86-64 alojan **V8/Code Mode fuera de la Raspberry**. No sustituyen la aplicación oficial de escritorio y no son los ejecutables ARMHF de la Pi. Tampoco son binarios x86 de 32 bits: ambos son **x86-64**.

| Si el equipo que alojará V8 es… | Descargar |
|---|---|
| Windows x86-64 | [codex-remote-v8-windows-x86_64.zip](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/codex-remote-v8-windows-x86_64.zip) |
| Linux x86-64 | [codex-remote-v8-linux-x86_64.tar.gz](https://github.com/Rodrigo14090/aeroforge/releases/download/codex-armhf-v0.163.0-remote-v8-20261020/codex-remote-v8-linux-x86_64.tar.gz) |

Se elige **uno** según el equipo anfitrión. Si se utilizará Windows, el paquete Linux no hace falta. Este último se entregó porque fue el anfitrión utilizado en Cloud y también permite desplegar V8 en un PC Linux.

## Windows

El ZIP contiene los scripts PowerShell y `official-host.zip`, que incluye el ejecutable oficial OpenAI `codex-code-mode-host-x86_64-pc-windows-msvc.exe` **0.163.0**. Su hash se verifica antes de extraerlo.

Después de extraer el paquete, en PowerShell:

```powershell
.\Start-CodexArmhfCodeModeHost.ps1
```

El script coloca el host en `%LOCALAPPDATA%\CodexArmhf\hosts\0.163.0` y lo inicia escuchando únicamente en `127.0.0.1:46730`. Si el ZIP oficial no está adjunto, lo descarga de la publicación oficial fijada. Mantener el terminal abierto.

En otro terminal, con un alias SSH previamente configurado y de confianza:

```powershell
.\Start-CodexArmhfTunnel.ps1 -SshHost pi-zero
```

El túnel dirige `127.0.0.1:46731` del equipo ARMHF a `127.0.0.1:46730` del PC. Requiere `ssh.exe`, autenticación por clave/agente y reenvíos remotos permitidos en el servidor SSH. Mantiene la verificación de la clave del servidor. No necesita un servidor SSH en Windows.

El host no requiere una clave API ni un token ChatGPT. La autenticación de los modelos pertenece al App Server remoto.

**Estado:** EXE oficial inspeccionado como PE32+ x86-64 y hash verificado; sintaxis de scripts comprobada. No se ha probado su ejecución nativa en Windows ni la GUI oficial.

## Linux

El tar contiene el host oficial Linux x86-64 renombrado como `codex-code-mode-host`, junto con documentación y licencia:

```sh
tar -xzf codex-remote-v8-linux-x86_64.tar.gz
./codex-code-mode-host --listen grpc://127.0.0.1:46730
```

Para acceder desde ARMHF, mantener abierto otro terminal con el túnel inverso:

```sh
ssh -N -T -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes \
  -R 127.0.0.1:46731:127.0.0.1:46730 pi-zero
```

**Estado:** este host sí ejecutó V8 y llamadas de herramientas reales en las pruebas Cloud.

## Qué falta en ambos casos

Iniciar V8 y el túnel no configura por sí solo Codex Desktop. El App Server ARMHF debe arrancar con `--code-mode-host http://127.0.0.1:46731`; el lanzador `codex-app-server-remote-v8` prepara esa selección.

La entrega actual tiene una incompatibilidad confirmada: el shim `codex-remote-v8` rechaza `app-server proxy`, utilizado por Desktop Remote SSH. Por tanto, **estos comandos no son una receta validada de integración completa con la aplicación oficial**.

Los hosts proceden de OpenAI 0.163.0 y se mantienen fijados para el servidor ARMHF utilizado. Si la aplicación oficial ya incluye un helper compatible, puede investigarse su reutilización; no se debe sustituirlo a ciegas por otra versión.

No publicar gRPC fuera de loopback. El equipo que aloja V8 debe ser de confianza, porque recibe JavaScript y resultados de herramientas. Cerrar el host o el túnel interrumpe ese canal; no se ha certificado cómo se cancelan todos los procesos ya iniciados en cada caso.

[Estado completo y límites del proyecto](ESTADO-DEL-PROYECTO.md) · [Publicación y checksums](https://github.com/Rodrigo14090/aeroforge/releases/tag/codex-armhf-v0.163.0-remote-v8-20261020)
