import unittest
from unittest import mock
import requests

import text_representation


class TestFormatDate(unittest.TestCase):
    # Test if only the year is extracted when month and day are not provided.
    def test_year_only(self):
        self.assertEqual(text_representation.format_date("+2016-00-00T00:00:00Z"), "2016")

    # Test if the year and month are correctly formatted when the day is not provided.
    def test_year_month(self):
        self.assertEqual(text_representation.format_date("+2016-07-00T00:00:00Z"), "2016-07")

    # Test if the full date is correctly formatted when year, month, and day are provided.
    def test_full_date(self):
        self.assertEqual(text_representation.format_date("+2016-07-15T00:00:00Z"), "2016-07-15")

    # Test if 'unknown date' is returned when an invalid date is provided.
    def test_invalid_date(self):
        self.assertEqual(text_representation.format_date("+2016-13-00T00:00:00Z"), "unknown date")

    # Test if 'unknown date' is returned when an empty string is provided as the date.
    def test_empty_date(self):
        self.assertEqual(text_representation.format_date(""), "unknown date")

    # Test if 'unknown date' is returned when None is provided as the date.
    def test_none_date(self):
        self.assertEqual(text_representation.format_date(None), "unknown date")

    def test_short_string_year_month_no_day(self):
        self.assertEqual(text_representation.format_date("+2016-07"), "2016-07")

    def test_short_string_year_month_no_day_invalid_month(self):
        self.assertEqual(text_representation.format_date("+2016-17"), "unknown date")

    def test_short_string_year_month_no_day_zero_month(self):
        self.assertEqual(text_representation.format_date("+2016-00"), "2016")

    def test_short_string_year_only(self):
        self.assertEqual(text_representation.format_date("+2016"), "2016")



class TestMakeHttpRequest(unittest.TestCase):
    # Test if make_http_request returns the correct JSON response for a successful request.
    @mock.patch("text_representation.requests.get")
    def test_make_http_request_success(self, mock_get):
        mock_get.return_value.json.return_value = {"key": "value"}
        mock_get.return_value.raise_for_status = lambda: None
        url = "http://example.com/api"
        response = text_representation.make_http_request(url)
        self.assertEqual(response, {"key": "value"})

    # Test if make_http_request raises an HTTPError for a failed request.
    @mock.patch("text_representation.requests.get")
    def test_make_http_request_failure(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError
        )
        url = "http://example.com/api"
        with self.assertRaises(requests.exceptions.HTTPError):
            text_representation.make_http_request(url)


class TestLoadItemCache(unittest.TestCase):
    # Test if load_item_cache correctly loads the cache when the cache file exists.
    @mock.patch("text_representation.os.path.exists")
    @mock.patch("text_representation.json.load")
    @mock.patch(
        "text_representation.open",
        new_callable=mock.mock_open,
        read_data='{"Q1": "entity1"}',
    )
    def test_load_item_cache_exists(self, mock_open, mock_json_load, mock_exists):
        mock_exists.return_value = True
        mock_json_load.return_value = {"Q1": "entity1"}
        cache = text_representation.load_item_cache()
        self.assertEqual(cache, {"Q1": "entity1"})

    # Test if load_item_cache returns an empty dictionary when the cache file does not exist.
    @mock.patch("text_representation.os.path.exists")
    def test_load_item_cache_not_exists(self, mock_exists):
        mock_exists.return_value = False
        cache = text_representation.load_item_cache()
        self.assertEqual(cache, {})


class TestReplacePropLabel(unittest.TestCase):
    # Test if replace_prop_label correctly replaces a known property label with its replacement.
    def test_replace_known_label(self):
        self.assertEqual(text_representation.replace_prop_label("instance of"), "is a")

    # Test if replace_prop_label returns the original label when no replacement is found.
    def test_replace_unknown_label(self):
        self.assertEqual(text_representation.replace_prop_label("some unknown label"), "some unknown label")


class TestPropSkip(unittest.TestCase):
    # Test if prop_skip correctly identifies labels that should be skipped.
    def test_skip_known_label(self):
        self.assertTrue(text_representation.prop_skip("flag"))

    # Test if prop_skip does not skip labels that are not in the skip list.
    def test_not_skip_unknown_label(self):
        self.assertFalse(text_representation.prop_skip("some unknown label"))


class TestLoadLabelCache(unittest.TestCase):
    # Test loading label cache when cache file exists.
    @mock.patch("text_representation.os.path.exists")
    @mock.patch("text_representation.json.load")
    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data='{"P123": "Label for P123"}',
    )
    def test_load_label_cache_exists(self, mock_file, mock_json_load, mock_exists):
        mock_exists.return_value = True
        mock_json_load.return_value = {"P123": "Label for P123"}
        label_cache = text_representation.load_label_cache()
        self.assertEqual(label_cache, {"P123": "Label for P123"})

    # Test loading label cache when cache file does not exist.
    @mock.patch("text_representation.os.path.exists")
    def test_load_label_cache_not_exists(self, mock_exists):
        mock_exists.return_value = False
        label_cache = text_representation.load_label_cache()
        self.assertEqual(label_cache, {})


class TestSaveItemCache(unittest.TestCase):
    # Test if save_item_cache creates a new file with the correct name if it does not exist
    @mock.patch("text_representation.open", new_callable=mock.mock_open)
    @mock.patch("text_representation.json.dump")
    @mock.patch("text_representation.os.path.exists")
    def test_save_item_cache_creates_file(self, mock_exists, mock_json_dump, mock_open):
        mock_exists.return_value = False
        text_representation.save_item_cache()
        mock_open.assert_called_once_with(text_representation.item_cache_file_path, "w")
        mock_json_dump.assert_called_once()

    # Test if save_item_cache writes the correct data to the file
    @mock.patch("text_representation.open", new_callable=mock.mock_open, read_data='{}')
    @mock.patch("text_representation.json.dump")
    @mock.patch("text_representation.os.path.exists")
    def test_save_item_cache_writes_data(self, mock_exists, mock_json_dump, mock_open):
        mock_exists.return_value = True
        test_cache = {"Q1": "entity1"}
        text_representation.item_cache = test_cache
        text_representation.save_item_cache()
        mock_json_dump.assert_called_once_with(test_cache, mock_open.return_value, indent=2)

    # Test if save_item_cache correctly updates the item cache when called
    @mock.patch("text_representation.load_item_cache")
    @mock.patch("text_representation.open", new_callable=mock.mock_open)
    @mock.patch("text_representation.json.dump")
    @mock.patch("text_representation.os.path.exists")
    def test_save_item_cache_updates_cache(
        self, mock_exists, mock_json_dump, mock_open, mock_load_item_cache
    ):
        mock_exists.return_value = True
        test_cache = {"Q1": "entity1"}
        text_representation.item_cache = test_cache
        text_representation.save_item_cache()
        mock_load_item_cache.assert_called_once()


class TestSaveLabelCache(unittest.TestCase):
    # Test if save_label_cache creates a new file with the correct name if it does not exist
    @mock.patch("text_representation.open", new_callable=mock.mock_open)
    @mock.patch("text_representation.json.dump")
    @mock.patch("text_representation.os.path.exists")
    def test_save_label_cache_creates_file(
        self, mock_exists, mock_json_dump, mock_open
    ):
        mock_exists.return_value = False
        text_representation.save_label_cache()
        mock_open.assert_called_once_with(
            text_representation.label_cache_file_path, "w"
        )
        mock_json_dump.assert_called_once()

    # Test if save_label_cache writes the correct data to the file
    @mock.patch("text_representation.open", new_callable=mock.mock_open, read_data='{}')
    @mock.patch("text_representation.json.dump")
    @mock.patch("text_representation.os.path.exists")
    def test_save_label_cache_writes_data(self, mock_exists, mock_json_dump, mock_open):
        mock_exists.return_value = True
        test_cache = {"P123": "Label for P123"}
        text_representation.label_cache = test_cache
        text_representation.save_label_cache()
        mock_json_dump.assert_called_once_with(
            test_cache, mock_open.return_value, indent=2
        )

    # Test if save_label_cache correctly updates the label cache when called
    @mock.patch("text_representation.load_label_cache")
    @mock.patch("text_representation.open", new_callable=mock.mock_open)
    @mock.patch("text_representation.json.dump")
    @mock.patch("text_representation.os.path.exists")
    def test_save_label_cache_updates_cache(
        self, mock_exists, mock_json_dump, mock_open, mock_load_label_cache
    ):
        mock_exists.return_value = True
        test_cache = {"P123": "Label for P123"}
        text_representation.label_cache = test_cache
        text_representation.save_label_cache()
        mock_load_label_cache.assert_called_once()

class TestFetchLabelsByIds(unittest.TestCase):
    @mock.patch("text_representation.make_http_request")
    @mock.patch("text_representation.save_label_cache")
    def test_fetch_labels_by_ids_returns_correct_labels(self, mock_save_label_cache, mock_make_http_request):
        # Setup mock response from the API
        mock_response = {
            "entities": {
                "Q1": {"labels": {"en": {"language": "en", "value": "Universe"}}},
                "Q2": {"labels": {"en": {"language": "en", "value": "Earth"}}},
            }
        }
        mock_make_http_request.return_value = mock_response

        # Call fetch_labels_by_ids with IDs that are not in the cache
        labels = text_representation.fetch_labels_by_ids(["Q1", "Q2"])

        # Check that the labels are correctly returned
        self.assertEqual(labels, {"Q1": "Universe", "Q2": "Earth"})
        # Check that the API was called since these labels were not in the cache
        mock_make_http_request.assert_called_once()
        # Check that the label cache is saved after fetching
        mock_save_label_cache.assert_called_once()

    @mock.patch("text_representation.make_http_request")
    def test_fetch_labels_by_ids_uses_cache(self, mock_make_http_request):
        # Pre-populate the label cache
        text_representation.label_cache = {"Q1": "Universe"}

        # Call fetch_labels_by_ids with an ID that is in the cache
        labels = text_representation.fetch_labels_by_ids(["Q1"])

        # Check that the labels are correctly returned from the cache
        self.assertEqual(labels, {"Q1": "Universe"})
        # Check that the API was not called since the label was in the cache
        mock_make_http_request.assert_not_called()

    @mock.patch("text_representation.make_http_request")
    @mock.patch("text_representation.save_label_cache")
    def test_fetch_labels_by_ids_updates_cache(self, mock_save_label_cache, mock_make_http_request):
        # Setup mock response from the API
        mock_response = {
            "entities": {
                "Q2": {"labels": {"en": {"language": "en", "value": "Earth"}}},
            }
        }
        mock_make_http_request.return_value = mock_response

        # Pre-populate the label cache with a different ID
        text_representation.label_cache = {"Q1": "Universe"}

        # Call fetch_labels_by_ids with a new ID that is not in the cache
        labels = text_representation.fetch_labels_by_ids(["Q2"])

        # Check that the labels are correctly returned and include the new label from the API
        self.assertEqual(labels, {"Q2": "Earth"})
        # Check that the label cache now contains the new label
        self.assertIn("Q2", text_representation.label_cache)
        self.assertEqual(text_representation.label_cache["Q2"], "Earth")
        # Check that the label cache is saved after fetching
        mock_save_label_cache.assert_called_once()


class TestCreateStatementsRepresentation(unittest.TestCase):
    def setUp(self):
        self.item_label = "Sample Item"
        # Start the fetch_labels_by_ids mock and set return values for entity IDs
        self.mock_fetch_labels = mock.patch("text_representation.fetch_labels_by_ids")
        self.mock_fetch_labels_start = self.mock_fetch_labels.start()
        self.mock_fetch_labels_start.return_value = {
            "P123": "sample property",
            "Q42": "Douglas Adams",
        }

    def tearDown(self):
        # Stop the fetch_labels_by_ids mock
        self.mock_fetch_labels.stop()

    def test_empty_statements(self):
        statements = {}
        result = text_representation.create_statements_representation(self.item_label, statements)
        self.assertEqual(result, "")

    def test_statements_with_single_group(self):
        statements = {
            "P123": [
                {
                    "mainsnak": {
                        "datatype": "wikibase-item",
                        "datavalue": {"value": {"entity-type": "item", "id": "Q42"}},
                    }
                }
            ]
        }
        result = text_representation.create_statements_representation(self.item_label, statements)
        self.assertIn("Sample Item sample property Douglas Adams.", result)

    def test_statements_with_multiple_groups(self):
        statements = {
            "P123": [
                {
                    "mainsnak": {
                        "datatype": "wikibase-item",
                        "datavalue": {"value": {"entity-type": "item", "id": "Q42"}},
                    }
                }
            ],
            "P124": [
                {
                    "mainsnak": {
                        "datatype": "string",
                        "datavalue": {"value": "Sample string"},
                    }
                }
            ],
        }
        self.mock_fetch_labels_start.return_value.update({"P124": "another property"})
        result = text_representation.create_statements_representation(self.item_label, statements)
        self.assertIn("Sample Item sample property Douglas Adams.", result)
        self.assertIn("Sample Item another property Sample string.", result)

    def test_statements_should_skip(self):
        statements = {
            "P123": [
                {
                    "mainsnak": {
                        "datatype": "wikibase-item",
                        "datavalue": {"value": {"entity-type": "item", "id": "Q42"}},
                    }
                }
            ],
            "P125": [
                {
                    "mainsnak": {
                        "datatype": "wikibase-item",
                        "datavalue": {"value": {"entity-type": "item", "id": "Q42"}},
                    }
                }
            ],
        }
        self.mock_fetch_labels_start.return_value.update({"P125": "flag"})
        result = text_representation.create_statements_representation(self.item_label, statements)
        self.assertIn("Sample Item sample property Douglas Adams.", result)
        self.assertNotIn("Sample Item flag Douglas Adams.", result)
        result = text_representation.create_statements_representation(self.item_label, statements)
        self.assertIn("Sample Item sample property Douglas Adams.", result)
        self.assertNotIn("Sample Item flag Douglas Adams.", result)


class TestCreateStatementGroupRepresentation(unittest.TestCase):
    def setUp(self):
        self.item_label = "Sample Item"
        # Start the fetch_labels_by_ids mock and set return values for entity IDs
        self.mock_fetch_labels = mock.patch(
            "text_representation.fetch_labels_by_ids",
            return_value={"Q42": "Douglas Adams", "Q11573": "unit"},
        )
        self.mock_fetch_labels.start()

    def tearDown(self):
        # Stop the fetch_labels_by_ids mock
        self.mock_fetch_labels.stop()

    def test_empty_statement_group(self):
        prop_label = "sample property"
        statement_group = []
        result = text_representation.create_statement_group_representation(
            self.item_label, prop_label, statement_group
        )
        self.assertEqual(result, "")

    def test_statement_group_with_different_datatypes(self):
        prop_label = "sample property"
        statement_group = [
            {
                "mainsnak": {
                    "datatype": "wikibase-item",
                    "datavalue": {"value": {"entity-type": "item", "id": "Q42"}},
                }
            },
            {
                "mainsnak": {
                    "datatype": "time",
                    "datavalue": {"value": {"time": "+2023-04-01T00:00:00Z"}},
                }
            },
            {
                "mainsnak": {
                    "datatype": "string",
                    "datavalue": {"value": "Sample string"},
                }
            },
            {
                "mainsnak": {
                    "datatype": "quantity",
                    "datavalue": {
                        "value": {
                            "amount": "+42",
                            "unit": "http://www.wikidata.org/entity/Q11573",
                        }
                    },
                }
            },
        ]
        result = text_representation.create_statement_group_representation(
            self.item_label, prop_label, statement_group
        )
        self.assertIn("Sample Item sample property Douglas Adams", result)
        self.assertIn("Sample Item sample property on 2023-04-01", result)
        self.assertIn("Sample Item sample property Sample string", result)
        self.assertIn("Sample Item sample property 42 unit", result)

    def test_statement_group_with_qualifiers(self):
        prop_label = "sample property"
        statement_group = [
            {
                "mainsnak": {
                    "datatype": "wikibase-item",
                    "datavalue": {"value": {"entity-type": "item", "id": "Q42"}},
                },
                "qualifiers": {
                    "P580": [
                        {"datavalue": {"value": {"time": "+2023-04-01T00:00:00Z"}}}
                    ]
                },
            }
        ]
        result = text_representation.create_statement_group_representation(
            self.item_label, prop_label, statement_group
        )
        self.assertIn(
            "Sample Item sample property Douglas Adams since 2023-04-01 until today",
            result,
        )

    def test_statement_group_should_skip(self):
        prop_label = "flag"
        statement_group = [
            {
                "mainsnak": {
                    "datatype": "wikibase-item",
                    "datavalue": {"value": {"entity-type": "item", "id": "Q42"}},
                }
            }
        ]
        result = text_representation.create_statements_representation(
            self.item_label, {prop_label: statement_group}
        )
        self.assertEqual(result, "")

class TestWikidataItemToText(unittest.TestCase):
    @mock.patch("text_representation.make_http_request")
    @mock.patch("text_representation.save_item_cache")
    def test_wikidata_item_to_text_not_in_cache(self, mock_save_item_cache, mock_make_http_request):
        # Setup mock response from the API
        mock_response = {
            "entities": {
                "Q42": {
                    "labels": {"en": {"language": "en", "value": "Douglas Adams"}},
                    "descriptions": {"en": {"language": "en", "value": "English writer and humorist"}},
                    "claims": {}
                }
            }
        }
        mock_make_http_request.return_value = mock_response

        # Clear the item cache before testing
        text_representation.item_cache = {}

        # Call wikidata_item_to_text with an item ID that is not in the cache
        item_text = text_representation.wikidata_item_to_text("Q42")

        # Check that the text representation is as expected
        expected_text = "Douglas Adams: English writer and humorist\n\n"
        self.assertEqual(item_text, expected_text)

        # Check that the API was called since the item was not in the cache
        mock_make_http_request.assert_called_once()

        # Check that the item cache is saved after fetching
        mock_save_item_cache.assert_called_once()
