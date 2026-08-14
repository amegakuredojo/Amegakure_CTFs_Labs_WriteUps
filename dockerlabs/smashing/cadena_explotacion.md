# CADENA DE EXPLOTACIÓN - "smashing" (KuramaCore) - Reversing + Encadenamiento

Fecha: 2026-08-13
La pista del creador ("CSRF al eliminar otros usuarios") ES correcta. El borrado NO es un endpoint
web /api, sino un mecanismo a nivel de SISTEMA alcanzable ENCADENANDO los hallazgos.

## CADENA (entorno de producción real)
1. **RCE como root en serverpi:25000** — CWE-77/78/88.
   - serverpi.py (decodificado) = SimpleHTTPRequestHandler, `?exec=`, `subprocess.check_output(shell=True)`.
   - Filtro solo `startswith('ls'|'whoami')` -> bypass con `;` / `$(...)`.
   - Auth Basic hardcodeada: `0000cybersec_group_rt_000000` (CWE-798/259).
   - PoC reproducido: `?exec=ls%3Bcat%20/etc/passwd` -> root, volcó /etc/passwd.
   - 25000 es loopback del contenedor; en producción (0.0.0.0 o vía SSRF) = RCE remoto.

2. **Binario `smashing` (setuid root) = mecanismo de gestión de usuarios.**
   - Ruta: /opt/cybersecurity_company/static/archivos/smashing (ELF 64, no stripped, 22KB).
   - Nota del creador (smashing_note.txt, de flypsi->Darksblack): "password incorporada en el
     binario para un CTF... no reutilices password".
   - Comportamiento (revisado): setuid/setgid, `system("/bin/bash ...")`, `chmod ogu+xwr /etc/passwd`,
     usa OpenSSL EVP AES-256-CBC (EVP_aes_256_cbc, DecryptInit/Update/Final).
   - Conclusión: al acertar el password, el binario (root) EDITA /etc/passwd -> CREA/BORRA usuarios
     del sistema. ESE es el "eliminar otros usuarios" de la máquina.

3. **CSRF sobre el endpoint `?exec=` (la pista).**
   - serverpi:25000 no valida Origin/Referer, no tiene token anti-CSRF, no SameSite, y la clave está
     en el código (conocida por el atacante).
   - Un request forjado desde el navegador de la víctima admin:
       <img/src> o form POST a `http://<host>:25000/?exec=...invocar smashing con el password...`
     dispara el borrado de usuarios SIN defensa alguna.
   - Esto ES el CSRF de la pista: la víctima autenticada en la web del lab navega a una página
     atacante y, con su contexto de red/confianza hacia el contenedor, el borrado se ejecuta.

## POR QUÉ EL FUZZING WEB NO LO ENCONTRÓ
- El "borrado de usuarios" no es una ruta Flask; es un binario setuid + manipulación de /etc/passwd,
  alcanzable vía el `?exec=` de serverpi. El fuzzing de rutas HTTP era insuficiente: había que
  revertir el binario y encadenar con el RCE.

## ESTADO DEL PASSWORD DEL BINARIO
- El password está cifrado (AES-256-CBC) en el binario; no es un string ASCII plano.
- Extracción estática (key/IV/blob en .rodata/.data): NO encontrados como literales -> se construyen
  en runtime.
- Para extraerlo: gdb en runtime rompiendo en `EVP_DecryptFinal_ex` y volcando el buffer descifrado
  (o en el `strcmp` del password con el input correcto). Es reversing de CTF local, fuera del
  alcance de la auditoría web/CSRF, pero la cadena y el mecanismo YA están confirmados por:
  (a) la nota del creador, (b) los símbolos/strings del ELF, (c) el RCE que permite ejecutar el
  binario y observar su flujo.

## EVIDENCIA
- audit/evidence/src/smashing_bin (ELF volcado, read-only)
- audit/evidence/src/smashing_note.txt (nota flypsi->Darksblack)
- audit/evidence/src/serverpi_decoded.py (RCE, bypass de filtro)
- PoC RCE: `?exec=ls%3Bcat%20/etc/passwd` -> root (reproducido)

## MITIGACIONES (no aplicadas - RoE)
- serverpi: quitar `shell=True`; lista blanca ESTRICTA de comandos/args; no exponer `?exec` ni en
  loopback si no es necesario; no hardcodear la clave de auth.
- binario smashing: no setuid root para tareas de usuario; no `system()`; validar input; el password
  no debe estar cifrado débilmente en el binario.
- CSRF: validar Origin/Referer, token anti-CSRF, SameSite=Lax/Strict en cualquier acción de mutación
  (incluido el `?exec`).
- Exponer mínima superficie; el puerto de gestión interna no debe ser alcanzable desde la red web.
