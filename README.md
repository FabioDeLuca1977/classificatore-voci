# Classificatore Voci - Prototipo

Sistema di classificazione vocale basato sui 4 elementi naturali per l'analisi delle fasi comunicative.

![Status](https://img.shields.io/badge/Status-Prototipo-orange)
![Version](https://img.shields.io/badge/Version-0.1.0-blue)

## 🎯 Obiettivo

Sviluppare un sistema di machine learning per classificare automaticamente le voci umane secondo i 4 elementi naturali, correlati alle fasi della comunicazione:

- **🌪️ Aria**: Apertura con connessione
- **🌊 Acqua**: Condivisione di domande e bisogni  
- **🌍 Terra**: Argomentazioni e concetti
- **🔥 Fuoco**: Chiusura con impegno

## 🏗️ Architettura

- **Frontend**: React.js con interfaccia intuitiva per upload e classificazione
- **Backend**: Python con ML pipeline (scikit-learn, librosa)
- **Target Accuracy**: 96-97%

## 🚀 Roadmap

### Fase 1 - Prototipo (Attuale)
- [x] Setup progetto
- [x] Prototipo UI/UX
- [ ] Setup ML Pipeline
- [ ] Sistema di training supervisionato
- [ ] Feature extraction audio

### Fase 2 - Sviluppo
- [ ] API Backend
- [ ] Integrazione Frontend-Backend
- [ ] Sistema di validazione umana
- [ ] Export modelli

### Fase 3 - VoiceBreakApp
- [ ] Migrazione a piattaforma finale
- [ ] Gamification e training
- [ ] Sistema di coaching vocale
- [ ] Deploy produzione

## 🛠️ Tecnologie

- **Frontend**: React, Tailwind CSS, Lucide Icons
- **Backend**: Python, FastAPI, scikit-learn, librosa
- **ML**: Random Forest, SVM, Feature Engineering
- **Deploy**: Lovable, Vercel, o simili

## 📊 Dataset

Il sistema apprende da audio etichettati organizzati per elemento:
```
datasets/training/
├── aria/     # Audio di apertura/connessione
├── acqua/    # Audio di condivisione bisogni
├── terra/    # Audio di argomentazioni
└── fuoco/    # Audio di chiusura/impegno
```

## 🎵 Riferimenti Musicali

- **Aria**: Lorenzo Cherubini - "Bella"
- **Acqua**: Negrita - "Ho imparato a sognare"  
- **Terra**: Fabrizio De André - "Bocca di rosa"
- **Fuoco**: Bennato - "Gatto e la volpe"

## 📈 Parametri di Analisi

- Ritmo (frequenza frasi/tempo)
- Volume (decibel)
- Tono (salita/discesa/stabile)
- Pause (numero e lunghezza)
- Stopwords
- Allungamento finali
- Velocità eloquio

## 🚀 Setup Rapido

### Frontend
```bash
cd frontend
npm install
npm start
```

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 👥 Team

Progetto sviluppato da Maieutike SRL per l'analisi e training delle competenze vocali.

---

*Questo è un prototipo in sviluppo. La versione finale sarà VoiceBreakApp.*
