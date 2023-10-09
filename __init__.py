from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from cgitb import lookup
from pathlib import Path
import zipfile
import json
import os
import sys

SCRIPT_DIR = Path(__file__).parent
dictionary_map = {}
dictionarReading_map = {}


def load_dictionary(dictionary):
    output_map = {}
    archive = zipfile.ZipFile(dictionary, "r")

    result = list()
    for file in archive.namelist():
        if file.startswith("term"):
            with archive.open(file) as f:
                data = f.read()
                d = json.loads(data.decode("utf-8"))
                result.extend(d)

    for entry in result:
        if entry[0] in output_map:
            output_map[entry[0]].append(entry)
        else:
            output_map[entry[0]] = [
                entry
            ]  # Using headword as key for finding the dictionary entry
    return output_map


def load_dictionaryReadings(dictionary):
    output_mapReadings = {}
    archive = zipfile.ZipFile(dictionary, "r")

    result = list()
    for file in archive.namelist():
        if file.startswith("term"):
            with archive.open(file) as f:
                data = f.read()
                d = json.loads(data.decode("utf-8"))
                result.extend(d)

    for entry in result:
        if entry[1] in output_mapReadings:
            output_mapReadings[entry[1]].append(entry)
        else:
            output_mapReadings[entry[1]] = [
                entry
            ]  # Using headword as key for finding the dictionary entry
    return output_mapReadings


def setup():
    global dictionary_map
    global dictionarReading_map
    dictionary_map = load_dictionary(
        str(Path(SCRIPT_DIR, "dictionaries", "jmdict_english.zip"))
    )
    dictionarReading_map = load_dictionaryReadings(
        str(Path(SCRIPT_DIR, "dictionaries", "jmdict_english.zip"))
    )


setup()
config = mw.addonManager.getConfig(__name__)

max_number = config["max number of definitions"]
source_field = config["source field"]
destination_field = config["destination field"]
search = config["search"]

def addDefinitionToCardsWrapper():
    addDefinitionToCards(source_field, destination_field, search, max_number)


def addDefinitionToCards(source_field, destination_field, search, max_number):
    cards = mw.col.findCards(f"{search}")
    showInfo("Card count: %d" % len(cards))

    for id in cards:
        card = mw.col.getCard(id)
        note = card.note()
        source_text = note[source_field]
        result_def = look_up(source_text, max_number)
        if result_def == None:
            result_def = ""
        note[destination_field] = result_def
        note.flush()


def look_up(word, nb_definitions):
    dictionary_option = dictionary_map
    word = word.strip()
    if word not in dictionary_map:
        dictionary_option = dictionarReading_map
        if word not in dictionarReading_map:
            return None
    result = [
        {
            "headword": entry[0],
            "reading": entry[1],
            "tags": entry[2],
            "glossary_list": wrapperComplexContentToHtml(entry[5]),
            "sequence": entry[6],
        }
        for entry in dictionary_option[word]
    ]
    definitions = ""
    for definition in result[:nb_definitions]:
        definitionTemplate = "<li><br>"
        definitionTemplate += f"{definition['reading']} 【{definition['headword']}】<br>"
        definitionTemplate += f"{definition['tags']}<br>"
        if definition["glossary_list"]:
            if type(definition["glossary_list"]) is list:
                if type(definition["glossary_list"][0]) is list:
                    definitions += (
                        definitionTemplate
                        + definition["glossary_list"][0][0]
                        + "</li><br>"
                    )
                else:
                    for item in definition["glossary_list"]:
                        if type(item) is str:
                            definitions += definitionTemplate + item + "</li><br>"
            else:
                definitions += (
                    definitionTemplate + definition["glossary_list"] + "</li><br>"
                )
    return definitions


def insertTags(tag, list):
    list.insert(0, f"<{tag}>")
    list.append(f"</{tag}>")

def contentToHtml(contentElement):
    content = contentElement.get("content")
    htmlOutput = []
    if content:
        htmlOutput.append(content)
    return htmlOutput


def complexContentToHtml(dictList):
    htmlOutput = []
    for contentItem in dictList:
        if "content" in contentItem and "data" in contentItem:
            if contentItem["data"]["content"] == "glossary":
                if type(contentItem["content"]) is list:
                    for li in contentItem["content"]:
                        li = contentToHtml(li)
                        htmlOutput.append(li)

                elif type(contentItem["content"]) is dict:
                    li = contentItem["content"]
                    li = contentToHtml(li)
                    htmlOutput.append(li)
    return htmlOutput


def wrapperComplexContentToHtml(textOrDict):
    if type(textOrDict) is list:
        return wrapperComplexContentToHtml(textOrDict[0])
    if type(textOrDict) is dict:
        return complexContentToHtml(textOrDict["content"])
    return textOrDict


tagsReplacements = {"n": "Common Noun"}


def abreviationsToFullText(tags):
    tags = tags.split(" ")
    for index, tag in enumerate(tags):
        print(tag)
        tagReplacement = tagsReplacements.get(tag)
        if tagReplacement:
            tags[index] = tagReplacement

    return "".join(tags)

action = QAction(f"Add definition to {destination_field}", mw)
mw.form.menuTools.addAction(action)
action.triggered.connect(addDefinitionToCardsWrapper)

listest = "まあ 両方 似る 集まる 奇遇 キャラクター まかせる 頷く"
for word in listest.split(" "):
    print(f"Looking up: {word}")
    print(look_up(word, 10))
