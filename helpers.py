import os, re
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
from bs4 import BeautifulSoup


def lookup(word):
    """Look up the term on Wiktionary."""
    # Get the URL, then pass the main section of the article into a variable
    url = 'https://en.wiktionary.org/wiki/' + word.lower().strip().replace("'", "%27").replace(" ", "_")
    try:
        result = requests.get(url)
        article = BeautifulSoup(result.content, "lxml").find("div", {"class": "mw-parser-output"})
    except requests.RequestException:
        return None
    if article == None:
        return None
    # Look for the English section and get the definitions ONLY under this section
    # Avoid naming the list "list" to avoid confusion with the list attribute
    # Return none if no English entry was found
    ol = []
    found = 0
    for e in article:
        try:
            tag = e.name
        except AttributeError:
            tag = "None"
        if tag == "h2":
            if e.find("span", {"class": "mw-headline"}).get("id") == "English":
                found = 1
            # Stop looking if the h2 tag doesn't belong to the English section AND the English section has been found
            elif found == 1:
                break
        if tag == "ol" and found == 1:
            ol.append(e)
    if len(ol) == 0:
        return None
    elements = []
    for element in ol:
        # either ul, span, or dl elements
        # OR for s in element.find_all(re.compile(r'(ul|dl|sup)')):
        for arg, arg2 in [(["ul","dl"],""),("span", {"class":["defdate","qualifier-content", "maintenance-line"]}),("sup", {"class":"reference"})]:
            for s in element.findAll(arg,arg2):
                s.extract()
        elements = elements + element.find_all("li")
    definitions = []
    for element in elements:
        # Ensure element is not empty. Remove any nonsensical characters and handle newline characters so that definitions
        # will display correctly and nicely on browser.
        if re.search('[a-zA-Z]', element.text) != None:
            # Replace multiple newline characters with a single newline character
            el = re.sub(r'\n+', '\n', element.text)
            # Strip off () and any trailing and heading \n
            # \n that appears in the middle of the string indicates a sub-definition.
            # Convert them to the HTML <br> tag so that each sub-definition will be printed on a separate line in browser
            el = el.strip("\n").strip().replace("()", "").replace('\n', '<br>- ')
            definitions.append(el)
    # Filter out duplicates by converting the list to set, then back to list
    definitions = list(set(definitions))
    return definitions

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



