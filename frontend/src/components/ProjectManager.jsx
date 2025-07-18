// ProjectManager.jsx - Gestione progetti nel frontend
import React, { useState, useEffect } from 'react';
import { Save, FolderOpen, Plus, Copy, Trash2, Download, Upload, Users, Clock, BarChart, Settings } from 'lucide-react';

const ProjectManager = ({ onProjectChange, currentProject, API_BASE }) => {
  const [projects, setProjects] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showImportForm, setShowImportForm] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '', trainer: '' });
  const [selectedProjects, setSelectedProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      const data = await response.json();
      setProjects(data.projects || []);
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  };

  const createProject = async () => {
    if (!newProject.name.trim()) {
      alert('Nome progetto richiesto');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('name', newProject.name);
      formData.append('description', newProject.description);
      formData.append('trainer', newProject.trainer);

      const response = await fetch(`${API_BASE}/projects/create`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        await loadProjects();
        setShowCreateForm(false);
        setNewProject({ name: '', description: '', trainer: '' });
        
        // Carica automaticamente il nuovo progetto
        await loadProject(result.project.project_id);
        
        alert(`Progetto "${result.project.name}" creato e caricato!`);
      }
    } catch (error) {
      console.error('Error creating project:', error);
      alert('Errore nella creazione del progetto');
    } finally {
      setIsLoading(false);
    }
  };

  const loadProject = async (projectId) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/projects/load/${projectId}`, {
        method: 'POST',
      });

      if (response.ok) {
        const result = await response.json();
        onProjectChange(result.project);
        await loadProjects(); // Refresh list
        alert(result.message);
      }
    } catch (error) {
      console.error('Error loading project:', error);
      alert('Errore nel caricamento del progetto');
    } finally {
      setIsLoading(false);
    }
  };

  const saveCurrentProject = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/projects/save`, {
        method: 'POST',
      });

      if (response.ok) {
        const result = await response.json();
        await loadProjects(); // Refresh list
        alert('Progetto salvato con successo!');
      }
    } catch (error) {
      console.error('Error saving project:', error);
      alert('Errore nel salvataggio del progetto');
    } finally {
      setIsLoading(false);
    }
  };

  const duplicateProject = async (projectId, projectName) => {
    const newName = prompt(`Nome per la copia di "${projectName}":`, `${projectName} - Copia`);
    if (!newName) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('new_name', newName);
      formData.append('trainer', newProject.trainer || 'Unknown');

      const response = await fetch(`${API_BASE}/projects/duplicate/${projectId}`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        await loadProjects();
        alert(`Progetto duplicato: ${result.new_project.name}`);
      }
    } catch (error) {
      console.error('Error duplicating project:', error);
      alert('Errore nella duplicazione del progetto');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteProject = async (projectId, projectName) => {
    if (!confirm(`Sei sicuro di voler eliminare "${projectName}"?\nQuesta azione creerà un backup ma il progetto non sarà più visibile.`)) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/projects/${projectId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await loadProjects();
        alert('Progetto eliminato con successo');
      }
    } catch (error) {
      console.error('Error deleting project:', error);
      alert('Errore nell\'eliminazione del progetto');
    } finally {
      setIsLoading(false);
    }
  };

  const exportProject = async (projectId, projectName) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/projects/export/${projectId}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName}_export.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('Progetto esportato con successo!');
      }
    } catch (error) {
      console.error('Error exporting project:', error);
      alert('Errore nell\'esportazione del progetto');
    } finally {
      setIsLoading(false);
    }
  };

  const importProject = async (file) => {
    const newName = prompt('Nome per il progetto importato:', file.name.replace('.zip', ''));
    if (!newName) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('project_file', file);
      formData.append('new_name', newName);

      const response = await fetch(`${API_BASE}/projects/import`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        await loadProjects();
        alert(`Progetto "${result.project.name}" importato con successo!`);
      }
    } catch (error) {
      console.error('Error importing project:', error);
      alert('Errore nell\'importazione del progetto');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('it-IT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getProjectStatusColor = (project) => {
    const totalFiles = project.statistics?.total_files || 0;
    const accuracy = project.statistics?.best_accuracy || 0;
    
    if (totalFiles === 0) return 'bg-gray-100 text-gray-600';
    if (accuracy >= 0.96) return 'bg-green-100 text-green-700';
    if (accuracy >= 0.85) return 'bg-yellow-100 text-yellow-700';
    return 'bg-blue-100 text-blue-700';
  };

  const getProjectStatusText = (project) => {
    const totalFiles = project.statistics?.total_files || 0;
    const accuracy = project.statistics?.best_accuracy || 0;
    
    if (totalFiles === 0) return 'Vuoto';
    if (accuracy >= 0.96) return 'Ottimale';
    if (accuracy >= 0.85) return 'Buono';
    return 'In sviluppo';
  };

  return (
    <div className="space-y-6">
      
      {/* Header con azioni principali */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center">
              <FolderOpen className="mr-3 text-blue-600" size={28} />
              Gestione Progetti
            </h2>
            <p className="text-gray-600">Organizza e gestisci i tuoi esperimenti di analisi vocale</p>
          </div>
          
          <div className="flex space-x-3">
            {currentProject && (
              <button
                onClick={saveCurrentProject}
                disabled={isLoading}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
              >
                <Save size={18} />
                <span>Salva Corrente</span>
              </button>
            )}
            
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
            >
              <Plus size={18} />
              <span>Nuovo Progetto</span>
            </button>
            
            <label className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors cursor-pointer">
              <Upload size={18} />
              <span>Importa</span>
              <input
                type="file"
                accept=".zip"
                onChange={(e) => e.target.files[0] && importProject(e.target.files[0])}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Progetto attivo */}
        {currentProject && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-blue-800">📂 Progetto Attivo:</h3>
                <p className="text-blue-700">{currentProject.name}</p>
                <p className="text-sm text-blue-600">
                  {currentProject.trainer && `Trainer: ${currentProject.trainer} • `}
                  Modificato: {formatDate(currentProject.last_modified)}
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-700">
                  {currentProject.statistics?.total_files || 0}
                </div>
                <div className="text-sm text-blue-600">file caricati</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Lista progetti */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">I Tuoi Progetti</h3>
        
        {projects.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FolderOpen size={48} className="mx-auto mb-4 opacity-50" />
            <p>Nessun progetto trovato. Crea il tuo primo progetto!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div key={project.project_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                
                {/* Header progetto */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-800 truncate">{project.name}</h4>
                    <p className="text-sm text-gray-600 line-clamp-2">{project.description || 'Nessuna descrizione'}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${getProjectStatusColor(project)}`}>
                    {getProjectStatusText(project)}
                  </span>
                </div>

                {/* Statistiche */}
                <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
                  <div className="bg-gray-50 rounded p-2">
                    <div className="font-medium text-gray-700">{project.statistics?.total_files || 0}</div>
                    <div className="text-gray-500">File audio</div>
                  </div>
                  <div className="bg-gray-50 rounded p-2">
                    <div className="font-medium text-gray-700">
                      {project.statistics?.best_accuracy ? `${(project.statistics.best_accuracy * 100).toFixed(1)}%` : 'N/A'}
                    </div>
                    <div className="text-gray-500">Best accuracy</div>
                  </div>
                </div>

                {/* Distribuzione elementi */}
                {project.statistics?.elements_distribution && (
                  <div className="mb-3">
                    <div className="text-xs text-gray-600 mb-1">Distribuzione:</div>
                    <div className="flex space-x-1">
                      {Object.entries(project.statistics.elements_distribution).map(([element, count]) => (
                        <div key={element} className="flex-1 text-center">
                          <div className={`h-2 rounded ${
                            element === 'aria' ? 'bg-sky-400' :
                            element === 'acqua' ? 'bg-blue-500' :
                            element === 'terra' ? 'bg-amber-600' :
                            'bg-red-500'
                          }`} style={{ opacity: count > 0 ? 1 : 0.2 }}></div>
                          <div className="text-xs text-gray-500 mt-1">{count}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Meta info */}
                <div className="text-xs text-gray-500 mb-3 space-y-1">
                  {project.trainer && <div className="flex items-center"><Users size={12} className="mr-1" />{project.trainer}</div>}
                  <div className="flex items-center"><Clock size={12} className="mr-1" />{formatDate(project.last_modified)}</div>
                </div>

                {/* Azioni */}
                <div className="flex space-x-1">
                  <button
                    onClick={() => loadProject(project.project_id)}
                    disabled={isLoading}
                    className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white py-1 px-2 rounded text-sm transition-colors"
                  >
                    Carica
                  </button>
                  
                  <button
                    onClick={() => duplicateProject(project.project_id, project.name)}
                    disabled={isLoading}
                    className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-300 text-white p-1 rounded transition-colors"
                    title="Duplica"
                  >
                    <Copy size={14} />
                  </button>
                  
                  <button
                    onClick={() => exportProject(project.project_id, project.name)}
                    disabled={isLoading}
                    className="bg-green-500 hover:bg-green-600 disabled:bg-gray-300 text-white p-1 rounded transition-colors"
                    title="Esporta"
                  >
                    <Download size={14} />
                  </button>
                  
                  <button
                    onClick={() => deleteProject(project.project_id, project.name)}
                    disabled={isLoading}
                    className="bg-red-500 hover:bg-red-600 disabled:bg-gray-300 text-white p-1 rounded transition-colors"
                    title="Elimina"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal Crea Progetto */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">Nuovo Progetto</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Progetto *</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject(prev => ({...prev, name: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Es: Esperimento Voci Commerciali"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject(prev => ({...prev, description: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="3"
                  placeholder="Descrizione dell'esperimento..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Trainer</label>
                <input
                  type="text"
                  value={newProject.trainer}
                  onChange={(e) => setNewProject(prev => ({...prev, trainer: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Nome del formatore"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createProject}
                disabled={isLoading || !newProject.name.trim()}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-2 px-4 rounded-lg transition-colors"
              >
                {isLoading ? 'Creazione...' : 'Crea Progetto'}
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors"
              >
                Annulla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-40">
          <div className="bg-white rounded-lg p-6 flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span>Elaborazione in corso...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectManager;