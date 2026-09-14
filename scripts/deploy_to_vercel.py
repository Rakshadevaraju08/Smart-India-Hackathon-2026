import hashlib
import os
import requests
import json

def get_token():
    if os.environ.get("VERCEL_TOKEN"):
        return os.environ.get("VERCEL_TOKEN").strip()
    
    # Check standard Vercel CLI config paths
    candidate_paths = [
        os.path.join(os.environ.get("APPDATA", ""), "xdg.data", "com.vercel.cli", "auth.json"),
        os.path.join(os.path.expanduser("~"), ".vercel", "auth.json"),
        os.path.join(os.path.expanduser("~"), ".local", "share", "com.vercel.cli", "auth.json"),
        os.path.join(os.path.dirname(__file__), "..", ".vercel", "auth.json")
    ]
    
    for auth_file in candidate_paths:
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    tok = data.get("token")
                    if tok:
                        return tok.strip()
            except Exception:
                continue
                
    # Fallback to cached CLI token if present
    raise ValueError("Vercel authorization token not configured. Please ensure Vercel CLI is logged in.")

TOKEN = get_token()
TEAM_ID = os.environ.get("VERCEL_TEAM_ID", "team_5GKT1NXvvvLB309swbfNPdkq")
PROJECT_NAME = "kairos-command-twin"

headers_auth = {
    "Authorization": f"Bearer {TOKEN}"
}

files_to_deploy = [
    ("index.html", "frontend/index.html"),
    ("data/chennai_flood_data.js", "frontend/data/chennai_flood_data.js")
]

file_metadata = []

for vpath, fpath in files_to_deploy:
    with open(fpath, "rb") as f:
        content = f.read()
    sha = hashlib.sha1(content).hexdigest()
    size = len(content)
    file_metadata.append({
        "file": vpath,
        "sha": sha,
        "size": size
    })
    
    upload_url = f"https://api.vercel.com/v2/files?teamId={TEAM_ID}"
    upload_headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Length": str(size),
        "x-vercel-digest": sha
    }
    r = requests.post(upload_url, headers=upload_headers, data=content)
    print(f"Uploaded {vpath} (status {r.status_code})")

deploy_url = f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}"
deploy_payload = {
    "name": PROJECT_NAME,
    "target": "production",
    "files": file_metadata,
    "projectSettings": {
        "framework": None
    }
}

r_deploy = requests.post(deploy_url, headers={**headers_auth, "Content-Type": "application/json"}, json=deploy_payload)
res_json = r_deploy.json()
print("Deployment response:", r_deploy.status_code)
print("Deployment ID:", res_json.get("id"))
print("Production URL: https://kairos-command-twin.vercel.app")
