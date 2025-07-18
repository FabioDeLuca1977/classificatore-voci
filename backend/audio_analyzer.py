# audio_analyzer.py - Core del Laboratorio Fonico
import librosa
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioFeatures:
    """Struttura per contenere tutte le features estratte da un audio"""
    filename: str
    element: str
    
    # Features Prosodiche
    pitch_mean: float
    pitch_std: float
    pitch_trend: str  # 'ascending', 'descending', 'stable'
    pitch_range: float
    
    # Features Volume/Energia
    rms_mean: float
    rms_std: float
    rms_trend: str
    peak_amplitude: float
    dynamic_range: float
    
    # Features Temporali
    duration: float
    speech_rate: float  # sillabe/secondo stimato
    pause_ratio: float
    num_pauses: int
    avg_pause_duration: float
    
    # Features Spettrali
    spectral_centroid_mean: float
    spectral_rolloff_mean: float
    zero_crossing_rate: float
    mfcc_coefficients: List[float]
    
    # Features Linguistiche/Vocaliche
    vowel_elongation_ratio: float
    word_duration_variance: float
    
    # Features Temporali Avanzate
    tempo_stability: float
    rhythm_regularity: float

class AudioAnalyzer:
    """Analizzatore principale per l'estrazione di features audio"""
    
    def __init__(self, sr=22050):
        self.sr = sr
        self.hop_length = 512
        self.frame_length = 2048
        
    def extract_features(self, audio_path: str, element: str) -> AudioFeatures:
        """Estrae tutte le features da un file audio"""
        try:
            # Carica l'audio
            y, sr = librosa.load(audio_path, sr=self.sr)
            logger.info(f"Analyzing {audio_path}: {len(y)/sr:.2f}s")
            
            # Estrai features
            prosodic = self._extract_prosodic_features(y, sr)
            energy = self._extract_energy_features(y, sr)
            temporal = self._extract_temporal_features(y, sr)
            spectral = self._extract_spectral_features(y, sr)
            linguistic = self._extract_linguistic_features(y, sr)
            
            return AudioFeatures(
                filename=os.path.basename(audio_path),
                element=element,
                **prosodic,
                **energy,
                **temporal,
                **spectral,
                **linguistic
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {audio_path}: {e}")
            raise
    
    def _extract_prosodic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Estrae features prosodiche (pitch, intonazione)"""
        # Estrai pitch usando algoritmo YIN
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, threshold=0.1)
        
        # Seleziona pitch più prominenti
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if len(pitch_values) == 0:
            pitch_values = [0]
            
        pitch_values = np.array(pitch_values)
        
        # Calcola trend del pitch
        if len(pitch_values) > 1:
            slope, _, _, _, _ = stats.linregress(range(len(pitch_values)), pitch_values)
            if slope > 0.5:
                trend = 'ascending'
            elif slope < -0.5:
                trend = 'descending'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'pitch_mean': float(np.mean(pitch_values)),
            'pitch_std': float(np.std(pitch_values)),
            'pitch_trend': trend,
            'pitch_range': float(np.max(pitch_values) - np.min(pitch_values))
        }
    
    def _extract_energy_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Estrae features di energia e volume"""
        # RMS Energy
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        
        # Trend RMS
        if len(rms) > 1:
            slope, _, _, _, _ = stats.linregress(range(len(rms)), rms)
            if slope > 0.001:
                rms_trend = 'ascending'
            elif slope < -0.001:
                rms_trend = 'descending'
            else:
                rms_trend = 'stable'
        else:
            rms_trend = 'stable'
        
        return {
            'rms_mean': float(np.mean(rms)),
            'rms_std': float(np.std(rms)),
            'rms_trend': rms_trend,
            'peak_amplitude': float(np.max(np.abs(y))),
            'dynamic_range': float(20 * np.log10(np.max(rms) / (np.min(rms) + 1e-8)))
        }
    
    def _extract_temporal_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Estrae features temporali (pause, ritmo, velocità)"""
        duration = len(y) / sr
        
        # Detect pause usando energy threshold
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        rms_threshold = np.mean(rms) * 0.1  # 10% della media
        
        # Frame con energia bassa = pause
        pause_frames = rms < rms_threshold
        pause_ratio = np.sum(pause_frames) / len(pause_frames)
        
        # Conta pause consecutive
        pauses = []
        in_pause = False
        pause_start = 0
        
        for i, is_pause in enumerate(pause_frames):
            if is_pause and not in_pause:
                in_pause = True
                pause_start = i
            elif not is_pause and in_pause:
                in_pause = False
                pause_duration = (i - pause_start) * self.hop_length / sr
                if pause_duration > 0.1:  # Pause > 100ms
                    pauses.append(pause_duration)
        
        # Stima speech rate (approssimativo)
        active_time = duration * (1 - pause_ratio)
        estimated_syllables = len(y) / sr * 4  # Stima grezza: 4 sillabe/secondo
        speech_rate = estimated_syllables / active_time if active_time > 0 else 0
        
        # Onset detection per rhythm analysis
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=self.hop_length)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)
        
        # Regolarità del ritmo
        if len(onset_times) > 1:
            intervals = np.diff(onset_times)
            rhythm_regularity = 1.0 / (1.0 + np.std(intervals))
            tempo_stability = 1.0 / (1.0 + np.std(intervals) / np.mean(intervals))
        else:
            rhythm_regularity = 0.0
            tempo_stability = 0.0
        
        return {
            'duration': duration,
            'speech_rate': float(speech_rate),
            'pause_ratio': float(pause_ratio),
            'num_pauses': len(pauses),
            'avg_pause_duration': float(np.mean(pauses)) if pauses else 0.0,
            'tempo_stability': float(tempo_stability),
            'rhythm_regularity': float(rhythm_regularity)
        }
    
    def _extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Estrae features spettrali"""
        # Spectral centroid (luminosità del suono)
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        
        # Spectral rolloff (frequenza sotto cui è concentrato 85% dell'energia)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        
        # Zero crossing rate (cambi di segno del segnale)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # MFCC (Mel-frequency cepstral coefficients)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = [float(np.mean(mfcc)) for mfcc in mfccs]
        
        return {
            'spectral_centroid_mean': float(np.mean(spectral_centroids)),
            'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
            'zero_crossing_rate': float(np.mean(zcr)),
            'mfcc_coefficients': mfcc_means
        }
    
    def _extract_linguistic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Estrae features linguistiche approssimate"""
        # Onset detection per stimare "parole"
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=self.hop_length)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)
        
        # Stima durata parole
        if len(onset_times) > 1:
            word_durations = np.diff(onset_times)
            word_duration_variance = float(np.var(word_durations))
        else:
            word_duration_variance = 0.0
        
        # Stima allungamento vocali (energia sostenuta)
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        rms_smooth = np.convolve(rms, np.ones(10)/10, mode='same')  # Smooth
        
        # Trova segmenti di energia sostenuta (possibili allungamenti)
        sustained_threshold = np.mean(rms_smooth) * 1.2
        sustained_frames = rms_smooth > sustained_threshold
        
        # Conta gruppi consecutivi di frame sostenuti
        elongations = 0
        in_elongation = False
        elongation_length = 0
        
        for frame in sustained_frames:
            if frame and not in_elongation:
                in_elongation = True
                elongation_length = 1
            elif frame and in_elongation:
                elongation_length += 1
            elif not frame and in_elongation:
                in_elongation = False
                if elongation_length > 20:  # > ~200ms di energia sostenuta
                    elongations += 1
        
        total_potential_words = len(onset_times)
        vowel_elongation_ratio = elongations / total_potential_words if total_potential_words > 0 else 0
        
        return {
            'vowel_elongation_ratio': float(vowel_elongation_ratio),
            'word_duration_variance': word_duration_variance
        }

class DatasetAnalyzer:
    """Analizza interi dataset e trova pattern distintivi"""
    
    def __init__(self):
        self.analyzer = AudioAnalyzer()
        self.features_df = None
        
    def analyze_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Analizza tutti i file in un dataset organizzato per cartelle"""
        all_features = []
        
        elements = ['aria', 'acqua', 'terra', 'fuoco']
        
        for element in elements:
            element_path = os.path.join(dataset_path, element)
            if not os.path.exists(element_path):
                logger.warning(f"Cartella {element} non trovata in {dataset_path}")
                continue
                
            for filename in os.listdir(element_path):
                if filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
                    file_path = os.path.join(element_path, filename)
                    try:
                        features = self.analyzer.extract_features(file_path, element)
                        all_features.append(features)
                        logger.info(f"✅ Analyzed: {filename} ({element})")
                    except Exception as e:
                        logger.error(f"❌ Failed: {filename} - {e}")
        
        # Converti in DataFrame per analisi
        self.features_df = pd.DataFrame([vars(f) for f in all_features])
        return self.features_df
    
    def find_distinctive_patterns(self) -> Dict[str, Any]:
        """Trova le features più distintive tra i 4 elementi"""
        if self.features_df is None:
            raise ValueError("Devi prima analizzare il dataset!")
        
        # Seleziona solo features numeriche
        numeric_features = self.features_df.select_dtypes(include=[np.number]).columns
        numeric_features = [f for f in numeric_features if f not in ['filename']]
        
        distinctive_features = {}
        
        for feature in numeric_features:
            # Calcola F-statistic per ANOVA tra i 4 gruppi
            groups = []
            for element in ['aria', 'acqua', 'terra', 'fuoco']:
                element_data = self.features_df[self.features_df['element'] == element][feature]
                if len(element_data) > 0:
                    groups.append(element_data)
            
            if len(groups) >= 2:  # Servono almeno 2 gruppi per confronto
                try:
                    f_stat, p_value = stats.f_oneway(*groups)
                    distinctive_features[feature] = {
                        'f_statistic': f_stat,
                        'p_value': p_value,
                        'distinctive_score': f_stat * (1 - p_value)  # Score combinato
                    }
                except:
                    pass
        
        # Ordina per distintività
        sorted_features = sorted(
            distinctive_features.items(), 
            key=lambda x: x[1]['distinctive_score'], 
            reverse=True
        )
        
        return {
            'most_distinctive_features': sorted_features[:10],
            'element_statistics': self._calculate_element_stats()
        }
    
    def _calculate_element_stats(self) -> Dict[str, Dict[str, float]]:
        """Calcola statistiche per ogni elemento"""
        stats_by_element = {}
        
        for element in ['aria', 'acqua', 'terra', 'fuoco']:
            element_data = self.features_df[self.features_df['element'] == element]
            if len(element_data) > 0:
                stats_by_element[element] = {
                    'count': len(element_data),
                    'avg_duration': element_data['duration'].mean(),
                    'avg_pitch': element_data['pitch_mean'].mean(),
                    'avg_volume': element_data['rms_mean'].mean(),
                    'avg_speech_rate': element_data['speech_rate'].mean(),
                    'pause_ratio': element_data['pause_ratio'].mean(),
                    'pitch_trend_distribution': element_data['pitch_trend'].value_counts().to_dict()
                }
        
        return stats_by_element
    
    def remove_audio_file(self, filename: str, element: str) -> bool:
        """Rimuove un file specifico dal dataset analizzato"""
        if self.features_df is None:
            return False
        
        # Rimuovi dal DataFrame
        mask = (self.features_df['filename'] == filename) & (self.features_df['element'] == element)
        removed_count = mask.sum()
        self.features_df = self.features_df[~mask]
        
        logger.info(f"Removed {removed_count} entries for {filename} ({element})")
        return removed_count > 0
    
    def export_analysis(self, output_path: str):
        """Esporta l'analisi completa in formato JSON"""
        if self.features_df is None:
            raise ValueError("Nessun dataset analizzato!")
        
        analysis = {
            'dataset_summary': {
                'total_files': len(self.features_df),
                'elements_distribution': self.features_df['element'].value_counts().to_dict(),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            },
            'distinctive_patterns': self.find_distinctive_patterns(),
            'raw_features': self.features_df.to_dict('records')
        }
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"Analysis exported to {output_path}")

# Esempio di utilizzo
if __name__ == "__main__":
    # Inizializza analizzatore
    dataset_analyzer = DatasetAnalyzer()
    
    # Analizza dataset (assumendo struttura: dataset/aria/, dataset/acqua/, etc.)
    dataset_path = "datasets/training"
    
    print("🔬 Avvio analisi del dataset...")
    features_df = dataset_analyzer.analyze_dataset(dataset_path)
    
    print(f"📊 Analizzati {len(features_df)} file audio")
    
    # Trova pattern distintivi
    patterns = dataset_analyzer.find_distinctive_patterns()
    
    print("\n🎯 Features più distintive:")
    for feature, stats in patterns['most_distinctive_features'][:5]:
        print(f"- {feature}: F={stats['f_statistic']:.2f}, p={stats['p_value']:.4f}")
    
    # Esporta analisi
    dataset_analyzer.export_analysis("analysis_results.json")
    print("\n✅ Analisi completata e salvata!")