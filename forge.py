#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import getpass

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def sanitize_for_cnf(text_input):
    return text_input.replace('\n', ' ').replace('\r', ' ').replace('\"', '').replace("'", '')

def validar_pareja(key_path, req_path, password):
    print("\n[+] Verificando integridad criptográfica (Key/CSR Modulus Match)...")
    try:
        cmd_key_mod = f'openssl pkey -in "{key_path}" -passin stdin -noout -modulus'
        key_mod_proc = subprocess.run(cmd_key_mod, shell=True, input=password.encode(), check=True, capture_output=True, text=True)
        key_modulus = key_mod_proc.stdout.strip()

        cmd_req_mod = f'openssl req -in "{req_path}" -noout -modulus'
        req_mod_proc = subprocess.run(cmd_req_mod, shell=True, check=True, capture_output=True, text=True)
        req_modulus = req_mod_proc.stdout.strip()

        if key_modulus == req_modulus:
            print("[+] Verificación exitosa: La llave privada corresponde al requerimiento.")
        else:
            print("\n[!] ERROR CRÍTICO DE INTEGRIDAD: El módulo no coincide.", file=sys.stderr)
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error en validación: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def main():
    clear_screen()
    print("--- COATLICUE FORGE (v10.0): Forja Soberana de Firma Electrónica ---")

    tipo = input("¿Trámite para Persona Física (F) o Moral (M)?: ").strip().upper()
    nombre = sanitize_for_cnf(input("Nombre Completo o Razón Social: ").strip().upper())
    rfc = sanitize_for_cnf(input("RFC (12 o 13 caracteres): ").strip().upper())

    if tipo == 'F':
        id_secundario = rfc
    else:
        id_secundario = rfc

    email = sanitize_for_cnf(input("Correo electrónico: ").strip())

    password = getpass.getpass("Asigna la Contraseña de la llave privada: ")
    if not password: print("Error: Contraseña vacía."); sys.exit(1)
    confirm = getpass.getpass("Confirma la Contraseña: ")
    if password != confirm: print("Error: No coinciden."); sys.exit(1)

    temp_dir = '/dev/shm' if os.path.exists('/dev/shm') else tempfile.gettempdir()

    with tempfile.TemporaryDirectory(dir=temp_dir) as tmpdir:
        cnf_path, key_pem, req_pem = os.path.join(tmpdir, 'openssl.cnf'), os.path.join(tmpdir, 'temp.key'), os.path.join(tmpdir, 'temp.req')
        final_key, final_req = os.path.join(os.getcwd(), f'FIEL_{rfc}.key'), os.path.join(os.getcwd(), f'FIEL_{rfc}.req')

        cnf_content = f"""
[ req ]
distinguished_name = req_distinguished_name
prompt = no
[ req_distinguished_name ]
C = MX
ST = Estado de Mexico
L = Ecatepec de Morelos
O = {nombre}
CN = {nombre}
emailAddress = {email}
x500UniqueIdentifier = {rfc}
serialNumber = {id_secundario}
"""
        with open(cnf_path, 'w') as f: f.write(cnf_content)

        print("\n[+] Forjando identidad en RAM...")
        subprocess.run(f'openssl req -new -newkey rsa:2048 -nodes -keyout "{key_pem}" -out "{req_pem}" -config "{cnf_path}" ', shell=True, check=True, capture_output=True)

        print("[+] Cifrando llave y convirtiendo a DER...")
        subprocess.run(f'openssl pkcs8 -topk8 -inform PEM -outform DER -v2 aes-256-cbc -in "{key_pem}" -out "{final_key}" ', shell=True, input=password.encode(), check=True)
        os.chmod(final_key, 0o600)

        print("[+] Generando requerimiento (.req) en DER...")
        subprocess.run(f'openssl req -inform PEM -outform DER -in "{req_pem}" -out "{final_req}" ', shell=True, check=True)

        validar_pareja(final_key, final_req, password)

        os.sync()

        print(f"\n¡ÉXITO! Archivos listos:\n- {final_key}\n- {final_req}")


if __name__ == "__main__":
    main()