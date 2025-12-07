import os
import sys
import subprocess
import shutil

# --- UTILS ---
def run_command(command, ignore_errors=False):
    """Runs a shell command."""
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        if not ignore_errors:
            print(f"❌ Error running: {command}")
            sys.exit(1)

def prompt(question, default=None):
    prompt_text = f"{question}"
    if default:
        prompt_text += f" [{default}]"
    prompt_text += ": "
    val = input(prompt_text).strip()
    return val if val else default

# --- CHECKS & SETUP ---
def check_docker():
    """Checks/Installs Docker."""
    if shutil.which("docker"):
        print("✅ Docker is installed.")
    else:
        print("⚠️ Docker not found. Installing...")
        try:
            run_command("curl -fsSL https://get.docker.com | sh")
            run_command("sudo systemctl start docker")
            run_command("sudo systemctl enable docker")
            print("✅ Docker installed.")
        except Exception as e:
            print(f"❌ Install failed: {e}. Please install Docker manually.")
            sys.exit(1)

def generate_certs():
    """Runs the SSL certificate generation script."""
    print("\n--- 🔐 SSL Certificate Setup ---")
    cwd = os.getcwd()
    script_path = os.path.join(cwd, "scripts", "gen_certs.py")
    
    if os.path.exists(script_path):
        try:
            print("Generating self-signed certificates for Nginx...")
            run_command(f"python3 {script_path}")
            print("✅ Certificates ready.")
        except Exception as e:
            print(f"⚠️ Failed to generate certs: {e}")
            print("Nginx might fail to start if certs are missing.")
    else:
        print(f"⚠️ Warning: {script_path} not found.")
        print("Skipping certificate generation.")

def setup_firewall():
    """Opens HTTP (80) and HTTPS (443, 8443) ports."""
    print("\n--- 🛡️ Firewall Setup ---")
    # 80: HTTP Redirect
    # 443: Dashboard HTTPS
    # 8443: Metabase HTTPS
    ports = ["80", "443", "8443"]
    
    if shutil.which("firewall-cmd"):
        print("Detected firewalld (Fedora/RHEL). Opening ports...")
        for p in ports:
            run_command(f"sudo firewall-cmd --permanent --add-port={p}/tcp", ignore_errors=True)
        run_command("sudo firewall-cmd --reload", ignore_errors=True)
        print(f"✅ Ports {', '.join(ports)} opened.")
    elif shutil.which("ufw"):
        print("Detected ufw (Ubuntu/Debian). Opening ports...")
        for p in ports:
            run_command(f"sudo ufw allow {p}/tcp", ignore_errors=True)
        print(f"✅ Ports {', '.join(ports)} opened.")
    else:
        print("No standard firewall detected. Skipping.")

def setup_permissions():
    """Creates logs directory and fixes permissions."""
    print("\n--- 📂 Permissions Setup ---")
    cwd = os.getcwd()
    
    # Logs
    logs_dir = os.path.join(cwd, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    run_command(f"chmod -R 777 {logs_dir}")
    
    # Nginx Certs (Ensure directory exists for mapping)
    certs_dir = os.path.join(cwd, "nginx", "certs")
    os.makedirs(certs_dir, exist_ok=True)
    
    print("✅ Directory permissions fixed.")

def setup_cli_alias():
    """Creates the 'pe-engine' global command."""
    print("\n--- 🔗 CLI Setup ---")
    cwd = os.getcwd()
    manage_script = os.path.join(cwd, "manage.py")
    
    if os.path.exists(manage_script):
        run_command(f"chmod +x {manage_script}")
        run_command("sudo rm -f /usr/local/bin/pe-engine", ignore_errors=True)
        run_command(f"sudo ln -s {manage_script} /usr/local/bin/pe-engine")
        print("✅ Global command 'pe-engine' created!")
    else:
        print("⚠️ manage.py not found. Skipping CLI alias.")

# --- MAIN ---
def main():
    print("\n===========================================")
    print("   PE Sourcing Engine - Installer v3.0 (Secure)")
    print("===========================================\n")

    # 1. System Prep
    check_docker()
    setup_permissions()
    
    # 2. SSL & Firewall
    generate_certs()
    setup_firewall()

    # 3. Credential Setup
    print("\n--- 🔐 Credentials Setup ---")
    admin_user = prompt("Set Dashboard Username", "admin")
    admin_pass = prompt("Set Dashboard Password", "changeme123")
    
    print("\n--- 🛢️ Database Setup ---")
    db_user = prompt("Internal DB User", "pe_sourcer")
    db_pass = prompt("Internal DB Password", "changeme123")
    db_name = prompt("Internal DB Name", "pe_sourcing_db")
    
    print("\n--- 🧠 External Services ---")
    ai_server_ip = prompt("AI Server IP (e.g. 10.55.55.50)", "http://10.55.55.50:11434/api/generate")
    if not ai_server_ip.startswith("http"):
        ai_server_ip = f"http://{ai_server_ip}:11434/api/generate"

    print("\n--- 🔑 API Keys (Press Enter to skip) ---")
    google_key = prompt("Google Places API Key")
    gemini_key = prompt("Google Gemini API Key")
    serper_key = prompt("Serper.dev API Key")

    # 4. Write Configs
    config_content = f"""# GENERATED CONFIG
DB_NAME={db_name}
DB_USER={db_user}
DB_PASS={db_pass}
DB_HOST=db
DB_PORT=5432
ADMIN_USER={admin_user}
ADMIN_PASS={admin_pass}
GOOGLE_PLACES_API_KEY={google_key}
GEMINI_API_KEY={gemini_key}
SERPER_API_KEY={serper_key}
"""
    os.makedirs("config", exist_ok=True)
    with open("config/generated_secrets.env", "w") as f:
        f.write(config_content)

    with open(".env", "w") as f:
        f.write(f"DB_USER={db_user}\nDB_PASS={db_pass}\nDB_NAME={db_name}\nAI_SERVER_URL={ai_server_ip}\n")

    # 5. Finalize
    setup_cli_alias()
    
    print("\n🚀 Building and Starting Containers...")
    try:
        run_command("sudo docker compose up -d --build")
        print("\n" + "="*40)
        print("      🎉 INSTALLATION COMPLETE 🎉")
        print("="*40)
        print(f"1. Secure Dashboard: https://<SERVER_IP>")
        print(f"2. Secure Metabase:  https://<SERVER_IP>:8443")
        print(f"3. CLI Management:   Type 'pe-engine'")
        print("="*40 + "\n")
        print("Note: You will see a 'Not Secure' warning in browser")
        print("      because we used a self-signed certificate.")
        print("      Click 'Advanced' -> 'Proceed' to access.")
    except:
        print("\n❌ Docker start failed. Try running 'sudo docker compose up -d' manually.")

if __name__ == "__main__":
    main()
