import re
import html


def convertHtmlEntitiesToCharacters(inputString):
    # Check if the string contains any HTML entities
    if "&" in inputString:
        # Convert HTML entities to characters
        return html.unescape(inputString)
    else:
        # No HTML entities found, return the original string
        return inputString
