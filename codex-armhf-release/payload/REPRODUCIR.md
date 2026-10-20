# Reproducir en un anfitrión Cloud x86_64

No ejecutar la compilación en la Raspberry. El paquete de evidencias contiene el parche, los scripts y los registros; el código base se obtiene de GitHub.

Crear un directorio de trabajo, extraer allí las evidencias y clonar:

```sh
git clone --depth 1 --branch rust-v0.163.0 https://github.com/openai/codex.git codex
git -C codex switch -c work/armhf-rust-v0.163.0
git -C codex apply ../codex-armhf-source.patch
mkdir -p logs artifacts
```

El commit base debe ser `83086188ae0614bd882818ff1aa23f3194962012`. El parche incluye las dos dependencias modificadas y el lockfile actualizado. No hay que actualizar dependencias externas.

Se utilizó Docker con `debian:trixie-slim`, sin privilegios y sin KVM. En Codex Cloud, conservar la configuración de proxy del daemon y el cliente y montar el bundle CA del anfitrión de solo lectura:

```sh
bash docker-local.sh run -d --name codex-armhf-builder \
  --memory 7g --cpus 2 \
  --mount "type=bind,src=$PWD,dst=/work" \
  --mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/cloud-ca-bundle.pem,readonly \
  -e SSL_CERT_FILE=/run/cloud-ca-bundle.pem \
  -e CURL_CA_BUNDLE=/run/cloud-ca-bundle.pem \
  -e CARGO_HTTP_CAINFO=/run/cloud-ca-bundle.pem \
  -e GIT_SSL_CAINFO=/run/cloud-ca-bundle.pem \
  -e CARGO_HOME=/work/toolchain/cargo \
  -e RUSTUP_HOME=/work/toolchain/rustup \
  debian:trixie-slim sleep infinity

bash docker-local.sh exec codex-armhf-builder bash /work/setup-builder.sh
bash docker-local.sh exec codex-armhf-builder bash /work/build-armhf.sh
```

`build-armhf.sh` usa `--locked` por defecto. `CODEX_ARMHF_UPDATE_LOCK=1` fue necesario para resolver la etiqueta original antes de generar el parche; no debería ser necesario con el parche completo. Los inventarios de herramientas y paquetes del trabajo original están en `logs/`. Los repositorios APT pueden cambiar con el tiempo; no se promete reproducción bit a bit.

La compilación entregada usó GNU ld. Como alternativa para un build nuevo, se probó que LLD enlaza CLI mucho más rápidamente a partir de los mismos objetos. Para elegirlo desde el principio:

```sh
bash docker-local.sh exec \
  -e 'CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_RUSTFLAGS=-C link-arg=-fuse-ld=lld' \
  codex-armhf-builder bash /work/build-armhf.sh
```

Esa variante cambia el enlazador de la reproducción; los paquetes entregados contienen los ejecutables del intento completo de Cargo con GNU. El script `link-cli-with-lld.py` conserva el experimento sobre un enlace en curso; no es necesario para el procedimiento normal.

Después de compilar, copiar los dos archivos de `codex/codex-rs/target/armv7-unknown-linux-gnueabihf/release/` a `validated-binaries/`, conservando sus nombres y permisos de ejecución. Ejecutar solo cuando no queden compiladores activos:

```sh
bash docker-local.sh update --memory 512m --memory-swap 512m codex-armhf-builder
bash docker-local.sh exec codex-armhf-builder python3 /work/verify-armhf.py
bash docker-local.sh exec codex-armhf-builder python3 /work/mock-turn-armhf.py
```

La prueba de turno usa un servidor HTTP **local simulado**, sin API ni credenciales reales. Selecciona metadatos incorporados de `gpt-5.5`, porque los modelos `code_mode_only` requieren el auxiliar V8 ausente. No prueba herramientas sandboxed, Code Mode ni voz.

Solo si las verificaciones pasan:

```sh
bash docker-local.sh update --memory 7g --memory-swap 7g codex-armhf-builder
bash docker-local.sh exec codex-armhf-builder python3 /work/package-armhf.py
bash docker-local.sh exec codex-armhf-builder python3 /work/verify-packages.py
```

Los scripts de empaquetado esperan directorios de staging nuevos para evitar reutilizar resultados antiguos. No instalan el `.deb` ni contactan con una Raspberry. Las dependencias Debian se calculan de los ELF ARMHF y se vuelven a verificar los ejecutables extraídos de ambos formatos.

Los 14 tests del backend seccompiler se ejecutaron en una copia independiente del crate parcheado con un `[workspace]` vacío, `CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_LINKER=arm-linux-gnueabihf-gcc` y `CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_RUNNER='qemu-arm -cpu cortex-a7 -L /'`, mediante `cargo +1.95.0 test --target armv7-unknown-linux-gnueabihf --lib backend:: -- --test-threads=1`. Esta separación evita compilar los tests del workspace completo.
