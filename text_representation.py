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
text_representations_dir = "./text_representations"


def make_http_request(url):
    """
    Make an HTTP GET request to the specified URL and return the JSON response.

    Args:
        url (str): The URL to which the request will be sent.

    Returns:
        dict: The JSON response from the request.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


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
        "capital of": "is capital of",
        "located in the administrative territorial entity": "is located in the administrative territorial entity",
    }
    l = property_label_replacements.get(label)
    if l is not None:
        return l
    return label


def prop_skip(label):
    """
    Determine if a property label should be skipped.

    Args:
        label (str): The label of the property.

    Returns:
        bool: True if the label should be skipped, False otherwise.
    """
    skip = [
        "topic's main category",
        "topic's main wikimedia portal",
        "flag",
        "permanent duplicated item",
        "history of topic",
        "geography of topic",
        "related category",
        "demographics of topic",
        "economy of topic",
        "different from",
        "on focus list of wikimedia project",
        "open data portal",
        "commons category",
        "ipa transcription",
    ]

    return label in skip


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
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={labels_to_fetch}&format=json&props=labels"
        data = make_http_request(url)

        for entity_id, content in data["entities"].items():
            entity_label = content["labels"].get("en", {}).get("value", entity_id)
            label_cache[entity_id] = entity_label
        # Save updated label cache to disk
        save_label_cache()

    # Now build the result using the label cache
    labels = {id_: label_cache.get(id_, id_) for id_ in ids}
    return labels


def format_date(date_value):
    """
    Format a Wikidata date value to a common date format or as text if incomplete.

    Args:
        date_value (str): The date value from Wikidata in the format '+YYYY-MM-DDTHH:MM:SSZ'.

    Returns:
        str: The formatted date in ISO 8601 format (YYYY, YYYY-MM, or YYYY-MM-DD), 
             or 'unknown date' if input is None or cannot be parsed.
    """
    if date_value:
        # Remove the '+' sign and time component from the date string
        date_str = date_value.lstrip('+').split('T')[0]
        # Split the date into components, expecting at most 3 parts (year, month, day)
        date_parts = date_str.split('-', 2)

        # Check the number of parts and format accordingly
        if len(date_parts) == 3:
            year, month, day = date_parts
            if int(month) > 12 or int(day) > 31:  # Check for invalid month or day
                return 'unknown date'
            if month == '00' and day == '00':
                return year  # Year only
            elif month != '00' and day == '00':
                return f"{year}-{month}"  # Year and month
            else:
                return f"{year}-{month}-{day}"  # Full date
        elif len(date_parts) == 2:
            year, month = date_parts
            if int(month) > 12:  # Check for invalid month or day
                return 'unknown date'
            if month == '00':
                return year  # Year only
            else:
                return f"{year}-{month}"  # Year and month
        elif len(date_parts) == 1:
            return date_parts[0]  # Year only
    return 'unknown date'


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

    if start_time_qualifier and not (end_time_qualifier):
        start_time = format_date(start_time_qualifier)
        time_span += f"since {start_time} until today"
    elif start_time_qualifier:
        start_time = format_date(start_time_qualifier)
        time_span += f"from {start_time} "

    if end_time_qualifier:
        end_time = format_date(end_time_qualifier)
        time_span += f"to {end_time}"
    if point_in_time_qualifier and not (start_time_qualifier or end_time_qualifier):
        point_in_time = format_date(point_in_time_qualifier)
        time_span += f"in {point_in_time}"

    return time_span.strip()


def create_statement_group_representation(item_label, prop_label, statement_group):
    """
    Create a text representation of a statement group for an item, ensuring each non-empty group ends with a newline.

    Args:
        item_label (str): The label of the item.
        prop_label (str): The label of the property.
        statement_group (list): The list of statements for the property.

    Returns:
        str: The text representation of the statement group, ending with a newline if not empty.
    """
    statement_group_text = []
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
            if value_label:
                statement_group_text.append(
                    f"{item_label} {prop_label} {value_label}{time_span_text}."
                )

        elif datatype == "time" and value:
            time_value = format_date(value.get("time"))
            statement_group_text.append(
                f"{item_label} {prop_label} on {time_value}{time_span_text}."
            )

        elif datatype == "string":
            string_value = value if isinstance(value, str) else "Unknown"
            statement_group_text.append(
                f"{item_label} {prop_label} {string_value}{time_span_text}."
            )

        elif datatype == "quantity":
            quantity_value = format_quantity(value)
            statement_group_text.append(
                f"{item_label} {prop_label} {quantity_value}{time_span_text}."
            )

    # Ensure each non-empty statement group ends with a newline
    return "\n".join(statement_group_text) + "\n" if statement_group_text else ""


def create_statements_representation(item_label, statements):
    """
    Create a text representation of all statement groups for an item.

    Args:
        item_label (str): The label of the item.
        statements (dict): The dictionary of all statement groups.

    Returns:
        str: The text representation of all statement groups.
    """
    statements_representation = []
    # Iterate over all statement groups
    for prop_id, statement_group in statements.items():
        labels = fetch_labels_by_ids([prop_id])
        prop_label = labels.get(prop_id, prop_id)

        if prop_label.lower().startswith("category") or prop_skip(prop_label.lower()):
            continue

        prop_label = replace_prop_label(prop_label.lower())
        statement_group_text = create_statement_group_representation(
            item_label, prop_label, statement_group
        )

        if statement_group_text:
            statements_representation.append(statement_group_text)

    return "\n".join(statements_representation)


# Function to get the label, description, and statements of a Wikidata item
def wikidata_item_to_text(item_id):
    """
    Get the text representation of a Wikidata item including its label, description, and statements.

    Args:
        item_id (str): The ID of the Wikidata item.

    Returns:
        str: The text representation of the Wikidata item.
    """
    # Check if the item is already in the cache
    item_data = item_cache.get(item_id)
    if not item_data:
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{item_id}.json"
        data = make_http_request(url)
        item_data = data.get("entities", {}).get(item_id, {})
        item_cache[item_id] = item_data
        save_item_cache()

    item_label = (
        item_data.get("labels", {}).get("en", {}).get("value", "No item label found")
    )
    description = (
        item_data.get("descriptions", {})
        .get("en", {})
        .get("value", "No description found")
    )
    text_representation = f"{item_label}: {description}\n\n"
    text_representation += create_statements_representation(
        item_label, item_data.get("claims", {})
    )
    return text_representation


capitals = ["Q64", "Q84", "Q90", "Q1085"]

for c in capitals:
    text_representation = wikidata_item_to_text(c)
    # Write to a file named after the Wikidata ID
    with open(f"{text_representations_dir}/{c}.txt", "w") as file:
        file.write(text_representation)
