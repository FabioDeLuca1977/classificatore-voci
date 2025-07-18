# project_manager.py - Sistema di gestione progetti multipli
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
import zipfile
import tempfile
from pathlib import Path

class ProjectManager:
    """Gestisce salvataggio/caricamento di progetti multipli del laboratorio"""
    
    def __init__(self, base_projects_dir: str = "projects"):
        self.projects_dir = Path(base_projects_dir)
        self.projects_dir.mkdir(exist_ok=True)
        self.current_project = None
        
    def create_project(self, name: str, description: str = "", trainer: str = "") -> Dict[str, Any]:
        """Crea un nuovo progetto"""
        # Sanitize project name
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        project_id = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        project_path = self.projects_dir / project_id
        project_path.mkdir(exist_ok=True)
        
        # Crea struttura dataset per il progetto
        dataset_path = project_path / "dataset"
        dataset_path.mkdir(exist_ok=True)
        
        for element in ['aria', 'acqua', 'terra', 'fuoco']:
            (dataset_path / element).mkdir(exist_ok=True)
        
        # Metadata del progetto
        metadata = {
            "project_id": project_id,
            "name": name,
            "description": description,
            "trainer": trainer,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "version": "1.0",
            "status": "active",
            "statistics": {
                "total_files": 0,
                "analysis_runs": 0,
                "best_accuracy": 0.0,
                "elements_distribution": {"aria": 0, "acqua": 0, "terra": 0, "fuoco": 0}
            },
            "settings": {
                "target_accuracy": 0.96,
                "auto_backup": True,
                "analysis_threshold": 0.85
            }
        }
        
        # Salva metadata
        with open(project_path / "project.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.current_project = project_id
        return metadata
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """Lista tutti i progetti disponibili"""
        projects = []
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / "project.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        # Aggiorna statistiche in tempo reale
                        metadata["statistics"] = self._calculate_project_stats(project_dir)
                        projects.append(metadata)
                    except Exception as e:
                        print(f"Error loading project {project_dir}: {e}")
        
        # Ordina per data di modifica
        projects.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
        return projects
    
    def load_project(self, project_id: str) -> Dict[str, Any]:
        """Carica un progetto specifico"""
        project_path = self.projects_dir / project_id
        
        if not project_path.exists():
            raise ValueError(f"Progetto {project_id} non trovato")
        
        metadata_file = project_path / "project.json"
        if not metadata_file.exists():
            raise ValueError(f"Metadata del progetto {project_id} mancante")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Copia i file del progetto nella cartella di lavoro attiva
        self._activate_project_dataset(project_id)
        
        self.current_project = project_id
        
        # Aggiorna last_modified
        metadata['last_modified'] = datetime.now().isoformat()
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    def save_project_state(self, analysis_results: Optional[Dict] = None) -> bool:
        """Salva lo stato attuale del progetto"""
        if not self.current_project:
            raise ValueError("Nessun progetto attivo")
        
        project_path = self.projects_dir / self.current_project
        
        # Copia i file dal dataset attivo al progetto
        self._backup_current_dataset()
        
        # Salva risultati analisi se forniti
        if analysis_results:
            analysis_file = project_path / "latest_analysis.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis_results, f, indent=2)
        
        # Aggiorna metadata
        metadata_file = project_path / "project.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        metadata['last_modified'] = datetime.now().isoformat()
        metadata['statistics'] = self._calculate_project_stats(project_path)
        
        if analysis_results and 'analysis_summary' in analysis_results:
            summary = analysis_results['analysis_summary']
            metadata['statistics']['analysis_runs'] += 1
            metadata['statistics']['total_files'] = summary.get('total_files', 0)
            
            # Aggiorna best accuracy se migliore
            if 'accuracy' in summary:
                current_accuracy = summary['accuracy']
                if current_accuracy > metadata['statistics']['best_accuracy']:
                    metadata['statistics']['best_accuracy'] = current_accuracy
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
    
    def duplicate_project(self, project_id: str, new_name: str, trainer: str = "") -> Dict[str, Any]:
        """Duplica un progetto esistente"""
        source_path = self.projects_dir / project_id
        
        if not source_path.exists():
            raise ValueError(f"Progetto sorgente {project_id} non trovato")
        
        # Crea nuovo progetto
        new_metadata = self.create_project(new_name, f"Duplicato da {project_id}", trainer)
        new_project_id = new_metadata['project_id']
        new_path = self.projects_dir / new_project_id
        
        # Copia tutti i file del dataset
        source_dataset = source_path / "dataset"
        target_dataset = new_path / "dataset"
        
        if source_dataset.exists():
            shutil.copytree(source_dataset, target_dataset, dirs_exist_ok=True)
        
        # Copia analisi se esistono
        source_analysis = source_path / "latest_analysis.json"
        if source_analysis.exists():
            shutil.copy2(source_analysis, new_path / "latest_analysis.json")
        
        return new_metadata
    
    def delete_project(self, project_id: str) -> bool:
        """Elimina un progetto (con conferma)"""
        project_path = self.projects_dir / project_id
        
        if not project_path.exists():
            raise ValueError(f"Progetto {project_id} non trovato")
        
        # Crea backup prima di eliminare
        backup_path = self.projects_dir / f"DELETED_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(str(project_path), str(backup_path))
        
        if self.current_project == project_id:
            self.current_project = None
        
        return True
    
    def export_project(self, project_id: str, export_path: str = None) -> str:
        """Esporta un progetto come file ZIP"""
        project_path = self.projects_dir / project_id
        
        if not project_path.exists():
            raise ValueError(f"Progetto {project_id} non trovato")
        
        if not export_path:
            export_path = f"{project_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_path)
                    zipf.write(file_path, arcname)
        
        return export_path
    
    def import_project(self, zip_path: str, new_name: str = None) -> Dict[str, Any]:
        """Importa un progetto da file ZIP"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Estrai ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Leggi metadata originale
            metadata_file = Path(temp_dir) / "project.json"
            if not metadata_file.exists():
                raise ValueError("File ZIP non valido: manca project.json")
            
            with open(metadata_file, 'r') as f:
                original_metadata = json.load(f)
            
            # Crea nuovo progetto
            project_name = new_name or f"Imported_{original_metadata.get('name', 'Unknown')}"
            new_metadata = self.create_project(
                project_name, 
                f"Importato da {original_metadata.get('name', 'Unknown')}", 
                original_metadata.get('trainer', '')
            )
            
            # Copia file
            new_project_path = self.projects_dir / new_metadata['project_id']
            
            # Copia dataset
            source_dataset = Path(temp_dir) / "dataset"
            if source_dataset.exists():
                target_dataset = new_project_path / "dataset"
                shutil.copytree(source_dataset, target_dataset, dirs_exist_ok=True)
            
            # Copia analisi
            source_analysis = Path(temp_dir) / "latest_analysis.json"
            if source_analysis.exists():
                shutil.copy2(source_analysis, new_project_path / "latest_analysis.json")
        
        return new_metadata
    
    def _calculate_project_stats(self, project_path: Path) -> Dict[str, Any]:
        """Calcola statistiche del progetto"""
        stats = {
            "total_files": 0,
            "elements_distribution": {"aria": 0, "acqua": 0, "terra": 0, "fuoco": 0},
            "total_size_mb": 0.0,
            "analysis_available": False
        }
        
        dataset_path = project_path / "dataset"
        if dataset_path.exists():
            for element in ['aria', 'acqua', 'terra', 'fuoco']:
                element_path = dataset_path / element
                if element_path.exists():
                    audio_files = [f for f in element_path.iterdir() 
                                 if f.suffix.lower() in ['.wav', '.mp3', '.m4a', '.flac']]
                    stats['elements_distribution'][element] = len(audio_files)
                    stats['total_files'] += len(audio_files)
                    
                    # Calcola dimensione
                    for file in audio_files:
                        stats['total_size_mb'] += file.stat().st_size / (1024 * 1024)
        
        # Verifica se esiste analisi
        analysis_file = project_path / "latest_analysis.json"
        stats['analysis_available'] = analysis_file.exists()
        
        return stats
    
    def _activate_project_dataset(self, project_id: str):
        """Copia il dataset del progetto nella cartella di lavoro"""
        project_path = self.projects_dir / project_id
        source_dataset = project_path / "dataset"
        target_dataset = Path("uploads/dataset")
        
        # Pulisci dataset attuale
        if target_dataset.exists():
            shutil.rmtree(target_dataset)
        
        # Copia dataset del progetto
        if source_dataset.exists():
            shutil.copytree(source_dataset, target_dataset)
        else:
            # Crea struttura vuota
            target_dataset.mkdir(parents=True, exist_ok=True)
            for element in ['aria', 'acqua', 'terra', 'fuoco']:
                (target_dataset / element).mkdir(exist_ok=True)
    
    def _backup_current_dataset(self):
        """Salva il dataset attuale nel progetto corrente"""
        if not self.current_project:
            return
        
        project_path = self.projects_dir / self.current_project
        source_dataset = Path("uploads/dataset")
        target_dataset = project_path / "dataset"
        
        if source_dataset.exists():
            if target_dataset.exists():
                shutil.rmtree(target_dataset)
            shutil.copytree(source_dataset, target_dataset)
    
    def get_project_comparison(self, project_ids: List[str]) -> Dict[str, Any]:
        """Confronta statistiche tra progetti"""
        comparison = {
            "projects": [],
            "summary": {
                "total_projects": len(project_ids),
                "avg_files_per_project": 0,
                "best_accuracy": 0.0,
                "most_balanced_project": None
            }
        }
        
        total_files = 0
        best_accuracy = 0.0
        best_balance_score = float('inf')
        most_balanced = None
        
        for project_id in project_ids:
            project_path = self.projects_dir / project_id
            if project_path.exists():
                metadata_file = project_path / "project.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    stats = self._calculate_project_stats(project_path)
                    metadata['statistics'] = stats
                    
                    comparison['projects'].append(metadata)
                    total_files += stats['total_files']
                    
                    # Best accuracy
                    project_accuracy = metadata['statistics'].get('best_accuracy', 0)
                    if project_accuracy > best_accuracy:
                        best_accuracy = project_accuracy
                    
                    # Bilancimento dataset
                    distribution = stats['elements_distribution']
                    if sum(distribution.values()) > 0:
                        values = list(distribution.values())
                        balance_score = max(values) / min(v for v in values if v > 0) if min(values) > 0 else float('inf')
                        if balance_score < best_balance_score:
                            best_balance_score = balance_score
                            most_balanced = project_id
        
        comparison['summary']['avg_files_per_project'] = total_files / len(project_ids) if project_ids else 0
        comparison['summary']['best_accuracy'] = best_accuracy
        comparison['summary']['most_balanced_project'] = most_balanced
        
        return comparison