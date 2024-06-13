from aqt import mw
from aqt.qt import QAction, QInputDialog, QMessageBox
from aqt.utils import showInfo
from anki.notes import Note
from anki.decks import DeckManager
from anki.models import ModelManager
from bs4 import BeautifulSoup
import requests

def fetch_and_create_deck():
    # Prompt user for the URL
    url, ok = QInputDialog.getText(mw, "Brainscape to Anki", "Please enter the URL to the Brainscape flashcards:")

    if not ok or not url:
        showInfo("No URL provided. Operation canceled.")
        return

    # Fetch the flashcard data from the URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    flashcard_text = soup.find_all("div", class_="scf-face")

    card_text = []
    card_answer = []
    n = 0

    for flashcard in flashcard_text:
        temp = flashcard.text
        if n % 2 == 0:
            card_text.append(temp)
        else:
            card_answer.append(temp)
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
