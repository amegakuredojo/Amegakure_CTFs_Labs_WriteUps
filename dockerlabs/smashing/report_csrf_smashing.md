# REPORTE FORENSE - Auditoría "smashing" (KuramaCore)

Fecha: 2026-08-13
Target: 172.17.0.2:80 (Docker bridge) — Flask/Werkzeug 2.2.2, vhost `cybersec.dl`
Metodología: black-box (recon/fuzzing ffuf+SecLists) + lectura forense del código (RoE modificada:
lectura permitida, modificación/re-deploy prohibidos). Sigilo 13 req/seg.

## RESUMEN EJECUTIVO
La pista del creador ("CSRF al eliminar otros usuarios") NO se corresponde con esta versión del
laboratorio. Tras lectura forense completa de `app.py`, `serverpi.py` (ofuscado, decodificado) y
las 3 plantillas HTML, **NO EXISTE ningún endpoint ni formulario de eliminación/borrado de usuarios**.
La hipótesis CSRF de borrado de usuarios se CIERRA como NO APLICABLE a esta máquina.

Sin embargo, la auditoría encontró hallazgos de seguridad REALES y graves (más relevantes que la
pista original):

## HALLAZGOS

### H1 — Credenciales por defecto hardcodeadas y válidas (CRÍTICO)
- Evidencia: `app.py:38-41` define `users = {"admin":"undertaker", "user":"user123"}`.
- Verificación en vivo (1 req, sigilo): `POST /api/login` con `admin:undertaker` y `user:user123`
  devuelve 200 "Login successful".
- Impacto: acceso autenticado al servicio sin fuerza bruta.

### H2 — Ausencia total de defensas anti-CSRF (ALTO, coherente con pista)
- `app.py:53-73` `/api/login`: compara credenciales en diccionario plano.
- NO emite `Set-Cookie`/`SameSite`, NO hay token anti-CSRF, NO valida `Origin`/`Referer`,
  NO configura CORS (verificado black-box: POST con `Origin: evil.attacker` llega a validación).
- Impacto: cualquier endpoint con estado de mutación sería vulnerable a CSRF. En esta versión no
  hay endpoint de mutación alcanzable, pero el patrón es vulnerable por diseño.

### H3 — serverpi.py: exec remoto filtrado + auth Basic hardcodeada (ALTO)
- `serverpi.py` (decodificado) = `SimpleHTTPRequestHandler` en 127.0.0.1:25000.
- Auth Basic con clave hardcodeada `AUTH_KEY_BASE64` → decodificada: `0000cybersec_group_rt_000000`.
- Endpoint `?exec=` usa `subprocess.check_output(command, shell=True)` (línea ~55), filtrado solo a
  `ls`/`whoami` vía `allowed_commands`. El `shell=True` + filtro por prefijo es frágil
  (p.ej. `ls; <cmd>` o `ls$(cmd)` podría bypassear el inicio-con-prefijo).
- Impacto: si el atacante alcanza 25000 (loopback interno del contenedor), tiene RCE limitado;
  la clave está expuesta en el código.

### H4 — Flask en modo debug=True (ALTO)
- `app.py:112` `app.run(host='0.0.0.0', port=80, debug=True)`.
- Impacto: Werkzeug debugger expuesto en 0.0.0.0:80 → RCE si se conoce el PIN del debugger
  (el PIN es derivable de info del host). Expuesto en la red del bridge Docker.

### H5 — Redirección por Host header (MEDIO / recon)
- `app.py:17-20` `before_request` redirige a `http://cybersec.dl` si el Host no es
  cybersec.dl / 0internal_down.cybersec.dl / mail.cybersec.dl. Fuzz sin Host → 302.
  No es vuln por sí mismo, pero habilita el requisito de Host para alcanzar rutas.

## RUTAS CONFIRMADAS (app.py, puerto 80)
- `/` (index.html, vitrina)
- `/api/login` [POST] — credenciales planas, sin sesión
- `/api/1passwsecu0` [GET] — genera "contraseña segura" de ejemplo (decoy)
- subdominio `0internal_down.cybersec.dl` → bin.html + `/download/<file>`
- subdominio `mail.cybersec.dl` → mail.html (login ficticio)
- serverpi (25000, loopback): `GET /?exec=<ls|whoami>` con Auth Basic

## CONTRASTE CON RAG LOCAL
- MITRE CAPEC-493 (CSRF) y exploit VWD-CMS "remove Admins Role" documentan el patrón de borrado sin
  token/origen. El lab replica la AUSENCIA de defensas (H2) pero no implementa el endpoint de borrado.
- Pentesting_KB / Session-Hijacking.md: mitigantes = SameSite+HttpOnly, token anti-CSRF,
  validación Origin/Referer. NINGUNO presente (H2).
- El RAG no contiene write-up de esta máquina concreta (no se usó; RoE cumplida).

## ACCIONES DE MITIGACIÓN (recomendadas, NO aplicadas — RoE prohíbe modificar el lab)
1. H1: eliminar credenciales hardcodeadas; usar store externo + hash (bcrypt) + rate-limit.
2. H2: añadir token anti-CSRF (synchronizer/double-submit) + cookie `SameSite=Lax/Strict`
   + validación de `Origin`/`Referer` en acciones de mutación.
3. H3: quitar `shell=True`; usar lista blanca estricta de comandos; no hardcodear claves;
   no exponer `?exec` ni en loopback si no es necesario.
4. H4: `debug=False` en producción; no exponer Werkzeug debugger.
5. H5: validar Host contra lista explícita (ya lo hace, pero sin impacto de seguridad real).

## ARCHIVOS DE EVIDENCIA (audit/)
- evidence/src/app.py, serverpi.py, serverpi_decoded.py, index.html, bin.html, mail.html
- ffuf/: api_endpoints.json, actions.json, dirigido.json, dirigido2.json, params_dirigido.json
- intel_consolidada.md

## NOTA DE CUMPLIMIENTO RoE
- No se modificó el contenedor ni su configuración (solo `cat`/`docker exec` read-only y `grep`).
- No se re-desplegó con configuraciones no previstas.
- `docker diff` del contenedor sin cambios (no se escribió dentro del lab).
- No se usaron write-ups externos.
