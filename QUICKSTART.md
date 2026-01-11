# Interview Sathi - Quick Start Guide

## ✅ What's Already Done

### Backend Setup
- ✅ Python 3.13.5 detected
- ✅ All Python dependencies installed:
  - deepgram-sdk
  - groq
  - websockets
  - pyaudio
  - pyaudiowpatch (Windows audio capture)
  - python-dotenv

### Receiver Setup
- ✅ All receiver dependencies installed:
  - fastapi
  - uvicorn
  - websockets
  - deepgram-sdk
  - groq
  - python-multipart

### Configuration
- ✅ `.env` files created in both `backend/` and `receiver/`

---

## 🔧 What You Need to Do

### 1. Get API Keys (5 minutes)

#### Deepgram API Key
1. Go to https://deepgram.com
2. Sign up for free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

#### Groq API Key
1. Go to https://groq.com
2. Sign up for free account
3. Go to API Keys section
4. Create a new API key
5. Copy the key

### 2. Configure Environment Variables

Edit both `.env` files:

**backend/.env**:
```env
DEEPGRAM_API_KEY=your_actual_deepgram_key_here
GROQ_API_KEY=your_actual_groq_key_here
```

**receiver/.env**:
```env
DEEPGRAM_API_KEY=your_actual_deepgram_key_here
GROQ_API_KEY=your_actual_groq_key_here
INPUT_MODE=hardware
HARDWARE_DEVICE_INDEX=0
```

### 3. Install Node.js (for React UI)

**Option A: Using Winget (Recommended)**
```powershell
winget install OpenJS.NodeJS.LTS
```

**Option B: Manual Download**
1. Go to https://nodejs.org
2. Download LTS version (v20.x)
3. Run installer
4. Restart terminal after installation

### 4. Setup React Prompter UI

After installing Node.js:
```powershell
cd receiver\prompter_ui
npm install
```

---

## 🚀 Running the System

### Mode 1: Single Device (Transparent Overlay)

**Terminal 1 - Backend**:
```powershell
cd backend
python main.py
```

**Terminal 2 - Frontend**:
```powershell
cd frontend
npm install  # First time only
npm start
```

### Mode 2: Multi-Device Stealth (RECOMMENDED)

**On Second Device (Phone/Laptop)**:

**Terminal 1 - Receiver Server**:
```powershell
cd receiver
python audio_server.py
```

**Terminal 2 - Prompter UI**:
```powershell
cd receiver\prompter_ui
npm run dev
```

Then open browser: `http://localhost:3000`

**Hardware Setup**:
1. Connect 3.5mm splitter to main laptop
2. One output → headphones
3. Second output → aux cable → USB sound card → second device

---

## 🧪 Testing Individual Components

### Test Backend Audio Capture
```powershell
cd backend
python audio_capture.py
```

### Test Deepgram STT
```powershell
cd backend
python deepgram_stt.py
```

### Test Groq LLM
```powershell
cd backend
python groq_llm.py
```

### Test Receiver Server
```powershell
cd receiver
python audio_server.py
```

Then visit: http://localhost:8000/status

---

## 📱 Mobile Setup (Android)

If using phone as second device:

1. **Install Termux** (from F-Droid)
2. **Setup Python**:
```bash
pkg install python
pip install -r receiver/requirements.txt
```

3. **Find your laptop's IP**:
```powershell
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.100)
```

4. **Update prompter UI**:
Edit `receiver/prompter_ui/app/page.tsx` line 22:
```typescript
const wsUrl = 'ws://192.168.1.100:8000/ws/ui';  // Use your laptop IP
```

5. **Access from phone browser**:
```
http://192.168.1.100:3000
```

---

## 🔍 Troubleshooting

### "DEEPGRAM_API_KEY not found"
- Check `.env` file exists
- Verify API key is correct (no quotes needed)
- Restart the server after editing .env

### "No audio captured"
- Run `python -m sounddevice` to list devices
- Update `HARDWARE_DEVICE_INDEX` in `.env`
- Check cable connections

### "Module not found"
- Ensure you're in correct directory
- Run `pip install -r requirements.txt` again

### Port already in use
- Backend uses port 8765
- Receiver uses port 8000
- Frontend uses port 3000
- Kill existing processes or change ports in .env

---

## 📊 Expected Output

### Backend Running Successfully:
```
✓ API keys found
✓ All components initialized
✓ WebSocket server started on ws://localhost:8765
Starting audio pipeline...
✓ Capturing from device 0
✓ Connected to Deepgram
```

### Receiver Running Successfully:
```
INFO:     Started server process
INFO:     Waiting for application startup.
✓ Components initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Prompter UI:
- Green dot = Connected
- Live transcripts appearing
- AI hints when questions detected

---

## 🎯 Next Steps After Setup

1. **Test with YouTube**: Play an interview video and verify transcription
2. **Adjust settings**: Tune `GROQ_MAX_TOKENS` and `GROQ_TEMPERATURE` in .env
3. **Practice positioning**: Set up second device near webcam
4. **Test latency**: Measure end-to-end response time

---

## 📚 Documentation

- **Full Setup Guide**: See `STEALTH_SETUP.md`
- **Implementation Details**: See `implementation_plan.md`
- **Architecture**: See `README.md`

---

## ⚠️ Important Notes

1. **API Limits**: Free tiers have rate limits
   - Deepgram: 45,000 minutes/month
   - Groq: Generous free tier

2. **Privacy**: All processing happens via APIs
   - No local storage of audio
   - Transcripts kept in memory only

3. **Legal**: Use responsibly
   - Educational purposes only
   - Don't violate terms of service
   - Respect academic integrity

---

## 🆘 Need Help?

1. Check logs in terminal
2. Verify API keys are valid
3. Test components individually
4. Check `STEALTH_SETUP.md` for detailed troubleshooting

**Ready to start!** Get your API keys and configure the .env files.
