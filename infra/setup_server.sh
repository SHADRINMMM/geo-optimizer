#!/bin/bash
# One-time EC2 server setup script
# Run as: bash setup_server.sh
set -e

echo "=== GEO Optimizer — EC2 Setup ==="

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# Install nginx + certbot
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Install git
sudo apt-get install -y git

# Clone repo (replace with actual repo URL)
cd /home/ubuntu
git clone https://github.com/SHADRINMMM/geo-optimizer.git || true

# Set up nginx
sudo cp /home/ubuntu/geo-optimizer/infra/nginx.conf /etc/nginx/sites-available/geo-optimizer
sudo ln -sf /etc/nginx/sites-available/geo-optimizer /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# SSL cert (certbot)
echo "Run: sudo certbot --nginx -d ai.causabi.com"
echo ""
echo "Then set GitHub secrets:"
echo "  EC2_HOST = 98.89.42.222"
echo "  EC2_SSH_KEY = (contents of causa.pem)"
echo ""
echo "Setup complete. Add .env file to /home/ubuntu/geo-optimizer/backend/.env"
