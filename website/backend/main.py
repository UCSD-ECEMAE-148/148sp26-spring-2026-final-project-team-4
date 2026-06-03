import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import logging

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from mission_receiver import start_mission_receiver

OLLAMA_VLM_MODEL = os.environ.get('OLLAMA_VLM_MODEL', 'llava:13b')
OLLAMA_LLM_MODEL = os.environ.get('OLLAMA_LLM_MODEL', 'llama3.1:8b')

DATA_ROOT = Path('./data/missions')
DATA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI()
status_queue: asyncio.Queue = asyncio.Queue()
clients = set()

logger = logging.getLogger('backend')
logging.basicConfig(level=logging.INFO)


async def _check_ollama():
    try:
        r = httpx.get('http://localhost:11434/api/tags', timeout=5.0)
    except Exception as e:
        logger.warning('Ollama not reachable at http://localhost:11434 — continuing without Ollama. Start it with: ollama serve')
        return
    tags = r.json()
    models = [t.get('name') for t in tags]
    missing = []
    if OLLAMA_VLM_MODEL not in models:
        missing.append(f"OLLAMA_VLM_MODEL ({OLLAMA_VLM_MODEL}) not pulled: ollama pull {OLLAMA_VLM_MODEL}")
    if OLLAMA_LLM_MODEL not in models:
        missing.append(f"OLLAMA_LLM_MODEL ({OLLAMA_LLM_MODEL}) not pulled: ollama pull {OLLAMA_LLM_MODEL}")
    if missing:
        for m in missing:
            logger.warning(m)


@app.on_event('startup')
async def startup_event():
    await _check_ollama()
    # start mission receiver background task
    loop = asyncio.get_event_loop()
    loop.create_task(start_mission_receiver(status_queue, DATA_ROOT))


@app.get('/api/missions')
def list_missions():
    items = []
    for p in sorted(DATA_ROOT.iterdir(), reverse=True):
        if p.is_dir():
            items.append(p.name)
    return {'missions': items}


@app.get('/api/missions/{mid}')
def get_mission(mid: str):
    mdir = DATA_ROOT / mid
    if not mdir.exists():
        raise HTTPException(status_code=404, detail='Mission not found')
    report = None
    ann = None
    if (mdir / 'report.md').exists():
        report = (mdir / 'report.md').read_text()
    if (mdir / 'annotations.json').exists():
        ann = json.loads((mdir / 'annotations.json').read_text())
    images = [p.name for p in (mdir / 'images').glob('*')]
    return {'id': mid, 'report': report, 'annotations': ann, 'images': images}


@app.get('/api/missions/{mid}/map.png')
def get_map(mid: str):
    p = DATA_ROOT / mid / 'map.png'
    if not p.exists():
        raise HTTPException(status_code=404, detail='Map not found')
    return FileResponse(p, media_type='image/png')


@app.get('/api/missions/{mid}/images/{filename}')
def get_image(mid: str, filename: str):
    p = DATA_ROOT / mid / 'images' / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail='Image not found')
    return FileResponse(p)


@app.websocket('/ws/status')
async def ws_status(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            msg = await status_queue.get()
            # broadcast to connected clients
            living = set()
            for c in list(clients):
                try:
                    await c.send_json(msg)
                    living.add(c)
                except Exception:
                    pass
            clients.clear()
            clients.update(living)
    except WebSocketDisconnect:
        clients.discard(ws)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
