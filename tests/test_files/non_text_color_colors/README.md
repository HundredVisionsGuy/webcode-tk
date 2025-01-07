# Image Gallery Project
Put your html and css files in here.

## Goal:
Students will code and design an image gallery project that contains a minimum of 9 related thumbnail-sized images that when clicked open up a full-sized version of those images. The design of the layout should be a grid of images that are styled using fonts, colors, borders, and other styles.

## Requirements
### Folder and file structure requirements
* Create a single web page named `index.html`
* Create a folder titled, `images` (all lowercase letters)
* at least 18 images in all (each stored in the images folder)
  - at least 9 full-sized images
  - at least 9 thumbnail (cropped and resized to no wider than 450px)
    + one for each of the full-sized images

### HTML requirements
* A single web page (HTML file)
* 1 or more stylesheets (a style tag can count)
* All standard HTML5 required tags (`DOCTYPE`, `html`, `head`, `title`, `body`)
* A title (using the proper tag)
* A `header` element with your title (in a `h1` tag)
* A `main` element where you'll put all your `figure` elements.
* A minimum of 9 `figure` elements
* Each `figure` element needs to contain the following
    - A thumbnail image (no wider than 450px)
        - The image tag must contain a brief description using the `alt` attribute
    - Wrap a link around the image that will link to the full-sized image
    - Add a caption after the link and image with appropriate credit given (should be a `figcaption` surrounding a `cite` tag)
    - Unless you took the image yourself, the caption should also link to the source of the image.

### Validity Requirements
* No HTML errors (this will be tested in the html tests)
* No CSS errors (this will be tested in the css tests)

### CSS Requirements
* A font pairing.
* Background color set on the page and at least 1 other color set for text.
* Any color or background color set on an element passes the AIM color contrast checker
    - Must pass at a AAA rating for any non-heading
    - May pass at a AA rating for headings
* The container uses the `flex` property and related flex properties to contribute to the layout.
* The figures are styled using the `margin`, `border`, `padding`, and `background-color` properties

### Design Requirements
* Content must be visible and readable (with high contrast)
* Images are all related in some way (through topic or theme)
* Fonts, colors, and any other styling is consistent with the theme of the images
* Layout is fluid and works on any browser/viewport width

### Assignment Submission Requirements
* Student must commit and push their changes to the repo (repo has the latest work)
* Layout should not look broken at any width
* No horizontal scrollbars should appear unless the window is more narrow that a single figure
* Student must record their image gallery at various viewport widths (or zoom levels) - best will go towards a video showing the browser being set to different screen widths.
