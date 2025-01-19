import pytest

from webcode_tk import utils


dictionaries = [
    {
        "animations.html": {
            "keyframes": [],
            "pct_keyframes": [],
        }
    },
    {"brand": "Ford", "model": "Mustang", "year": 1964},
    {"a": "Geeks", "b": "for", "c": "Geeks"},
    {"Germany": "Berlin", "Canada": "Ottawa", "England": "London"},
]


first_key_expectations = (
    (dictionaries[0], "animations.html"),
    (dictionaries[1], "brand"),
    (dictionaries[2], "a"),
    (dictionaries[3], "Germany"),
)


@pytest.mark.parametrize("dict,key", first_key_expectations)
def test_get_first_dict_key(dict, key):
    result = utils.get_first_dict_key(dict)
    assert result == key
