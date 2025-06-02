# MangaGen

manga panel generator using comfyui and some python scripts

## setup

need python 3.10+ and comfyui running on localhost:8188

```bash
pip install -r requirements.txt
```

## usage

```bash
# basic generation
python scripts/run_full_pipeline.py --prompt "ninja in forest"

# or just run with default prompts
python scripts/run_full_pipeline.py

# see what you made
python scripts/run_full_pipeline.py --list-runs
```

## what it does

generates manga panels and tries to organize the output so you don't lose track of stuff

- makes base panels from prompts
- does some emotion analysis on dialogue
- validates the panels look decent
- puts everything in organized folders

## folder structure

```
scripts/run_full_pipeline.py  # main script
core/                         # pipeline modules
image_gen/                    # comfyui integration
assets/                       # prompts and workflows
outputs/runs/                 # where your panels go
```

## config

edit `config/output_config.json` if you want to change how many runs to keep around

## testing

```bash
python tests/test_pipeline.py
```

## output

each run makes a folder like `outputs/runs/run_20250603_123456/` with your panels and some analysis files

## requirements

- python 3.10+
- comfyui running on localhost:8188
- install deps with `pip install -r requirements.txt`

## notes

this is a work in progress, some features might be rough around the edges
