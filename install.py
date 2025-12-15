#!/usr/bin/env python3
"""
PE Sourcing Engine v5.1 - Interactive Installer
Walks users through Docker deployment setup
"""

import os
import sys
import subprocess
import shutil
import secrets

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
    """Check if Docker is installed, offer to install if not"""
    print("\n--- 🐳 Docker Check ---")
    if shutil.which("docker"):
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
    # Try docker compose (newer) first
    result = subprocess.run(['docker', 'compose', 'version'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Docker Compose is available.")
        return 'docker compose'
    
    # Try docker-compose (older)
    if shutil.which("docker-compose"):
        print("✅ Docker Compose (legacy) is available.")
        return 'docker-compose'
    
    print("❌ Docker Compose not found.")
    print("Please install Docker Compose: https://docs.docker.com/compose/install/")
    sys.exit(1)

def setup_firewall():
    """Configure firewall to allow HTTP/HTTPS"""
    print("\n--- 🛡️ Firewall Setup ---")
    setup = prompt("Would you like to open ports 80 and 443? (y/n)", "y")
    
    if setup.lower() != 'y':
        print("⚠️ Skipping firewall setup. You may need to manually open ports.")
        return
    
    ports = ["80", "443"]
    
    if shutil.which("firewall-cmd"):
        print("Detected firewalld...")
        for p in ports:
            run_command(f"sudo firewall-cmd --permanent --add-port={p}/tcp", ignore_errors=True)
        run_command("sudo firewall-cmd --reload", ignore_errors=True)
        print("✅ Ports opened (firewalld).")
    elif shutil.which("ufw"):
        print("Detected UFW...")
        for p in ports:
            run_command(f"sudo ufw allow {p}/tcp", ignore_errors=True)
        print("✅ Ports opened (UFW).")
    else:
        print("⚠️ No standard firewall detected. Please open ports 80 and 443 manually.")

def generate_secrets():
    """Generate secure random secrets"""
    jwt_secret = secrets.token_hex(32)
    csrf_secret = secrets.token_hex(32)
    return jwt_secret, csrf_secret

def setup_caddy(domain):
    """Create Caddyfile configuration"""
    print("\n--- 🔒 Caddy Configuration ---")
    
    if not domain:
        caddy_content = """{
    # Global options
    admin off
}

:80 {
    reverse_proxy app:8000
}

:3000 {
    reverse_proxy metabase:3000
}
"""
        print("⚠️ No domain provided. Configuring for HTTP only (Port 80).")
        print("   You will not have HTTPS/SSL without a domain name.")
    else:
        caddy_content = f"""{{
    # Global options
    admin off
}}

# Main application
{domain} {{
    reverse_proxy app:8000
    
    # Security headers
    header {{
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
    }}
    
    # Logging
    log {{
        output file /data/access.log
    }}
}}

# Metabase analytics
metabase.{domain} {{
    reverse_proxy metabase:3000
    
    # Security headers
    header {{
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
    }}
}}
"""
        print(f"✅ Configuring HTTPS for {domain} and metabase.{domain}")
    
    with open("Caddyfile", "w") as f:
        f.write(caddy_content)
    
    print("✅ Caddyfile created.")

def create_env_file(config):
    """Create .env file with all configuration"""
    env_content = f"""# PE Sourcing Engine v5.1 - Environment Variables
# Generated by installer

# Database Configuration
DB_USER={config['db_user']}
DB_PASS={config['db_pass']}
DB_NAME={config['db_name']}

# Authentication Secrets (v5.1)
JWT_SECRET_KEY={config['jwt_secret']}
CSRF_SECRET={config['csrf_secret']}

# API Keys
GOOGLE_PLACES_API_KEY={config.get('google_places_key', '')}
GOOGLE_GEMINI_API_KEY={config.get('gemini_key', '')}
SERPER_API_KEY={config.get('serper_key', '')}

# Optional
AI_SERVER_URL={config.get('ai_server_url', '')}
DOMAIN={config.get('domain', '')}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ .env file created.")

def main():
    print("\n" + "="*60)
    print("   PE Sourcing Engine v5.1 - Interactive Installer")
    print("   Multi-User SaaS Platform with JWT Authentication")
    print("="*60 + "\n")
    
    # Check prerequisites
    check_docker()
    compose_cmd = check_docker_compose()
    
    # Create necessary directories
    print("\n--- 📁 Directory Setup ---")
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    print("✅ Created logs/ and config/ directories.")
    
    # Firewall setup
    setup_firewall()
    
    # Domain configuration
    print("\n--- 🌐 Domain Setup ---")
    print("If you have a domain (e.g., dealgenome.com), enter it below.")
    print("Caddy will automatically provision SSL certificates for HTTPS.")
    print("If you only have an IP address, leave this blank for HTTP-only setup.")
    domain = prompt("Your Domain Name (leave blank for IP-only)", "")
    
    setup_caddy(domain)
    
    # Database configuration
    print("\n--- 🗄️ Database Configuration ---")
    print("PostgreSQL will run inside Docker with these credentials.")
    db_user = prompt("Database Username", "pe_sourcer")
    db_pass = prompt("Database Password", secrets.token_urlsafe(16))
    db_name = prompt("Database Name", "pe_sourcing_db")
    
    # Generate authentication secrets
    print("\n--- 🔐 Security Configuration ---")
    print("Generating secure random secrets for JWT and CSRF...")
    jwt_secret, csrf_secret = generate_secrets()
    print("✅ Secrets generated.")
    
    # API Keys
    print("\n--- 🔑 API Keys (Optional) ---")
    print("You can add these later via the Admin dashboard.")
    print("Press Enter to skip for now.")
    google_places_key = prompt("Google Places API Key", "")
    gemini_key = prompt("Google Gemini API Key", "")
    serper_key = prompt("Serper.dev API Key", "")
    
    # Optional AI Server
    print("\n--- 🤖 AI Server (Optional) ---")
    ai_server_url = prompt("AI Server URL (leave blank to skip)", "")
    
    # Create configuration
    config = {
        'db_user': db_user,
        'db_pass': db_pass,
        'db_name': db_name,
        'jwt_secret': jwt_secret,
        'csrf_secret': csrf_secret,
        'google_places_key': google_places_key,
        'gemini_key': gemini_key,
        'serper_key': serper_key,
        'ai_server_url': ai_server_url,
        'domain': domain
    }
    
    print("\n--- 💾 Creating Configuration Files ---")
    create_env_file(config)
    
    # Confirm before building
    print("\n--- 🚀 Ready to Deploy ---")
    print("\nConfiguration Summary:")
    print(f"  Database: {db_name} (user: {db_user})")
    print(f"  Domain: {domain if domain else 'HTTP-only (no domain)'}")
    print(f"  API Keys: {'Configured' if google_places_key else 'Not configured'}")
    print(f"\nDefault Login Credentials:")
    print(f"  Email: admin@dealgenome.local")
    print(f"  Password: admin123")
    print(f"  ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
    
    proceed = prompt("\nBuild and start containers now? (y/n)", "y")
    
    if proceed.lower() != 'y':
        print("\n✅ Configuration saved. Run 'docker compose up -d' when ready.")
        sys.exit(0)
    
    # Build and start
    print("\n--- 🔨 Building Docker Images ---")
    print("This may take a few minutes on first run...")
    
    try:
        # Build first
        if not run_command(f"{compose_cmd} build", ignore_errors=True):
            print("❌ Build failed. Check the error messages above.")
            sys.exit(1)
        
        print("\n--- 🚀 Starting Containers ---")
        
        # Start without Caddy first (just app, db, metabase)
        if not run_command(f"{compose_cmd} up -d db app metabase", ignore_errors=True):
            print("❌ Failed to start containers. Check the error messages above.")
            sys.exit(1)
        
        # If domain is set, start Caddy too
        if domain:
            print("\n--- 🌐 Starting Caddy (HTTPS) ---")
            run_command(f"{compose_cmd} --profile with-caddy up -d caddy", ignore_errors=True)
        
        print("\n" + "="*60)
        print("      🎉 INSTALLATION COMPLETE! 🎉")
        print("="*60)
        
        # Display access information
        print("\n📍 Access Your Application:")
        if domain:
            print(f"  Dashboard: https://{domain}")
            print(f"  Metabase:  https://metabase.{domain}")
        else:
            # Try to get server IP
            try:
                ip = subprocess.check_output(['hostname', '-I'], text=True).split()[0]
            except:
                ip = "YOUR_SERVER_IP"
            print(f"  Dashboard: http://{ip}:8000")
            print(f"  Metabase:  http://{ip}:3000")
        
        print("\n🔐 Default Login:")
        print("  Email:    admin@dealgenome.local")
        print("  Password: admin123")
        print("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
        
        print("\n🛠️ Useful Commands:")
        print(f"  View logs:     {compose_cmd} logs -f")
        print(f"  Stop all:      {compose_cmd} down")
        print(f"  Restart app:   {compose_cmd} restart app")
        print(f"  View status:   {compose_cmd} ps")
        
        print("\n📚 Documentation:")
        print("  README:        README-DOCKER.md")
        print("  GitHub:        https://github.com/gpatkins/pe-sourcing-engine")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print(f"Try running manually: {compose_cmd} up -d")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user.")
        sys.exit(1)
