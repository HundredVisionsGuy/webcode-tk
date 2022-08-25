# Explanation

## Created by a CS and Web Development teacher.
During the pandemic, I decided to start a Python project that addressed one of my greatest pain-points: grading my Web Design students' projects.

It was tedious to run all pages through the W3C validator, and then open each page in either the inspector or with a text editor to see if my students used particular tags.

I also would run the stylesheets and style tags through the CSS validator, and have to examine each stylesheet if I wanted to make sure they were applying the correct properties and values.

I realized that if I could automate all those tasks, then I could just come in and grade the visual element and save a good 3 minutes or more per student.

I'll highlight those in the following *Use Case section*.

## Use Case

### For [colortools.py](reference/colortools.md)

I primarily created the color tools to deal with CSS color codes. In particular, hexadecimal, rgb(), rgba(), hsl(), and hsla(). I use it to calculate whether two colors meet the color contrast guidelines.

### For [css.py](reference/css.md)

These tools are used to convert CSS code (whether from a css file or a style tag) into a Stylesheet object that contains Rulesets, Nested At-rules, Declaration blocks, and Declarations.

The css module can be used to determine whether any selectors are repeated, get data on colors that are set, determine specificity scores, check to see if a particular property is present, and more.

### For [html.py](reference/html.md)

The HTML module allows you to get and analyze what tags are present in a project, get contents from elements, find out how many particular elements were present or not.

### For [validator.py](reference/validator.md)

The validator is used to check both HTML and CSS files to see if they contain valid code or not by running the code through the W3C Validator.

## licensing
I selected to use the MIT license for this library. I selected it for three main reasons:

1. I found that the majority of the OSS (Open Source Software) licenses out there are MIT.
2. MIT is permissive and doesn't force any of my other projects to be of the same license.
3. In my webanalyst project, the majority of the licenses were also MIT, so I decided to do the same.
