@echo off
REM Build VeriSight Extension for Chrome Web Store
REM Creates a production-ready zip file

echo Building VeriSight Extension...

REM Set variables
set EXTENSION_DIR=frontend
set BUILD_DIR=build

REM Clean build directory
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

REM Copy extension files
echo Copying extension files...
xcopy /E /I /Y "%EXTENSION_DIR%\*" "%BUILD_DIR%\"

REM Create zip file (requires PowerShell)
echo Creating zip file...
powershell -Command "Compress-Archive -Path '%BUILD_DIR%\*' -DestinationPath 'verisight-extension-v1.0.0.zip' -Force"

echo Extension built successfully: verisight-extension-v1.0.0.zip
echo Ready for Chrome Web Store upload!
