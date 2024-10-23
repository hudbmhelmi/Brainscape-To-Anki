from aqt import mw
from aqt.qt import QAction, QInputDialog
from aqt.utils import showInfo
from anki.notes import Note
from bs4 import BeautifulSoup
import requests
import os
import re

def sanitize_filename(filename):
    """Remove invalid characters from filenames."""
    return re.sub(r'[^\w\-_\. ]', '_', filename)

def fetch_and_create_deck():
    # Prompt user for the URL
    url, ok = QInputDialog.getText(mw, "Brainscape to Anki", "Please enter the URL to the Brainscape flashcards:")

    if not ok or not url:
        showInfo("No URL provided. Operation canceled.")
        return

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    }
    
    
    # Fetch the flashcard data from the URL
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise error for bad HTTP responses
    except requests.RequestException as e:
        showInfo(f"Failed to fetch the flashcards: {e}")
        return
    soup = BeautifulSoup(response.content, "html.parser")
    flashcard_elements = soup.find_all("div", class_="scf-face")

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
