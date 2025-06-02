import json

"""
JSON configuration settings.
"""

with open("settings.json", "r") as file:
    config = json.load(file)
