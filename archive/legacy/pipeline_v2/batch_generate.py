import os
import json
import csv
import traceback
from typing import List, Dict, Optional
from generate_panel import generate_panel

def load_panel_list(input_path: str) -> List[Dict]:
    if input_path.endswith('.json'):
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif input_path.endswith('.csv'):
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        raise ValueError('Input file must be .json or .csv')

def batch_generate(input_path: str, log_path: Optional[str] = None):
    panels = load_panel_list(input_path)
    log_path = log_path or os.path.join(os.path.dirname(__file__), 'logs', 'batch_log.txt')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    successes = 0
    failures = 0
    with open(log_path, 'a', encoding='utf-8') as logf:
        for idx, panel in enumerate(panels):
            try:
                output_path = panel['output_path']
                scene_type = panel['scene_type']
                emotion = panel['emotion']
                pose = panel['pose']
                style = panel['style']
                seed = int(panel['seed']) if 'seed' in panel and panel['seed'] else None
                generate_panel(
                    output_path=output_path,
                    scene_type=scene_type,
                    emotion=emotion,
                    pose=pose,
                    style=style,
                    seed=seed
                )
                logf.write(f"SUCCESS: {output_path}\n")
                successes += 1
            except Exception as e:
                logf.write(f"FAIL: {panel.get('output_path', 'unknown')} | {str(e)}\n")
                logf.write(traceback.format_exc() + '\n')
                failures += 1
    print(f"Batch generation complete: {successes} succeeded, {failures} failed. Log: {log_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python batch_generate.py <input.json|input.csv>")
        exit(1)
    batch_generate(sys.argv[1])
