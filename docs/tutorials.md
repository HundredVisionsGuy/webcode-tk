# Tutorials

## Set up
In order to grade student projects, you'll want to create a directory in your root project folder. I title mine "project".

Be sure you have installed and imported webcode-tk (I prefer poetry: `poetry install webcode-tk`)

Place your web documents in the project folder.

Be sure to import one or more of the webcode-tk scripts:
`from webcode_tk import html`
or
`from webcode_tk import validator`

In your Python script, set the project folder as a path:
`project_path = "project"`

### HTML Tasks
Get a list of all HTML files:
```
# at the top of the script with any other imports:
from webcode_tk import html
html_docs = html.get_all_html_files(project_path)
```
