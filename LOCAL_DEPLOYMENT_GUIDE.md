# SatQuery-AI — Local GPU Deployment + Cloudflare Tunnel Guide

> **Audience**: SIH team members running the backend on a GPU laptop and exposing it
> to the internet so the hosted frontend can reach it during a live demo.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Backend Setup — Step by Step](#3-backend-setup--step-by-step)
4. [Running the Backend](#4-running-the-backend)
5. [Installing Cloudflare Tunnel (`cloudflared`)](#5-installing-cloudflare-tunnel-cloudflared)
6. [Creating and Running the Tunnel](#6-creating-and-running-the-tunnel)
7. [Connecting the Frontend to the Tunnel](#7-connecting-the-frontend-to-the-tunnel)
8. [End-to-End Verification](#8-end-to-end-verification)
9. [GPU & REAL Mode Setup](#9-gpu--real-mode-setup)
10. [Troubleshooting](#10-troubleshooting)
11. [SIH Demo Day Checklist](#11-sih-demo-day-checklist)

---

## 1. Architecture Overview

```
┌─────────────────────────────────┐
│  Frontend (Vercel / Netlify)    │
│  https://geolens.vercel.app     │
└──────────────┬──────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────┐
│  Cloudflare Tunnel (cloudflared)│
│  https://<random>.trycloudflare │
│  .com                           │
└──────────────┬──────────────────┘
               │ localhost:8000
               ▼
┌─────────────────────────────────┐
│  FastAPI Backend (uvicorn)      │
│  Running on your GPU laptop     │
│  http://localhost:8000          │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Qwen2.5-VL-3B-Instruct (GPU)  │
│  or MOCK mode for testing       │
└─────────────────────────────────┘
```

**How it works:**

1. Your GPU laptop runs the FastAPI backend on `localhost:8000`.
2. `cloudflared` creates an encrypted tunnel from Cloudflare's edge network to your laptop.
3. Cloudflare gives you a public HTTPS URL (e.g., `https://abc-xyz-123.trycloudflare.com`).
4. The frontend (hosted on Vercel/Netlify or running locally) sends API requests to that public URL.
5. Cloudflare routes those requests through the tunnel to your local backend.

---

## 2. Prerequisites

### 2.1 Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU       | NVIDIA with 4 GB VRAM (MOCK mode works without GPU) | NVIDIA with 8+ GB VRAM (RTX 3060 Ti or better) |
| RAM       | 8 GB | 16 GB |
| Storage   | 5 GB free (backend + deps) | 15 GB free (includes model weights ~6 GB) |
| Internet  | Stable connection (any speed) | 10+ Mbps upload for smooth demo |

### 2.2 Software

| Software | Version | Check Command | Install |
|----------|---------|---------------|---------|
| **Python** | 3.10 – 3.14 | `python --version` | [python.org](https://www.python.org/downloads/) |
| **Git** | Any recent | `git --version` | [git-scm.com](https://git-scm.com/downloads) |
| **NVIDIA Driver** | 535+ (for REAL mode) | `nvidia-smi` | [nvidia.com/drivers](https://www.nvidia.com/Download/index.aspx) |
| **CUDA Toolkit** | 11.8 or 12.x (for REAL mode) | `nvcc --version` | [developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads) |
| **Node.js** | 18+ (only if running frontend locally) | `node --version` | [nodejs.org](https://nodejs.org/) |

> [!NOTE]
> If you only want to run in **MOCK mode** (fake AI responses for testing), you do NOT need
> NVIDIA drivers, CUDA, or a GPU at all. MOCK mode runs entirely on CPU.

---

## 3. Backend Setup — Step by Step

### 3.1 Clone the Repository

```powershell
# Pick a directory for the project
cd C:\Users\YourUser\Desktop

# Clone the backend
git clone https://github.com/shriyanshu22/SatQuery-AI.git backend
cd backend
```

### 3.2 Create a Python Virtual Environment

```powershell
# Create the virtual environment
python -m venv .venv

# Activate it (PowerShell)
.\.venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

> [!TIP]
> On **Command Prompt** (cmd), use `.\.venv\Scripts\activate.bat` instead.

### 3.3 Install Dependencies

```powershell
# Upgrade pip first
pip install --upgrade pip

# Install core dependencies
pip install fastapi uvicorn[standard] pydantic pydantic-settings pillow numpy scikit-image opencv-python-headless tifffile scipy structlog httpx pyyaml aiofiles

# Verify installation
pip list | findstr fastapi
```

**Expected output:** `fastapi   0.115.x` (or similar)

### 3.4 Install GPU Dependencies (REAL Mode Only)

Skip this section if you only need MOCK mode.

```powershell
# Install PyTorch with CUDA support
# For CUDA 11.8:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CUDA 12.4+:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install Hugging Face Transformers (for Qwen2.5-VL)
pip install transformers accelerate

# Verify CUDA is available
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

**Expected output:** `CUDA available: True, Device: NVIDIA GeForce RTX XXXX`

### 3.5 Configure the Environment File

Create a file called `.env` in the **backend root directory** (same level as the `backend/` package folder):

```ini
# ============================================================
# SatQuery-AI Backend Configuration
# ============================================================

# --- Server ---
SATQUERY_SERVER__HOST=0.0.0.0
SATQUERY_SERVER__PORT=8000
SATQUERY_SERVER__CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","https://geolens.vercel.app"]

# --- Model ---
# Set to "MOCK" for testing without GPU, "REAL" for actual inference
SATQUERY_MODEL__BACKEND_TYPE=MOCK

# --- Storage ---
SATQUERY_STORAGE__UPLOAD_DIR=./uploads
SATQUERY_STORAGE__ARTIFACT_DIR=./artifacts
```

> [!IMPORTANT]
> **CORS Origins**: Add your frontend's deployed URL to the `CORS_ORIGINS` list.
> For example, if your frontend is at `https://my-sih-app.vercel.app`, add it:
> ```ini
> SATQUERY_SERVER__CORS_ORIGINS=["http://localhost:5173","https://my-sih-app.vercel.app"]
> ```
> The tunnel URL does NOT go here — CORS origins are where the **frontend** is served from.

### 3.6 Create Required Directories

```powershell
# From the backend root directory
mkdir uploads -ErrorAction SilentlyContinue
mkdir artifacts -ErrorAction SilentlyContinue
```

---

## 4. Running the Backend

### 4.1 Start in MOCK Mode (No GPU Required)

```powershell
# Make sure your venv is activated
.\.venv\Scripts\Activate.ps1

# Start the server
python -m uvicorn backend.api.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX]
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 4.2 Verify the Backend is Running

Open a **new terminal** (keep the server running in the first one):

```powershell
# Health check
curl http://localhost:8000/health

# Or use a browser: http://localhost:8000/health
```

**Expected response:**
```json
{"status": "healthy", "version": "0.1.0"}
```

```powershell
# Check capabilities
curl http://localhost:8000/api/v1/capabilities
```

### 4.3 Start in REAL Mode (GPU Required)

1. Edit `.env` and change:
   ```ini
   SATQUERY_MODEL__BACKEND_TYPE=REAL
   ```

2. Start the server (same command):
   ```powershell
   python -m uvicorn backend.api.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
   ```

3. The first request will download the Qwen2.5-VL-3B-Instruct model (~6 GB). Subsequent
   starts will use the cached model from `~/.cache/huggingface/`.

> [!WARNING]
> **VRAM Usage**: The Qwen2.5-VL-3B model uses approximately **6–7 GB of VRAM**.
> Close other GPU-intensive applications (games, video editors, other ML models)
> before starting in REAL mode. Monitor VRAM with `nvidia-smi` in a separate terminal.

---

## 5. Installing Cloudflare Tunnel (`cloudflared`)

You have three options to install `cloudflared` on Windows:

### Option A: Direct Download (Simplest)

1. Download the latest Windows binary:
   - **64-bit**: https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe

2. Rename the file to `cloudflared.exe`

3. Move it to a convenient location, e.g., `C:\Tools\cloudflared.exe`

4. (Optional) Add to PATH:
   ```powershell
   # Add to PATH for current session
   $env:PATH += ";C:\Tools"

   # Or add permanently via System Settings:
   # Settings → System → About → Advanced system settings → Environment Variables
   # Edit "Path" under User variables → Add "C:\Tools"
   ```

### Option B: Using `winget` (Windows Package Manager)

```powershell
winget install Cloudflare.cloudflared
```

After installation, restart your terminal. `cloudflared` will be available globally.

### Option C: Using Chocolatey

```powershell
# If you have Chocolatey installed
choco install cloudflared
```

### Verify Installation

```powershell
cloudflared --version
```

**Expected output:** `cloudflared version 2024.x.x (built ...)` or similar.

---

## 6. Creating and Running the Tunnel

### 6.1 Quick Tunnel (No Account Required — Recommended for Demo)

This is the **simplest approach** and requires no Cloudflare account:

```powershell
# Make sure your backend is running on port 8000 first!
cloudflared tunnel --url http://localhost:8000
```

**Output will include something like:**
```
2024-xx-xx INFO Starting tunnel
2024-xx-xx INFO +-----------------------------------------------------------+
2024-xx-xx INFO |  Your quick Tunnel has been created! Visit it at:          |
2024-xx-xx INFO |  https://random-words-here.trycloudflare.com               |
2024-xx-xx INFO +-----------------------------------------------------------+
```

> [!IMPORTANT]
> **Copy that URL!** You'll need it for the frontend configuration.
> The URL changes every time you restart the tunnel, so note it down each time.

### 6.2 Named Tunnel (Requires Free Cloudflare Account — Stable URL)

If you want a **persistent, stable URL** that doesn't change between restarts:

#### Step 1: Create a Cloudflare Account

Go to https://dash.cloudflare.com/sign-up and create a free account.

#### Step 2: Authenticate `cloudflared`

```powershell
cloudflared tunnel login
```

This opens a browser. Log in and authorize `cloudflared`. A certificate is saved locally.

#### Step 3: Create a Named Tunnel

```powershell
cloudflared tunnel create satquery-backend
```

**Output:** `Created tunnel satquery-backend with id <TUNNEL-UUID>`

Note the **Tunnel UUID**.

#### Step 4: Create a Configuration File

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL-UUID>
credentials-file: C:\Users\YourUser\.cloudflared\<TUNNEL-UUID>.json

ingress:
  - hostname: satquery-api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

> [!NOTE]
> Named tunnels require you to **own a domain** and add it to Cloudflare.
> For SIH demo, the **Quick Tunnel** (Section 6.1) is usually sufficient.

#### Step 5: Route DNS

```powershell
cloudflared tunnel route dns satquery-backend satquery-api.yourdomain.com
```

#### Step 6: Run the Named Tunnel

```powershell
cloudflared tunnel run satquery-backend
```

### 6.3 Summary: Quick vs Named Tunnel

| Feature | Quick Tunnel | Named Tunnel |
|---------|-------------|--------------|
| Account needed | No | Yes (free) |
| Custom domain | No (random `.trycloudflare.com`) | Yes |
| URL persistence | Changes on restart | Permanent |
| Setup time | 30 seconds | 15 minutes |
| Best for | Demo day, testing | Production, long-term |

**Recommendation for SIH**: Use **Quick Tunnel**. It's instant and requires zero setup.

---

## 7. Connecting the Frontend to the Tunnel

### 7.1 If Frontend is Hosted (Vercel / Netlify)

You need to update the environment variable on your hosting platform:

#### Vercel

1. Go to your Vercel project dashboard
2. Navigate to **Settings → Environment Variables**
3. Set (or update):
   ```
   VITE_API_BASE_URL = https://random-words-here.trycloudflare.com
   ```
4. **Redeploy** the frontend (Vercel → Deployments → Redeploy)

#### Netlify

1. Go to your Netlify site dashboard
2. Navigate to **Site settings → Environment variables**
3. Set:
   ```
   VITE_API_BASE_URL = https://random-words-here.trycloudflare.com
   ```
4. **Trigger a redeploy** (Deploys → Trigger deploy)

> [!CAUTION]
> **Every time you restart the Quick Tunnel**, the URL changes. You must:
> 1. Copy the new tunnel URL
> 2. Update the environment variable on Vercel/Netlify
> 3. Redeploy the frontend
>
> **Pro tip for demo day**: Start the tunnel ONCE before the demo and don't restart it.

### 7.2 If Frontend is Running Locally

Edit the `.env` file in the frontend project root:

```ini
# For local frontend connecting to tunneled backend
VITE_API_BASE_URL=https://random-words-here.trycloudflare.com
VITE_API_MODE=real
```

Then restart the dev server:

```powershell
cd "C:\Users\YourUser\Desktop\SIH FRONTEND"
npm run dev
```

### 7.3 Runtime Override (No Rebuild Needed)

The frontend supports a **localStorage override** for the API URL. Open the browser console (F12) and run:

```javascript
localStorage.setItem('satquery_api_base_url', 'https://random-words-here.trycloudflare.com');
location.reload();
```

This works immediately without rebuilding or redeploying. To revert:

```javascript
localStorage.removeItem('satquery_api_base_url');
location.reload();
```

> [!TIP]
> The **localStorage override** is the fastest way to switch the backend URL during a demo.
> No redeployment needed — just paste the new URL in the console and reload.

---

## 8. End-to-End Verification

Run through this checklist to confirm everything is connected:

### Step 1: Verify Backend Locally

```powershell
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}
```

### Step 2: Verify Tunnel is Working

```powershell
curl https://random-words-here.trycloudflare.com/health
# Expected: {"status": "healthy", ...}
```

You can also open this URL in your browser.

### Step 3: Verify Frontend Can Reach Backend

1. Open the frontend in your browser
2. Open DevTools (F12) → **Network** tab
3. Trigger an action (e.g., upload an image, ask a query)
4. Check that API requests go to `https://random-words-here.trycloudflare.com/...`
5. Verify responses return `200 OK`

### Step 4: Test the Full Pipeline

1. Upload a satellite image through the frontend
2. Ask a question like "What land cover types are visible?"
3. Verify you get a response (mock or real depending on mode)

### Debugging Network Issues

If the frontend can't reach the backend through the tunnel:

```powershell
# Check if backend is listening
netstat -ano | findstr :8000

# Check if cloudflared is running
tasklist | findstr cloudflared

# Test tunnel directly in browser
# Open: https://your-tunnel-url.trycloudflare.com/health
```

---

## 9. GPU & REAL Mode Setup

### 9.1 NVIDIA Driver Installation

1. Go to https://www.nvidia.com/Download/index.aspx
2. Select your GPU model
3. Download and install the latest **Game Ready** or **Studio** driver
4. Restart your computer
5. Verify:
   ```powershell
   nvidia-smi
   ```
   You should see your GPU name, driver version, and CUDA version.

### 9.2 CUDA Toolkit Installation

1. Go to https://developer.nvidia.com/cuda-downloads
2. Select: Windows → x86_64 → Your Windows version → exe (local)
3. Download and run the installer
4. Choose **Custom installation** → check only **CUDA** (uncheck Visual Studio integration if not needed)
5. Verify:
   ```powershell
   nvcc --version
   ```

### 9.3 Switching Between MOCK and REAL Mode

Edit the `.env` file in the backend root:

```ini
# MOCK mode (no GPU, fake responses for testing)
SATQUERY_MODEL__BACKEND_TYPE=MOCK

# REAL mode (GPU required, actual AI inference)
SATQUERY_MODEL__BACKEND_TYPE=REAL
```

Then **restart** the backend server (Ctrl+C and re-run the `uvicorn` command).

### 9.4 Pre-downloading the Model

To avoid downloading the model during the demo:

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Pre-download the Qwen2.5-VL model
python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-VL-3B-Instruct', trust_remote_code=True); AutoTokenizer.from_pretrained('Qwen/Qwen2.5-VL-3B-Instruct', trust_remote_code=True); print('Model downloaded successfully!')"
```

The model will be cached at `C:\Users\YourUser\.cache\huggingface\hub\`.

### 9.5 Monitoring GPU Usage

Keep `nvidia-smi` running in a separate terminal during the demo:

```powershell
# One-time check
nvidia-smi

# Continuous monitoring (updates every 2 seconds)
nvidia-smi -l 2
```

Key metrics to watch:
- **GPU-Util**: Should spike during inference, ~0% when idle
- **Memory-Usage**: Qwen2.5-VL-3B uses ~6–7 GB
- **Temperature**: Keep below 85°C

---

## 10. Troubleshooting

### 10.1 Backend Won't Start

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'fastapi'` | Virtual env not activated | Run `.\.venv\Scripts\Activate.ps1` |
| `Address already in use` | Port 8000 is taken | Kill the process: `netstat -ano \| findstr :8000` then `taskkill /PID <PID> /F` |
| `CUDA out of memory` | Not enough VRAM | Close other GPU apps, or switch to MOCK mode |
| `ImportError: torch` | PyTorch not installed | Install with CUDA: `pip install torch --index-url ...` |

### 10.2 Tunnel Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `cloudflared` command not found | Not installed or not on PATH | Reinstall via winget or add to PATH |
| Tunnel starts but URL doesn't work | Backend not running | Start the backend first, then the tunnel |
| `connection refused` in cloudflared logs | Wrong port | Ensure `--url http://localhost:8000` matches your server port |
| Tunnel disconnects randomly | Unstable internet | Use a wired connection; restart `cloudflared` |
| URL changed after restart | Normal for Quick Tunnels | Update frontend config with new URL |

### 10.3 Frontend Can't Connect

| Symptom | Cause | Fix |
|---------|-------|-----|
| CORS errors in browser console | Frontend origin not in CORS list | Add your frontend URL to `SATQUERY_SERVER__CORS_ORIGINS` in `.env` |
| `net::ERR_CONNECTION_REFUSED` | Wrong API URL | Check `VITE_API_BASE_URL` matches the tunnel URL |
| Requests go to `localhost:8000` | Old env var | Update `.env` or use localStorage override |
| Mixed content error | Frontend on HTTPS, backend on HTTP | The tunnel provides HTTPS — use the tunnel URL, not localhost |

### 10.4 CORS Configuration for Tunnel

When using a tunnel, ensure the **frontend's origin** is in the CORS list, NOT the tunnel URL:

```ini
# CORRECT — frontend origins
SATQUERY_SERVER__CORS_ORIGINS=["http://localhost:5173","https://geolens.vercel.app"]

# WRONG — don't put the tunnel URL here
# SATQUERY_SERVER__CORS_ORIGINS=["https://xxx.trycloudflare.com"]
```

The tunnel URL is where the **backend** is exposed. CORS needs the **frontend's** origin.

---

## 11. SIH Demo Day Checklist

### 🔧 Before Demo Day (Day Before)

- [ ] **Test everything end-to-end** on the actual demo laptop
- [ ] **Pre-download the AI model** (Section 9.4) — don't rely on demo-day WiFi
- [ ] **Install `cloudflared`** and verify it works
- [ ] **Charge laptop** fully and bring the charger
- [ ] **Prepare backup**: Have MOCK mode ready as a fallback
- [ ] **Test on venue WiFi** if possible (some networks block tunnels)
- [ ] **Close unnecessary apps** to free up RAM and VRAM

### 🚀 Demo Day — Startup Sequence

Follow this exact order:

```
Step 1: Open Terminal #1 — Start Backend
─────────────────────────────────────────
cd C:\path\to\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.api.main:create_app --factory --host 0.0.0.0 --port 8000
# Wait for "Application startup complete"

Step 2: Open Terminal #2 — Start Tunnel
─────────────────────────────────────────
cloudflared tunnel --url http://localhost:8000
# Copy the https://xxx.trycloudflare.com URL

Step 3: Update Frontend
─────────────────────────────────────────
# Option A: localStorage override (fastest)
# In browser console (F12):
localStorage.setItem('satquery_api_base_url', 'https://xxx.trycloudflare.com');
location.reload();

# Option B: Update Vercel env var and redeploy

Step 4: Verify
─────────────────────────────────────────
# In browser, open: https://xxx.trycloudflare.com/health
# Should return: {"status": "healthy", ...}
```

### ⚡ Quick Recovery Procedures

**If the backend crashes:**
```powershell
# Terminal #1: Restart
python -m uvicorn backend.api.main:create_app --factory --host 0.0.0.0 --port 8000
# Tunnel stays connected — no URL change needed
```

**If the tunnel drops:**
```powershell
# Terminal #2: Restart
cloudflared tunnel --url http://localhost:8000
# NEW URL — must update frontend!
```

**If GPU runs out of memory:**
```powershell
# Switch to MOCK mode instantly
# Edit .env: SATQUERY_MODEL__BACKEND_TYPE=MOCK
# Restart backend (Ctrl+C then re-run)
```

**If venue WiFi blocks tunnels:**
```
# Fallback: Use phone hotspot
# Mobile hotspot → Connect laptop → Restart tunnel
```

### 🛡️ Keeping the Tunnel Alive

The Quick Tunnel can disconnect after extended inactivity. To prevent this:

1. **Don't minimize the cloudflared terminal** — keep it visible
2. **Disable laptop sleep**: Settings → Power → Screen & sleep → Never
3. **Disable WiFi power saving**:
   ```powershell
   # Run as Administrator
   powercfg -change -standby-timeout-ac 0
   ```
4. **Optional**: Set up a keep-alive ping from another terminal:
   ```powershell
   # Ping the tunnel every 60 seconds to keep it warm
   while ($true) { curl -s https://xxx.trycloudflare.com/health | Out-Null; Start-Sleep 60 }
   ```

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════╗
║                  SATQUERY-AI QUICK REFERENCE                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  START BACKEND:                                              ║
║  cd backend                                                  ║
║  .\.venv\Scripts\Activate.ps1                                ║
║  python -m uvicorn backend.api.main:create_app \             ║
║    --factory --host 0.0.0.0 --port 8000                      ║
║                                                              ║
║  START TUNNEL:                                               ║
║  cloudflared tunnel --url http://localhost:8000               ║
║                                                              ║
║  UPDATE FRONTEND (browser console):                          ║
║  localStorage.setItem('satquery_api_base_url',               ║
║    'https://xxx.trycloudflare.com');                          ║
║  location.reload();                                          ║
║                                                              ║
║  HEALTH CHECK:                                               ║
║  curl https://xxx.trycloudflare.com/health                   ║
║                                                              ║
║  TOGGLE MOCK/REAL:                                           ║
║  Edit .env → SATQUERY_MODEL__BACKEND_TYPE=MOCK or REAL       ║
║  Then restart backend                                        ║
║                                                              ║
║  MONITOR GPU:                                                ║
║  nvidia-smi -l 2                                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

*Last updated: September 2026 | SatQuery-AI / GeoLens — SIH Project*
