'''Collection of local functions that may be imported when defining agents, for inclusion in their 'tools' list.
'''

from strands.tools import tool

@tool
def simple_greeting(name: str = "World") -> str:
    '''Return a simple greeting "Hello, {name}!" with default name="World".
    '''
    return (f"Hello, {name}!")

@tool
def letter_counter(letter, text):
    """Count the number of times a letter appears in a text."""
    return text.lower().count(letter.lower())
