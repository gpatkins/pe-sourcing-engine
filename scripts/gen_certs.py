import os
import subprocess

def generate_self_signed_cert():
    cert_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nginx", "certs")
    os.makedirs(cert_dir, exist_ok=True)

    key_path = os.path.join(cert_dir, "selfsigned.key")
    crt_path = os.path.join(cert_dir, "selfsigned.crt")

    if os.path.exists(key_path) and os.path.exists(crt_path):
        print("✅ SSL Certificates already exist.")
        return

    print("🔐 Generating Self-Signed SSL Certificates...")

    # OpenSSL command to generate a 10-year cert
    cmd = [
        "openssl", "req", "-x509", "-nodes", "-days", "3650",
        "-newkey", "rsa:2048",
        "-keyout", key_path,
        "-out", crt_path,
        "-subj", "/C=US/ST=State/L=City/O=PE-Engine/CN=pe-sourcing"
    ]

    try:
        subprocess.check_call(cmd)
        print(f"✅ Certificates created at: {cert_dir}")
    except FileNotFoundError:
        print("❌ Error: 'openssl' command not found. Please install it (sudo apt install openssl or sudo dnf install openssl).")
    except Exception as e:
        print(f"❌ Error generating certs: {e}")

if __name__ == "__main__":
    generate_self_signed_cert()
