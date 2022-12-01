# Flashcard!
#### Video Demo:
https://youtu.be/yTSyDbN-j4E

#### Description:
A simple flashcard web application built on Flask using Python, SQL, HTML, CSS, and Bootstrap.
User can automatically generate e-flashcards from dictionary lookups (the current version only supports English-English flashcards).

#### Features:
- Add, remove, or edit a flashcard set
- Create a flashcard manually or automatically from dictionary lookup (English words and phrases only)
- Review flashcards with the option to shuffle the cards.

#### What's Included in the Directory:
The directory includes two folders and three files.
The `static` and `templates` folders contain the CSS stylesheet and the HTML templates used for this project, respectively.
The first file `application.py` stores the main function of this application. The second file `helpers.py` contains the helpers functions to be used for validating user's lookup request, prompting user to log into the application, and rendering error messages. The last file `vocab.db` is a SQLite database used for storing user's data.

#### Usage:
Here is an overview of how the application works:
1. User will need to log into their account before they can access the rest of the application. They must create an account if they do not have one.
2. Onced logged in, user will be redirected to the homepage which shows all of their active flashcard sets (if any). User can review, edit, or remove any sets. The navigation bar at the top of the app shows four options, `New Set` and `New Flashcard` on the left side, and `Change Password` and `Log Out` on the right side.
3. User must have at least one flashcard set before they can create a flashcard with `New Flashcard`.
4. User can create their flashcards in two ways: entering the definition(s) manually or having the application parse the definition(s) from Wiktionary (the term must be English).
5. If the user's input is invalid, the application will render an error message explaining why the input was rejected.

#### What's Stored in the SQL Database:
The `vocab.db` database consists of four tables for storing users, their flashcard sets and the content of each set. Each entry of each table is assigned a unique index (ID), which gives the application the ability to access any flashcard set and flashcard upon user's request.
1. The `users` table stores the registered users of the application. Each entry includes the user's display name, username, password hash, and ID.
2. The `folders` table stores the flashcard sets owned by each user. Each entry includes the owner's ID, the ID and title of the set, and the number of flashcards inside the set (the default value is 0).
3. The `words` table stores the front side of a flashcard i.e the term. Each entry includes the owner's ID, the ID of the set containing the card, and the front side of the card.
4. The `definitions` table stores the back side of a flashcard i.e the definition(s) of the term. Each entry includes the owner's ID, the ID of the set containing the card, the ID of the card, and the back of the card. If there are more than one definition, then each definition will be assigned a unique index.

The structure of this database allows a user to own multiple sets, each of which can contain multiple flashcards, and to include as many definitions in a flashcard as they want.

#### How This Application Uses BeautifulSoup4 to Generate Flashcards Automatically:
BeautifulSoup4 (BS4) is a Python library for scraping data from a HTML or XML file. The application can utilize this libary to look up any English term on Wiktionary and extract from the source a list of definitions that can be added to the flashcard. I chose Wiktionary due to its simple HTML structure compared to other online dictionary websites, allowing the application to parse the definitions with ease.
The application will send a GET request to Wiktionary with `requests.get(url)`, where url is the link to the Wiktionary definition of the term. The HTML elements containing the English definitions will be obtained with `find_all`. The text of the elements will be extracted, reformatted, and appended to an array to be returned to the user.
