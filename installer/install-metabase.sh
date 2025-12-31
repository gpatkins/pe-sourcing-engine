#!/bin/bash
#
# Metabase Installation Script for DealGenome
# ============================================
# Tested on: Fedora 40+
#
# This script installs and configures:
# - Docker and Docker Compose
# - Metabase (via Docker)
# - Systemd service for Metabase (auto-start on boot)
#
# Run as a regular user with sudo privileges.
# Usage: ./install-metabase.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
METABASE_DIR="/opt/metabase"
SERVICE_NAME="metabase"

# Get the current user (who ran the script)
CURRENT_USER=$(whoami)

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Metabase Installation Script                     ║"
echo "║              For DealGenome Analytics                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# -----------------------------------------------------------------------------
# Pre-flight checks
# -----------------------------------------------------------------------------
echo -e "${BLUE}[1/5] Pre-flight checks...${NC}"

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
# Install Docker
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/5] Installing Docker...${NC}"

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    echo "Docker already installed."
else
    # Install Docker via dnf
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
    echo -e "${YELLOW}Note: You were added to the docker group. You may need to log out and back in for this to take effect.${NC}"
fi

echo -e "${GREEN}✓ Docker installed and running${NC}"

# -----------------------------------------------------------------------------
# Create Metabase directory and docker-compose.yml
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/5] Setting up Metabase...${NC}"

sudo mkdir -p "$METABASE_DIR"
sudo chown "$CURRENT_USER:$CURRENT_USER" "$METABASE_DIR"

# Create docker-compose.yml
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

echo -e "${GREEN}✓ Metabase configuration created${NC}"

# -----------------------------------------------------------------------------
# Create systemd service for Metabase
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/5] Creating systemd service...${NC}"

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
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
sudo systemctl enable ${SERVICE_NAME}.service

echo -e "${GREEN}✓ Systemd service created${NC}"

# -----------------------------------------------------------------------------
# Start Metabase
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[5/5] Starting Metabase...${NC}"

cd "$METABASE_DIR"

# Use sudo to run docker compose (in case group membership not active yet)
sudo docker compose up -d

echo -e "${GREEN}✓ Metabase containers starting${NC}"

# Wait for Metabase to be ready
echo ""
echo "Waiting for Metabase to initialize (this may take 1-2 minutes)..."
sleep 10

# Check if container is running
if sudo docker ps | grep -q metabase; then
    echo -e "${GREEN}✓ Metabase container is running${NC}"
else
    echo -e "${YELLOW}⚠ Metabase container may still be starting. Check with: docker ps${NC}"
fi

# -----------------------------------------------------------------------------
# Final summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Metabase Installation Complete                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}Metabase URL:${NC}     http://$(hostname -I | awk '{print $1}'):3000"
echo -e "  ${YELLOW}Config File:${NC}      $METABASE_DIR/docker-compose.yml"
echo ""
echo -e "  ${YELLOW}Service Commands:${NC}"
echo "    sudo systemctl status $SERVICE_NAME     # Check status"
echo "    sudo systemctl restart $SERVICE_NAME    # Restart"
echo "    cd $METABASE_DIR && docker compose logs -f  # View logs"
echo ""
echo -e "  ${YELLOW}First-Time Setup:${NC}"
echo "    1. Open http://$(hostname -I | awk '{print $1}'):3000 in your browser"
echo "    2. Create your Metabase admin account"
echo "    3. Add DealGenome database connection:"
echo "       - Database type: PostgreSQL"
echo "       - Host: host.docker.internal (or server IP)"
echo "       - Port: 5432"
echo "       - Database: pe_sourcing_db"
echo "       - Username: pe_sourcer"
echo "       - Password: (your database password)"
echo ""
echo -e "  ${YELLOW}Update DealGenome:${NC}"
echo "    Update METABASE_URL in /opt/pe-sourcing-engine/config/secrets.env"
echo "    to: http://localhost:3000"
echo ""
echo -e "${GREEN}Metabase installation complete!${NC}"
