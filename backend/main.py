# main.py - FastAPI Backend per Laboratorio Fonico
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
import tempfile
from typing import List, Optional
import json
import asyncio
from audio_analyzer import DatasetAnalyzer, AudioAnalyzer
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Laboratorio Fonico API",
    description="API per analisi vocale dei 4 elementi: Aria, Acqua, Terra, Fuoco",
    version="1.0.0"
)

# CORS per frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://fabiodeluca1977.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
dataset_analyzer = DatasetAnalyzer()
audio_analyzer = AudioAnalyzer()

# Configurazione cartelle
UPLOAD_DIR = "uploads"
DATASET_DIR = os.path.join(UPLOAD_DIR, "dataset")
TEMP_DIR = os.path.join(UPLOAD_DIR, "temp")

# Crea cartelle se non esistono
for directory in [UPLOAD_DIR, DATASET_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

for element in ['aria', 'acqua', 'terra', 'fuoco']:
    os.makedirs(os.path.join(DATASET_DIR, element), exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Laboratorio Fonico API - 4 Elementi",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload-audio/{element}",
            "analyze": "/analyze-dataset",
            "remove": "/remove-audio",
            "live_analysis": "/analyze-live",
            "patterns": "/distinctive-patterns",
            "stats": "/dataset-stats"
        }
    }

@app.post("/upload-audio/{element}")
async def upload_audio(
    element: str,
    files: List[UploadFile] = File(...)
):
    """Upload file audio per un elemento specifico"""
    if element not in ['aria', 'acqua', 'terra', 'fuoco']:
        raise HTTPException(status_code=400, detail="Elemento non valido")
    
    uploaded_files = []
    element_dir = os.path.join(DATASET_DIR, element)
    
    for file in files:
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
            continue
        
        # Salva file
        file_path = os.path.join(element_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append({
            "filename": file.filename,
            "element": element,
            "size": os.path.getsize(file_path),
            "path": file_path
        })
        
        logger.info(f"Uploaded: {file.filename} to {element}")
    
    return {
        "message": f"Caricati {len(uploaded_files)} file per {element}",
        "files": uploaded_files
    }

@app.post("/analyze-dataset")
async def analyze_dataset():
    """Analizza tutto il dataset e estrae features"""
    try:
        logger.info("🔬 Avvio analisi completa del dataset...")
        
        # Analizza dataset
        features_df = dataset_analyzer.analyze_dataset(DATASET_DIR)
        
        if len(features_df) == 0:
            raise HTTPException(status_code=400, detail="Nessun file audio trovato nel dataset")
        
        # Trova pattern distintivi
        patterns = dataset_analyzer.find_distinctive_patterns()
        
        # Prepara risultati
        results = {
            "analysis_summary": {
                "total_files": len(features_df),
                "elements_distribution": features_df['element'].value_counts().to_dict(),
                "analysis_status": "completed"
            },
            "distinctive_features": patterns['most_distinctive_features'][:10],
            "element_statistics": patterns['element_statistics'],
            "raw_data": features_df.to_dict('records')
        }
        
        # Salva risultati
        output_file = os.path.join(UPLOAD_DIR, "latest_analysis.json")
        dataset_analyzer.export_analysis(output_file)
        
        logger.info(f"✅ Analisi completata: {len(features_df)} file processati")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Errore durante l'analisi: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nell'analisi: {str(e)}")

@app.delete("/remove-audio")
async def remove_audio(filename: str, element: str):
    """Rimuove un file specifico dal dataset"""
    if element not in ['aria', 'acqua', 'terra', 'fuoco']:
        raise HTTPException(status_code=400, detail="Elemento non valido")
    
    # Rimuovi file fisico
    file_path = os.path.join(DATASET_DIR, element, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"🗑️ Removed file: {file_path}")
    
    # Rimuovi dal dataset analizzato
    removed = dataset_analyzer.remove_audio_file(filename, element)
    
    return {
        "message": f"File {filename} rimosso da {element}",
        "removed_from_analysis": removed,
        "removed_from_disk": os.path.exists(file_path) == False
    }

@app.post("/analyze-live")
async def analyze_live_audio(
    audio_file: UploadFile = File(...),
    element_hint: Optional[str] = Form(None)
):
    """Analizza un audio caricato/registrato live"""
    try:
        # Salva file temporaneo
        temp_path = os.path.join(TEMP_DIR, f"live_{audio_file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Analizza features
        features = audio_analyzer.extract_features(temp_path, element_hint or "unknown")
        
        # Predizione elemento (se hai dataset analizzato)
        prediction = None
        confidence = 0.0
        
        if dataset_analyzer.features_df is not None:
            prediction, confidence = _predict_element(features)
        
        # Cleanup
        os.remove(temp_path)
        
        return {
            "analysis": {
                "filename": audio_file.filename,
                "duration": features.duration,
                "features": vars(features)
            },
            "prediction": {
                "element": prediction,
                "confidence": confidence,
                "suggestion": _get_element_suggestion(features)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Errore analisi live: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nell'analisi: {str(e)}")

@app.post("/add-to-dataset")
async def add_to_dataset(
    audio_file: UploadFile = File(...),
    element: str = Form(...),
    confidence_threshold: float = Form(0.8)
):
    """Aggiunge un audio al dataset se l'analisi è buona"""
    if element not in ['aria', 'acqua', 'terra', 'fuoco']:
        raise HTTPException(status_code=400, detail="Elemento non valido")
    
    # Prima analizza l'audio
    live_analysis = await analyze_live_audio(audio_file, element)
    predicted_confidence = live_analysis['prediction']['confidence']
    
    if predicted_confidence < confidence_threshold:
        return {
            "added": False,
            "message": f"Confidence troppo bassa ({predicted_confidence:.2f} < {confidence_threshold})",
            "analysis": live_analysis
        }
    
    # Se la confidence è alta, aggiunge al dataset
    element_dir = os.path.join(DATASET_DIR, element)
    final_path = os.path.join(element_dir, audio_file.filename)
    
    # Reset file pointer e salva
    audio_file.file.seek(0)
    with open(final_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
    
    logger.info(f"✅ Added {audio_file.filename} to {element} dataset")
    
    return {
        "added": True,
        "message": f"Audio aggiunto al dataset {element}",
        "confidence": predicted_confidence,
        "path": final_path
    }

@app.get("/distinctive-patterns")
async def get_distinctive_patterns():
    """Restituisce i pattern più distintivi trovati"""
    if dataset_analyzer.features_df is None:
        raise HTTPException(status_code=400, detail="Nessun dataset analizzato")
    
    patterns = dataset_analyzer.find_distinctive_patterns()
    return patterns

@app.get("/dataset-stats")
async def get_dataset_stats():
    """Statistiche del dataset corrente"""
    stats = {}
    
    for element in ['aria', 'acqua', 'terra', 'fuoco']:
        element_dir = os.path.join(DATASET_DIR, element)
        if os.path.exists(element_dir):
            files = [f for f in os.listdir(element_dir) 
                    if f.lower().endswith(('.wav', '.mp3', '.m4a', '.flac'))]
            stats[element] = {
                "file_count": len(files),
                "files": files
            }
    
    return {
        "dataset_statistics": stats,
        "total_files": sum(s["file_count"] for s in stats.values()),
        "analysis_available": dataset_analyzer.features_df is not None
    }

@app.get("/export-analysis")
async def export_analysis():
    """Esporta l'analisi completa"""
    if dataset_analyzer.features_df is None:
        raise HTTPException(status_code=400, detail="Nessun dataset analizzato")
    
    export_path = os.path.join(UPLOAD_DIR, "complete_analysis.json")
    dataset_analyzer.export_analysis(export_path)
    
    return {
        "message": "Analisi esportata",
        "export_path": export_path,
        "file_size": os.path.getsize(export_path)
    }

def _predict_element(features) -> tuple[str, float]:
    """Predice l'elemento basandosi sui pattern del dataset"""
    # Implementazione semplificata - in produzione useresti ML
    # Per ora, usa regole basate sui pattern trovati
    
    if features.pitch_trend == 'ascending' and features.rms_mean > 0.1:
        if features.speech_rate > 3.5:
            return "fuoco", 0.85
        else:
            return "aria", 0.78
    elif features.pitch_trend == 'descending':
        if features.pause_ratio > 0.3:
            return "acqua", 0.82
        else:
            return "terra", 0.75
    else:
        return "unknown", 0.5

def _get_element_suggestion(features) -> str:
    """Suggerisce caratteristiche dell'elemento identificato"""
    element, confidence = _predict_element(features)
    
    suggestions = {
        "aria": f"Caratteristiche ARIA rilevate: tono in salita, ritmo {features.speech_rate:.1f} frasi/min, energia media-alta",
        "acqua": f"Caratteristiche ACQUA rilevate: tono in discesa, pause lunghe ({features.pause_ratio:.1%}), energia bassa",
        "terra": f"Caratteristiche TERRA rilevate: tono stabile-discesa, ritmo regolare, energia media",
        "fuoco": f"Caratteristiche FUOCO rilevate: tono in salita, ritmo sostenuto ({features.speech_rate:.1f}), energia alta",
        "unknown": "Pattern non chiaro - servono più dati per training"
    }
    
    return suggestions.get(element, "Analisi inconclusiva")

# Endpoint per gestione recording dal browser
@app.post("/upload-recording")
async def upload_recording(
    audio_blob: UploadFile = File(...),
    auto_classify: bool = Form(True)
):
    """Gestisce recording dal microfono del browser"""
    try:
        # Salva recording temporaneo
        temp_filename = f"recording_{audio_blob.filename or 'audio.wav'}"
        temp_path = os.path.join(TEMP_DIR, temp_filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_blob.file, buffer)
        
        # Analizza se richiesto
        analysis_result = None
        if auto_classify:
            features = audio_analyzer.extract_features(temp_path, "live_recording")
            prediction, confidence = _predict_element(features)
            
            analysis_result = {
                "predicted_element": prediction,
                "confidence": confidence,
                "features_summary": {
                    "duration": features.duration,
                    "pitch_trend": features.pitch_trend,
                    "average_volume": features.rms_mean,
                    "speech_rate": features.speech_rate,
                    "pause_ratio": features.pause_ratio
                },
                "suggestion": _get_element_suggestion(features)
            }
        
        return {
            "status": "recording_processed",
            "filename": temp_filename,
            "size": os.path.getsize(temp_path),
            "analysis": analysis_result,
            "actions": {
                "can_add_to_dataset": analysis_result and analysis_result["confidence"] > 0.7,
                "suggested_element": analysis_result["predicted_element"] if analysis_result else None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Errore processing recording: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nel processing: {str(e)}")

@app.get("/compare-elements/{feature_name}")
async def compare_elements_by_feature(feature_name: str):
    """Confronta i 4 elementi per una specifica feature"""
    if dataset_analyzer.features_df is None:
        raise HTTPException(status_code=400, detail="Nessun dataset analizzato")
    
    df = dataset_analyzer.features_df
    
    if feature_name not in df.columns:
        available_features = [col for col in df.columns if col not in ['filename', 'element']]
        raise HTTPException(
            status_code=400, 
            detail=f"Feature '{feature_name}' non trovata. Disponibili: {available_features}"
        )
    
    comparison = {}
    for element in ['aria', 'acqua', 'terra', 'fuoco']:
        element_data = df[df['element'] == element][feature_name]
        if len(element_data) > 0:
            comparison[element] = {
                "mean": float(element_data.mean()),
                "std": float(element_data.std()),
                "min": float(element_data.min()),
                "max": float(element_data.max()),
                "count": len(element_data),
                "values": element_data.tolist()  # Per grafici dettagliati
            }
    
    return {
        "feature": feature_name,
        "comparison": comparison,
        "interpretation": _interpret_feature_comparison(feature_name, comparison)
    }

def _interpret_feature_comparison(feature_name: str, comparison: dict) -> str:
    """Interpreta il confronto tra elementi per una feature"""
    interpretations = {
        "pitch_mean": "Frequenza fondamentale media - indica registro vocale",
        "pitch_trend": "Direzione melodica - salita=energia, discesa=rilassamento",
        "rms_mean": "Volume medio - intensità energetica della voce",
        "speech_rate": "Velocità eloquio - rapidità di espressione",
        "pause_ratio": "Rapporto pause - quanto silenzio nella comunicazione",
        "spectral_centroid_mean": "Brillantezza del suono - chiarezza vs gravità",
        "vowel_elongation_ratio": "Allungamenti vocalici - espressività emotiva"
    }
    
    base_interpretation = interpretations.get(feature_name, "Feature sconosciuta")
    
    # Trova elemento con valore più alto e più basso
    if comparison:
        max_element = max(comparison.keys(), key=lambda k: comparison[k]['mean'])
        min_element = min(comparison.keys(), key=lambda k: comparison[k]['mean'])
        
        return f"{base_interpretation}. {max_element.upper()} ha valori più alti, {min_element.upper()} più bassi."
    
    return base_interpretation

@app.get("/sample-audio/{element}")
async def get_sample_audio(element: str, sample_type: str = "representative"):
    """Restituisce un campione rappresentativo per un elemento"""
    if element not in ['aria', 'acqua', 'terra', 'fuoco']:
        raise HTTPException(status_code=400, detail="Elemento non valido")
    
    if dataset_analyzer.features_df is None:
        raise HTTPException(status_code=400, detail="Nessun dataset analizzato")
    
    df = dataset_analyzer.features_df
    element_data = df[df['element'] == element]
    
    if len(element_data) == 0:
        raise HTTPException(status_code=404, detail=f"Nessun campione trovato per {element}")
    
    # Seleziona campione in base al tipo richiesto
    if sample_type == "representative":
        # Campione più vicino alla media dell'elemento
        means = element_data.select_dtypes(include=[np.number]).mean()
        distances = element_data.select_dtypes(include=[np.number]).apply(
            lambda row: np.sqrt(((row - means) ** 2).sum()), axis=1
        )
        sample_idx = distances.idxmin()
    elif sample_type == "extreme_high":
        # Campione con energia più alta
        sample_idx = element_data['rms_mean'].idxmax()
    elif sample_type == "extreme_low":
        # Campione con energia più bassa
        sample_idx = element_data['rms_mean'].idxmin()
    else:
        # Random
        sample_idx = element_data.sample(1).index[0]
    
    sample = element_data.loc[sample_idx]
    
    return {
        "element": element,
        "sample_type": sample_type,
        "filename": sample['filename'],
        "features": sample.to_dict(),
        "interpretation": f"Campione {sample_type} per {element}: {sample['filename']}"
    }

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Restituisce tutti i dati necessari per il dashboard scientifico"""
    if dataset_analyzer.features_df is None:
        return {
            "status": "no_analysis",
            "message": "Nessun dataset analizzato. Carica file e avvia analisi."
        }
    
    df = dataset_analyzer.features_df
    patterns = dataset_analyzer.find_distinctive_patterns()
    
    # Prepara dati per grafici
    chart_data = {}
    
    # Top 5 features più distintive
    top_features = [item[0] for item in patterns['most_distinctive_features'][:5]]
    
    for feature in top_features:
        chart_data[feature] = {}
        for element in ['aria', 'acqua', 'terra', 'fuoco']:
            element_data = df[df['element'] == element][feature].tolist()
            chart_data[feature][element] = element_data
    
    return {
        "status": "ready",
        "summary": {
            "total_files": len(df),
            "elements_count": df['element'].value_counts().to_dict(),
            "top_distinctive_features": patterns['most_distinctive_features'][:10]
        },
        "element_profiles": patterns['element_statistics'],
        "chart_data": chart_data,
        "correlation_matrix": _calculate_feature_correlations(df),
        "recommendations": _generate_analysis_recommendations(df, patterns)
    }

def _calculate_feature_correlations(df):
    """Calcola correlazioni tra features numeriche"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlation_matrix = df[numeric_cols].corr()
    
    # Converte in formato JSON-friendly
    return {
        "features": numeric_cols.tolist(),
        "matrix": correlation_matrix.round(3).to_dict()
    }

def _generate_analysis_recommendations(df, patterns):
    """Genera raccomandazioni per migliorare l'analisi"""
    recommendations = []
    
    # Controlla bilanciamento dataset
    counts = df['element'].value_counts()
    if counts.max() / counts.min() > 3:
        recommendations.append({
            "type": "balance",
            "message": f"Dataset sbilanciato: {counts.to_dict()}. Aggiungi più campioni per elementi con meno file.",
            "priority": "high"
        })
    
    # Controlla numero minimo campioni
    for element, count in counts.items():
        if count < 5:
            recommendations.append({
                "type": "samples",
                "message": f"Solo {count} campioni per {element}. Minimo consigliato: 10 per analisi robusta.",
                "priority": "medium"
            })
    
    # Controlla distintività
    avg_distinctiveness = np.mean([item[1]['distinctive_score'] 
                                  for item in patterns['most_distinctive_features'][:5]])
    if avg_distinctiveness < 5:
        recommendations.append({
            "type": "distinctiveness",
            "message": "Pattern poco distintivi. Considera di rivedere la classificazione di alcuni file.",
            "priority": "medium"
        })
    
    return recommendations

# Aggiungere al main.py - Endpoints per gestione progetti

from project_manager import ProjectManager
from fastapi import UploadFile
from fastapi.responses import FileResponse

# Inizializza project manager
project_manager = ProjectManager()

@app.get("/projects")
async def list_projects():
    """Lista tutti i progetti disponibili"""
    try:
        projects = project_manager.list_projects()
        return {
            "projects": projects,
            "total": len(projects),
            "current_project": project_manager.current_project
        }
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/create")
async def create_project(
    name: str = Form(...),
    description: str = Form(""),
    trainer: str = Form("")
):
    """Crea un nuovo progetto"""
    try:
        metadata = project_manager.create_project(name, description, trainer)
        logger.info(f"✅ Created project: {metadata['project_id']}")
        return {
            "status": "created",
            "project": metadata
        }
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/load/{project_id}")
async def load_project(project_id: str):
    """Carica un progetto specifico"""
    try:
        metadata = project_manager.load_project(project_id)
        logger.info(f"✅ Loaded project: {project_id}")
        return {
            "status": "loaded",
            "project": metadata,
            "message": f"Progetto {metadata['name']} caricato con successo"
        }
    except Exception as e:
        logger.error(f"Error loading project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/projects/save")
async def save_current_project():
    """Salva lo stato attuale del progetto"""
    try:
        if not project_manager.current_project:
            raise HTTPException(status_code=400, detail="Nessun progetto attivo")
        
        # Ottieni risultati analisi se disponibili
        analysis_results = None
        if dataset_analyzer.features_df is not None:
            patterns = dataset_analyzer.find_distinctive_patterns()
            analysis_results = {
                "analysis_summary": {
                    "total_files": len(dataset_analyzer.features_df),
                    "elements_distribution": dataset_analyzer.features_df['element'].value_counts().to_dict(),
                    "analysis_timestamp": pd.Timestamp.now().isoformat()
                },
                "distinctive_patterns": patterns
            }
        
        success = project_manager.save_project_state(analysis_results)
        
        if success:
            return {
                "status": "saved",
                "project_id": project_manager.current_project,
                "message": "Progetto salvato con successo"
            }
    except Exception as e:
        logger.error(f"Error saving project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/duplicate/{project_id}")
async def duplicate_project(
    project_id: str,
    new_name: str = Form(...),
    trainer: str = Form("")
):
    """Duplica un progetto esistente"""
    try:
        new_metadata = project_manager.duplicate_project(project_id, new_name, trainer)
        logger.info(f"✅ Duplicated project {project_id} to {new_metadata['project_id']}")
        return {
            "status": "duplicated",
            "original_project": project_id,
            "new_project": new_metadata
        }
    except Exception as e:
        logger.error(f"Error duplicating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Elimina un progetto"""
    try:
        success = project_manager.delete_project(project_id)
        if success:
            logger.info(f"🗑️ Deleted project: {project_id}")
            return {
                "status": "deleted",
                "project_id": project_id,
                "message": "Progetto eliminato con successo"
            }
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/export/{project_id}")
async def export_project(project_id: str):
    """Esporta un progetto come file ZIP"""
    try:
        export_path = project_manager.export_project(project_id)
        logger.info(f"📦 Exported project {project_id} to {export_path}")
        
        return FileResponse(
            path=export_path,
            filename=f"{project_id}_export.zip",
            media_type="application/zip"
        )
    except Exception as e:
        logger.error(f"Error exporting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/import")
async def import_project(
    project_file: UploadFile = File(...),
    new_name: str = Form(None)
):
    """Importa un progetto da file ZIP"""
    try:
        # Salva file temporaneo
        temp_path = os.path.join(TEMP_DIR, f"import_{project_file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(project_file.file, buffer)
        
        # Importa progetto
        metadata = project_manager.import_project(temp_path, new_name)
        
        # Cleanup
        os.remove(temp_path)
        
        logger.info(f"📥 Imported project: {metadata['project_id']}")
        return {
            "status": "imported",
            "project": metadata,
            "message": f"Progetto {metadata['name']} importato con successo"
        }
    except Exception as e:
        logger.error(f"Error importing project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/compare")
async def compare_projects(project_ids: str):
    """Confronta statistiche tra progetti"""
    try:
        # Parse project IDs (comma separated)
        ids_list = [pid.strip() for pid in project_ids.split(',')]
        
        comparison = project_manager.get_project_comparison(ids_list)
        return comparison
    except Exception as e:
        logger.error(f"Error comparing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/current")
async def get_current_project():
    """Ottieni informazioni sul progetto attualmente attivo"""
    if not project_manager.current_project:
        return {
            "status": "no_active_project",
            "message": "Nessun progetto attivo"
        }
    
    try:
        project_path = project_manager.projects_dir / project_manager.current_project
        metadata_file = project_path / "project.json"
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Aggiorna statistiche
        metadata['statistics'] = project_manager._calculate_project_stats(project_path)
        
        return {
            "status": "active",
            "project": metadata
        }
    except Exception as e:
        logger.error(f"Error getting current project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/auto-save")
async def toggle_auto_save(project_id: str, enabled: bool = Form(...)):
    """Attiva/disattiva salvataggio automatico per un progetto"""
    try:
        project_path = project_manager.projects_dir / project_id
        metadata_file = project_path / "project.json"
        
        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        metadata['settings']['auto_backup'] = enabled
        metadata['last_modified'] = datetime.now().isoformat()
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "status": "updated",
            "auto_save": enabled,
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Error updating auto-save for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Middleware per auto-save
@app.middleware("http")
async def auto_save_middleware(request, call_next):
    """Middleware per salvataggio automatico dopo operazioni critiche"""
    response = await call_next(request)
    
    # Auto-save dopo upload o analisi
    if (request.url.path.startswith("/upload-audio") or 
        request.url.path.startswith("/analyze-dataset")) and \
        response.status_code == 200:
        
        try:
            if project_manager.current_project:
                # Verifica se auto-save è abilitato
                project_path = project_manager.projects_dir / project_manager.current_project
                metadata_file = project_path / "project.json"
                
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    if metadata.get('settings', {}).get('auto_backup', True):
                        # Auto-save asincrono
                        import asyncio
                        asyncio.create_task(async_auto_save())
        except Exception as e:
            logger.warning(f"Auto-save failed: {e}")
    
    return response

async def async_auto_save():
    """Salvataggio automatico asincrono"""
    try:
        await asyncio.sleep(1)  # Piccolo delay per non interferire con operazioni in corso
        
        analysis_results = None
        if dataset_analyzer.features_df is not None:
            patterns = dataset_analyzer.find_distinctive_patterns()
            analysis_results = {
                "analysis_summary": {
                    "total_files": len(dataset_analyzer.features_df),
                    "elements_distribution": dataset_analyzer.features_df['element'].value_counts().to_dict(),
                    "analysis_timestamp": pd.Timestamp.now().isoformat()
                },
                "distinctive_patterns": patterns
            }
        
        project_manager.save_project_state(analysis_results)
        logger.info(f"🔄 Auto-saved project: {project_manager.current_project}")
    except Exception as e:
        logger.warning(f"Auto-save failed: {e}")

if __name__ == "__main__":
    import uvicorn
    
    print("🎙️ Avvio Laboratorio Fonico API...")
    print("📊 Endpoints disponibili su http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )