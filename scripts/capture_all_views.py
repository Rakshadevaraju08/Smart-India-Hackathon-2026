import subprocess
import os

browser_exe = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Inspector Tab
html_tab2 = html.replace("renderRoutes();", "renderRoutes(); switchTab('inspector');")
with open('frontend/preview_inspector.html', 'w', encoding='utf-8') as f:
    f.write(html_tab2)

cmd2 = [
    browser_exe,
    '--headless',
    '--disable-gpu',
    '--window-size=1920,1080',
    '--virtual-time-budget=3500',
    '--screenshot=' + os.path.abspath('dashboard_inspector_screenshot.png'),
    'file:///' + os.path.abspath('frontend/preview_inspector.html').replace('\\', '/')
]
subprocess.run(cmd2, timeout=20)
print('Inspector screenshot created:', os.path.exists('dashboard_inspector_screenshot.png'))

# 2. Clogging Tab
html_tab3 = html.replace("renderRoutes();", "renderRoutes(); switchTab('clogging');")
with open('frontend/preview_clogging.html', 'w', encoding='utf-8') as f:
    f.write(html_tab3)

cmd3 = [
    browser_exe,
    '--headless',
    '--disable-gpu',
    '--window-size=1920,1080',
    '--virtual-time-budget=3500',
    '--screenshot=' + os.path.abspath('dashboard_clogging_screenshot.png'),
    'file:///' + os.path.abspath('frontend/preview_clogging.html').replace('\\', '/')
]
subprocess.run(cmd3, timeout=20)
print('Clogging screenshot created:', os.path.exists('dashboard_clogging_screenshot.png'))

# Clean up temporary HTMLs
if os.path.exists('frontend/preview_inspector.html'):
    os.remove('frontend/preview_inspector.html')
if os.path.exists('frontend/preview_clogging.html'):
    os.remove('frontend/preview_clogging.html')
