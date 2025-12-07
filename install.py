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
    print("\n--- 🛡️ Firewall Setup (Ports 8000 & 3000) ---")
    if shutil.which("firewall-cmd"):
        run_command("sudo firewall-cmd --permanent --add-port=8000/tcp", ignore_errors=True)
        run_command("sudo firewall-cmd --permanent --add-port=3000/tcp", ignore_errors=True)
        run_command("sudo firewall-cmd --reload", ignore_errors=True)
        print("✅ Ports opened (Firewalld).")
    elif shutil.which("ufw"):
        run_command("sudo ufw allow 8000/tcp", ignore_errors=True)
        run_command("sudo ufw allow 3000/tcp", ignore_errors=True)
        print("✅ Ports opened (UFW).")
    else:
        print("No standard firewall detected. Skipping.")

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
    print("   PE Sourcing Engine - Installer v3.0")
    print("===========================================\n")

    check_docker()
    
    # Create logs dir
    os.makedirs("logs", exist_ok=True)
    run_command("chmod -R 777 logs")

    setup_firewall()

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
        print("\n🎉 INSTALLATION COMPLETE!")
        print("Type 'pe-engine' to open the Management Console.")
    except:
        print("\n❌ Docker start failed. Try running 'sudo docker compose up -d' manually.")

if __name__ == "__main__":
    main()
