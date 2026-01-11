# Interview Sathi - Multi-Device Stealth Setup Guide

Complete guide for setting up the **Hardware Bridge** approach (RECOMMENDED for stealth operation).

## 🎯 What You'll Need

### Hardware
1. **3.5mm Aux Splitter** (~₹100-200)
   - Splits laptop audio into 2 outputs
2. **3.5mm Aux Cable** (~₹100-150)
   - Connects splitter to USB sound card
3. **USB Sound Card** (~₹500-1000)
   - Receives audio on second device
   - Example: Generic USB Audio Adapter
4. **Second Device**
   - Android/iOS phone OR
   - Second laptop/tablet

### Software
- Python 3.10+ (on second device)
- Node.js 18+ (on second device)
- Deepgram API Key (free tier)
- Groq API Key (free tier)

---

## 📋 Step-by-Step Setup

### Part 1: Hardware Connection

```
Main Laptop (Interview Running)
    |
    | Audio Output (3.5mm jack)
    |
    v
[3.5mm Splitter]
    |
    |---> Output 1 ---> Your Headphones (you hear the interview)
    |
    |---> Output 2 ---> 3.5mm Cable ---> USB Sound Card
                                              |
                                              v
                                    Second Device (Phone/Laptop)
                                    (receives crystal clear audio)
```

**Physical Setup**:
1. Plug 3.5mm splitter into main laptop's audio jack
2. Connect your headphones to one output of the splitter
3. Connect aux cable from second splitter output to USB sound card
4. Plug USB sound card into second device

**Result**: Main laptop has ZERO software footprint. Audio is physically routed.

---

### Part 2: Second Device Setup

#### On Windows/Mac/Linux Second Laptop

1. **Install Python dependencies**:
```bash
cd receiver
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. **Find USB sound card device index**:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```
Look for your USB sound card and note its index number.

4. **Update .env**:
```env
INPUT_MODE=hardware
HARDWARE_DEVICE_INDEX=<your_device_index>
```

5. **Start the receiver server**:
```bash
python audio_server.py
```

6. **Start the prompter UI** (in new terminal):
```bash
cd prompter_ui
npm install
npm run dev
```

7. **Open browser**: Navigate to `http://localhost:3000`

#### On Android Phone

1. **Install Termux** from F-Droid
2. **Install dependencies**:
```bash
pkg install python nodejs
pip install -r requirements.txt
```

3. **Use USB OTG adapter** for USB sound card
4. Follow same steps as laptop

#### On iPhone/iPad

Use a second laptop instead - iOS doesn't support USB audio input easily.

---

### Part 3: Testing

1. **Play a YouTube video** on main laptop
2. **Check receiver logs** - you should see:
   ```
   ✓ Capturing from device X
   ✓ Connected to Deepgram
   Final: [transcribed text] (0.95)
   ```

3. **Check prompter UI** - you should see:
   - Live transcripts appearing
   - AI hints when questions are detected

---

## 🎨 Using During Interview

### Positioning

**Phone Setup**:
- Place phone **directly behind webcam** at eye level
- Use a small phone stand
- This prevents your eyes from looking down

**Second Laptop Setup**:
- Position screen just below webcam
- Adjust brightness to minimum (less distraction)

### Reading Hints

1. **Don't stare** - glance naturally like you're thinking
2. **Use filler phrases** while reading:
   - "That's an interesting question..."
   - "Let me think about that for a moment..."
   - "To break this down..."

3. **Paraphrase hints** - don't read verbatim
4. **Add your own examples** to sound natural

---

## 🔧 Troubleshooting

### No audio captured
```bash
# List all audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test recording from USB sound card
python -c "
import sounddevice as sd
import numpy as np
duration = 5
print('Recording for 5 seconds...')
recording = sd.rec(int(duration * 16000), samplerate=16000, channels=1, device=YOUR_DEVICE_INDEX)
sd.wait()
print(f'Recorded {len(recording)} samples')
print(f'Max amplitude: {np.max(np.abs(recording))}')
"
```

If max amplitude is near 0, check:
- Cable connections
- USB sound card drivers
- Device index in .env

### High latency
- Check internet speed (need stable connection for APIs)
- Reduce `GROQ_MAX_TOKENS` in .env
- Use wired ethernet instead of WiFi on second device

### Hints not appearing
- Check receiver logs for errors
- Verify Groq API key is valid
- Ensure questions have question words (what, how, why, etc.)

---

## 🚀 Advanced: Network Streaming (Alternative)

If you can't use hardware bridge, use network streaming:

### On Main Laptop (RISKY - leaves software trace)

1. **Install VB-Audio VBAN**:
   - Download from vb-audio.com
   - Configure to stream system audio over LAN

2. **Or use AudioRelay**:
   - Install from audiorelay.net
   - Easier setup but commercial software

### On Second Device

1. **Update .env**:
```env
INPUT_MODE=network
NETWORK_STREAM_PORT=9000
```

2. **Modify audio_server.py** to receive network stream instead of USB input

**WARNING**: This approach installs software on main laptop which may be detected by proctoring software.

---

## 📊 Performance Metrics

Expected latencies:
- Audio capture: ~50ms
- Network transfer (hardware): 0ms
- Deepgram STT: 200-400ms
- Groq LLM: 400-800ms
- UI update: 50ms

**Total: 700ms - 1.3s** (well under 2s target)

---

## 🎓 Portfolio Positioning

When showcasing this project:

**Title**: "Real-time Contextual Meeting Assistant"

**Description**:
> Built a low-latency multi-device audio processing system using FastAPI, Deepgram STT, and Groq LLM. Implemented hardware audio routing and WebSocket streaming for <1.5s end-to-end latency. Features React-based real-time UI with mobile optimization.

**Skills Demonstrated**:
- Real-time audio processing
- WebSocket architecture
- Low-latency API integration
- Multi-device system design
- React/Next.js frontend development
- Hardware-software integration

**GitHub README**: Focus on technical architecture, not use case.

---

## ⚠️ Legal & Ethical Notice

This tool is for **educational purposes** and **personal learning assistance**.

**DO NOT USE** for:
- Academic exams (violates academic integrity)
- Professional certifications (violates terms)
- Any assessment where external assistance is prohibited

**Legitimate Use Cases**:
- Practice interviews
- Learning technical concepts
- Meeting note-taking
- Accessibility assistance

**You are responsible** for ensuring your use complies with applicable rules and regulations.

---

## 🆘 Support

If you encounter issues:

1. Check receiver logs: `python audio_server.py`
2. Check browser console: F12 in browser
3. Verify API keys are valid
4. Test audio capture independently
5. Check network connectivity

For hardware issues, test each component separately before combining.
