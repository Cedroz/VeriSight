@echo off
REM Production Setup Script for VeriSight Backend
REM Sets up production environment with proper permissions and configuration

echo Setting up VeriSight for production...

REM Check if .env exists
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env with your production values!
)

REM Create necessary directories
echo Creating directories...
if not exist logs mkdir logs
if not exist data mkdir data
if not exist backups mkdir backups

REM Copy database if it exists
if exist backend\brands.db.json (
    echo Copying database to data directory...
    copy backend\brands.db.json data\brands.db.json
)

echo Production setup complete!
echo.
echo Next steps:
echo 1. Edit .env with your production configuration
echo 2. Update CORS_ORIGINS to restrict access
echo 3. Run: docker-compose up -d
echo    OR: python backend\main.py
