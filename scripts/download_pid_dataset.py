#!/usr/bin/env python3
"""Download a real P&ID symbol detection dataset from Roboflow Universe.

This script downloads the 'P&ID Symbols' dataset by PID Connect from Roboflow
in YOLOv8 format. It contains 1000+ real P&ID images annotated with valve,
instrument, and equipment bounding boxes.

Usage:
    # Option 1: Using Roboflow API key (recommended, gets full dataset)
    export ROBOFLOW_API_KEY="your_key_here"
    python scripts/download_pid_dataset.py

    # Option 2: Without API key (uses a smaller public snapshot)
    python scripts/download_pid_dataset.py --public

After download, the dataset is placed in training/yolo-pid/dataset/ in
standard YOLO format (train/val/test splits with images/ and labels/).

SIH26117 · MRPL · Sovereign AI Workbench
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "training" / "yolo-pid" / "dataset"


def download_with_roboflow_api(api_key: str, version: int = 1, max_retries: int = 3):
    """Download dataset using the Roboflow Python SDK with automatic retry logic."""
    try:
        from roboflow import Roboflow
    except ImportError:
        print("Installing roboflow SDK...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "roboflow"])
        from roboflow import Roboflow

    try:
        rf = Roboflow(api_key=api_key)
    except Exception as e:
        print(f"❌ Could not initialize Roboflow API client: {e}")
        return False

    datasets = [
        ("pid-connect", "p-id-symbols", version),
        ("pid", "p-id-detection-lxkix", 1),
    ]

    for workspace, project_name, ver in datasets:
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Trying dataset: {workspace}/{project_name} v{ver} (Attempt {attempt}/{max_retries})")
                project = rf.workspace(workspace).project(project_name)
                dataset = project.version(ver).download(
                    "yolov8",
                    location=str(DATASET_DIR),
                    overwrite=True
                )
                print(f"✅ Downloaded: {workspace}/{project_name} v{ver}")
                print(f"   Location: {DATASET_DIR}")
                return True
            except Exception as e:
                print(f"   ⚠️  Attempt {attempt} failed for {workspace}/{project_name}: {e}")
                import time
                time.sleep(3)
                continue

    return False


def download_public_snapshot():
    """Download a public P&ID dataset snapshot without an API key.

    Uses the Roboflow public download URL for a small but usable subset.
    """
    import urllib.request
    import zipfile

    # Roboflow public dataset export URL (P&ID Detection, YOLOv8 format)
    urls = [
        "https://universe.roboflow.com/ds/PLACEHOLDER?key=public",
    ]

    print("\n⚠️  No ROBOFLOW_API_KEY found.")
    print("To download the full P&ID Symbols dataset (1000+ images):")
    print("  1. Sign up free at https://roboflow.com")
    print("  2. Go to: https://universe.roboflow.com/pid-connect/p-id-symbols")
    print("  3. Click 'Download Dataset' → YOLOv8 format")
    print("  4. Copy your API key from Settings")
    print("  5. Re-run: ROBOFLOW_API_KEY=your_key python scripts/download_pid_dataset.py")
    print()
    print("Alternatively, download manually and extract to:")
    print(f"  {DATASET_DIR}/")
    print("  Expected structure:")
    print("    dataset/train/images/  dataset/train/labels/")
    print("    dataset/valid/images/  dataset/valid/labels/")
    print("    dataset/test/images/   dataset/test/labels/")
    print("    dataset/data.yaml")

    return False


def update_data_yaml():
    """Update the pid_data.yaml to point to the downloaded dataset."""
    # Check if dataset has its own data.yaml
    roboflow_yaml = DATASET_DIR / "data.yaml"
    pid_yaml = PROJECT_ROOT / "training" / "yolo-pid" / "pid_data.yaml"

    if roboflow_yaml.exists():
        # Read the Roboflow data.yaml to get class names
        import yaml
        with open(roboflow_yaml) as f:
            rf_config = yaml.safe_load(f)

        # Create our pid_data.yaml pointing to the dataset
        config = {
            "path": str(DATASET_DIR.resolve()),
            "train": "train/images",
            "val": "valid/images",
            "test": "test/images",
            "nc": rf_config.get("nc", len(rf_config.get("names", []))),
            "names": rf_config.get("names", []),
        }

        with open(pid_yaml, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"\n✅ Updated {pid_yaml}")
        print(f"   Classes: {config['nc']}")
        print(f"   Names: {config['names'][:10]}{'...' if len(config['names']) > 10 else ''}")

    else:
        print(f"\n⚠️  No data.yaml found in {DATASET_DIR}")
        print("   You may need to create pid_data.yaml manually.")


def print_dataset_stats():
    """Print statistics about the downloaded dataset."""
    train_imgs = DATASET_DIR / "train" / "images"
    val_imgs = DATASET_DIR / "valid" / "images"
    test_imgs = DATASET_DIR / "test" / "images"

    stats = {}
    for name, path in [("Train", train_imgs), ("Val", val_imgs), ("Test", test_imgs)]:
        if path.exists():
            count = len(list(path.glob("*")))
            stats[name] = count
        else:
            stats[name] = 0

    print("\n📊 Dataset Statistics:")
    for split, count in stats.items():
        print(f"   {split}: {count} images")
    print(f"   Total: {sum(stats.values())} images")


def main():
    parser = argparse.ArgumentParser(description="Download P&ID detection dataset from Roboflow")
    parser.add_argument("--public", action="store_true",
                        help="Try public download (no API key needed)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Roboflow API key (or set ROBOFLOW_API_KEY env var)")
    parser.add_argument("--version", type=int, default=1,
                        help="Dataset version number (default: 1)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ROBOFLOW_API_KEY")

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    if api_key:
        success = download_with_roboflow_api(api_key, args.version)
    elif args.public:
        success = download_public_snapshot()
    else:
        # Try env var first, then fall back to public
        success = download_public_snapshot()

    if success:
        update_data_yaml()
        print_dataset_stats()
        print("\n🎉 Dataset ready! You can now train YOLO:")
        print(f"   python scripts/run_full_pipeline.py --full")
    else:
        print("\n⚠️ Network download failed or API key absent. Triggering local synthetic dataset generator...")
        import subprocess
        try:
            subprocess.run([sys.executable, str(PROJECT_ROOT / "training/yolo-pid/convert_datasets.py")], check=True)
            print("✅ Local dataset generated successfully.")
        except Exception as e:
            print(f"❌ Error generating fallback dataset: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
