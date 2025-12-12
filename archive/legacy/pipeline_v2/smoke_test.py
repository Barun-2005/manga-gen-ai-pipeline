from generate_panel import generate_panel
import os

def main():
    output_path = os.path.join(os.path.dirname(__file__), 'output', 'panel_basic_bw_test.png')
    try:
        generate_panel(
            output_path=output_path,
            scene_type='basic',
            emotion='neutral',
            pose='standing',
            style='bw',
            seed=42
        )
        print(f"Smoke test succeeded: {output_path}")
    except Exception as e:
        print(f"Smoke test failed: {e}")

if __name__ == "__main__":
    main()
