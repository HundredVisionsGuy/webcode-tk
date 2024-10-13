# color_keywords.py
::: webcode_tk.cascade_tools


## Notes:

Cascade Tools was created to help with identify color contrast based on computed font sizing and background colors. It uses recursive functions to traverse the DOM and see which elements inherit various styles.

At this point, the focus has been on font sizing and colors since the color contrast tool requires knowing whether the font is large or not.

Going forward, we could check anything else that gets applied through inheritance by modifying the `CSSAppliedTree` object.

References:
    * [WebAIM's Color Contrast Checker](https://webaim.org/resources/contrastchecker/)
