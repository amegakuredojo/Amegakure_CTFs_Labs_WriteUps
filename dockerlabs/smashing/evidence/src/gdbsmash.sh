#!/bin/sh
# Extraccion runtime del password del binario smashing (read-only, no modifica lab)
# Rompe en obtener_texto_descifrado y desencriptar; vuelca el plaintext retornado.
printf 'test\nsi\n' | gdb -q -batch \
  -ex 'set pagination off' \
  -ex 'break obtener_texto_descifrado' \
  -ex 'break desencriptar' \
  -ex 'run' \
  -ex 'printf "RET1:\\n"' -ex 'x/s $rax' \
  -ex 'continue' \
  -ex 'printf "RET2:\\n"' -ex 'x/s $rax' \
  /opt/cybersecurity_company/static/archivos/smashing
