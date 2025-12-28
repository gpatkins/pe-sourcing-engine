#!/usr/bin/env python3
"""
PE Sourcing Engine v5.7 - Docker Installer
Clean automated setup mirroring dg production environment
"""

import os
import sys
import subprocess
import secrets
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

def check_docker():
    """Check if Docker is installed"""
    print("\n--- 🐳 Docker Check ---")
    if subprocess.run(['which', 'docker'], capture_output=True).returncode == 0:
        print("✅ Docker is installed.")
        return True
    else:
        print("⚠️ Docker not found.")
        install = prompt("Would you like to install Docker now? (y/n)", "y")
        if install.lower() == 'y':
            try:
                print("Installing Docker...")
                run_command("curl -fsSL https://get.docker.com | sh")
                run_command("sudo systemctl start docker")
                run_command("sudo systemctl enable docker")
                run_command("sudo usermod -aG docker $USER", ignore_errors=True)
                print("✅ Docker installed.")
                print("⚠️ You may need to log out and back in for Docker permissions.")
                return True
            except Exception as e:
                print(f"❌ Install failed: {e}")
                print("Please install Docker manually: https://docs.docker.com/get-docker/")
                sys.exit(1)
        else:
            print("❌ Docker is required. Please install it manually.")
            sys.exit(1)

def check_docker_compose():
    """Check if Docker Compose is available"""
    print("\n--- 🔧 Docker Compose Check ---")
    result = subprocess.run(['docker', 'compose', 'version'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Docker Compose is available.")
        return 'docker compose'
    
    if subprocess.run(['which', 'docker-compose'], capture_output=True).returncode == 0:
        print("✅ Docker Compose (legacy) is available.")
        return 'docker-compose'
    
    print("❌ Docker Compose not found.")
    print("Please install Docker Compose: https://docs.docker.com/compose/install/")
    sys.exit(1)

def ensure_config_dir():
    """Ensure config directory exists"""
    config_dir = Path("../config")
    config_dir.mkdir(exist_ok=True)
    return config_dir

def create_secrets_env(config_dir):
    """Create or update config/secrets.env"""
    secrets_file = config_dir / "secrets.env"
    
    print("\n--- 🔐 Configuration Setup ---")
    
    # Check if file exists
    if secrets_file.exists():
        print(f"Found existing config/secrets.env")
        update = prompt("Update API keys? (y/n)", "n")
        if update.lower() != 'y':
            print("Keeping existing configuration.")
            return
    
    print("\nEnter your API keys (press Enter to skip):")
    google_places = prompt("Google Places API Key", "")
    google_gemini = prompt("Google Gemini API Key", "")
    serper = prompt("Serper API Key", "")
    
    # Database config
    print("\n--- 🗄️ Database Configuration ---")
    db_user = prompt("Database User", "pe_sourcer")
    db_pass = prompt("Database Password", secrets.token_urlsafe(16))
    db_name = prompt("Database Name", "pe_sourcing_db")
    
    # Security secrets
    print("\n--- 🔒 Security Secrets ---")
    print("Generating JWT and CSRF secrets...")
    jwt_secret = secrets.token_hex(32)
    csrf_secret = secrets.token_hex(32)
    
    # Write secrets.env
    with open(secrets_file, 'w') as f:
        f.write("# PE Sourcing Engine v5.7 - Configuration\n")
        f.write(f"# Generated: {subprocess.check_output('date', shell=True).decode().strip()}\n\n")
        
        f.write("# Database\n")
        f.write(f"DB_HOST=localhost\n")
        f.write(f"DB_USER={db_user}\n")
        f.write(f"DB_PASS={db_pass}\n")
        f.write(f"DB_NAME={db_name}\n")
        f.write(f"DB_PORT=5432\n\n")
        
        f.write("# Security\n")
        f.write(f"JWT_SECRET_KEY={jwt_secret}\n")
        f.write(f"CSRF_SECRET={csrf_secret}\n\n")
        
        f.write("# API Keys\n")
        f.write(f"GOOGLE_PLACES_API_KEY={google_places}\n")
        f.write(f"GOOGLE_GEMINI_API_KEY={google_gemini}\n")
        f.write(f"GEMINI_API_KEY={google_gemini}\n")
        f.write(f"SERPER_API_KEY={serper}\n\n")
        
        f.write("# Optional\n")
        f.write(f"AI_SERVER_URL=\n")
        f.write(f"METABASE_URL=http://localhost:3001\n")
    
    print(f"✅ Configuration saved to {secrets_file}")
    print(f"   Database password: {db_pass}")
    print(f"   (Save this information securely!)")

def main():
    print("\n" + "="*60)
    print("   PE Sourcing Engine v5.7 - Docker Installer")
    print("   Clean setup mirroring dg production environment")
    print("="*60 + "\n")
    
    # Change to docker-v5.7 directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}\n")
    
    # Prerequisites
    check_docker()
    compose_cmd = check_docker_compose()
    
    # Configuration
    config_dir = ensure_config_dir()
    create_secrets_env(config_dir)
    
    # Summary
    print("\n--- 📋 Installation Summary ---")
    print("✅ Docker and Docker Compose verified")
    print("✅ Configuration files created")
    print("\n--- 🚀 Ready to Deploy ---")
    
    print("\nDefault Login Credentials:")
    print("  Email: admin@dealgenome.local")
    print("  Password: admin123")
    print("  ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
    
    print("\nAccess URLs (after deployment):")
    print("  Dashboard: http://YOUR_SERVER_IP:8001")
    print("  Metabase:  http://YOUR_SERVER_IP:3001 (if enabled)")
    
    proceed = prompt("\nBuild and start containers now? (y/n)", "y")
    
    if proceed.lower() != 'y':
        print("\n✅ Configuration saved. Run manually when ready:")
        print(f"   cd {script_dir}")
        print(f"   {compose_cmd} -f docker-compose-v5.7.yml up -d")
        sys.exit(0)
    
    # Build and deploy
    print("\n--- 🔨 Building Docker Images ---")
    print("This may take a few minutes on first run...")
    
    try:
        # Build
        if not run_command(f"{compose_cmd} -f docker-compose-v5.7.yml build", ignore_errors=True):
            print("❌ Build failed. Check the error messages above.")
            sys.exit(1)
        
        print("\n--- 🚀 Starting Containers ---")
        
        # Start services
        if not run_command(f"{compose_cmd} -f docker-compose-v5.7.yml up -d", ignore_errors=True):
            print("❌ Failed to start containers. Check the error messages above.")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("      🎉 INSTALLATION COMPLETE! 🎉")
        print("="*60)
        
        # Get server IP
        try:
            ip = subprocess.check_output(['hostname', '-I'], text=True).split()[0]
        except:
            ip = "YOUR_SERVER_IP"
        
        print("\n📍 Access Your Application:")
        print(f"  Dashboard: http://{ip}:8001")
        print(f"  Metabase:  http://{ip}:3001 (start with --profile with-metabase)")
        
        print("\n🔐 Default Login:")
        print("  Email:    admin@dealgenome.local")
        print("  Password: admin123")
        print("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
        
        print("\n🛠️ Useful Commands:")
        print(f"  Management: python3 docker-manage-v5.7.py")
        print(f"  View logs:  {compose_cmd} -f docker-compose-v5.7.yml logs -f")
        print(f"  Stop all:   {compose_cmd} -f docker-compose-v5.7.yml down")
        
        print("\n📚 Documentation:")
        print("  README: docker-README-v5.7.md")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print(f"Try running manually: {compose_cmd} -f docker-compose-v5.7.yml up -d")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user.")
        sys.exit(1)
