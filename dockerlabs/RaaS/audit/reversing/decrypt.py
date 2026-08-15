#!/usr/bin/env python3
"""
Descifrador del RaaS (DockerLabs) - AES-256-CBC / PKCS7.
Key e IV extraidos por reversing ESTATICO del binario 'encript2'
(NUNCA se ejecuto el binario: reversing solo con objdump/strings/readelf).

Reversing:
  recon():  KEY = "y0qpfjxbd79047929ew0omqad3f4gscl"  (32 bytes)
  main():   IV  = "1234567890123456"                   (16 bytes)
  EVP_aes_256_cbc + EVP_EncryptInit_ex(ctx, cipher, NULL, key, iv)
  -> CBC, PKCS7 padding por defecto de OpenSSL.
  Cifrado IN-PLACE: ciphertext sin IV prepended, mismo IV reutilizado.
"""
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
import sys

KEY = b"y0qpfjxbd79047929ew0omqad3f4gscl"   # 32 bytes -> AES-256
IV  = b"1234567890123456"                    # 16 bytes

def decrypt(ct: bytes) -> bytes:
    assert len(KEY) == 32, "KEY must be 32 bytes for AES-256"
    assert len(IV) == 16, "IV must be 16 bytes"
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV))
    dec = cipher.decryptor()
    pt = dec.update(ct) + dec.finalize()
    # Quitar padding PKCS7
    unpadder = PKCS7(128).unpadder()
    pt = unpadder.update(pt) + unpadder.finalize()
    return pt

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "private.enc"
    with open(src, "rb") as f:
        ct = f.read()
    pt = decrypt(ct)
    print(f"[+] Cifrado   : {src} ({len(ct)} bytes)")
    print(f"[+] Key(AES256): {KEY.decode()}")
    print(f"[+] IV(CBC)    : {IV.decode()}")
    print(f"[+] Descifrado : {pt!r}")
    try:
        print("[+] Texto      : " + pt.decode("utf-8"))
    except UnicodeDecodeError:
        print("[!] No es UTF-8 (¿binario?)")
