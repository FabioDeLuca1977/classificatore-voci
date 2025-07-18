# Migration Script PowerShell - Solo comandi Windows
Write-Host "🔬 MIGRAZIONE A LABORATORIO FONICO" -ForegroundColor Cyan

$projectPath = "C:\temp-deploy\classificatore-voci"
$backendPath = Join-Path $projectPath "backend"

# Creare struttura backend
Write-Host "🏗️ Creazione struttura backend..." -ForegroundColor Yellow

$backendDirs = @(
    "backend",
    "backend\uploads", 
    "backend\uploads\dataset",
    "backend\uploads\dataset\aria",
    "backend\uploads\dataset\acqua",
    "backend\uploads\dataset\terra", 
    "backend\uploads\dataset\fuoco",
    "backend\uploads\temp"
)

foreach ($dir in $backendDirs) {
    $fullPath = Join-Path $projectPath $dir
    if (!(Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "✅ Creata: $dir" -ForegroundColor Green
    }
}

# Aggiornare App.js
$appJsContent = @"
import React from 'react';
import VoiceLab from './components/VoiceLab';
import './App.css';

function App() {
  return (
    <div className="App">
      <VoiceLab />
    </div>
  );
}

export default App;
"@

$appJsContent | Out-File -FilePath (Join-Path $projectPath "frontend\src\App.js") -Encoding UTF8

# Creare cartella components
$componentsPath = Join-Path $projectPath "frontend\src\components"
if (!(Test-Path $componentsPath)) {
    New-Item -ItemType Directory -Path $componentsPath -Force | Out-Null
}

# Creare file VoiceLab.jsx vuoto
$voiceLabPath = Join-Path $componentsPath "VoiceLab.jsx"
New-Item -ItemType File -Path $voiceLabPath -Force | Out-Null

Write-Host "✅ STRUTTURA CREATA!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 PASSI MANUALI:" -ForegroundColor Cyan
Write-Host "1. Copiare il backend Python dagli artifact di Claude" -ForegroundColor White
Write-Host "2. Copiare VoiceLab.jsx dall'artifact React" -ForegroundColor White
Write-Host "3. Copiare README.md dall'artifact documentazione" -ForegroundColor White
Write-Host ""
Write-Host "📁 File da creare manualmente:" -ForegroundColor Yellow
Write-Host "- backend\audio_analyzer.py" -ForegroundColor Gray
Write-Host "- backend\main.py" -ForegroundColor Gray  
Write-Host "- backend\requirements.txt" -ForegroundColor Gray
Write-Host "- frontend\src\components\VoiceLab.jsx" -ForegroundColor Gray
Write-Host "- README.md" -ForegroundColor Gray

Read-Host "Premere Enter per continuare..."