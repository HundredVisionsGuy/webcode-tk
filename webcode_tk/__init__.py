# __init__.py
"""Deals with html and css documents to check their code.

Modules exported by this package:
- `cascade_tools`: library to calculate how the cascade affects font-size
          and background color and color through inheritance and will be
          used for calculating color contrast.
- `color_keywords`: helper library to align color keywords with their
          properties and hex and rgb values.
- `color_tools`: processes CSS color related properties and values.
- `css_tools`: creates Stylesheet objects that store CSS information.
- `html_tools`: gets html files from a project folder, gets the HTML code
          from files, gets number of a particular element in a file
          or folder, gets elements as tags, and much more.
- `ux_tools`: gets readability stats for paragraphs of text (could
          be from just `p` tags or a list of other tags e.g. `li`,
          `div`, etc.).
- `validator_tools`: sends HTML or CSS code to the W3C Validator to check
          for errors.
"""
__version__ = "1.0.2"
