Write-Host "Creazione struttura backend..." -ForegroundColor Yellow

# Creare cartelle backend
New-Item -Path "backend" -ItemType Directory -Force
New-Item -Path "backend\uploads" -ItemType Directory -Force
New-Item -Path "backend\uploads\dataset" -ItemType Directory -Force
New-Item -Path "backend\uploads\dataset\aria" -ItemType Directory -Force
New-Item -Path "backend\uploads\dataset\acqua" -ItemType Directory -Force  
New-Item -Path "backend\uploads\dataset\terra" -ItemType Directory -Force
New-Item -Path "backend\uploads\dataset\fuoco" -ItemType Directory -Force
New-Item -Path "backend\uploads\temp" -ItemType Directory -Force

# Creare cartella components frontend
New-Item -Path "frontend\src\components" -ItemType Directory -Force

Write-Host "Struttura creata!" -ForegroundColor Green
Write-Host "Ora copia manualmente i file dagli artifact di Claude:" -ForegroundColor Yellow
Write-Host "1. backend\audio_analyzer.py" -ForegroundColor White
Write-Host "2. backend\main.py" -ForegroundColor White  
Write-Host "3. backend\requirements.txt" -ForegroundColor White
Write-Host "4. frontend\src\components\VoiceLab.jsx" -ForegroundColor White