import React, { useState, useRef, useCallback } from 'react';
import { Upload, Play, Pause, Save, BarChart3, Brain, Target, TrendingUp, Mic, MicOff, Trash2, Download, RefreshCw, Settings, Eye, Zap } from 'lucide-react';

const VoiceLab = () => {
  const [currentProject, setCurrentProject] = useState('Laboratorio Fonico');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioFiles, setAudioFiles] = useState({
    aria: [],
    acqua: [],
    terra: [],
    fuoco: []
  });
  const [analysisResults, setAnalysisResults] = useState(null);
  const [liveAnalysis, setLiveAnalysis] = useState(null);
  const [selectedFeature, setSelectedFeature] = useState('pitch_mean');
  const [dashboardData, setDashboardData] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const elementColors = {
    aria: 'bg-gradient-to-r from-sky-400 to-blue-500',
    acqua: 'bg-gradient-to-r from-blue-500 to-blue-700',
    terra: 'bg-gradient-to-r from-amber-600 to-orange-700',
    fuoco: 'bg-gradient-to-r from-red-500 to-orange-600'
  };

  const elementIcons = {
    aria: '🌪️',
    acqua: '🌊',
    terra: '🌍',
    fuoco: '🔥'
  };

  // Backend API calls
  const API_BASE = 'http://localhost:8000';

  const uploadFiles = async (element, files) => {
    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(`${API_BASE}/upload-audio/${element}`, {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      
      setAudioFiles(prev => ({
        ...prev,
        [element]: [...prev[element], ...result.files]
      }));
      
      return result;
    } catch (error) {
      console.error('Upload error:', error);
      alert('Errore durante l\'upload. Assicurati che il backend sia avviato.');
    }
  };

  const analyzeDataset = async () => {
    setIsAnalyzing(true);
    try {
      const response = await fetch(`${API_BASE}/analyze-dataset`, {
        method: 'POST',
      });
      const results = await response.json();
      
      setAnalysisResults(results);
      await loadDashboardData();
      
    } catch (error) {
      console.error('Analysis error:', error);
      alert('Errore durante l\'analisi. Verifica che ci siano file caricati.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE}/dashboard-data`);
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Dashboard data error:', error);
    }
  };

  const removeFile = async (filename, element) => {
    try {
      const response = await fetch(`${API_BASE}/remove-audio?filename=${filename}&element=${element}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setAudioFiles(prev => ({
          ...prev,
          [element]: prev[element].filter(f => f.filename !== filename)
        }));
      }
    } catch (error) {
      console.error('Remove error:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = event => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await analyzeLiveAudio(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Recording error:', error);
      alert('Errore accesso microfono');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const analyzeLiveAudio = async (audioBlob) => {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');

    try {
      const response = await fetch(`${API_BASE}/analyze-live`, {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      setLiveAnalysis(result);
    } catch (error) {
      console.error('Live analysis error:', error);
    }
  };

  const addToDataset = async (element) => {
    if (!liveAnalysis) return;

    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio_file', audioBlob, `live_${element}_${Date.now()}.wav`);
    formData.append('element', element);

    try {
      const response = await fetch(`${API_BASE}/add-to-dataset`, {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      
      if (result.added) {
        alert(`Audio aggiunto al dataset ${element}!`);
        setLiveAnalysis(null);
      } else {
        alert(result.message);
      }
    } catch (error) {
      console.error('Add to dataset error:', error);
    }
  };

  const FeatureChart = ({ feature, data }) => {
    if (!data || !data[feature]) return null;

    const maxValue = Math.max(...Object.values(data[feature]).flat());
    
    return (
      <div className="bg-white rounded-lg p-4 shadow-md">
        <h4 className="font-semibold mb-3 capitalize">{feature.replace('_', ' ')}</h4>
        <div className="space-y-3">
          {Object.entries(data[feature]).map(([element, values]) => (
            <div key={element} className="flex items-center space-x-3">
              <span className="w-16 text-sm font-medium capitalize">{element}</span>
              <div className="flex-1 bg-gray-200 rounded-full h-6 relative">
                <div 
                  className={`h-6 rounded-full ${elementColors[element]} opacity-80`}
                  style={{ width: `${(values.reduce((a, b) => a + b, 0) / values.length / maxValue) * 100}%` }}
                />
                <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-gray-700">
                  {(values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center">
                🔬 Laboratorio Fonico - 4 Elementi
              </h1>
              <p className="text-gray-600 text-lg">
                Analisi scientifica delle caratteristiche vocali
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <input
                type="text"
                value={currentProject}
                onChange={(e) => setCurrentProject(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Nome progetto"
              />
              <button
                onClick={analyzeDataset}
                disabled={isAnalyzing}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-6 py-2 rounded-lg flex items-center space-x-2 transition-colors"
              >
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Analizzando...</span>
                  </>
                ) : (
                  <>
                    <Brain size={20} />
                    <span>Analizza Dataset</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Upload e Dataset */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
              <div className="flex items-center space-x-3 mb-6">
                <Upload className="text-blue-600" size={24} />
                <h2 className="text-xl font-bold text-gray-800">Dataset Audio</h2>
              </div>

              <div className="space-y-4">
                {Object.entries(elementColors).map(([element, colorClass]) => (
                  <div key={element} className={`${colorClass} rounded-xl p-4 text-white`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{elementIcons[element]}</span>
                        <h3 className="font-bold capitalize">{element}</h3>
                      </div>
                      <span className="bg-white bg-opacity-20 px-2 py-1 rounded-full text-xs">
                        {audioFiles[element].length} file
                      </span>
                    </div>
                    
                    <div className="relative">
                      <input
                        type="file"
                        multiple
                        accept="audio/*"
                        onChange={(e) => uploadFiles(element, e.target.files)}
                        className="hidden"
                        id={`upload-${element}`}
                      />
                      <label
                        htmlFor={`upload-${element}`}
                        className="flex items-center justify-center w-full h-12 border-2 border-dashed border-white border-opacity-40 rounded-lg cursor-pointer hover:bg-white hover:bg-opacity-10 transition-colors"
                      >
                        <Upload size={18} className="mr-2" />
                        <span className="text-sm">Carica audio {element}</span>
                      </label>
                    </div>

                    {audioFiles[element].length > 0 && (
                      <div className="mt-3 bg-white bg-opacity-15 rounded-lg p-2 max-h-32 overflow-y-auto">
                        <div className="text-xs font-semibold mb-1">File caricati:</div>
                        {audioFiles[element].map((file, index) => (
                          <div key={index} className="flex justify-between items-center text-xs mb-1">
                            <span className="truncate mr-2">{file.filename}</span>
                            <div className="flex items-center space-x-1">
                              <span className="text-white text-opacity-70">
                                {(file.size / 1024 / 1024).toFixed(1)} MB
                              </span>
                              <button
                                onClick={() => removeFile(file.filename, element)}
                                className="text-red-300 hover:text-red-100"
                              >
                                <Trash2 size={12} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Recording Live */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <div className="flex items-center space-x-3 mb-6">
                <Mic className="text-purple-600" size={24} />
                <h2 className="text-xl font-bold text-gray-800">Registrazione Live</h2>
              </div>

              <div className="text-center">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`w-full py-4 rounded-xl font-semibold text-lg transition-colors flex items-center justify-center space-x-2 ${
                    isRecording 
                      ? 'bg-red-500 hover:bg-red-600 text-white' 
                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }`}
                >
                  {isRecording ? <MicOff size={24} /> : <Mic size={24} />}
                  <span>{isRecording ? 'Ferma Registrazione' : 'Inizia Registrazione'}</span>
                </button>

                {liveAnalysis && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-semibold mb-2">Analisi Live:</h4>
                    <p className="text-sm mb-2">
                      <strong>Predizione:</strong> {liveAnalysis.prediction.element} 
                      ({(liveAnalysis.prediction.confidence * 100).toFixed(1)}%)
                    </p>
                    <p className="text-xs text-gray-600 mb-3">
                      {liveAnalysis.prediction.suggestion}
                    </p>
                    
                    <div className="grid grid-cols-2 gap-2">
                      {['aria', 'acqua', 'terra', 'fuoco'].map(element => (
                        <button
                          key={element}
                          onClick={() => addToDataset(element)}
                          className={`py-2 px-3 text-xs rounded-lg ${elementColors[element]} text-white hover:opacity-90`}
                        >
                          + {element}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Dashboard Scientifico */}
          <div className="lg:col-span-2">
            {dashboardData && dashboardData.status === 'ready' ? (
              <div className="space-y-6">
                
                {/* Statistiche Generali */}
                <div className="bg-white rounded-2xl shadow-xl p-6">
                  <div className="flex items-center space-x-3 mb-6">
                    <BarChart3 className="text-green-600" size={24} />
                    <h2 className="text-xl font-bold text-gray-800">Risultati Analisi</h2>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {Object.entries(dashboardData.summary.elements_count).map(([element, count]) => (
                      <div key={element} className={`${elementColors[element]} rounded-lg p-4 text-white text-center`}>
                        <div className="text-2xl font-bold">{count}</div>
                        <div className="text-sm opacity-90 capitalize">{element}</div>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-semibold mb-2">🎯 Features più Distintive:</h4>
                      <div className="text-sm space-y-1">
                        {dashboardData.summary.top_distinctive_features.slice(0, 5).map(([feature, stats], index) => (
                          <div key={feature} className="flex justify-between">
                            <span className="capitalize">{feature.replace('_', ' ')}</span>
                            <span className="font-mono text-xs">{stats.distinctive_score.toFixed(2)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-semibold mb-2">📊 Profili Elementi:</h4>
                      <div className="text-sm space-y-2">
                        {Object.entries(dashboardData.element_profiles).map(([element, profile]) => (
                          <div key={element} className="capitalize">
                            <strong>{element}:</strong> {profile.count} campioni, 
                            {profile.avg_duration?.toFixed(1)}s media
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Grafici Comparativi */}
                <div className="bg-white rounded-2xl shadow-xl p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                      <TrendingUp className="text-blue-600" size={24} />
                      <h2 className="text-xl font-bold text-gray-800">Confronto Features</h2>
                    </div>
                    <select
                      value={selectedFeature}
                      onChange={(e) => setSelectedFeature(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      {Object.keys(dashboardData.chart_data).map(feature => (
                        <option key={feature} value={feature}>
                          {feature.replace('_', ' ').toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>

                  <FeatureChart feature={selectedFeature} data={dashboardData.chart_data} />
                </div>

                {/* Raccomandazioni */}
                {dashboardData.recommendations && dashboardData.recommendations.length > 0 && (
                  <div className="bg-white rounded-2xl shadow-xl p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <Zap className="text-yellow-600" size={24} />
                      <h2 className="text-xl font-bold text-gray-800">Raccomandazioni</h2>
                    </div>
                    <div className="space-y-3">
                      {dashboardData.recommendations.map((rec, index) => (
                        <div key={index} className={`p-3 rounded-lg ${
                          rec.priority === 'high' ? 'bg-red-50 border-l-4 border-red-400' :
                          rec.priority === 'medium' ? 'bg-yellow-50 border-l-4 border-yellow-400' :
                          'bg-blue-50 border-l-4 border-blue-400'
                        }`}>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 text-xs rounded ${
                              rec.priority === 'high' ? 'bg-red-200 text-red-800' :
                              rec.priority === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                              'bg-blue-200 text-blue-800'
                            }`}>
                              {rec.priority.toUpperCase()}
                            </span>
                            <span className="text-sm">{rec.message}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            ) : (
              // Stato iniziale
              <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
                <Brain size={64} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  Inizia l'Analisi
                </h3>
                <p className="text-gray-600 mb-6">
                  Carica file audio nelle 4 categorie e clicca "Analizza Dataset" per iniziare lo studio scientifico delle caratteristiche vocali.
                </p>
                <div className="flex justify-center space-x-4 text-sm text-gray-500">
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-sky-400 rounded-full"></div>
                    <span>Aria: Apertura</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span>Acqua: Condivisione</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-amber-600 rounded-full"></div>
                    <span>Terra: Argomentazioni</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span>Fuoco: Chiusura</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceLab;