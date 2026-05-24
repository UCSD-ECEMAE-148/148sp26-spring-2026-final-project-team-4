import os
import json
import httpx

OLLAMA_LLM_MODEL = os.environ.get('OLLAMA_LLM_MODEL', 'llama3.1:8b')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/chat')


def generate_report(annotations, mission_metadata):
    context_bundle = {
        'mission': mission_metadata,
        'observations': [
            {
                'timestamp': a.get('timestamp'),
                'pose': a.get('pose'),
                'score': a.get('score'),
                'description': a.get('description'),
                'tags': a.get('tags'),
            }
            for a in annotations
        ]
    }

    payload = {
        'model': OLLAMA_LLM_MODEL,
        'stream': False,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'You are a mission report writer for an autonomous robot system. '
                    'Write a clear, factual Markdown report based on the structured data provided. '
                    'Use exactly these sections: ## Mission Summary, ## Route Overview, '
                    '## Notable Observations, ## Obstacles & Anomalies, ## Recommendations. '
                    'Be concise and technical. Do not add any sections beyond those listed.'
                )
            },
            {
                'role': 'user',
                'content': json.dumps(context_bundle)
            }
        ]
    }

    r = httpx.post(OLLAMA_URL, json=payload, timeout=120)
    report_md = r.json().get('message', {}).get('content', '')
    return report_md
