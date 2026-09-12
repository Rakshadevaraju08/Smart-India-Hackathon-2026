import subprocess
import os
import time

browser_exe = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
base_dir = r'c:\Users\Gagan K S\Documents\SIH'

with open(os.path.join(base_dir, 'frontend', 'index.html'), 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Main Dashboard Screenshot (Tab 1: Navigation & Layers)
preview1_path = os.path.join(base_dir, 'frontend', 'preview_main.html')
# Ensure map and data load, and center on routing
html_tab1 = html
with open(preview1_path, 'w', encoding='utf-8') as f:
    f.write(html_tab1)

cmd1 = [
    browser_exe,
    '--headless',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1920,1080',
    '--virtual-time-budget=4000',
    '--screenshot=' + os.path.join(base_dir, 'dashboard_screenshot.png'),
    'file:///' + preview1_path.replace('\\', '/')
]
print("Capturing dashboard_screenshot.png...")
subprocess.run(cmd1, timeout=30)

# 2. Inspector Tab Screenshot (Tab 2: Inspector with selected asset)
preview2_path = os.path.join(base_dir, 'frontend', 'preview_inspector.html')
html_tab2 = html.replace("renderRoutes();", "renderRoutes(); switchTab('inspector'); if (state.data && state.data.segments.length > 0) selectAsset(state.data.segments[12]);")
with open(preview2_path, 'w', encoding='utf-8') as f:
    f.write(html_tab2)

cmd2 = [
    browser_exe,
    '--headless',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1920,1080',
    '--virtual-time-budget=4000',
    '--screenshot=' + os.path.join(base_dir, 'dashboard_inspector_screenshot.png'),
    'file:///' + preview2_path.replace('\\', '/')
]
print("Capturing dashboard_inspector_screenshot.png...")
subprocess.run(cmd2, timeout=30)

# 3. Clogging Tab Screenshot (Tab 3: Clogging Simulator with slider at 65%)
preview3_path = os.path.join(base_dir, 'frontend', 'preview_clogging.html')
html_tab3 = html.replace("renderRoutes();", "renderRoutes(); switchTab('clogging'); document.getElementById('clog-slider').value = 65; updateClogging(65);")
with open(preview3_path, 'w', encoding='utf-8') as f:
    f.write(html_tab3)

cmd3 = [
    browser_exe,
    '--headless',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1920,1080',
    '--virtual-time-budget=4000',
    '--screenshot=' + os.path.join(base_dir, 'dashboard_clogging_screenshot.png'),
    'file:///' + preview3_path.replace('\\', '/')
]
print("Capturing dashboard_clogging_screenshot.png...")
subprocess.run(cmd3, timeout=30)

# Clean up
for p in [preview1_path, preview2_path, preview3_path]:
    if os.path.exists(p):
        os.remove(p)

print("All 3 screenshots updated successfully!")
for name in ['dashboard_screenshot.png', 'dashboard_inspector_screenshot.png', 'dashboard_clogging_screenshot.png']:
    p = os.path.join(base_dir, name)
    print(f"  {name}: {os.path.getsize(p)} bytes")
