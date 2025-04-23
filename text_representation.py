import requests
import json
import os
from tqdm import tqdm

# Path to the item cache file
item_cache_file_path = "wikidata_item_cache.json"
# Path to the label cache file
label_cache_file_path = "wikidata_label_cache.json"
alias_cache_file_path = "wikidata_alias_cache.json"

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
    tqdm.write(f"  GET {url}...")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def load_item_cache():
    if os.path.exists(item_cache_file_path):
        cache = {}
        with open(item_cache_file_path, "r") as file:
            for line in file:
                item = json.loads(line)
                if "id" in item:
                    cache[item["id"]] = item
                else:
                    print("Broken cache entry:", item)
        return cache
    else:
        return {}


def load_label_cache():
    if os.path.exists(label_cache_file_path):
        with open(label_cache_file_path, "r") as cache_file:
            return json.load(cache_file)
    else:
        return {}


def load_alias_cache():
    if os.path.exists(alias_cache_file_path):
        with open(alias_cache_file_path, "r") as cache_file:
            return json.load(cache_file)
    else:
        return {}


# Load item cache from file if it exists
item_cache = load_item_cache()
label_cache = load_label_cache()
alias_cache = load_alias_cache()


# Replacements for property labels
def replace_prop_label(label) -> str:
    property_label_replacements = {
        # "instance of": "is a",
        # "postal code": "has postal code",
        # "local dialing code": "has local dailing code",
        # "licence plate code": "has license plate code",
        # "enclave within": "is an enclave within",
        # "located in time zone": "is located in time zone",
        # "highest point": "has an highest point:",
        # "continent": "part of continent",
        # "hashtag": "has hashtag",
        # "award received": "has received award",
        # "located in or next to body of water": "is next to river or lake or sea",
        # "capital of": "is capital of",
        # "located in the administrative territorial entity": "is located in the administrative territorial entity",
        # "head of government": "has head of government",
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
        for _, i in item_cache.items():
            cache_file.write(json.dumps(i) + "\n")


# Save item cache to file
def save_alias_cache():
    with open(alias_cache_file_path, "w") as cache_file:
        cache_file.write(json.dumps(alias_cache))


def append_item_cache(item):
    with open(item_cache_file_path, "a") as cache_file:
        cache_file.write(json.dumps(item) + "\n")


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


def fetch_alias_by_ids(ids):
    # Check the cache first
    uncached_ids = [id_ for id_ in ids if id_ not in alias_cache]
    labels_to_fetch = "|".join(uncached_ids)

    if labels_to_fetch:
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={labels_to_fetch}&format=json&props=aliases"
        data = make_http_request(url)

        for entity_id, content in data["entities"].items():
            # print(content)
            aliases = content["aliases"].get("en", {})
            # print(aliases)
            a = []
            for alias in aliases:
                a.append(alias.get("value", ""))
            alias_cache[entity_id] = a

        # Save updated label cache to disk
        save_alias_cache()

    # Now build the result using the label cache
    aliases = {id_: alias_cache.get(id_, id_) for id_ in ids}
    return aliases


def format_date(date_value):
    """
    Format a Wikidata date value to a common date format or as text if incomplete.

    Args:
        date_value (str): The date value from Wikidata in the format '+YYYY-MM-DDTHH:MM:SSZ'.

    Returns:
        str: The formatted date in ISO 8601 format (YYYY, YYYY-MM, or YYYY-MM-DD),
             or 'unknown date' if input is None or cannot be parsed.
    """
    try:
        # Remove the '+' sign and time component from the date string
        date_str = date_value.lstrip("+").split("T")[0]
        # Split the date into components, expecting at most 3 parts (year, month, day)
        date_parts = date_str.split("-", 2)

        # Check the number of parts and format accordingly
        if len(date_parts) == 3:
            year, month, day = date_parts
            if int(month) > 12 or int(day) > 31:  # Check for invalid month or day
                return "unknown date"
            if month == "00" and day == "00":
                return year  # Year only
            elif month != "00" and day == "00":
                return f"{year}-{month}"  # Year and month
            else:
                return f"{year}-{month}-{day}"  # Full date
        elif len(date_parts) == 2:
            year, month = date_parts
            if int(month) > 12:  # Check for invalid month or day
                return "unknown date"
            if month == "00":
                return year  # Year only
            else:
                return f"{year}-{month}"  # Year and month
        elif len(date_parts) == 1:
            return date_parts[0]  # Year only
    except:
        return "unknown date"

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
    ongoing = True
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

    if start_time_qualifier and not end_time_qualifier:
        start_time = format_date(start_time_qualifier)
        time_span += f"since {start_time} until today"
    elif start_time_qualifier:
        start_time = format_date(start_time_qualifier)
        time_span += f"from {start_time} "
        ongoing = False

    if end_time_qualifier:
        end_time = format_date(end_time_qualifier)
        time_span += f"until {end_time}"
        ongoing = False
    if point_in_time_qualifier and not (start_time_qualifier or end_time_qualifier):
        point_in_time = format_date(point_in_time_qualifier)
        time_span += f"in {point_in_time}"
        ongoing = False

    return time_span.strip(), ongoing


def create_statement_representation(statement, item_label, prop_label):
    # print(statement)
    mainsnak = statement.get("mainsnak", {})
    datavalue = mainsnak.get("datavalue", {})
    value = datavalue.get("value")
    datatype = mainsnak.get("datatype")
    # print(datatype)
    qualifiers = statement.get("qualifiers", {})
    time_span, ongoing = get_time_span(qualifiers)
    time_span_text = f" {time_span}" if time_span else ""
    adjusted_prop_label = prop_label

    if not ongoing:
        adjusted_prop_label = prop_label.replace("is", "was")
        adjusted_prop_label = adjusted_prop_label.replace("has", "had")

    if datatype == "wikibase-item" and value and value.get("entity-type") == "item":
        value_id = value.get("id")
        labels = fetch_labels_by_ids([value_id])
        value_label = labels.get(value_id, value_id)
        if value_label:
            return f"{item_label} {adjusted_prop_label} {value_label}{time_span_text}."

    elif datatype == "time" and value:
        time_value = format_date(value.get("time"))
        return f"{item_label} {adjusted_prop_label} on {time_value}{time_span_text}."

    elif datatype == "string":
        string_value = value if isinstance(value, str) else "Unknown"
        return f"{item_label} {adjusted_prop_label} {string_value}{time_span_text}."

    elif datatype == "quantity":
        quantity_value = format_quantity(value)
        return f"{item_label} {adjusted_prop_label} {quantity_value}{time_span_text}."


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
        statement_group_text.append(
            create_statement_representation(statement, item_label, prop_label)
        )

    # Ensure each non-empty statement group ends with a newline
    return "\n".join(statement_group_text) + "\n" if statement_group_text else ""


def get_item(item_id):
    item_data = item_cache.get(item_id)

    if not item_data:
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{item_id}.json"
        data = make_http_request(url)
        item_data = data.get("entities", {}).get(item_id, {})
        item_cache[item_id] = item_data
        # save_item_cache()
        append_item_cache(item_data)

    return item_data


def item_label_description_to_text(item_data, lang="en"):
    text_representation = ""

    item_label = (
        item_data.get("labels", {}).get(lang, {}).get("value", "No item label found")
    )
    item_description = (
        item_data.get("descriptions", {})
        .get(lang, {})
        .get("value", "No description found")
    )

    text_representation += f"{item_label}: {item_description}\n"

    return text_representation


def item_aliases_to_text(item_data, lang="en"):
    text_representation = ""

    item_label = (
        item_data.get("labels", {}).get(lang, {}).get("value", "No item label found")
    )
    item_aliases = item_data.get("aliases", {}).get(lang, [])

    # for alias in item_aliases:
    #     text_representation += f"{item_label} is also known as {alias.get('value')}.\n"


    if item_aliases and len(item_aliases) > 0:
        text_representation += f"{item_label} is also known as "
        for alias in item_aliases:
            text_representation += f"{alias.get('value')}, "
        text_representation = text_representation[:-2] + ".\n"

    return text_representation


def statement_group_to_text(item_data, prop_id, statement_group, lang="en"):
    item_label = (
        item_data.get("labels", {}).get(lang, {}).get("value", "No item label found")
    )

    labels = fetch_labels_by_ids([prop_id])
    prop_label = labels.get(prop_id, prop_id)
    aliases = fetch_alias_by_ids([prop_id])
    prop_aliases = aliases.get(prop_id, [])

    if prop_label.lower().startswith("category") or prop_skip(prop_label.lower()):
        return None

    prop_label = replace_prop_label(prop_label.lower())

    text_representation = ""
    text_representation += item_label_description_to_text(item_data)
    text_representation += item_aliases_to_text(item_data)

    has_statements = False
    for statement in statement_group:
        statement_representation = create_statement_representation(
            statement, item_label, prop_label
        )
        if statement_representation is not None:
            has_statements = True
            text_representation += statement_representation + "\n"

    if prop_aliases and len(prop_aliases) > 0:
        text_representation += f"The term '{prop_label}' could also be referred to as "
        for alias in prop_aliases:
            text_representation += f"{alias}, "
        text_representation = text_representation[:-2] + ".\n"

    if has_statements:
        return text_representation


items = ["Q64"]
# capitals
# items = ["Q61", "Q64", "Q70", "Q84", "Q85", "Q90", "Q216", "Q220", "Q269", "Q270", "Q384", "Q437", "Q472", "Q585", "Q598", "Q649", "Q807", "Q911", "Q956", "Q987", "Q994", "Q1085", "Q1335", "Q1362", "Q1486", "Q1515", "Q1520", "Q1524", "Q1530", "Q1533", "Q1555", "Q1563", "Q1741", "Q1748", "Q1754", "Q1757", "Q1761", "Q1770", "Q1780", "Q1781", "Q1844", "Q1848", "Q1850", "Q1858", "Q1861", "Q1863", "Q1865", "Q1867", "Q1899", "Q1930", "Q1947", "Q1963", "Q2082", "Q2280", "Q2337", "Q2449", "Q2471", "Q2841", "Q2844", "Q2868", "Q2887", "Q2900", "Q2933", "Q3001", "Q3037", "Q3043", "Q3070", "Q3110", "Q3114", "Q3238", "Q3274", "Q3306", "Q3551", "Q3561", "Q3579", "Q3604", "Q3616", "Q3642", "Q3659", "Q3692", "Q3703", "Q3711", "Q3718", "Q3726", "Q3748", "Q3751", "Q3761", "Q3768", "Q3780", "Q3787", "Q3792", "Q3805", "Q3808", "Q3818", "Q3820", "Q3825", "Q3826", "Q3832", "Q3844", "Q3856", "Q101418", "Q103717", "Q112813", "Q129072", "Q131233", "Q131620", "Q131694", "Q132572", "Q132679", "Q132754", "Q132997", "Q147738", "Q154002", "Q157035", "Q159273", "Q165341", "Q166065", "Q167436", "Q167551", "Q168652", "Q168929", "Q170454", "Q170578", "Q170762", "Q172512", "Q173310", "Q174461", "Q178993", "Q180773", "Q181007", "Q181056", "Q192541", "Q211030", "Q217610", "Q232615", "Q277540", "Q319476", "Q331584", "Q385445", "Q429059", "Q569107", "Q605319", "Q624467", "Q696193", "Q706215", "Q738250", "Q752394", "Q822679", "Q834162", "Q841342", "Q854672", "Q977305", "Q993064", "Q1000140", "Q1020758", "Q1069007", "Q1107569", "Q1113311", "Q1131299", "Q1136681", "Q1190403", "Q1199713", "Q1330294", "Q1518300", "Q1769924", "Q1815305", "Q2313393", "Q2483679", "Q2594448", "Q3233968", "Q3344424", "Q3344926", "Q3393642", "Q3528033", "Q3683885", "Q3894902", "Q3947434", "Q3947744", "Q3947745", "Q3948919", "Q4070999", "Q4803191", "Q5316658", "Q5865090", "Q7223839", "Q7856199", "Q8262638", "Q10054424", "Q11955673", "Q12254217", "Q12259792", "Q12489692", "Q14634615", "Q14934767", "Q15941322", "Q18342086", "Q23000330", "Q23986680", "Q24008400", "Q28519583", "Q31877477", "Q31878333", "Q31879456", "Q31880915", "Q31887734", "Q31911550", "Q31912265", "Q31924170", "Q31924457", "Q47461088", "Q49286541", "Q49344178", "Q65300020", "Q70591145", "Q97132512", "Q98008573", "Q98686735", "Q101186473", "Q105076255", "Q3859", "Q3861", "Q3866", "Q3870", "Q3876", "Q3881", "Q3889", "Q3894", "Q3897", "Q3901", "Q3904", "Q3909", "Q3915", "Q3919", "Q3921", "Q3926", "Q3929", "Q3932", "Q3935", "Q3940", "Q4361", "Q5426", "Q5465", "Q8678", "Q8684", "Q9022", "Q9248", "Q9279", "Q9310", "Q9347", "Q9361", "Q9365", "Q10686", "Q10690", "Q10717", "Q11194", "Q12919", "Q16666", "Q18808", "Q19660", "Q19689", "Q21197", "Q23436", "Q23438", "Q25270", "Q25390", "Q27660", "Q30958", "Q30970", "Q30985", "Q31026", "Q31487", "Q33929", "Q34126", "Q34261", "Q34692", "Q34820", "Q35178", "Q35381", "Q36168", "Q36260", "Q36281", "Q36378", "Q36526", "Q37400", "Q37701", "Q37806", "Q37995", "Q38807", "Q38834", "Q40236", "Q40269", "Q40921", "Q41128", "Q41295", "Q41474", "Q41547", "Q41699", "Q41963", "Q42751", "Q42800", "Q44059", "Q44211", "Q44215", "Q44244", "Q47916", "Q48329", "Q48338", "Q52101", "Q63964", "Q66485", "Q68481", "Q69345", "Q79281", "Q80484", "Q80989", "Q82500", "Q83189", "Q83442", "Q83786",]

for i in tqdm(items):
    tqdm.write(f"Generating {i}...")

    item_data = get_item(i)
    statements = item_data.get("claims", {})

    for prop_id, statement_group in statements.items():
        for statement in statement_group:
            # text = statement_group_to_text(item_data, prop_id, statement_group, lang="en")
            text = statement_group_to_text(item_data, prop_id, [statement], lang="en")
            if text:
                print(text)
