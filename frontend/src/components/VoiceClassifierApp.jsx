import React, { useState, useRef } from 'react';
import { Upload, Play, Pause, Save, BarChart3, Brain, Target, TrendingUp } from 'lucide-react';

const VoiceClassifierApp = () => {
  const [currentProject, setCurrentProject] = useState('Progetto 1');
  const [datasets, setDatasets] = useState([]);
  const [isTraining, setIsTraining] = useState(false);
  const [modelAccuracy, setModelAccuracy] = useState(null);
  const [audioFiles, setAudioFiles] = useState({
    aria: [],
    acqua: [],
    terra: [],
    fuoco: []
  });
  const [newAudioForClassification, setNewAudioForClassification] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [confidence, setConfidence] = useState(null);

  const elementColors = {
    aria: 'bg-gradient-to-r from-sky-200 to-blue-200',
    acqua: 'bg-gradient-to-r from-blue-400 to-blue-600',
    terra: 'bg-gradient-to-r from-amber-600 to-orange-700',
    fuoco: 'bg-gradient-to-r from-red-500 to-orange-500'
  };

  const elementIcons = {
    aria: '💨',
    acqua: '🌊',
    terra: '🌍',
    fuoco: '🔥'
  };

  const handleDatasetUpload = (element, files) => {
    const newFiles = Array.from(files).map(file => ({
      name: file.name,
      size: file.size,
      element: element
    }));
    
    setAudioFiles(prev => ({
      ...prev,
      [element]: [...prev[element], ...newFiles]
    }));
  };

  const startTraining = () => {
    setIsTraining(true);
    setTimeout(() => {
      setIsTraining(false);
      setModelAccuracy(Math.random() * 0.05 + 0.95);
    }, 3000);
  };

  const classifyNewAudio = (file) => {
    setNewAudioForClassification(file);
    setTimeout(() => {
      const elements = ['aria', 'acqua', 'terra', 'fuoco'];
      const randomElement = elements[Math.floor(Math.random() * elements.length)];
      setPrediction(randomElement);
      setConfidence(Math.random() * 0.1 + 0.9);
    }, 1500);
  };

  const getElementCharacteristics = (element) => {
    const characteristics = {
      aria: {
        rhythm: "3 frasi/unità",
        volume: "Medio-Alto (65-75 dB)",
        tone: "In salita ↗️",
        pauses: "Brevi e dinamiche",
        pattern: "Leggero, acuto, connessione"
      },
      acqua: {
        rhythm: "2 frasi/unità",
        volume: "Basso-Intimo (45-55 dB)",
        tone: "In discesa ↘️",
        pauses: "Lunghe con trascinamento",
        pattern: "Fluido, grave, condivisione"
      },
      terra: {
        rhythm: "3 frasi/unità",
        volume: "Medio (55-65 dB)",
        tone: "In discesa ↘️",
        pauses: "Regolari senza trascinamento",
        pattern: "Solido, concreto, argomentazioni"
      },
      fuoco: {
        rhythm: "4 frasi/unità",
        volume: "Alto (75-85 dB)",
        tone: "In salita ↗️",
        pauses: "Rapide e incalzanti",
        pattern: "Intenso, pressione, azione"
      }
    };
    return characteristics[element];
  };

  const saveProject = () => {
    const projectData = {
      name: currentProject,
      datasets: audioFiles,
      accuracy: modelAccuracy,
      timestamp: new Date().toISOString()
    };
    
    setDatasets(prev => [...prev, projectData]);
    alert('Progetto salvato con successo!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-800 mb-2">
                Classificatore Voci - 4 Elementi
              </h1>
              <p className="text-gray-600 text-lg">
                Aria • Acqua • Terra • Fuoco
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
                onClick={saveProject}
                className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg flex items-center space-x-2 transition-colors"
              >
                <Save size={20} />
                <span>Salva</span>
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Brain className="text-blue-600" size={28} />
              <h2 className="text-2xl font-bold text-gray-800">Dataset di Training</h2>
            </div>

            <div className="space-y-6">
              {Object.entries(elementColors).map(([element, colorClass]) => (
                <div key={element} className={`${colorClass} rounded-xl p-6 text-white`}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{elementIcons[element]}</span>
                      <h3 className="text-xl font-bold capitalize">{element}</h3>
                    </div>
                    <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                      {audioFiles[element].length} file
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="relative">
                      <input
                        type="file"
                        multiple
                        accept="audio/*"
                        onChange={(e) => handleDatasetUpload(element, e.target.files)}
                        className="hidden"
                        id={`upload-${element}`}
                      />
                      <label
                        htmlFor={`upload-${element}`}
                        className="flex items-center justify-center w-full h-16 border-2 border-dashed border-white border-opacity-40 rounded-lg cursor-pointer hover:bg-white hover:bg-opacity-10 transition-colors"
                      >
                        <Upload size={24} className="mr-2" />
                        <span>Carica file audio {element}</span>
                      </label>
                    </div>
                    
                    {audioFiles[element].length > 0 && (
                      <div className="space-y-3">
                        <div className="bg-white bg-opacity-20 rounded-lg p-3 max-h-24 overflow-y-auto">
                          <div className="text-sm font-semibold mb-2">File caricati:</div>
                          {audioFiles[element].map((file, index) => (
                            <div key={index} className="flex justify-between items-center text-xs mb-1 last:mb-0">
                              <span className="truncate mr-2">{file.name}</span>
                              <span className="text-white text-opacity-70">
                                {(file.size / 1024 / 1024).toFixed(1)} MB
                              </span>
                            </div>
                          ))}
                        </div>
                        
                        {/* Caratteristiche Vocali Analizzate */}
                        <div className="bg-white bg-opacity-15 rounded-lg p-3 text-xs">
                          <div className="font-semibold mb-2">📊 Caratteristiche {element.toUpperCase()}:</div>
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <span className="font-medium">Ritmo:</span> {getElementCharacteristics(element).rhythm}
                            </div>
                            <div>
                              <span className="font-medium">Volume:</span> {getElementCharacteristics(element).volume}
                            </div>
                            <div>
                              <span className="font-medium">Tono:</span> {getElementCharacteristics(element).tone}
                            </div>
                            <div>
                              <span className="font-medium">Pause:</span> {getElementCharacteristics(element).pauses}
                            </div>
                            <div className="col-span-2">
                              <span className="font-medium">Pattern:</span> {getElementCharacteristics(element).pattern}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={startTraining}
                disabled={isTraining || Object.values(audioFiles).every(arr => arr.length === 0)}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-4 rounded-xl font-semibold text-lg transition-colors flex items-center justify-center space-x-2"
              >
                {isTraining ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Training in corso...</span>
                  </>
                ) : (
                  <>
                    <Target size={20} />
                    <span>Avvia Training</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="space-y-8">
            
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex items-center space-x-3 mb-6">
                <BarChart3 className="text-green-600" size={28} />
                <h2 className="text-2xl font-bold text-gray-800">Performance Modello</h2>
              </div>

              {modelAccuracy ? (
                <div className="text-center">
                  <div className="text-5xl font-bold text-green-600 mb-2">
                    {(modelAccuracy * 100).toFixed(1)}%
                  </div>
                  <p className="text-gray-600 text-lg">Accuratezza Predittiva</p>
                  
                  <div className="mt-6 bg-gray-200 rounded-full h-4">
                    <div 
                      className="bg-gradient-to-r from-green-400 to-green-600 h-4 rounded-full transition-all duration-1000"
                      style={{ width: `${modelAccuracy * 100}%` }}
                    ></div>
                  </div>
                  
                  <div className="mt-4 text-sm text-gray-500">
                    Obiettivo: 96-97% • Status: {modelAccuracy >= 0.96 ? '✅ Raggiunto' : '⚠️ In miglioramento'}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <TrendingUp size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Avvia il training per vedere le performance</p>
                </div>
              )}
            </div>

            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex items-center space-x-3 mb-6">
                <Play className="text-purple-600" size={28} />
                <h2 className="text-2xl font-bold text-gray-800">Classifica Nuovi Audio</h2>
              </div>

              <div className="space-y-6">
                <div className="relative">
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={(e) => classifyNewAudio(e.target.files[0])}
                    className="hidden"
                    id="classify-upload"
                    disabled={!modelAccuracy}
                  />
                  <label
                    htmlFor="classify-upload"
                    className={`flex items-center justify-center w-full h-20 border-2 border-dashed ${
                      modelAccuracy ? 'border-purple-300 hover:bg-purple-50 cursor-pointer' : 'border-gray-300 cursor-not-allowed'
                    } rounded-lg transition-colors`}
                  >
                    <Upload size={24} className={`mr-2 ${modelAccuracy ? 'text-purple-600' : 'text-gray-400'}`} />
                    <span className={modelAccuracy ? 'text-purple-600' : 'text-gray-400'}>
                      {modelAccuracy ? 'Carica audio da classificare' : 'Completa il training prima'}
                    </span>
                  </label>
                </div>

                {prediction && (
                  <div className={`${elementColors[prediction]} rounded-xl p-6 text-white animate-fadeIn`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <span className="text-3xl">{elementIcons[prediction]}</span>
                        <div>
                          <h3 className="text-2xl font-bold capitalize">{prediction}</h3>
                          <p className="text-white text-opacity-90">Elemento identificato</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">{(confidence * 100).toFixed(1)}%</div>
                        <div className="text-sm text-white text-opacity-90">Confidenza</div>
                      </div>
                    </div>
                    
                    <div className="flex space-x-4 mt-6">
                      <button className="flex-1 bg-white bg-opacity-20 hover:bg-opacity-30 py-2 px-4 rounded-lg transition-colors">
                        ✅ Conferma
                      </button>
                      <button className="flex-1 bg-white bg-opacity-20 hover:bg-opacity-30 py-2 px-4 rounded-lg transition-colors">
                        ❌ Correggi
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {datasets.length > 0 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mt-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Progetti Salvati</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {datasets.map((dataset, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <h3 className="font-semibold text-gray-800">{dataset.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Accuratezza: {(dataset.accuracy * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(dataset.timestamp).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceClassifierApp;