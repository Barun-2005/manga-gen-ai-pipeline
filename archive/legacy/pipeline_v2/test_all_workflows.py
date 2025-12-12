from generate_panel import generate_panel
import os

def main():
    tests = [
        # (scene_type, style, emotion, pose, output_name)
        ("basic", "bw", "neutral", "standing", "test_bw_manga_workflow.png"),
        ("basic", "color", "happy", "sitting", "test_color_manga_workflow.png"),
        ("closeup", "bw", "angry", "arms_crossed", "test_adapter_workflow_bw.png"),
        ("closeup", "color", "surprised", "openpose", "test_adapter_workflow_color.png"),
        ("sketch", "bw", "sad", "openpose", "test_controlnet_workflow_bw.png"),
        ("sketch", "color", "happy", "sitting", "test_controlnet_workflow_color.png"),
        ("scene_ref", "bw", "neutral", "standing", "test_scene_reference_workflow_bw.png"),
        ("scene_ref", "color", "happy", "openpose", "test_scene_reference_workflow_color.png"),
    ]
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    for scene_type, style, emotion, pose, fname in tests:
        output_path = os.path.join(output_dir, fname)
        print(f"Generating {fname} with scene_type={scene_type}, style={style}...")
        try:
            generate_panel(
                output_path=output_path,
                scene_type=scene_type,
                emotion=emotion,
                pose=pose,
                style=style,
                seed=1234
            )
            print(f"SUCCESS: {fname}")
        except Exception as e:
            print(f"FAIL: {fname} | {e}")

if __name__ == "__main__":
    main()
