import requests
import json
import os
import sys

# import tiktoken

# Path to the item cache file
item_cache_file_path = "wikidata_item_cache.json"
# Path to the label cache file
label_cache_file_path = "wikidata_label_cache.json"

# Path to text_representations directory
text_representations_dir="./text_representations"

def load_item_cache():
    if os.path.exists(item_cache_file_path):
        with open(item_cache_file_path, "r") as cache_file:
            return json.load(cache_file)
    else:
        return {}

def load_label_cache():
    if os.path.exists(label_cache_file_path):
        with open(label_cache_file_path, "r") as cache_file:
            return json.load(cache_file)
    else:
        return {}
# Load item cache from file if it exists
item_cache = load_item_cache()
label_cache = load_label_cache()


# Replacements for property labels
def replace_prop_label(label) -> str:
    property_label_replacements = {
        "instance of": "is a",
        "postal code": "has postal code",
        "local dialing code": "has local dailing code",
        "licence plate code": "has license plate code",
        "enclave within": "is an enclave within",
        "located in time zone": "is located in time zone",
        "highest point": "has an highest point:",
        "continent": "part of continent",
        "hashtag": "has hashtag",
        "award received": "has received award",
        "located in or next to body of water": "is next to river or lake or sea",
    }
    l = property_label_replacements.get(label)
    if l is not None:
        return l
    return label


def prop_skip(label):
    skip = {
        "topic's main category": True,
        "topic's main wikimedia portal": True,
        "flag": True,
        "permanent duplicated item": True,
        "history of topic": True,
        "geography of topic": True,
        "related category": True,
        "demographics of topic": True,
        "economy of topic": True,
        "different from": True,
        "on focus list of wikimedia project": True,
        "open data portal": True,
        "commons category": True,
        "ipa transcription": True,
    }

    return skip.get(label)


# Save label cache to file
def save_label_cache():
    with open(label_cache_file_path, "w") as cache_file:
        json.dump(label_cache, cache_file, indent=2)
    load_label_cache()


# Save item cache to file
def save_item_cache():
    with open(item_cache_file_path, "w") as cache_file:
        json.dump(item_cache, cache_file, indent=2)
    load_item_cache()


# Modified fetch_labels_by_ids function with caching
def fetch_labels_by_ids(ids):
    # Check the cache first
    uncached_ids = [id_ for id_ in ids if id_ not in label_cache]
    labels_to_fetch = "|".join(uncached_ids)

    if labels_to_fetch:
        print(f"Fetching labels for {uncached_ids}", file=sys.stderr)
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={labels_to_fetch}&format=json&props=labels"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for entity_id, content in data["entities"].items():
            entity_label = content["labels"].get("en", {}).get("value", entity_id)
            label_cache[entity_id] = entity_label
        # Save updated label cache to disk
        save_label_cache()

    # Now build the result using the label cache
    labels = {id_: label_cache.get(id_, id_) for id_ in ids}
    return labels


# Function to format time values
def format_time(time_value):
    if time_value:
        # The time string usually is in the format '+YYYY-MM-DDTHH:MM:SSZ'
        # We can split by '-' to get the year and ignore the rest
        date_part = time_value.split("-")[0]
        # Remove the '+' sign at the beginning
        date_formatted = date_part.lstrip("+")
        return date_formatted
    return "unknown date"


def format_quantity(value):
    amount = value.get("amount", "Unknown quantity").lstrip(
        "+"
    )  # Remove '+' prefix if it exists
    # Check if the 'unit' key exists and if it's not the 'no unit' URL
    if "unit" in value and value["unit"] not in [
        "http://www.wikidata.org/entity/Q199",
        "1",
    ]:
        unit_id = value["unit"].split("/")[-1]  # Extract the unit ID from the URL
        labels = fetch_labels_by_ids([unit_id])
        unit_label = labels.get(unit_id, unit_id)
        return f"{amount} {unit_label}"
    return amount


# Function to get qualifiers for time span
def get_time_span(qualifiers):
    time_span = ""
    start_time_qualifier = (
        qualifiers.get("P580", [{}])[0]
        .get("datavalue", {})
        .get("value", {})
        .get("time")
    )
    end_time_qualifier = (
        qualifiers.get("P582", [{}])[0]
        .get("datavalue", {})
        .get("value", {})
        .get("time")
    )
    point_in_time_qualifier = (
        qualifiers.get("P585", [{}])[0]
        .get("datavalue", {})
        .get("value", {})
        .get("time")
    )

    if start_time_qualifier and not(end_time_qualifier):
        start_time = format_time(start_time_qualifier)
        time_span += f"since {start_time} until today"
    elif start_time_qualifier:
        start_time = format_time(start_time_qualifier)
        time_span += f"from {start_time} "

    if end_time_qualifier:
        end_time = format_time(end_time_qualifier)
        time_span += f"to {end_time}"
    if point_in_time_qualifier and not (start_time_qualifier or end_time_qualifier):
        point_in_time = format_time(point_in_time_qualifier)
        time_span += f"in {point_in_time}"

    return time_span.strip()

def create_statement_group_representation(item_label, prop_label, statement_group):
    statement_group_text = ""
    # Iterate over all statements in group
    for statement in statement_group:
        mainsnak = statement.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value")
        datatype = mainsnak.get("datatype")
        qualifiers = statement.get("qualifiers", {})
        time_span = get_time_span(qualifiers)
        time_span_text = f" {time_span}" if time_span else ""

        if datatype == "wikibase-item" and value and value.get("entity-type") == "item":
            value_id = value.get("id")
            # Fetch labels value
            labels = fetch_labels_by_ids([value_id])
            value_label = labels.get(value_id, value_id)
            if(value_label):
                statement_group_text += f"{item_label} {prop_label} {value_label}{time_span_text}.\n"

        elif datatype == "time" and value:
            if len(statement_group_text) == 0:
                statement_group_text = item_label + " " + prop_label
            else:
                statement_group_text += ","

            # Format the time value
            time_value = format_time(value.get("time"))
            statement_group_text += f" {time_value}{time_span_text}"

        elif datatype == "string":
            if len(statement_group_text) == 0:
                statement_group_text = item_label + " " + prop_label
            else:
                statement_group_text += ","

            # Directly use the string value
            string_value = value if isinstance(value, str) else "Unknown"
            statement_group_text += f" {string_value}{time_span_text}"

        elif datatype == "quantity":
            if len(statement_group_text) == 0:
                statement_group_text = item_label + " " + prop_label
            else:
                statement_group_text += ","

            # Format the quantity value
            quantity_value = format_quantity(value)
            statement_group_text += f" {quantity_value}{time_span_text}"

    if statement_group_text and len(statement_group_text) != 0:
        return statement_group_text + "\n"
    else:
        return


def create_statements_representation(item_label, statements):
    statements_representation = ""
    # Iterate over all statement groups
    for prop_id, statement_group in statements.items():
        prop_text: str = ""

        labels = fetch_labels_by_ids([prop_id])
        prop_label = labels.get(prop_id, prop_id)

        if prop_label.lower().startswith("category"):
            continue
        if prop_skip(prop_label.lower()):
            continue

        prop_label = replace_prop_label(prop_label.lower())

        statement_group_text = create_statement_group_representation(item_label, prop_label, statement_group)

        if( statement_group_text ):
            statements_representation += statement_group_text

    return statements_representation


# Function to get the label, description, and statements of a Wikidata item
def wikidata_item_to_text(item_id):
    # Check if the item is already in the cache
    if item_id in item_cache:
        print(f"Retrieving cached data for item: {item_id}", file=sys.stderr)
        item_data = item_cache[item_id]
    else:
        print(f"Fetching data for item: {item_id}", file=sys.stderr)
        # Build the URL for the JSON version of the item
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{item_id}.json"

        # Make the HTTP request to the Wikidata API
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code

        # Parse the JSON response
        data = response.json()

        # Navigate through the JSON to find the desired data
        entities = data.get("entities", {})
        item_data = entities.get(item_id, {})

        # Cache the fetched data
        item_cache[item_id] = item_data
        save_item_cache()

    # Get the Item's label and description in English
    item_label = item_data.get("labels", {}).get("en", {}).get("value", "No item label found")
    description = (
        item_data.get("descriptions", {})
        .get("en", {})
        .get("value", "No description found")
    )
    text_representation = f"{item_label}: {description}\n"

    text_representation += create_statements_representation(item_label, item_data.get("claims", {}))

    # Return the concatenated string of labels and descriptions
    return text_representation


capitals = ["Q64","Q84","Q90", "Q1085"]

for c in capitals:
    text_representation = wikidata_item_to_text(c)
    # Write to a file named after the Wikidata ID
    with open(f"{text_representations_dir}/{c}.txt", "w") as file:
        file.write(text_representation)


# Example usage:
# text_representation = wikidata_item_to_text("Q64")  # Q64 is the item for Berlin
# print("\n\n")
# print(text_representation)


# enc = tiktoken.encoding_for_model("gpt-4")
# encoded = enc.encode(text_representation)
#
# print("\n\n")
# print(f"{len(encoded)} tokens")
