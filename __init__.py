from aqt import mw
from aqt.qt import QAction, QInputDialog
from aqt.utils import showInfo
from anki.notes import Note
from bs4 import BeautifulSoup
import requests
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

def sanitize_filename(filename):
    """Remove invalid characters from filenames."""
    return re.sub(r'[^\w\-_\. ]', '_', filename)

def fetch_and_create_deck():
    # Prompt user for the URL
    url, ok = QInputDialog.getText(mw, "Brainscape to Anki", "Please enter the URL to the Brainscape flashcards:")

    if not ok or not url:
        showInfo("No URL provided. Operation canceled.")
        return

    # Use Selenium to handle lazy loading
    try:
        # Set up headless browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for initial page load
        time.sleep(3)
        
        # Scroll down repeatedly to trigger lazy loading
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait to load page
            time.sleep(2)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Get the page source after all content is loaded
        page_source = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(page_source, "html.parser")
    except WebDriverException as e:
        showInfo(f"Failed to initialize Chrome driver. Make sure Chrome is installed: {e}")
        
        # Fallback to regular requests as before
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            showInfo(f"Failed to fetch the flashcards: {e}")
            return
        
        soup = BeautifulSoup(response.content, "html.parser")
    
    flashcard_elements = soup.find_all("div", class_="scf-face")
    
    if not flashcard_elements:
        showInfo("No flashcards found on the page. Try scrolling through the Brainscape page first to load all cards.")
        return

    card_text = []
    card_answer = []
    n = 0

    for flashcard in flashcard_elements:
        # Extract the raw HTML content of the flashcard
        raw_html = flashcard.decode_contents()
        try:
            temp = BeautifulSoup(flashcard.decode_contents(), "html.parser")
        except Exception as e:
            showInfo(f"Error parsing HTML content: {e}")
            return
        # Handle images
        for img in temp.find_all("img"):
            img_url = img["src"]
            img_name = sanitize_filename(os.path.basename(img_url))
            img_path = os.path.join(mw.col.media.dir(), img_name)

            try:
                img_data = requests.get(img_url).content
                with open(img_path, "wb") as f:
                    f.write(img_data)
                img['src'] = img_name  # Update the image tag to refer to the local file
            except Exception as e:
                showInfo(f"Failed to download or save image: {e}")
                img.decompose()  # Remove the img tag if download failed

        # Replace <br> tags with newline characters
        processed_text = str(temp).replace("<br>", "\n")

        # Add the processed flashcard text to the appropriate list
        if n % 2 == 0:
            card_text.append(processed_text)
        else:
            card_answer.append(processed_text)
        n += 1

    # Prompt user for the new deck name
    new_deck, ok = QInputDialog.getText(mw, "Brainscape to Anki", "What would you like to call this new deck?")

    if not ok or not new_deck:
        showInfo("No deck name provided. Operation canceled.")
        return

    # Create the new deck
    deck_id = mw.col.decks.id(new_deck)
    showInfo(f"Created {new_deck}")

    # Add cards to the new deck
    model = mw.col.models.byName("Basic")
    if not model:
        showInfo("Model 'Basic' not found. Operation canceled. Tip: To potentially fix this error, you may try going to 'Tools' (top bar) -> 'Manage Note Types' -> 'Basic' -> 'Add'")
        return

    for i in range(len(card_text)):
        note = Note(mw.col, model)
        note["Front"] = card_text[i]
        note["Back"] = card_answer[i]
        mw.col.add_note(note, deck_id)

    mw.col.reset()
    mw.reset()
    showInfo(f"The end, check your Anki now for the deck called {new_deck}. Thank you, made by Dario G :]")

# Create a new menu item in Anki
action = QAction("Brainscape to Anki", mw)
action.triggered.connect(fetch_and_create_deck)
mw.form.menuTools.addAction(action)
