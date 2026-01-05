# 🎙️ Voice Scheduling Agent

An AI-powered voice scheduling assistant that uses natural language processing to schedule meetings in Google Calendar. Simply speak your meeting request, and the agent will extract the details, confirm with you, and add it to your calendar.

## ✨ Features

- 🗣️ **Voice Input**: Browser-based speech recognition
- 🤖 **AI-Powered**: Uses Groq's Llama 3.3 70B for natural language understanding
- 📅 **Google Calendar Integration**: Automatically creates calendar events
- ⏱️ **Smart Duration Handling**: Extracts duration from phrases like "30 mins" or "2 hours"
- 🔄 **Multi-turn Conversations**: Handles incomplete data, confirmations, and corrections
- ❌ **Cancellation Support**: Detects and handles cancellation requests
- ✅ **Confirmation Flow**: Always confirms before scheduling

## 🚀 Deployment

### Prerequisites

1. **Google Cloud Console Setup**:
   - Create a project
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URI: `https://voice-scheduling-agent.vercel.app/api/oauth/callback`

2. **API Keys Required**:
   - Groq API key (from [console.groq.com](https://console.groq.com))
   - Google OAuth credentials

### Vercel Deployment

1. **Fork/Clone Repository**:
   ```bash
   git clone https://github.com/Ohmdatazwld5/voice-scheduling-agent.git
   cd voice-scheduling-agent
   ```

2. **Configure Environment Variables in Vercel**:
   - Go to your Vercel project settings
   - Add the following environment variables:
     ```
     GROQ_API_KEY=your_groq_api_key
     GOOGLE_CLIENT_ID=your_google_client_id
     GOOGLE_CLIENT_SECRET=your_google_client_secret
     GOOGLE_REDIRECT_URI=https://your-app.vercel.app/api/oauth/callback
     ```

3. **Deploy to Vercel**:
   - Connect your GitHub repository to Vercel
   - Vercel will automatically detect the configuration
   - Deploy!

4. **Update Google OAuth Settings**:
   - In Google Cloud Console, add your Vercel URL to authorized redirect URIs
   - Add: `https://your-app.vercel.app/api/oauth/callback`

### Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**:
   Create a `.env` file:
   ```
   GROQ_API_KEY=your_groq_api_key
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
   ```

3. **Run the Server**:
   ```bash
   python run.py
   ```

4. **Open Browser**:
   Navigate to `http://localhost:8000`

## 📖 Usage

1. Click the microphone button
2. Speak your meeting request (e.g., "Schedule a meeting with John tomorrow at 3 PM for 30 minutes")
3. The agent will extract details and ask for any missing information
4. Confirm the details when prompted
5. Meeting is added to your Google Calendar!

## 🎯 Example Requests

- "Schedule a meeting with Sarah tomorrow at 2 PM"
- "Book a 30-minute call with the team on Friday at 10 AM"
- "Set up a meeting with clients next Monday from 3 to 4 PM"
- "I need to meet with the CEO on January 15th at 11 AM for 1 hour"

6. Open browser and navigate to `http://127.0.0.1:8000`

## VOICE & SPEECH ENHANCEMENTS(FUTURE ENHANCEMENTS)
## A. Advanced Voice Recognition
Real-time Streaming: Use Deepgram/AssemblyAI for continuous listening
Multi-language Support: Detect and process Spanish, French, Hindi, etc.
Accent Detection: Handle different English accents (British, Indian, Australian)
Speaker Diarization: Identify multiple speakers in group calls
Noise Cancellation: Filter background noise for better accuracy

## B. Natural Voice Output
Text-to-Speech Integration: Use Deepgram/ElevenLabs for voice responses
Emotion in Voice: Happy tone for success, empathetic for errors
Voice Cloning: User can select preferred assistant voice
Speed Control: Adjust speech rate based on user preference
Multilingual Responses: Reply in user's detected language

## ADVANCED AI FEATURES
## A. Predictive Intelligence
Meeting Outcome Prediction: "This meeting likely to go over time"
Attendee Suggestions: "Should invite the design team too?"
Agenda Generation: AI creates meeting agenda from context
Summary Generation: Auto-summarize what was discussed
Action Item Extraction: "John will send proposal by Friday"
## B. Conversational AI
Multi-step Reasoning: Handle complex scheduling logic
Clarification Questions: Ask for specifics when unclear
Negotiation: "2 PM is busy, how about 3 PM or 4 PM?"
Explanation: "Why was this meeting rescheduled?"
Small Talk: "How was your weekend?" before scheduling
## C. Autonomous Agent
Self-scheduling: AI finds and books time without asking
Auto-decline: Decline low-priority conflicts
Smart Batching: Group similar meetings together
Prep Briefs: "Here's what you need for the meeting"
Post-meeting Actions: Auto-send thank you emails

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
