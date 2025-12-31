#!/bin/bash
#
# DealGenome Full Installation Script
# ====================================
# Tested on: Fedora 40+
# Recommended: 1 CPU, 6GB RAM minimum, 20GB disk
#
# This script installs and configures:
# - PostgreSQL (local)
# - Python 3.13 with venv
# - DealGenome PE Sourcing Engine
# - Metabase Analytics (optional, via Docker)
# - Caddy for HTTPS (optional)
# - Systemd services (auto-start on boot)
#
# Run as a regular user with sudo privileges.
# Usage: ./install-dg-full.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/pe-sourcing-engine"
VENV_DIR="$INSTALL_DIR/venv"
METABASE_DIR="/opt/metabase"
SERVICE_NAME="pe-sourcing-gui"
DB_NAME="pe_sourcing_db"
DB_USER="pe_sourcer"
REPO_URL="https://github.com/gpatkins/pe-sourcing-engine.git"

# Get the current user (who ran the script)
CURRENT_USER=$(whoami)

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')

# Track what gets installed
METABASE_INSTALLED=false
CADDY_INSTALLED=false
HTTPS_URL=""
METABASE_HTTPS_URL=""

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        DealGenome Full Installation Script                 ║"
echo "║                    Version 5.8                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}System Requirements:${NC}"
echo "  • Tested on: Fedora 40+"
echo "  • Recommended: 1 CPU, 6GB RAM, 20GB disk"
echo ""
echo -e "${GREEN}Server IP Address: ${YELLOW}$SERVER_IP${NC}"
echo ""

# -----------------------------------------------------------------------------
# Pre-flight checks
# -----------------------------------------------------------------------------
echo -e "${BLUE}[1/12] Pre-flight checks...${NC}"

# Check if running as root (we don't want that)
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Do not run this script as root.${NC}"
    echo "Run as a regular user with sudo privileges."
    exit 1
fi

# Check sudo access
if ! sudo -v; then
    echo -e "${RED}Error: This script requires sudo privileges.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running as user: $CURRENT_USER${NC}"

# -----------------------------------------------------------------------------
# Install system packages
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/12] Installing system packages...${NC}"

sudo dnf install -y \
    python3.13 \
    python3.13-devel \
    postgresql-server \
    postgresql-contrib \
    postgresql-devel \
    git \
    gcc \
    libpq-devel \
    redhat-rpm-config \
    --skip-unavailable

# Verify critical components and install if missing
echo ""
echo "Verifying critical components..."

# Check Python 3.13
if ! command -v python3.13 &> /dev/null; then
    echo -e "${RED}Error: Python 3.13 not found after install. Aborting.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3.13 found${NC}"

# Check pip - install via ensurepip if missing
if ! python3.13 -m pip --version &> /dev/null; then
    echo "pip not found, installing via ensurepip..."
    python3.13 -m ensurepip --upgrade
fi
echo -e "${GREEN}✓ pip available${NC}"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: PostgreSQL client (psql) not found. Aborting.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL client found${NC}"

# Check gcc (needed for some pip packages)
if ! command -v gcc &> /dev/null; then
    echo -e "${RED}Error: gcc not found. Aborting.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ gcc found${NC}"

echo -e "${GREEN}✓ System packages installed and verified${NC}"

# -----------------------------------------------------------------------------
# Initialize PostgreSQL
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/12] Setting up PostgreSQL...${NC}"

# Check if PostgreSQL is already initialized
if sudo test -f /var/lib/pgsql/data/PG_VERSION; then
    echo "PostgreSQL already initialized."
else
    echo "Initializing PostgreSQL database..."
    sudo postgresql-setup --initdb
fi

# Configure PostgreSQL to listen on all interfaces (needed for Docker/Metabase)
if sudo grep -q "^listen_addresses = '\*'" /var/lib/pgsql/data/postgresql.conf 2>/dev/null; then
    echo "PostgreSQL listen_addresses already configured."
else
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /var/lib/pgsql/data/postgresql.conf
fi

# Configure PostgreSQL for password authentication
# Backup original config if not already backed up
if [ ! -f /var/lib/pgsql/data/pg_hba.conf.backup ]; then
    sudo cp /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.backup
fi

# Update pg_hba.conf to allow local and Docker network connections
sudo tee /var/lib/pgsql/data/pg_hba.conf > /dev/null <<EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
host    all             all             172.16.0.0/12           md5
host    all             all             192.168.0.0/16          md5
EOF

# Start and enable PostgreSQL
sudo systemctl restart postgresql
sudo systemctl enable postgresql

echo -e "${GREEN}✓ PostgreSQL configured and running${NC}"

# -----------------------------------------------------------------------------
# Prompt for database password
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/12] Database configuration...${NC}"

while true; do
    echo -n "Enter password for database user '$DB_USER': "
    read -s DB_PASS
    echo ""
    
    echo -n "Confirm password: "
    read -s DB_PASS_CONFIRM
    echo ""
    
    if [ "$DB_PASS" = "$DB_PASS_CONFIRM" ]; then
        if [ -z "$DB_PASS" ]; then
            echo -e "${RED}Password cannot be empty. Try again.${NC}"
        else
            break
        fi
    else
        echo -e "${RED}Passwords do not match. Try again.${NC}"
    fi
done

# Create database user and database
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
    ELSE
        ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo -e "${GREEN}✓ Database user and database created${NC}"

# -----------------------------------------------------------------------------
# Clone or update repository
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[5/12] Setting up application directory...${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Repository already exists. Pulling latest changes..."
    # Fix ownership if needed (handles case where repo was cloned as root)
    if [ ! -w "$INSTALL_DIR" ]; then
        echo "Fixing directory permissions..."
        sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
    fi
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "Cloning repository..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Ensure correct ownership of entire directory
sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"

cd "$INSTALL_DIR"
echo -e "${GREEN}✓ Application code ready at $INSTALL_DIR${NC}"

# -----------------------------------------------------------------------------
# Set up Python virtual environment
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[6/12] Setting up Python virtual environment...${NC}"

if [ ! -d "$VENV_DIR" ]; then
    python3.13 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Python environment configured${NC}"

# -----------------------------------------------------------------------------
# Configure secrets.env
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[7/12] Configuring application secrets...${NC}"

SECRETS_FILE="$INSTALL_DIR/config/secrets.env"
mkdir -p "$INSTALL_DIR/config"

# Generate JWT secret
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
CSRF_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo ""
echo "API keys can be configured now or later via the admin dashboard."
echo "(Press Enter to skip any key)"
echo ""

echo -n "Google Places API Key: "
read GOOGLE_PLACES_KEY

echo -n "Gemini API Key: "
read GEMINI_KEY

echo -n "Serper API Key: "
read SERPER_KEY

cat > "$SECRETS_FILE" <<EOF
# DealGenome secrets.env
# Generated by install script on $(date)

# Database Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASS=$DB_PASS

# Authentication Secrets
JWT_SECRET_KEY=$JWT_SECRET
CSRF_SECRET=$CSRF_SECRET

# API Keys (can be updated via Admin Dashboard)
GOOGLE_PLACES_API_KEY=$GOOGLE_PLACES_KEY
GEMINI_API_KEY=$GEMINI_KEY
SERPER_API_KEY=$SERPER_KEY

# Metabase URL (update after installing Metabase)
METABASE_URL=http://localhost:3000
EOF

chmod 600 "$SECRETS_FILE"
echo -e "${GREEN}✓ Secrets configured at $SECRETS_FILE${NC}"

# -----------------------------------------------------------------------------
# Initialize database schema
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[8/12] Initializing database schema...${NC}"

PGPASSWORD="$DB_PASS" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -f "$INSTALL_DIR/schema/current.sql"

echo -e "${GREEN}✓ Database schema initialized${NC}"

# -----------------------------------------------------------------------------
# Set up systemd service for DealGenome
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[9/12] Creating DealGenome systemd service...${NC}"

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=DealGenome PE Sourcing Engine
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/bin"
ExecStart=$VENV_DIR/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up sudoers for cleanup commands
sudo tee /etc/sudoers.d/pe-sourcing > /dev/null <<EOF
# Allow pe-sourcing-engine cleanup commands without password
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/bash $INSTALL_DIR/clean.sh
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/sh -c echo 3 > /proc/sys/vm/drop_caches
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart ${SERVICE_NAME}.service
EOF

sudo chmod 440 /etc/sudoers.d/pe-sourcing

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl start ${SERVICE_NAME}.service

# Create logs directory
mkdir -p "$INSTALL_DIR/logs"

echo -e "${GREEN}✓ DealGenome systemd service created and started${NC}"

# -----------------------------------------------------------------------------
# Optional: Metabase Installation
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[10/12] Metabase Analytics (Optional)...${NC}"
echo ""
echo "Metabase provides interactive dashboards and data visualization."
echo "It runs in Docker and requires ~2GB additional disk space."
echo ""
echo -n "Do you want to install Metabase? (y/N): "
read INSTALL_METABASE

if [[ "$INSTALL_METABASE" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing Docker..."
    
    # Install Docker
    if command -v docker &> /dev/null; then
        echo "Docker already installed."
    else
        sudo dnf install -y dnf-plugins-core
        
        # Add Docker repo (compatible with newer Fedora)
        sudo tee /etc/yum.repos.d/docker-ce.repo > /dev/null <<REPO
[docker-ce-stable]
name=Docker CE Stable - \$basearch
baseurl=https://download.docker.com/linux/fedora/\$releasever/\$basearch/stable
enabled=1
gpgcheck=1
gpgkey=https://download.docker.com/linux/fedora/gpg
REPO
        
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add current user to docker group
    if ! groups "$CURRENT_USER" | grep -q docker; then
        sudo usermod -aG docker "$CURRENT_USER"
    fi
    
    echo -e "${GREEN}✓ Docker installed${NC}"
    
    # Create Metabase directory and docker-compose.yml
    echo "Setting up Metabase..."
    sudo mkdir -p "$METABASE_DIR"
    sudo chown "$CURRENT_USER:$CURRENT_USER" "$METABASE_DIR"
    
    cat > "$METABASE_DIR/docker-compose.yml" <<EOF
services:
  metabase:
    image: metabase/metabase:latest
    container_name: metabase
    ports:
      - "3000:3000"
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase
      MB_DB_PORT: 5432
      MB_DB_USER: metabase
      MB_DB_PASS: metabase_password
      MB_DB_HOST: metabase-db
    depends_on:
      - metabase-db
    restart: always

  metabase-db:
    image: postgres:15-alpine
    container_name: metabase-db
    environment:
      POSTGRES_USER: metabase
      POSTGRES_PASSWORD: metabase_password
      POSTGRES_DB: metabase
    volumes:
      - metabase-data:/var/lib/postgresql/data
    restart: always

volumes:
  metabase-data:
EOF

    # Create systemd service for Metabase
    sudo tee /etc/systemd/system/metabase.service > /dev/null <<EOF
[Unit]
Description=Metabase Analytics (Docker Compose)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$METABASE_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable metabase.service
    
    # Start Metabase
    cd "$METABASE_DIR"
    sudo docker compose up -d
    
    METABASE_INSTALLED=true
    echo -e "${GREEN}✓ Metabase installed and starting${NC}"
else
    echo -e "${YELLOW}Skipping Metabase installation.${NC}"
fi

# -----------------------------------------------------------------------------
# Optional: Caddy HTTPS Setup
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[11/12] HTTPS Setup with Caddy (Optional)...${NC}"
echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}HTTPS Requirements:${NC}"
echo "  • Each service requires its own domain name"
echo "  • Domains must be pointed to this server's IP ($SERVER_IP)"
echo "  • Caddy will automatically obtain SSL certificates"
echo ""
echo "  Examples:"
echo "    DealGenome: deals.yourcompany.com"
if [ "$METABASE_INSTALLED" = true ]; then
echo "    Metabase:   metabase.yourcompany.com"
fi
echo ""
echo "  If you don't have domains configured, skip this step."
echo "  You can access services via IP address and ports:"
echo "    DealGenome: http://$SERVER_IP:8000"
if [ "$METABASE_INSTALLED" = true ]; then
echo "    Metabase:   http://$SERVER_IP:3000"
fi
echo -e "${CYAN}────────────────────────────────────────────────────────────${NC}"
echo ""
echo -n "Do you want to set up HTTPS with Caddy? (y/N): "
read SETUP_CADDY

if [[ "$SETUP_CADDY" =~ ^[Yy]$ ]]; then
    echo ""
    echo -n "Enter domain for DealGenome (e.g., deals.example.com): "
    read DG_DOMAIN
    
    if [ -z "$DG_DOMAIN" ]; then
        echo -e "${YELLOW}No domain entered. Skipping Caddy setup.${NC}"
    else
        # Ask for Metabase domain if Metabase was installed
        if [ "$METABASE_INSTALLED" = true ]; then
            echo -n "Enter domain for Metabase (e.g., metabase.example.com): "
            read MB_DOMAIN
        fi
        
        echo ""
        echo "Installing Caddy..."
        
        # Install Caddy
        sudo dnf install -y 'dnf-command(copr)'
        sudo dnf copr enable -y @caddy/caddy
        sudo dnf install -y caddy
        
        # Create Caddyfile
        if [ -n "$MB_DOMAIN" ]; then
            # Both DealGenome and Metabase
            sudo tee /etc/caddy/Caddyfile > /dev/null <<EOF
# DealGenome
$DG_DOMAIN {
    reverse_proxy localhost:8000
}

# Metabase Analytics
$MB_DOMAIN {
    reverse_proxy localhost:3000
}
EOF
            METABASE_HTTPS_URL="https://$MB_DOMAIN"
        else
            # DealGenome only
            sudo tee /etc/caddy/Caddyfile > /dev/null <<EOF
# DealGenome
$DG_DOMAIN {
    reverse_proxy localhost:8000
}
EOF
        fi
        
        # Open firewall ports
        if command -v firewall-cmd &> /dev/null; then
            echo "Configuring firewall..."
            sudo firewall-cmd --permanent --add-service=http
            sudo firewall-cmd --permanent --add-service=https
            sudo firewall-cmd --reload
        fi
        
        # Enable and start Caddy
        sudo systemctl enable caddy
        sudo systemctl start caddy
        
        CADDY_INSTALLED=true
        HTTPS_URL="https://$DG_DOMAIN"
        
        echo -e "${GREEN}✓ Caddy installed and configured${NC}"
    fi
else
    echo -e "${YELLOW}Skipping HTTPS setup.${NC}"
fi

# -----------------------------------------------------------------------------
# Final summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[12/12] Installation complete!${NC}"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           DealGenome Installation Complete                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                        SERVER INFO                           ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}Server IP:${NC}           $SERVER_IP"
echo -e "  ${YELLOW}Installed By:${NC}        $CURRENT_USER"
echo -e "  ${YELLOW}Install Directory:${NC}   $INSTALL_DIR"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                      DEALGENOME ACCESS                       ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
if [ -n "$HTTPS_URL" ]; then
echo -e "  ${YELLOW}URL (HTTPS):${NC}         $HTTPS_URL"
echo -e "  ${YELLOW}URL (HTTP):${NC}          http://$SERVER_IP:8000"
else
echo -e "  ${YELLOW}URL:${NC}                 http://$SERVER_IP:8000"
fi
echo -e "  ${YELLOW}Default Login:${NC}       admin@dealgenome.local"
echo -e "  ${YELLOW}Default Password:${NC}    admin123"
echo -e "  ${RED}⚠ IMPORTANT:${NC}         Change the default password immediately!"
echo ""
if [ "$METABASE_INSTALLED" = true ]; then
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                      METABASE ACCESS                         ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
if [ -n "$METABASE_HTTPS_URL" ]; then
echo -e "  ${YELLOW}URL (HTTPS):${NC}         $METABASE_HTTPS_URL"
echo -e "  ${YELLOW}URL (HTTP):${NC}          http://$SERVER_IP:3000"
else
echo -e "  ${YELLOW}URL:${NC}                 http://$SERVER_IP:3000"
fi
echo -e "  ${YELLOW}First-Time Setup:${NC}    Create admin account on first visit"
echo ""
echo -e "  ${YELLOW}Connect to DealGenome Database:${NC}"
echo -e "    Database Type:     PostgreSQL"
echo -e "    Host:              $SERVER_IP"
echo -e "    Port:              5432"
echo -e "    Database Name:     $DB_NAME"
echo -e "    Username:          $DB_USER"
echo -e "    Password:          (the password you set during install)"
echo ""
fi
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                     SERVICE COMMANDS                         ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}DealGenome:${NC}"
echo "    sudo systemctl status $SERVICE_NAME     # Check status"
echo "    sudo systemctl restart $SERVICE_NAME    # Restart"
echo "    sudo journalctl -u $SERVICE_NAME -f     # View logs"
echo ""
if [ "$METABASE_INSTALLED" = true ]; then
echo -e "  ${YELLOW}Metabase:${NC}"
echo "    sudo systemctl status metabase          # Check status"
echo "    sudo systemctl restart metabase         # Restart"
echo "    cd $METABASE_DIR && sudo docker compose logs -f  # View logs"
echo ""
fi
if [ "$CADDY_INSTALLED" = true ]; then
echo -e "  ${YELLOW}Caddy (HTTPS):${NC}"
echo "    sudo systemctl status caddy             # Check status"
echo "    sudo systemctl restart caddy            # Restart"
echo "    sudo journalctl -u caddy -f             # View logs"
echo ""
fi
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                       CONFIG FILES                           ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}DealGenome Secrets:${NC}  $SECRETS_FILE"
echo -e "  ${YELLOW}DealGenome Config:${NC}   $INSTALL_DIR/config/settings.yaml"
if [ "$METABASE_INSTALLED" = true ]; then
echo -e "  ${YELLOW}Metabase Docker:${NC}     $METABASE_DIR/docker-compose.yml"
fi
if [ "$CADDY_INSTALLED" = true ]; then
echo -e "  ${YELLOW}Caddy Config:${NC}        /etc/caddy/Caddyfile"
fi
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                        NEXT STEPS                            ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  1. Change the default admin password immediately"
echo "  2. Add API keys via Admin Dashboard (if not set during install)"
if [ "$METABASE_INSTALLED" = true ]; then
echo "  3. Complete Metabase setup at the URL above"
echo "  4. Connect Metabase to DealGenome database (see credentials above)"
fi
if [ "$CADDY_INSTALLED" = true ] && [ -n "$DG_DOMAIN" ]; then
echo ""
echo -e "  ${YELLOW}DNS Reminder:${NC}"
echo "    Ensure these domains point to $SERVER_IP:"
echo "      • $DG_DOMAIN"
if [ -n "$MB_DOMAIN" ]; then
echo "      • $MB_DOMAIN"
fi
fi
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        Thank you for installing DealGenome!                    ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
