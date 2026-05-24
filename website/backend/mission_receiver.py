import asyncio
import base64
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import logging

import websockets

from map_renderer import render_map
from vlm_pipeline import analyze_images
from llm_report import generate_report

logger = logging.getLogger('mission_receiver')
logging.basicConfig(level=logging.INFO)


async def start_mission_receiver(status_queue: asyncio.Queue, data_root: Path):
    """Connect to rosbridge, subscribe to /mission/payload, process missions."""
    uri = 'ws://localhost:9090'
    backoff = 1
    while True:
        try:
            async with websockets.connect(uri) as ws:
                logger.info('Connected to rosbridge')
                # subscribe to topic
                sub = {'op': 'subscribe', 'topic': '/mission/payload'}
                await ws.send(json.dumps(sub))
                backoff = 1
                async for message in ws:
                    try:
                        msg = json.loads(message)
                        if 'msg' in msg and isinstance(msg['msg'], dict) and 'data' in msg['msg']:
                            payload_text = msg['msg']['data']
                        else:
                            # rosbridge may wrap differently
                            payload_text = msg.get('msg', {}).get('data') or msg.get('data')
                        if not payload_text:
                            continue
                        bundle = json.loads(payload_text)
                        # process mission
                        await _process_bundle(bundle, status_queue, data_root)
                    except Exception as e:
                        logger.exception('Failed to process incoming message')
        except Exception as e:
            logger.warning(f'rosbridge connection failed: {e}; reconnecting in {backoff}s')
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)


async def _process_bundle(bundle, status_queue: asyncio.Queue, data_root: Path):
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    mission_dir = data_root / ts
    images_dir = mission_dir / 'images'
    mission_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    await status_queue.put({'status': 'started', 'mission_id': ts})

    # copy images
    src_images = bundle.get('images')
    manifest = bundle.get('image_manifest', [])
    copied = []
    for entry in manifest:
        fname = entry.get('filename')
        src = Path(src_images) / fname
        if src.exists():
            dst = images_dir / fname
            shutil.copy(src, dst)
            copied.append({'filepath': str(dst), 'pose': entry.get('pose')})
    await status_queue.put({'status': 'images_copied', 'mission_id': ts, 'count': len(copied)})

    # render map
    map_json = bundle.get('map')
    if map_json:
        try:
            img = render_map(map_json, bundle.get('path', []), manifest)
            map_path = mission_dir / 'map.png'
            img.save(map_path)
            await status_queue.put({'status': 'map_rendered', 'mission_id': ts})
        except Exception:
            logger.exception('Map rendering failed')
            await status_queue.put({'status': 'map_failed', 'mission_id': ts})

    # VLM analysis
    annotations = []
    try:
        annotations = analyze_images(copied)
        # save annotations
        with open(mission_dir / 'annotations.json', 'w') as fh:
            json.dump(annotations, fh)
        await status_queue.put({'status': 'images_analyzed', 'mission_id': ts, 'count': len(annotations)})
    except Exception:
        logger.exception('VLM analysis failed')
        await status_queue.put({'status': 'vlm_failed', 'mission_id': ts})

    # LLM report
    try:
        # compute simple metadata
        meta = {
            'duration_s': None,
            'distance_m': None,
            'start_time': None,
            'end_time': None,
            'num_images_captured': len(manifest),
            'num_images_notable': len(annotations),
        }
        report_md = generate_report(annotations, meta)
        with open(mission_dir / 'report.md', 'w') as fh:
            fh.write(report_md)
        await status_queue.put({'status': 'report_generated', 'mission_id': ts})
    except Exception:
        logger.exception('LLM report generation failed')
        await status_queue.put({'status': 'report_failed', 'mission_id': ts})

    await status_queue.put({'status': 'completed', 'mission_id': ts})
