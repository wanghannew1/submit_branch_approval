#!/usr/bin/env python3
"""
Feishu File Upload Demo Script
Tests the single-step upload: FeishuClient.upload_file_to_feishu(file_path) → file_code
Usage: python demo_upload.py /path/to/file.xlsx
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Import FeishuClient from demo_app (Task 5 implementation)
from demo_app import FeishuClient

ENV_PATH = Path(__file__).parent / ".env"
if not ENV_PATH.exists():
    print("❌ .env not found in project dir, copying from PaySignPrinter...")
    os.system("cp /home/ubuntu/coding/PaySignPrinter/.env " + str(ENV_PATH))
    print("✅ .env copied.")

load_dotenv(ENV_PATH)

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")

if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
    print("❌ Missing FEISHU_APP_ID or FEISHU_APP_SECRET in .env file")
    sys.exit(1)


def print_step(name):
    print(f"\n{'='*60}")
    print(f"▶ {name}")
    print('='*60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python demo_upload.py <path_to_file>")
        sys.exit(1)

    file_arg = sys.argv[1]
    file_path = Path(file_arg)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    file_name = file_path.name
    file_size = file_path.stat().st_size

    print(f"📄 File: {file_name}")
    print(f"📦 Size: {file_size} bytes")

    print_step("Step 1: Initialize FeishuClient")
    try:
        client = FeishuClient()
        print("✅ FeishuClient initialized")
    except Exception as e:
        print(f"❌ Failed to initialize FeishuClient: {e}")
        sys.exit(1)

    print_step("Step 2: Upload file to Feishu")
    try:
        file_code = client.upload_file_to_feishu(str(file_path))
        if not file_code:
            print("❌ Upload returned no file_code")
            sys.exit(1)
        print(f"✅ Upload succeeded")
        print(f"   file_code: {file_code}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

    print_step("Summary")
    print(f"   fileName: {file_name}")
    print(f"   fileSize: {file_size}")
    print(f"   file_code: {file_code}")
    print("\n✅ Demo completed.")


if __name__ == "__main__":
    main()
