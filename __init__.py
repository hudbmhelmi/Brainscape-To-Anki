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

    # Fetch the flashcard data from the URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    flashcard_elements = soup.find_all("div", class_="scf-face")

    card_text = []
    card_answer = []
    n = 0

    for flashcard in flashcard_elements:
        # Extract the raw HTML content of the flashcard
        raw_html = flashcard.decode_contents()

        # Process the HTML content
        temp = BeautifulSoup(raw_html, "html.parser")

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
        showInfo("Model 'Basic' not found. Operation canceled.")
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
