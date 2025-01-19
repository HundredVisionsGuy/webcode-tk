"""a script of utility functions that are useful for webcode-tk but don't
belong to any one particular webcode tool."""


def get_first_dict_key(some_dict: dict) -> str:
    """returns the first key of a dictionary.

    Args:
        some_dict: a dictionary (any dictionary)

    Returns:
        first_key: the first key of a dictionary"""
    first_key = some_dict.keys()
    first_key = list(first_key)
    first_key = first_key[0]
    return first_key
