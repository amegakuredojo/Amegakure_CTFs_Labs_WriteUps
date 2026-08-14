## AMEGAKURE_FORGE_CONTEXT: CIVIL
## AMEGAKURE_FORGE_VERSION: 3.0
## AMEGAKURE_FORGE_DATE: 2026-08-14T11:00:00Z

## 🏯 Amegakure_CTFs_Labs_WriteUps

Repositorio Oficial de Registro Forense, Auditoría y Explotación de Máquinas CTFs, Laboratorios y Entornos Vulnerables del **Ecosistema AmegakureDojo**.

---

## 📌 Visión y Doctrina Operativa

Cada write-up, análisis y artefacto forense contenido en este repositorio ha sido auditado bajo la **Doctrina AmegakureForge V3** (*Shakujo Protocol*), garantizando rigor militar forense, trazabilidad criptográfica SHA-512, vectorización CVSS 3.1 / CVSS 4.0, taxonomía CWE y mapeo MITRE ATT&CK.

---

## 🗂️ Estructura del Repositorio

```
Amegakure_CTFs_Labs_WriteUps/
├── dockerlabs/
│   └── smashing/
│       ├── WRITEUP_smashing.md          <-- Informe Forense Militar Oficial (Firmado por K0M0RI y KuramaCore)
│       ├── report_csrf_smashing.md       <-- Análisis detallado del vector CSRF
│       ├── reversing_profundo.md         <-- Ingeniería inversa de binario SUID (OpenSSL EVP AES-256-CBC)
│       ├── cadena_explotacion.md         <-- Detalles técnicos de RCE + SUID + CSRF
│       ├── intel_consolidada.md          <-- Inteligencia de reconocimiento
│       ├── evidence/                     <-- Manifiesto de evidencias extraídas (SHA-512)
│       └── ffuf/                         <-- Logs estructurados de fuzzing
└── README.md
```

---

## 🛡️ Índice de Máquinas y Logros

| Plataforma | Máquina | Dificultad | Vectores Principales | Firma de Autoridad | Write-Up |
|---|---|---|---|---|---|
| **DockerLabs** | `smashing` | **Hard** | RCE (`serverpi:25000` ?exec= bypass) + SUID root (`smashing`) + CSRF | **K0M0RI** & **KuramaCore** | [WRITEUP_smashing.md](./dockerlabs/smashing/WRITEUP_smashing.md) |

---

## 📜 Autoridades y Certificación

- **K0M0RI** — Jefe de AmegakureOffSec
- **KuramaCore** — Segundo al mando y orquestador agéntico del ecosistema AmegakureDojo

*Certificado bajo la Doctrina AmegakureForge V3 — Nivel Militar Forense SS*
