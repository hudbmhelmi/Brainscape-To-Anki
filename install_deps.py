import subprocess
import sys
import os
from aqt.utils import showInfo, showWarning

def install_dependencies():
    """Install required Python packages if they're missing."""
    missing_packages = []
    
    # Check if selenium is installed
    try:
        import selenium
    except ImportError:
        missing_packages.append("selenium>=4.10.0")
    
    # Check if beautifulsoup4 is installed
    try:
        import bs4
    except ImportError:
        missing_packages.append("beautifulsoup4>=4.9.0")
    
    # Check if requests is installed (usually comes with Anki, but check anyway)
    try:
        import requests
    except ImportError:
        missing_packages.append("requests>=2.25.0")
    
    # Install missing packages
    if missing_packages:
        showInfo("Brainscape to Anki: Installing required dependencies. This may take a moment...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user"] + missing_packages)
            showInfo("Dependencies installed successfully. Please restart Anki.")
        except Exception as e:
            showWarning(f"Failed to install dependencies: {e}\n\nPlease install manually: pip install selenium beautifulsoup4 requests")
    
    # Check for Chrome/Chromium
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.quit()
    except Exception:
        showWarning("Chrome/Chromium browser not detected. The lazy loading feature requires Chrome to be installed.")

# Run the dependency check
install_dependencies() 