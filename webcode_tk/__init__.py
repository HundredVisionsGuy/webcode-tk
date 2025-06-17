# __init__.py
"""Deals with html and css documents to check their code.

### Modules exported by this package:

- **`animation_tools`**: a library used to report back on animations applied.
           As of now, we are focusing entirely on keyframe animations (not)
          transitions.

- **`cascade_tools`**: library to calculate how the cascade affects font-size
          and background color and color through inheritance and will be
          used for calculating color contrast.

- **`color_keywords`**: helper library to align color keywords with their
          properties and hex and rgb values.

- **`color_tools`**: processes CSS color related properties and values.

- **`css_tools`**: creates Stylesheet objects that store CSS information.

- **`font_tools`**: A collection of functions used to process font-related
          styles.

- **`html_tools`**: gets html files from a project folder, gets the HTML code
          from files, gets number of a particular element in a file
          or folder, gets elements as tags, and much more.

- **`ux_tools`**: gets readability stats for paragraphs of text (could
          be from just `p` tags or a list of other tags e.g. `li`,
          `div`, etc.).

- **`utils.py`**: a library of helper functions to reduce the workload of the
          other libraries.

- **`validator_tools`**: sends HTML or CSS code to the W3C Validator to check
          for errors.
"""
__version__ = "1.2.3"
