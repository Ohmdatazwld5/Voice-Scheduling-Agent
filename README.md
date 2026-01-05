# Voice Scheduling Agent

A voice-powered AI assistant that schedules meetings using speech recognition and natural language processing.

## Features

- 🎤 Voice-based meeting scheduling
- 🤖 AI-powered information extraction using Groq LLM
- 📅 Google Calendar integration
- ❓ Intelligent follow-up questions for missing information
- 💬 Conversational interface

## Tech Stack

- **Backend**: FastAPI, Python
- **AI**: Groq API (Llama 3.3 70B)
- **Frontend**: HTML, JavaScript, Web Speech API
- **Calendar**: Google Calendar API

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/voice-scheduling-agent.git
cd voice-scheduling-agent
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file in project root:
```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
```

5. Run the application:
```bash
uvicorn backend.main:app --reload
```

6. Open browser and navigate to `http://127.0.0.1:8000`

## Usage

1. Click "🎙️ Click to Speak"
2. Say: "Schedule a meeting with John tomorrow at 2pm"
3. The AI will extract details and ask for missing information
4. Confirm and the meeting will be scheduled

## Environment Variables

- `GROQ_API_KEY`: Your Groq API key from https://console.groq.com
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

## Deployment

Deploy to Render, Railway, or Vercel. See deployment section in code.

## License

MIT
