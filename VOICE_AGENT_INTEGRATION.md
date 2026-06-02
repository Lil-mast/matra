# Voice AI Agent Integration Guide

**Ollama (Local LLM) + Eleven Labs (TTS) for Matra Health**

Integrating a voice agent transforms the Matra platform from a traditional data-entry tool into a conversational, empathetic medical assistant. The goal is to allow Community Health Workers (CHWs) and patients to converse naturally, while the system extracts the necessary vitals and danger signs to fill out the triage form automatically.

## Architecture Overview

The system requires three core components:
1. **Frontend (Browser):** Records audio using the Web Audio API, streams it to the backend, and plays back the AI's response.
2. **Backend (Python Flask / FastAPI):** Orchestrates the conversation. It handles Speech-to-Text (STT), routes the text to the LLM, and sends the LLM's response to Eleven Labs for Text-to-Speech (TTS).
3. **AI Pipeline (Ollama + Eleven Labs):** Ollama runs a quantized medical LLM (like Llama 3 8B or MedLlama) to process the conversation and extract JSON data. Eleven Labs synthesizes the text into a hyper-realistic, empathetic voice.

---

## Step-by-Step Integration

### 1. The Speech-to-Text (STT) Layer

When the frontend records audio, it sends it to your Python backend. You can use OpenAI's Whisper model (which can run locally) for fast, highly accurate transcription.

- **Action:** Install `faster-whisper` on your Python backend.
- **Workflow:** Frontend Audio Blob -> Backend -> Whisper STT -> Transcribed Text.

### 2. The Medical Reasoning Layer (Ollama)

Once you have the transcribed text (e.g., *"The patient says she has had a fever since yesterday and her head hurts"*), you send this text along with the conversation history to Ollama.

- **Setup Ollama:** 
  Download and install Ollama on your server. Run a model suitable for medical reasoning.
  `ollama run llama3`
- **System Prompt:** 
  You must restrict the LLM to only ask triage-related questions. 
  *Prompt Example:* "You are an empathetic medical assistant. You are speaking with a pregnant woman in a rural clinic. Extract her age, parity, blood pressure, and danger signs (fever, bleeding, convulsions). Ask one clear question at a time. Do not diagnose."
- **Workflow:** Transcribed Text -> Backend -> Ollama API (localhost:11434) -> AI Text Response.

### 3. The Text-to-Speech Layer (Eleven Labs)

Once Ollama generates the text response (e.g., *"I'm so sorry you're feeling unwell. Can you tell me if you've experienced any bleeding?"*), you send this text to Eleven Labs.

- **Setup Eleven Labs:**
  Get an API key from Eleven Labs. Create or select a custom voice that sounds warm, local, and empathetic.
- **Workflow:** AI Text Response -> Backend -> Eleven Labs API -> Audio Stream -> Frontend Playback.

---

## Example Backend Code (Python)

```python
import requests
from elevenlabs import generate, stream, set_api_key

# 1. Get Text from User (Assume Whisper STT is done)
user_text = "She has a fever and light bleeding."

# 2. Get Response from Ollama
ollama_payload = {
    "model": "llama3",
    "messages": [
        {"role": "system", "content": "You are a maternal health assistant. Ask about convulsions next."},
        {"role": "user", "content": user_text}
    ],
    "stream": False
}
ollama_res = requests.post("http://localhost:11434/api/chat", json=ollama_payload)
ai_text = ollama_res.json()["message"]["content"]

# 3. Generate Speech with Eleven Labs
set_api_key("YOUR_ELEVEN_LABS_API_KEY")
audio_stream = generate(
    text=ai_text,
    voice="Rachel", # Use your custom voice ID
    model="eleven_multilingual_v2",
    stream=True
)

# Stream this back to the frontend...
```

## Security & Connectivity Considerations

> [!WARNING]
> **Bandwidth Limits:** High-quality voice streams from Eleven Labs require stable 3G/4G. If the clinic is in a 2G area, the voice agent will time out. You must include a fallback to the manual text form.
> 
> **Data Privacy (HIPAA / GDPR):** Do not send PII (Personally Identifiable Information) like the patient's name or national ID to external APIs (Eleven Labs). Ensure the STT and LLM (Ollama) run locally on your secure server if possible, rather than using external cloud LLMs.
> 
> **PII Masking / Redaction:** Before sending any transcript to external services, redact patient identifiers from the text. Remove names, national IDs, phone numbers, email addresses, and other direct identifiers from the audio transcript and stored conversation history.

## Implementation Notes

- Backend voice session API endpoints:
  - `POST /api/voice/session` — start a new voice conversation session
  - `POST /api/voice/session/{session_id}/audio` — upload recorded audio and receive transcript, assistant text, extracted form values, and TTS audio
- Environment variables to configure:
  - `OLLAMA_URL`
  - `OLLAMA_MODEL`
  - `VOICE_STT_MODEL`
  - `VOICE_STT_DEVICE`
  - `ELEVENLABS_API_KEY`
  - `ELEVENLABS_VOICE_ID`
