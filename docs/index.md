# webcode-tk Docs

A collection of functions designed by a Web Design teacher for checking front-end web documents (in particular HTML and CSS files). It can automatically check validation on HTML and CSS.


The way I use it is to create a GitHub template with a project folder and a README file indicating which elements must be present. I deploy these templates on [GitHub Classroom](https://classroom.github.com/). Each template has a project folder with a README file both in the main repo folder as well as the project folder to indicate what I'll be testing for.


For **HTML checks**, I use it to make sure the project does not have any validation errors, meets the required number of elements, and can even check for a minimum number of image files.


For CSS, you can check validation, check to make sure specific properties are addressed, check for color contrast, and check to see if font families have been targetted. I also have a check that identifies if style attributes have been employed or not.


I have other helper tools that work with the html_tools and css_tools. I have included a ux_tools library that reports back on words per sentence, sentences per paragraph, list items in list, and readability scores. I have an animation_tools that can report back on the keyframe animations that are employed.

## Table Of Contents

1. [Tutorials](tutorials.md)
2. [html_tools.py](reference/html_tools.md)
3. [css_tools.py](reference/css_tools.md)
4. [cascade_tools.py](reference/cascade_tools.md)
5. [color_tools.py](reference/color_tools.md)
6. [color_keywords.py](reference/color_keywords.md)
7. [animation_tools.py](reference/animation_tools.md)
8. [ux_tools.py](reference/ux_tools.md)
9. [utils.py](reference/utils.md)
10. [validator_tools.py](reference/validator_tools.md)
11. [Explanation](explanation.md)

Quickly find what you're looking for depending on
your use case by looking at the different pages.

## Project Overview

::: webcode_tk

## Web Design Class Project Templates

Below are a few examples of how I use webcode-tk in a class project. If you look at the test files, you can see how I set it up.

I use `webcode-tk` to inspect all files in the `project` folder, and `pytest` looks at the reports and other tools to determine whether students' projects have met all the goals:

* **[One Pager Project](https://github.com/CenturyHSTech/one-pager-project)** contains two `pytest` files:

  + [test_html.py](https://github.com/CenturyHSTech/one-pager-project/blob/main/tests/test_html.py)
  + [test_css.py](https://github.com/CenturyHSTech/one-pager-project/blob/main/tests/test_css.py)

* **[Image Gallery Project](https://github.com/CenturyHSTech/Image-Gallery-Project)** contains four `pytest` files (I use the exceeds tests to determine the difference between a B or an A):

  + [test_html.py](https://github.com/CenturyHSTech/Image-Gallery-Project/blob/main/tests/test_html.py)
  + [test_html_exceeds.py](https://github.com/CenturyHSTech/Image-Gallery-Project/blob/main/tests/test_html_exceeds.py)
  + [test_css.py](https://github.com/CenturyHSTech/Image-Gallery-Project/blob/main/tests/test_css.py)
  + [test_css_exceeds.py](https://github.com/CenturyHSTech/Image-Gallery-Project/blob/main/tests/test_css_exceeds.py)

## Acknowledgements
I'd like to thank Guido van Rossum for his love of Monty Python and creating the Python programming language (pseudo-code that works) as well as the Python community and PyCon for running Development Sprints and giving rookies like me the chance to learn how to contribute to open-source projects.

I'd also like to thank [Real Python](https://realpython.com/) for being my go-to source for expanding my toolset.

If you can read this, it's because **Real Python** came through yet again by publishing ***[Build Your Python Project Documentation With MkDocs](https://realpython.com/python-project-documentation-with-mkdocs/)***, written by [Martin Breuss](https://realpython.com/python-project-documentation-with-mkdocs/#author) and his trusty team of developers who helped work on the tutorial.
