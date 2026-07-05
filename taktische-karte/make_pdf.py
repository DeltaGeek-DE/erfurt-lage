import subprocess, sys, os

# Install playwright if needed
subprocess.run([sys.executable, '-m', 'pip', 'install', 'playwright'], capture_output=True)
subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], capture_output=True)

from playwright.sync_api import sync_playwright

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'handbuch.html')
pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'handbuch.pdf')

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f'file:///{html_path.replace(chr(92), "/")}')
    page.pdf(path=pdf_path, format='A4', print_background=True)
    browser.close()

size_kb = os.path.getsize(pdf_path) / 1024
print(f'PDF erstellt: handbuch.pdf ({size_kb:.0f} KB)')
