# Lingua Workbench 🎧

A personal language learning platform designed for analyzing and studying spoken English from audio/video sources like TV shows and movies.

![Demo Screenshot](./docs/screenshots/demo-placeholder.png)

## ✨ Features

### 🎵 Audio Management
- **Source Audio Upload**: Upload audio files from TV shows/movies, organized by drama/season/episode
- **Auto Chunking**: Automatically splits long audio files into manageable chunks (5-minute segments)
- **Waveform Visualization**: Interactive waveform display with region selection

### ✂️ Audio Slicing & Annotation
- **Region Selection**: Click and drag on waveform to create audio slices
- **Whisper Transcription**: AI-powered speech-to-text for automatic transcription
- **Text Highlighting**: Select text portions to create highlights for deeper analysis

![Slice Editor](./docs/screenshots/slice-editor-placeholder.png)

### 🔊 AI Phonetic Analysis
- **Sound Script Analysis**: AI-generated phonetic breakdown of highlighted phrases
- **Phonetic Tags**: Automatic detection of:
  - Reductions (弱化)
  - Linking (连读)
  - Assimilations (同化)
  - Flap T / Glottal Stop
- **Ruby Text Display**: Shows pronunciation above original text
- **Ghost Sound Styling**: Strikethrough for omitted/silent sounds marked with `[brackets]`

![Phonetic Analysis](./docs/screenshots/phonetic-analysis-placeholder.png)

### 📖 Dictionary Integration
- **AI Dictionary Lookup**: Context-aware definitions for words/phrases
- **Bilingual Examples**: Example sentences in both English and Chinese
- **Example Refresh**: Generate new contextual examples on demand

### 🛠️ Editing Capabilities
- **Dual Edit Modes**: 
  - **AI Note Mode**: Edit phonetic annotations and notes
  - **Sound Display Mode**: Correct AI's pronunciation analysis
- **Time Adjustment**: Fine-tune slice boundaries with ±0.5s arrows
- **Favorite Marking**: Star important sentences for review
- **Independent Delete**: Instant server-side deletion for saved slices

### 🎛️ Playback Controls
- **Variable Speed Playback**: Adjustable playback speeds (0.5x - 1.5x)
- **Loop Playback**: Repeat audio regions for focused practice
- **Region Playback**: Click to play individual slices

## 🏗️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| Vue 3 | Reactive UI framework |
| TypeScript | Type-safe development |
| Vite | Fast build tool |
| Element Plus | UI component library |
| Tailwind CSS | Utility-first styling |
| WaveSurfer.js | Audio waveform visualization |
| Pinia | State management |
| Axios | HTTP client |

### Backend
| Technology | Purpose |
|------------|---------|
| Django | Web framework |
| Django REST Framework | API development |
| SimpleJWT | Authentication |
| LangChain + OpenAI | AI analysis |
| SQLite/PostgreSQL | Database |

### Services
| Service | Purpose |
|---------|---------|
| Whisper API | Speech-to-text transcription |
| OpenAI GPT | Phonetic analysis & dictionary |

## 📁 Project Structure

```
lingua-workbench/
├── frontend/                # Vue 3 frontend
│   ├── src/
│   │   ├── api/            # API client functions
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page views
│   │   └── stores/         # Pinia stores
│   └── package.json
├── backend/                 # Django backend
│   ├── audio_slicer/       # Audio management app
│   ├── ai_analysis/        # AI analysis app
│   └── requirements.in
├── whisper/                 # Whisper API service
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Node.js 20+ or 22+
- Python 3.11+
- ffmpeg (for audio processing)

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Environment Variables
Create `.env` files for both frontend and backend:

**Backend `.env`:**
```
SECRET_KEY=your-secret-key
DEBUG=True
OPENAI_API_KEY=your-openai-key
```

## 📸 Screenshots

| Feature | Screenshot |
|---------|------------|
| Audio Chunks | ![Chunks](./docs/screenshots/chunks-placeholder.png) |
| Slice Editor | ![Editor](./docs/screenshots/editor-placeholder.png) |
| Phonetic Analysis | ![Analysis](./docs/screenshots/analysis-placeholder.png) |
| Dictionary | ![Dictionary](./docs/screenshots/dictionary-placeholder.png) |

## 🎬 Demo Video

[Watch Demo Video](./docs/demo-placeholder.mp4)

## 📝 License

MIT License - See [LICENSE](./LICENSE) for details.

---

*Built for language learners who want to master natural spoken English through authentic audio sources.* 🌟
