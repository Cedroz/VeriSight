#!/bin/bash
# Production Setup Script for VeriSight Backend
# Sets up production environment with proper permissions and configuration

set -e

echo "Setting up VeriSight for production..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your production values!"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p backups

# Copy database if it exists
if [ -f backend/brands.db.json ]; then
    echo "Copying database to data directory..."
    cp backend/brands.db.json data/brands.db.json
fi

# Set proper permissions
echo "Setting permissions..."
chmod 600 .env 2>/dev/null || true
chmod 644 data/*.json 2>/dev/null || true

# Create log directory with proper permissions
touch logs/verisight.log 2>/dev/null || true
chmod 664 logs/verisight.log 2>/dev/null || true

echo "Production setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your production configuration"
echo "2. Update CORS_ORIGINS to restrict access"
echo "3. Run: docker-compose up -d"
echo "   OR: python backend/main.py (with production server)"
