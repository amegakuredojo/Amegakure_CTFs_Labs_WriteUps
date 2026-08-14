# INTELIGENCIA CONSOLIDADA - Auditoría CSRF "smashing" (KuramaCore)

Fecha: 2026-08-13
Target: 172.17.0.2:80 (Docker bridge) - Flask/Werkzeug 2.2.2, vhost cybersec.dl
Red previa: host 127.0.0.1:631 = CUPS real (FUERA SCOPE); 172.17.0.2 es el lab.

## 1. CONTROLES ANTI-CSRF OBSERVADOS (evidencia, sin ejecutar borrado)
- `POST /api/login` existe (Allow: POST, OPTIONS). 401 sin credenciales.
- NO emite `Set-Cookie`/`SameSite` en ninguna respuesta (login incluido).
- NO configura cabeceras `Access-Control-*` (CORS ausente).
- NO valida `Origin`/`Referer`: un POST con `Origin: http://evil.attacker` y
  `Referer` externo llega hasta la validación de credenciales (401), no 403.
=> Perfil de app SIN defensas CSRF (coincide con patrón vulnerable del RAG).

## 2. CONTRASTE CON RAG LOCAL (AmegakureDojo_RAG)
- MITRE CAPEC-493 (Cross Site Request Forgery): el atacante induce un request
  forjado que se ejecuta con los privilegios de la sesión de la víctima (confía
  implícitamente en la cookie de sesión).
- EXPLOITDB patron (VWD-CMS, CVE-2018-770x): "remove any Role especially Admins
  Role" vía request sin token ni validación de origen -> `?delete=yes&role=X` o
  formulario forjado. MISMO patrón que el objetivo de este lab ("eliminar otros
  usuarios").
- Pentesting_KB / Broken_Access_Control / Session-Hijacking.md: mitigantes CSRF =
  cookie `HttpOnly`+`SameSite`, token anti-CSRF (synchronizer/double-submit) y
  validación de `Origin`/`Referer`. NINGUNO presente en el lab (ver sección 1).
=> CONCLUSIÓN DE PATRÓN: el lab replica exactamente la arquitectura vulnerable que
   el RAG documenta. Alta probabilidad de CSRF explotable en el endpoint de borrado
   de usuarios, sujeto a que el endpoint sea alcanzable y se disponga de una sesión
   de víctima para el PoC.

## 3. FUZZING (ffuf + SecLists, rate 13 req/seg)
Listas ejecutadas (Host: cybersec.dl):
- api/api-endpoints.txt (295) -> 0 no-404 (todo 404)
- api/actions.txt (224) -> 0 no-404
- common.txt (parcial, 1473/4751, maxtime) -> 0 no-404 en lo evaluado
- dirigido es/ing (41) -> 0 no-404
- raft-large-directories-lowercase.txt CON Host (56162) -> EN CURSO
- raft-large-directories-lowercase.txt SIN Host (56162) -> EN CURSO
Hipótesis: el panel de gestión vive en una ruta de página no cubierta aún, O está
tras autenticación (el login 401 sugiere sesión requerida). El raft debe revelar
la ruta; si solo da 404/302, el endpoint de borrado requiere sesión autenticada.

## 4. BLOQUEO RESTANTE (RoE)
Para PoC CSRF completo de "eliminar usuarios" falta:
  (a) ruta exacta del endpoint de borrado (en vuelo vía raft),
  (b) sesión de víctima (cookie) para demostrar que el request forjado la aprovecha.
Sin leer el código fuente (RoE) ni write-ups (RoE), y sin credenciales por defecto
(accesibles), el PoC requiere o bien que el raft revele una ruta alcanzable sin
auth, o bien credencial/víctima del enunciado de la máquina.
