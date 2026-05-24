import os
import json
import base64
import httpx
import time
import logging

OLLAMA_VLM_MODEL = os.environ.get('OLLAMA_VLM_MODEL', 'llava:13b')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/chat')

logger = logging.getLogger('vlm')
logging.basicConfig(level=logging.INFO)


def _strip_fences(s: str):
    s = s.strip()
    if s.startswith('```'):
        # remove fences
        parts = s.split('\n')
        # drop leading fence line and trailing fence if present
        if parts[0].startswith('```'):
            parts = parts[1:]
        if parts and parts[-1].startswith('```'):
            parts = parts[:-1]
        return '\n'.join(parts).strip()
    return s


def analyze_images(image_entries):
    """Process images sequentially using Ollama VLM. Returns notable annotations."""
    results = []
    for ent in image_entries:
        path = ent['filepath']
        pose = ent.get('pose')
        try:
            with open(path, 'rb') as fh:
                b64 = base64.b64encode(fh.read()).decode()
        except Exception as e:
            logger.warning(f'Failed to read {path}: {e}')
            continue

        prompt = (
            "You are analyzing images from an autonomous robot exploration mission.\n"
            "Evaluate this image and return ONLY a JSON object with absolutely no other text,"
            " no markdown fences, no explanation:\n"
            "{\n  \"score\": <integer 1-10>,\n  \"description\": \"<1-2 sentence factual description>\",\n  \"tags\": [\"<tag1>\",\"<tag2>\"],\n  \"notable\": <true|false>\n}\n"
        )

        payload = {
            'model': OLLAMA_VLM_MODEL,
            'stream': False,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt,
                    'images': [b64],
                }
            ]
        }

        try:
            r = httpx.post(OLLAMA_URL, json=payload, timeout=60)
            text = r.json().get('message', {}).get('content', '')
            text = _strip_fences(text)
            data = json.loads(text)
            if data.get('notable'):
                results.append({
                    'filepath': path,
                    'pose': pose,
                    'score': data.get('score'),
                    'description': data.get('description'),
                    'tags': data.get('tags', []),
                })
        except Exception as e:
            logger.warning(f'Ollama VLM failed for {path}: {e}')
            continue
        # be polite to local model
        time.sleep(0.1)

    return results
