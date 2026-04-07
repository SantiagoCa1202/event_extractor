@echo off
REM Script para compilar el evento extractor a ejecutable
REM Requiere: Python + PyInstaller + Tesseract OCR instalados

echo ============================================
echo Event Extractor - Build Script
echo ============================================
echo.

REM Verificar si PyInstaller está instalado
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller no está instalado.
    echo Instalando PyInstaller...
    pip install pyinstaller
)

REM Verificar si Tesseract está instalado
if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo.
    echo ADVERTENCIA: Tesseract-OCR no se encontró en la ubicación por defecto
    echo Descárgalo en: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
)

echo.
echo Compilando aplicación...
echo.

pyinstaller event_extractor.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo ERROR: La compilación falló
    pause
    exit /b 1
)

echo.
echo ============================================
echo Compilación completada exitosamente!
echo ============================================
echo.
echo El ejecutable se encuentra en: dist\EventExtractor\
echo.
pause
