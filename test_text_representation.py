import unittest
import requests
from unittest import mock
from text_representation import make_http_request, load_item_cache, replace_prop_label, prop_skip
from text_representation import format_date

class TestFormatDate(unittest.TestCase):
    # Test if only the year is extracted when month and day are not provided.
    def test_year_only(self):
        self.assertEqual(format_date('+2016-00-00T00:00:00Z'), '2016')

    # Test if the year and month are correctly formatted when the day is not provided.
    def test_year_month(self):
        self.assertEqual(format_date('+2016-07-00T00:00:00Z'), '2016-07')

    # Test if the full date is correctly formatted when year, month, and day are provided.
    def test_full_date(self):
        self.assertEqual(format_date('+2016-07-15T00:00:00Z'), '2016-07-15')

    # Test if 'unknown date' is returned when an invalid date is provided.
    def test_invalid_date(self):
        self.assertEqual(format_date('+2016-13-00T00:00:00Z'), 'unknown date')

    # Test if 'unknown date' is returned when an empty string is provided as the date.
    def test_empty_date(self):
        self.assertEqual(format_date(''), 'unknown date')

    # Test if 'unknown date' is returned when None is provided as the date.
    def test_none_date(self):
        self.assertEqual(format_date(None), 'unknown date')

    # Test if make_http_request returns the correct JSON response for a successful request.
    @mock.patch('text_representation.requests.get')
    def test_make_http_request_success(self, mock_get):
        mock_get.return_value.json.return_value = {'key': 'value'}
        mock_get.return_value.raise_for_status = lambda: None
        url = 'http://example.com/api'
        response = make_http_request(url)
        self.assertEqual(response, {'key': 'value'})

    # Test if make_http_request raises an HTTPError for a failed request.
    @mock.patch('text_representation.requests.get')
    def test_make_http_request_failure(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
        url = 'http://example.com/api'
        with self.assertRaises(requests.exceptions.HTTPError):
            make_http_request(url)

class TestLoadItemCache(unittest.TestCase):
    # Test if load_item_cache correctly loads the cache when the cache file exists.
    @mock.patch('text_representation.os.path.exists')
    @mock.patch('text_representation.json.load')
    @mock.patch('text_representation.open', new_callable=mock.mock_open, read_data='{"Q1": "entity1"}')
    def test_load_item_cache_exists(self, mock_open, mock_json_load, mock_exists):
        mock_exists.return_value = True
        mock_json_load.return_value = {"Q1": "entity1"}
        cache = load_item_cache()
        self.assertEqual(cache, {"Q1": "entity1"})

    # Test if load_item_cache returns an empty dictionary when the cache file does not exist.
    @mock.patch('text_representation.os.path.exists')
    def test_load_item_cache_not_exists(self, mock_exists):
        mock_exists.return_value = False
        cache = load_item_cache()
        self.assertEqual(cache, {})

class TestReplacePropLabel(unittest.TestCase):
    # Test if replace_prop_label correctly replaces a known property label with its replacement.
    def test_replace_known_label(self):
        self.assertEqual(replace_prop_label('instance of'), 'is a')

    # Test if replace_prop_label returns the original label when no replacement is found.
    def test_replace_unknown_label(self):
        self.assertEqual(replace_prop_label('some unknown label'), 'some unknown label')

class TestPropSkip(unittest.TestCase):
    # Test if prop_skip correctly identifies labels that should be skipped.
    def test_skip_known_label(self):
        self.assertTrue(prop_skip('flag'))

    # Test if prop_skip does not skip labels that are not in the skip list.
    def test_not_skip_unknown_label(self):
        self.assertFalse(prop_skip('some unknown label'))

    # Test if the main function of the test suite is called correctly.
if __name__ == '__main__':
    unittest.main()
