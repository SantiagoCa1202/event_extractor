# Event Extractor - EXE Deployment Guide

## Requisitos previos para compilar

1. **Python 3.10+** instalado
2. **Tesseract-OCR** instalado en `C:\Program Files\Tesseract-OCR\`
3. **PyInstaller** (se instala automáticamente)

## Pasos para crear el EXE

### Opción 1: Script automático (Recomendado)

```bash
# En la raíz del proyecto
build.bat
```

El script:
- Verifica las dependencias
- Compila el ejecutable
- Genera la carpeta `dist/EventExtractor/`

### Opción 2: Manual

```bash
# Instalar dependencias
pip install -r requirements.txt
pip install pyinstaller

# Compilar
pyinstaller event_extractor.spec --noconfirm --clean
```

## Después de compilar

La carpeta `dist/EventExtractor/` contiene:
- `EventExtractor.exe` - Aplicación principal
- Todas las librerías necesarias (pdfplumber, openpyxl, etc.)
- Carpeta `assets/` con archivos de configuración

## Distribuir la aplicación

Para usar en otra máquina:

1. **Sin Tesseract instalado**: El EXE funcionará solo para funciones básicas
2. **Con Tesseract instalado**: Todas las funciones de OCR estarán disponibles

### Instalador Tesseract (si es necesario):
Descargar de: https://github.com/UB-Mannheim/tesseract/wiki

## Solución de problemas

### "Tesseract no encontrado"
- Instala Tesseract en `C:\Program Files\Tesseract-OCR\`
- O modifica `config.py` con la ruta correcta

### "Falta la carpeta assets"
- Asegúrate que `assets/` esté en la carpeta de distribución
- Se copia automáticamente durante la compilación

### El EXE es muy grande
- Esto es normal (~200-300 MB)
- Contiene todas las librerías necesarias

## Notas

- El primer ejecutable tarda más en iniciar (es normal)
- Requiere .NET Framework en máquinas muy viejas (Windows XP/Vista)
- Las máquinas con poca RAM (<2GB) pueden tener lentitud

## Próximas mejoras opcionales

- Crear instalador NSIS (.msi)
- Agregar actualizaciones automáticas
- Firmar digitalmente el ejecutable
