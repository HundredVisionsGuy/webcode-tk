# My Website Project
Put your html file/s in here.

## I Recommend the Following Strategy for building a website
I recommend you start with all the layout markup including `header`, `nav`, `article` (or `section`), and `footer` BEFORE you add the content of the site.

Once you do that, then, you should configure the `nav` and create your list of links inside. In fact, I always go so far is to creating links to every page before I've even created those pages. That way, you can use that single file to create all your other pages using the "File > Save As" method and naming each file you plan to create.

## Required Elements
### HTML Main Requirements
* Standard HTML Tags - there should be one for each page (no more no less)
    - `DOCTYPE`
    - `html`
    - `head`
    - `title`
* Other required tags (see minimum #)
    - `h1` -> one per page (in the header)
    - `header` -> one per page
    - `nav`  -> one (could be in the header or by itself)
    - `ul` -> at least one per page (inside the nav)
    - `li` -> at least 4 per page (inside the ul that's in the nav)
    - `a` -> at least 4 per page (inside each li inside the ul that's in the nav)
    - `section` OR `article` -> at least 1 per page
    - `h2` -> two (in the section or article)
    - `p`  -> at least 5 per page (in the section or article and at least 1 in the footer)
    - `footer` -> at least 1 per page

### Validity Requirements
* No HTML errors are allowed

### CSS Requirements
* Do NOT use style attributes in your HTML - only use a style tag in the head or an external stylesheet.
* Fonts:
    - Apply either a font or font-pair other than Times New Roman or Comic Sans
    - IMPORTANT NOTE ON TYPOGRAPHY AND READABILITY:
        + in design, the font you choose might hurt readability
        + avoid making all paragraph text bold because it makes content difficult to read
        + all bold test doesn't highlight key information effectively.
        + Instead, use bolding sparingly for emphasis on important words or phrases, balance it with regular text, and use semantic HTML like `<strong>` for accessibility.

* Colors:
    - ALL COLORS must meet [WebAIM color contrast](https://webaim.org/resources/contrastchecker/) goals at the ***"WCAG AAA"*** rating
    - Apply a **background color** to the page (through the body or html)
    - Apply a **color** to the text (through the body or html)
    - Apply a **color** to hyperlinks (to both the link and visited - hover is optional)
    - Add **padding** to any of the following layout elements if present (`header`, `nav`, `main`, `article`, `aside`, `hgroup` `section`, `footer`).

NOTE: to check for errors, be sure to upload your HTML file to the [W3C File Upload Validator](https://validator.w3.org/#validate_by_upload)
