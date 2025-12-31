#!/bin/bash
#
# DealGenome Installation Script
# ==============================
# Tested on: Fedora 40+
# Recommended: 1 CPU, 6GB RAM minimum
#
# This script installs and configures:
# - PostgreSQL (local)
# - Python 3.13 with venv
# - DealGenome PE Sourcing Engine
# - Systemd service (auto-start on boot)
# - Caddy for HTTPS (optional)
#
# Run as a regular user with sudo privileges.
# Usage: ./install-dealgenome.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/pe-sourcing-engine"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="pe-sourcing-gui"
DB_NAME="pe_sourcing_db"
DB_USER="pe_sourcer"
REPO_URL="https://github.com/gpatkins/pe-sourcing-engine.git"

# Get the current user (who ran the script)
CURRENT_USER=$(whoami)

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           DealGenome Installation Script                   ║"
echo "║                    Version 5.8                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}Note: Tested on Fedora. Recommended: 1 CPU, 6GB RAM${NC}"
echo ""
echo -e "${GREEN}Server IP Address: ${YELLOW}$SERVER_IP${NC}"
echo ""

# -----------------------------------------------------------------------------
# Pre-flight checks
# -----------------------------------------------------------------------------
echo -e "${BLUE}[1/11] Pre-flight checks...${NC}"

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
echo -e "${BLUE}[2/11] Installing system packages...${NC}"

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
echo -e "${BLUE}[3/11] Setting up PostgreSQL...${NC}"

# Check if PostgreSQL is already initialized
if [ -f /var/lib/pgsql/data/PG_VERSION ]; then
    echo "PostgreSQL already initialized."
else
    echo "Initializing PostgreSQL database..."
    sudo postgresql-setup --initdb
fi

# Configure PostgreSQL to listen on all interfaces (needed for Docker/Metabase)
if grep -q "^listen_addresses = '\*'" /var/lib/pgsql/data/postgresql.conf 2>/dev/null; then
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
echo -e "${BLUE}[4/11] Database configuration...${NC}"

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
echo -e "${BLUE}[5/11] Setting up application directory...${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Repository already exists. Pulling latest changes..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "Cloning repository..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
echo -e "${GREEN}✓ Application code ready at $INSTALL_DIR${NC}"

# -----------------------------------------------------------------------------
# Set up Python virtual environment
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[6/11] Setting up Python virtual environment...${NC}"

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
echo -e "${BLUE}[7/11] Configuring application secrets...${NC}"

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
echo -e "${BLUE}[8/11] Initializing database schema...${NC}"

PGPASSWORD="$DB_PASS" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -f "$INSTALL_DIR/schema/current.sql"

echo -e "${GREEN}✓ Database schema initialized${NC}"

# -----------------------------------------------------------------------------
# Set up systemd service
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[9/11] Creating systemd service...${NC}"

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

echo -e "${GREEN}✓ Systemd service created and started${NC}"

# -----------------------------------------------------------------------------
# Create logs directory
# -----------------------------------------------------------------------------
mkdir -p "$INSTALL_DIR/logs"

# -----------------------------------------------------------------------------
# Optional: Caddy HTTPS Setup
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[10/11] HTTPS Setup (Optional)...${NC}"
echo ""
echo "Caddy can provide automatic HTTPS for your domain."
echo "Skip this if you're only using the server locally or via IP address."
echo ""
echo -n "Do you want to set up HTTPS with Caddy? (y/N): "
read SETUP_CADDY

if [[ "$SETUP_CADDY" =~ ^[Yy]$ ]]; then
    echo ""
    echo -n "Enter your domain name (e.g., deals.example.com): "
    read DOMAIN_NAME
    
    if [ -z "$DOMAIN_NAME" ]; then
        echo -e "${YELLOW}No domain entered. Skipping Caddy setup.${NC}"
    else
        echo ""
        echo "Installing Caddy..."
        
        # Install Caddy
        sudo dnf install -y 'dnf-command(copr)'
        sudo dnf copr enable -y @caddy/caddy
        sudo dnf install -y caddy
        
        # Create Caddyfile
        sudo tee /etc/caddy/Caddyfile > /dev/null <<EOF
$DOMAIN_NAME {
    reverse_proxy localhost:8000
}
EOF
        
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
        
        echo -e "${GREEN}✓ Caddy installed and configured for $DOMAIN_NAME${NC}"
        
        HTTPS_URL="https://$DOMAIN_NAME"
    fi
else
    echo -e "${YELLOW}Skipping HTTPS setup.${NC}"
fi

# -----------------------------------------------------------------------------
# Final summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[11/11] Installation complete!${NC}"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              DealGenome Installation Complete              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}Server IP:${NC}        $SERVER_IP"
if [ -n "$HTTPS_URL" ]; then
echo -e "  ${YELLOW}Dashboard URL:${NC}    $HTTPS_URL"
echo -e "  ${YELLOW}HTTP URL:${NC}         http://$SERVER_IP:8000"
else
echo -e "  ${YELLOW}Dashboard URL:${NC}    http://$SERVER_IP:8000"
fi
echo -e "  ${YELLOW}Default Login:${NC}    admin@dealgenome.local / admin123"
echo -e "  ${YELLOW}Config File:${NC}      $SECRETS_FILE"
echo ""
echo -e "  ${YELLOW}Service Commands:${NC}"
echo "    sudo systemctl status $S
