```bash
./setup.sh
```

This checks and installs: Python 3.10+, pip, ffmpeg, ffprobe, Chrome, creates venv, installs dependencies, verifies imports.

> **Windows:** Use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) (`wsl --install`) or Git Bash. All bash scripts and commands assume a Unix shell.

### Manual setup

```bash
# Prerequisites: Python 3.10+, ffmpeg, Chrome
pip install -r requirements.txt
```

### Run

```bash
# 1. Load Chrome extension: chrome://extensions → Developer mode → Load unpacked → extension/
# 2. Open https://flow.google.com/ and sign in — leave the tab open
# 3. Create a project in the Flow UI and copy its uuid out of the URL
export FLOW_PROJECT_ID=<that uuid>

# 4. Start agent
source venv/bin/activate   # if using setup.sh
python -m agent.main

# 5. Verify
curl http://127.0.0.1:8100/health
# {"status":"ok","extension_connected":true}
curl http://127.0.0.1:8100/api/flow/status
# {"connected":true,"transport":"batch","flow_project_id":"…","flow_key_present":false}
```
# project
http://127.0.0.1:8100/api/projects
http://127.0.0.1:8100/api/flow/status
http://127.0.0.1:8100/openapi.json