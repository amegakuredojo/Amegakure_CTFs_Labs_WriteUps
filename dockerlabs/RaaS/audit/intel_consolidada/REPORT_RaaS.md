# AUDITORÍA FORENSE — Máquina RaaS (DockerLabs / AmegakureDojo)

**Objetivo:** 172.17.0.2 (docker bridge)  |  Contenedor: `raas` (Ubuntu 24.04 SMB+SSH)
**Fecha:** 2026-08-14  |  Agente: KuramaCore  |  Perfil RoE:blackbox + restricción HARD "no ejecutar binarios" (análisis de malware)

## RoE aplicada
- ✅ NO se modificó el contenedor ni su configuración.
- ✅ NO se ejecutó NEVER el binario `encript2`/`pokemongo` (malware). Reversing 100% estático (strings/objdump/readelf) + descifrado con script propio (cryptography/OpenSSL).
- ✅ Rate-limit respetado (pocas decenas de reqs, recon pasivo).
- ✅ Escalada documentada SOLO como vector teórico; NO explotada ni modificada.

## Fase 1 — Recon (nmap)
Host up. Puertos:
- 22/tcp  open  ssh   (OpenSSH 9.6p1 Ubuntu)
- 139/tcp open  netbios-ssn (Samba)
- 445/tcp open  microsoft-ds (Samba)  [signing enabled, not required; dialects SMB2/3]
Evidencia: `audit/recon/01_nmap_smb.txt`, `06_ssh_authmethods.txt`

## Fase 2 — Enumeración SMB (null session, read-only)
- `smbclient -L //172.17.0.2 -N` → shares: `print$`, **`ransomware`**, `IPC$`. Equipo: "dockerlabs server (Samba, Ubuntu)".
- `rpcclient -U "" -N -c enumdomusers` → usuarios sembrados:
  - patricio (RID 1000), bob (RID 1001), calamardo (RID 1002).
- `netshareenumall` → `ransomware` = path `C:\srv\ransom`.
- El share `ransomware` deniega null session (tree connect NT_STATUS_ACCESS_DENIED).
Evidencia: `audit/recon/02_smb_shares.txt`, `03_rpc_users.txt`, `07_netshareenum.txt`

## Fase 3/4 — Acceso a los artefactos víctima (read-only)
Del OCI image entregado (`raas.tar` = docker-save del lab) se extrajo copia forense en `./image/`
(sin tocar el contenedor vivo). Hallazgos en `/srv/ransom`:
- `smb.conf`: `[ransomware]` → `/srv/ransom`, `valid users = patricio, calamardo` (bob NO tiene acceso al share), `read only = yes`.
- `nota.txt`: patricio analizó el ransomware que "bob ejecutó"; no logró descifrar; comparte el binario para que calamardo ayude. Urge descifrar `private.txt`.
- `encript2` = ELF64 PIE, **NOT stripped**, linkado a OpenSSL EVP (AES-256-CBC). Mismo BuildID que `pokemongo` (es el mismo binario).
- `private.txt` = 48 bytes (múltiplo de 16 → AES-CBC bloque 16B).

## Fase 5 — Reversing estático (SIN ejecutar el binario)
Funciones visibles: `main`, `recon`, `encrypt`, `encrypt_files_in_directory`, `file_exists`, `handleErrors`.

- `main`:
  - `gethostname` + `strcmp(host, "dockerlabs")` → si no coincide, aborta (el gating es el hostname).
  - Verifica existencia de dos archivos (`/opt/ak.pk1` y `/bin/12bn`) vía `file_exists`; si faltan, aborta.
  - Construye IV de 16 bytes = `"12345678" + "90123456"` = **`1234567890123456`**.
  - Llama `encrypt_files_in_directory(buf, key, "/opt/ak.pk1"... )` — cifra in-place el contenido de archivos.
- `recon`:
  - Construye la KEY de 32 bytes concatenando literales:
    `"y0qp" + "fjxbd" + "79047" + "929ew" + "0omqad3f" + "4gscl"`
    = **`y0qpfjxbd79047929ew0omqad3f4gscl`**  (32 B → AES-256).
- `encrypt`:
  - `EVP_CIPHER_CTX_new` → `EVP_aes_256_cbc` → `EVP_EncryptInit_ex(ctx, cipher, NULL, KEY, IV)`
  - `EVP_EncryptUpdate` + `EVP_EncryptFinal_ex` → **CBC, PKCS7 padding por defecto de OpenSSL**.
  - Cifrado IN-PLACE: el ciphertext reescribe el archivo; IV fijo (NO se antepone al ciphertext).

KEY e IV extraídos íntegramente del código estático → ninguna ejecución necesaria.

## Fase 6 — Descifrado (script propio, NO malware)
`audit/reversing/decrypt.py` (cryptography: AES-256-CBC + PKCS7):
```
[+] Cifrado   : private.enc (48 bytes)
[+] Key(AES256): y0qpfjxbd79047929ew0omqad3f4gscl
[+] IV(CBC)    : 1234567890123456
[+] Descifrado : b'las credenciales ssh son: bob:56000nmqpL\n'
```
**PLAINTEXT:** `las credenciales ssh son: bob:56000nmqpL`

## Fase 6b — Pivote de acceso (validado, read-only)
- SSH como `bob:56000nmqpL` → **ACCESO CONFIRMADO**: `uid=1002(bob) gid=1002(bob) groups=1002(bob),100(users)`.
- `bob` ve `/srv/ransom` (nota.txt, pokemongo, private.txt).
Evidencia: `audit/recon/08_ssh_bob_access.txt`

## Vector de escalada a root / "liberación" (TEÓRICO — NO ejecutado, RoE prohibe modificar)
`bob` puede: `(calamardo) NOPASSWD: /bin/node`.
- Cadena: `sudo -u calamardo /bin/node -e '<JS reverse-shell / spawn("/bin/sh")>'` → shell como **calamardo**.
- `calamardo` SÍ está en `valid users` del share `ransomware` (patricio, calamardo) → acceso al share.
- `core.63123` (1.1 MB, home de bob) = core dump del binario caído → puede contener KEY/IV en memoria (evidencia forense adicional, no necesaria: ya tenemos key/IV por reversing).
- Teoría del lab: "consiguiendo root se puede cambiar la contraseña/clave que cifró el sistema y liberarlo del RaaS". La ruta sería node→calamardo→(escalada local a root)→revertir/descifrar. **No se realizó** por mandato RoE (no modificar el contenedor). La información secuestrada YA fue descifrada exitosamente con la clave recuperada por reversing.

## Conclusión
El lab se resuelve en la fase de **enumeración SMB + reversing de binario AES-256-CBC** (como indicaba la pista). Se recuperó la clave simétrica por análisis estático del malware (sin ejecutarlo) y se descifró `private.txt`, obteniendo credenciales SSH que validan el pivote de acceso. Todo el trabajo fue read-only / no destructivo, cumpliendo la restricción estricta de no ejecución de binarios y no modificación del contenedor.

## Artefactos / evidencia
- `audit/recon/01..09_*.txt` — nmap, smb, rpc, ssh.
- `audit/reversing/ransomware_bin` — copia del ELF (NO ejecutado).
- `audit/reversing/private.enc` — ciphertext original (48 B).
- `audit/reversing/decrypt.py` — descifrador propio (AES-256-CBC + PKCS7).
- `audit/reversing/nota.txt` — nota de la víctima.
- `image/` — extracción forense del OCI image (capas), sin tocar el contenedor vivo.
- `audit/intel_consolidada/REPORT_RaaS.md` — este reporte.
