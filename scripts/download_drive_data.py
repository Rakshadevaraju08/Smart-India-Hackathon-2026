"""
Automated Google Drive Dataset Downloader for SIH 2026 Urban Flood Nowcasting System.
Allows teammates, evaluators, and automated CI/CD runners to pull heavy raw datasets
directly from the team's Google Drive vault into the local Datasets/ directory.
"""

import os
import sys

# Paste your shared Google Drive Folder or File ID here once uploaded:
# (e.g., https://drive.google.com/drive/folders/<DRIVE_FOLDER_ID>?usp=sharing)
GOOGLE_DRIVE_FOLDER_ID = "PASTE_YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE"

def check_gdown():
    try:
        import gdown
        return gdown
    except ImportError:
        print("[!] 'gdown' package is required to download files from Google Drive.")
        print("    Installing gdown via pip...")
        os.system(f"{sys.executable} -m pip install gdown")
        import gdown
        return gdown

def download_datasets(drive_id=GOOGLE_DRIVE_FOLDER_ID, output_dir="Datasets"):
    if drive_id == "PASTE_YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE":
        print("[!] Please update 'GOOGLE_DRIVE_FOLDER_ID' in this script with your shared Google Drive link.")
        print("    Instructions:")
        print("    1. Upload Google_Drive_Datasets folder to Google Drive.")
        print("    2. Right-click folder -> Share -> 'Anyone with the link can view'.")
        print("    3. Copy the link ID and paste it into this script.")
        return

    gdown = check_gdown()
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Downloading team raw datasets from Google Drive into '{output_dir}'...")
    url = f"https://drive.google.com/drive/folders/{drive_id}"
    gdown.download_folder(url, output=output_dir, quiet=False, use_cookies=False)
    print("[+] Download complete! All heavy datasets are now ready locally.")

if __name__ == "__main__":
    download_datasets()
