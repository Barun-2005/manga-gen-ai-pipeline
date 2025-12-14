
print("Testing Progress Calculation for 8 panels (2x2 layout, 2 pages)...")

total_panels = 8

for i in range(total_panels):
    # Logic from api/main.py
    # panel_prog = 20 + int(70 * (idx + 1) / job.total_panels)
    
    idx = i
    percent = 20 + int(70 * (idx + 1) / total_panels)
    
    print(f"Panel {idx+1}/{total_panels}: {percent}%")

print("Done.")
