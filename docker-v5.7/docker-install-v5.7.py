#!/usr/bin/env python3
"""
PE Sourcing Engine v5.7 - Docker Installer
Clean automated setup mirroring dg production environment
"""

import os
import sys
import subprocess
import secrets
import time
from pathlib import Path

def run_command(command, ignore_errors=False):
    """Execute shell command"""
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError:
        if not ignore_errors:
            print(f"❌ Error running: {command}")
            sys.exit(1)
        return False

def prompt(question, default=None):
    """Prompt user for input with optional default"""
    prompt_text = f"{question}"
    if default: 
        prompt_text += f" [{default}]"
    prompt_text += ": "
    val = input(prompt_text).strip()
    return val if val else default

def check_docker_installed():
    """Check if Docker and Compose are installed"""
    if not run_command("docker --version", ignore_errors=True):
        print("❌ Docker not found. Installing...")
        run_command("sudo apt-get update && sudo apt-get install -y docker.io docker-compose")
        run_command("sudo systemctl start docker")
        run_command("sudo systemctl enable docker")
        run_command("sudo usermod -aG docker $USER")
        print("\n⚠️ Added user to docker group. Please log out and back in for changes to take effect.")
        sys.exit(0)
    
    if not run_command("docker compose version", ignore_errors=True):
        print("❌ Docker Compose v2 not found. Please install it.")
        sys.exit(1)

def create_env_file():
    """Create or update .env file with user input"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("\n📄 Existing .env found. Updating...")
        with open(env_path, 'r') as f:
            existing = dict(line.strip().split('=', 1) for line in f if '=' in line and not line.startswith('#'))
    else:
        existing = {}
        env_path.write_text("")
    
    # Required vars - always prompt to allow updates
    db_pass = prompt("Database Password", existing.get("DB_PASS", "changeme"))
    jwt_secret = prompt("JWT Secret Key (auto-generated if blank)", existing.get("JWT_SECRET_KEY") or secrets.token_hex(32))
    csrf_secret = prompt("CSRF Secret (auto-generated if blank)", existing.get("CSRF_SECRET") or secrets.token_hex(32))
    
    # API Keys - prompt even if exist
    google_places = prompt("Google Places API Key", existing.get("GOOGLE_PLACES_API_KEY", ""))
    gemini = prompt("Google Gemini API Key", existing.get("GOOGLE_GEMINI_API_KEY", ""))
    serper = prompt("Serper API Key", existing.get("SERPER_API_KEY", ""))
    
    env_lines = [
        f"DB_USER=pe_sourcer",
        f"DB_PASS={db_pass}",
        f"DB_NAME=pe_sourcing_db",
        f"JWT_SECRET_KEY={jwt_secret}",
        f"CSRF_SECRET={csrf_secret}",
        f"GOOGLE_PLACES_API_KEY={google_places}",
        f"GOOGLE_GEMINI_API_KEY={gemini}",
        f"SERPER_API_KEY={serper}",
    ]
    
    env_path.write_text("\n".join(env_lines) + "\n")
    print("✅ .env file created/updated")

def validate_setup():
    """Light validation - warn about missing keys but do not block"""
    print("\n🔍 Validating setup...")
    
    with open(".env", 'r') as f:
        content = f.read()
    
    # Only check for presence (allow blank API keys for testing)
    required_critical = ["DB_PASS", "JWT_SECRET_KEY", "CSRF_SECRET"]
    missing_critical = [k for k in required_critical if f"{k}=" not in content or content.split(f"{k}=")[1].split("\n")[0].strip() == ""]
    if missing_critical:
        print(f"❌ Critical missing: {', '.join(missing_critical)}. Please fill and rerun installer.")
        sys.exit(1)
    
    optional = ["GOOGLE_PLACES_API_KEY", "GOOGLE_GEMINI_API_KEY", "SERPER_API_KEY"]
    missing_optional = [k for k in optional if f"{k}=" not in content or content.split(f"{k}=")[1].split("\n")[0].strip() == ""]
    if missing_optional:
        print(f"⚠️ Optional API keys missing (pipeline steps will skip): {', '.join(missing_optional)}")
    else:
        print("✅ All API keys present")
    
    # Test DB connection
    run_command("docker compose -f docker-compose-v5.7.yml up -d db")
    time.sleep(10)
    test_cmd = "docker compose -f docker-compose-v5.7.yml exec db psql -U pe_sourcer -d pe_sourcing_db -c 'SELECT 1;'"
    if not run_command(test_cmd, ignore_errors=True):
        print("❌ DB connection test failed. Check logs with: docker compose logs db")
        sys.exit(1)
    
    print("✅ Validation passed (proceeding with optional keys blank if needed)")

def main():
    print("\n" + "="*60)
    print("🚀 PE Sourcing Engine v5.7 - Docker Installer")
    print("="*60 + "\n")
    
    # Change to script dir
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    check_docker_installed()
    create_env_file()
    
    print("\n🛠️ Building and starting services...")
    run_command("docker compose -f docker-compose-v5.7.yml build")
    run_command("docker compose -f docker-compose-v5.7.yml up -d")
    
    validate_setup()
    
    print("\n✅ Installation complete!")
    print("Access Dashboard: http://localhost:80/login")
    print("Default Login: admin@dealgenome.local / admin123")
    print("⚠️ Change password immediately after first login!")
    
    print("\n🛠️ Useful Commands:")
    print("  Management: python3 docker-manage-v5.7.py")
    print("  View logs:  docker compose -f docker-compose-v5.7.yml logs -f")
    print("  Stop all:   docker compose -f docker-compose-v5.7.yml down")
    
    print("\n📚 Documentation:")
    print("  README: docker-README-v5.7.md")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user.")
        sys.exit(1)
