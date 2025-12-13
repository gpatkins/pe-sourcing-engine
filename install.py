import os
import sys
import subprocess
import shutil

def run_command(command, ignore_errors=False):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError:
        if not ignore_errors:
            print(f"❌ Error running: {command}")
            sys.exit(1)

def prompt(question, default=None):
    prompt_text = f"{question}"
    if default: prompt_text += f" [{default}]"
    prompt_text += ": "
    val = input(prompt_text).strip()
    return val if val else default

def check_docker():
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
            print(f"❌ Install failed: {e}. Install Docker manually.")
            sys.exit(1)

def setup_firewall():
    print("\n--- 🛡️ Firewall Setup (Ports 80 & 443) ---")
    ports = ["80", "443"]
    
    if shutil.which("firewall-cmd"):
        for p in ports:
            run_command(f"sudo firewall-cmd --permanent --add-port={p}/tcp", ignore_errors=True)
        run_command("sudo firewall-cmd --reload", ignore_errors=True)
        print("✅ Ports opened (Firewalld).")
    elif shutil.which("ufw"):
        for p in ports:
            run_command(f"sudo ufw allow {p}/tcp", ignore_errors=True)
        print("✅ Ports opened (UFW).")
    else:
        print("No standard firewall detected. Skipping.")

def setup_caddy(domain):
    print("\n--- 🔒 Caddy Configuration ---")
    
    # If no domain, we fallback to simple IP-based HTTP (Port 80)
    if not domain:
        caddy_content = """
:80 {
    reverse_proxy app:8000
}
"""
        print("⚠️ No domain provided. Configuring for HTTP (Port 80) only.")
        print("   (You will not have HTTPS/SSL without a domain name)")
    else:
        # Production HTTPS setup
        caddy_content = f"""
{domain} {{
    reverse_proxy app:8000
}}

analytics.{domain} {{
    reverse_proxy metabase:3000
}}
"""
        print(f"✅ Configuring HTTPS for {domain} and analytics.{domain}")

    with open("Caddyfile", "w") as f:
        f.write(caddy_content)

def setup_cli_alias():
    print("\n--- 🔗 CLI Setup ---")
    cwd = os.getcwd()
    manage_script = os.path.join(cwd, "manage.py")
    if os.path.exists(manage_script):
        run_command(f"chmod +x {manage_script}")
        run_command("sudo rm -f /usr/local/bin/pe-engine", ignore_errors=True)
        run_command(f"sudo ln -s {manage_script} /usr/local/bin/pe-engine")
        print("✅ Command 'pe-engine' created!")

def main():
    print("\n===========================================")
    print("   PE Sourcing Engine - Installer v3.1")
    print("===========================================\n")

    check_docker()
    
    os.makedirs("logs", exist_ok=True)
    run_command("chmod -R 777 logs")

    setup_firewall()

    print("\n--- 🌐 Domain Setup ---")
    print("If you have a domain (e.g. my-pe-firm.com), enter it below.")
    print("This will auto-generate SSL certificates for HTTPS.")
    print("If you only have an IP address, leave this blank.")
    domain = prompt("Your Domain Name (Leave blank for IP-only)")
    setup_caddy(domain)

    print("\n--- 🔐 Credentials Setup ---")
    admin_user = prompt("Set Dashboard Username", "admin")
    admin_pass = prompt("Set Dashboard Password", "changeme123")
    
    print("\n--- 🛢️ Database Setup ---")
    db_user = prompt("Internal DB User", "pe_sourcer")
    db_pass = prompt("Internal DB Password", "changeme123")
    db_name = prompt("Internal DB Name", "pe_sourcing_db")
    
    print("\n--- 🧠 External Services ---")
    ai_server_ip = prompt("AI Server IP/URL", "http://10.55.55.50:11434/api/generate")
    if not ai_server_ip.startswith("http"): ai_server_ip = f"http://{ai_server_ip}:11434/api/generate"

    print("\n--- 🔑 API Keys (Press Enter to skip) ---")
    google_key = prompt("Google Places API Key")
    gemini_key = prompt("Google Gemini API Key")
    serper_key = prompt("Serper.dev API Key")

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

    setup_cli_alias()
    
    print("\n🚀 Building and Starting Containers...")
    try:
        run_command("sudo docker compose up -d --build")
        print("\n" + "="*40)
        print("      🎉 INSTALLATION COMPLETE 🎉")
        print("="*40)
        if domain:
            print(f"1. Dashboard: https://{domain}")
            print(f"2. Metabase:  https://analytics.{domain}")
        else:
            # Get current IP for display
            try:
                ip = subprocess.check_output(['hostname', '-I']).decode().split()[0]
            except:
                ip = "SERVER_IP"
            print(f"1. Dashboard: http://{ip} (Port 80)")
        print(f"3. CLI Management: Type 'pe-engine'")
        print("="*40 + "\n")
    except:
        print("\n❌ Docker start failed. Try running 'sudo docker compose up -d' manually.")

if __name__ == "__main__":
    main()
