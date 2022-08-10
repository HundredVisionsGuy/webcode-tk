# Explanation

## Created by a CS and Web Development teacher.
During the pandemic, I decided to start a Python project that addressed one of my greatest pain-points: grading my Web Design students' projects.

It was tedious to run all pages through the W3C validator, and then open each page in either the inspector or with a text editor to see if my students used particular tags.

I also would run the stylesheets and style tags through the CSS validator, and have to examine each stylesheet if I wanted to make sure they were applying the correct properties and values.

I realized that if I could automate all those tasks, then I could just come in and grade the visual element and save a good 3 minutes or more per student.

I'll highlight those in the following *Use Case section*.

## Use Case
If you want to manipulate files in a Python project, you may find this useful. Here are the main ways I use this library:

* **Grab a list of all files** - in a project folder.
* **Select just the filetypes I want** - typically, I am processing HTML, CSS, and CSV files)
* **Write contents to files** - this is handy for generating reports
* **My oddly specific tasks** for checking and processing student work, such as...
    - **Split paragraphs into sentences** - so I can check things like word count and sentences per paragraph
    - **remove inline tags from a container tag** - so I could count just words and sentences from a web document

## licensing
I selected to use the MIT license for this library. I selected it for three main reasons:

1. I found that the majority of the OSS (Open Source Software) licenses out there are MIT.
2. MIT is permissive and doesn't force any of my other projects to be of the same license.
3. In my webanalyst project, the majority of the licenses were also MIT, so I decided to do the same.
