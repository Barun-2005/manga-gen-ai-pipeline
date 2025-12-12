# Utility functions for ComfyUI integration

def safe_mkdir(path):
    import os
    os.makedirs(path, exist_ok=True)

# Add more helpers as needed for prompt formatting, workflow mapping, etc.
