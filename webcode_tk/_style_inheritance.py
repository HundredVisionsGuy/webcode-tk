"""
_style_inheritance.py
By Chris Winikka

Internal utiliities for computing CSS inheritance.

This module provides optimized functions for computing CSS inheritance and
visual background inheritance during contrast analysis. It is used internally
by contrast_tools and is not part of the public API.

Functions:
    apply_css_inheritance: Apply inheritable CSS properties top-down through
        DOM.
    apply_visual_background_inheritance: Propagate background colors via
        ancestry.
    find_ancestor_background: Locate first ancestor with explicit background.
    apply_inheritance: Wrapper combining CSS and visual inheritance.
"""

import re

from bs4 import Tag

DEFAULT_GLOBAL_BACKGROUND = "#ffffff"


def apply_css_inheritance(computed_styles: dict) -> None:
    """
    Apply CSS inheritance top-down (parent to children) instead of bottom-up.

    This is MUCH faster than walking up the tree for each element.
    O(n) instead of O(n*m*h) where n=elements, m=properties, h=tree_depth
    """
    inheritable_props = {"color", "font-size", "font-weight"}

    # Build parent-child relationships
    parent_to_children = {}
    child_to_parent = {}

    for element in computed_styles:
        parent = element.parent
        if parent and parent in computed_styles:
            if parent not in parent_to_children:
                parent_to_children[parent] = []
            parent_to_children[parent].append(element)
            child_to_parent[element] = parent

    # Process top-down: parent values flow to children
    visited = set()

    def traverse_tree(element, inherited_props_from_ancestors):
        """DFS traversal pushing inherited values down."""
        if element in visited:
            return
        visited.add(element)

        if element not in computed_styles:
            return

        element_styles = computed_styles[element]
        props_for_children = inherited_props_from_ancestors.copy()

        # For each inheritable property
        for prop in inheritable_props:
            current_prop = element_styles.get(prop)

            # If element has explicit rule, use it (don't inherit)
            if current_prop and current_prop.get("source") == "rule":
                props_for_children[prop] = current_prop
            # Otherwise inherit from ancestor if available
            elif prop in inherited_props_from_ancestors:
                inherited_value = inherited_props_from_ancestors[prop]
                element_styles[prop] = {
                    "value": inherited_value["value"],
                    "specificity": inherited_value["specificity"],
                    "source": "inheritance",
                    "selector": inherited_value.get("selector", "inherited"),
                    "css_file": inherited_value.get("css_file"),
                    "css_source_type": inherited_value.get("css_source_type"),
                    "inherited_from": child_to_parent.get(element),
                }
                # Also pass inherited value to children
                props_for_children[prop] = element_styles[prop]

        # Recurse to children with updated inherited values
        if element in parent_to_children:
            for child in parent_to_children[element]:
                traverse_tree(child, props_for_children)

    # Start traversal from root elements (with no parent in computed_styles)
    for element in computed_styles:
        if element not in child_to_parent:
            # This is a root element
            traverse_tree(element, {})


def apply_visual_background_inheritance(computed_styles: dict) -> None:
    """
    Apply visual background colors to elements without explicit backgrounds.

    Args:
        computed_styles: a dictionary of elements with computed styles.
    Returns:
        None
    """

    for element in computed_styles:
        element_styles = computed_styles[element]

        # Check for BOTH background-color AND background
        current_bg = element_styles.get("background-color")
        has_background_shorthand = "background" in element_styles

        # If element has background shorthand, process it for images
        if has_background_shorthand:
            bg_value = element_styles["background"]["value"]

            # Check if background contains a raster image
            if contains_raster_image(bg_value):
                # Mark as contrast-indeterminate - cannot analyze
                element_styles["background-color"] = {
                    "value": None,
                    "specificity": "000",
                    "contrast_analysis": "indeterminate",
                    "reason": "background_image_blocks_color_analysis",
                    "original_background": bg_value,
                    "visual_inheritance": False,
                }
                continue
            else:
                # Has usable background shorthand - skip inheritance
                continue
        if not current_bg:
            continue

        bg_source = current_bg.get("source")
        bg_value = current_bg.get("value")

        # Skip elements with explicit CSS rules
        if bg_source == "rule":
            continue

        # Only update elements that still have the default white background
        # This prevents overwriting elements with existing proper backgrounds
        if bg_source != "default":
            continue

        # Element needs background inheritance (lines 1120-1141)
        ancestor_bg = find_ancestor_background(element, computed_styles)

        if not ancestor_bg or ancestor_bg.get("source") == "default":
            # No explicit background to inherit - keep browser default
            continue

        if ancestor_bg.get("contrast_analysis") == "indeterminate":
            # Ancestor is indeterminate - propagate that status
            element_styles["background-color"] = {
                "value": None,
                "specificity": "000",
                "contrast_analysis": "indeterminate",
                "reason": ancestor_bg["reason"],
                "inherited_from": ancestor_bg["source_element"],
                "source": "visual_inheritance",
                "original_background": ancestor_bg.get("original_background"),
            }

        else:
            # Normal inheritance - extract usable color
            contrast_color = extract_contrast_color(ancestor_bg["value"])
            effective_color = (
                contrast_color if contrast_color else ancestor_bg["value"]
            )
            element_styles["background-color"] = {
                "value": effective_color,
                "specificity": "000",
                "source": "visual_inheritance",
                "inherited_from": ancestor_bg["source_element"],
                "contrast_analysis": "determinable",
                "original_background": (
                    ancestor_bg["value"]
                    if ancestor_bg["value"] != DEFAULT_GLOBAL_BACKGROUND
                    else None
                ),
            }


def contains_raster_image(background_value: str) -> bool:
    """Check if background contains a raster image that blocks color analysis.

    Args:
        background_value: the css value applied to the background property.

    Returns:
        bool: whether the background value includes a raster image or not.
    """
    # Add None check
    if background_value is None:
        return False

    return bool(
        re.search(
            r"url\([^)]*\.(jpg|jpeg|png|gif|webp|bmp)", background_value, re.I
        )
    )


def extract_contrast_color(background_value: str) -> str:
    """
    Extract usable color for contrast analysis, or None.

    Args:
        background_value (str): CSS background property value.

    Returns:
        str: Color value suitable for contrast analysis, or None if no
            usable color found.
    """
    # Add None check at the beginning
    if background_value is None:
        return None

    # Remove raster images - they block color visibility
    if re.search(
        r"url\([^)]*\.(jpg|jpeg|png|gif|webp|bmp)", background_value, re.I
    ):
        return None

    # Handle gradients - extract representative color
    if "gradient" in background_value.lower():
        return extract_gradient_contrast_color(background_value)

    # Handle solid colors
    re_pattern = r"(#[a-f0-9]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)|hsl\([^)]+\)|"
    re_pattern += r"hsla\([^)]+\)|[a-z]+)"
    color_match = re.search(
        re_pattern,
        background_value,
        re.I,
    )
    return color_match.group(1) if color_match else None


def find_ancestor_background(element: Tag, computed_styles: dict) -> dict:
    """
    Walk up DOM tree to find first ancestor with background.

    Args:
        element (Tag): BeautifulSoup Tag object to start searching from.
        computed_styles (dict): Dictionary mapping elements to their
            computed styles.

    Returns:
        dict: Dictionary containing 'value' (background color) and
            'source_element' (ancestor element or None).
    """
    current = element.parent

    while current:
        if current in computed_styles:
            current_styles = computed_styles[current]

            # Flag to track if we should skip this ancestor
            skip_ancestor = False

            # Check for background-color or background
            for bg_prop in ["background-color", "background"]:
                if bg_prop in current_styles:
                    bg_source = current_styles[bg_prop].get("source")

                    # Skip elements that only have visual inheritance
                    if bg_source == "visual_inheritance":
                        skip_ancestor = True
                        break  # ✅ Break out of property loop

                    # Accept both "rule" and "default" sources
                    if bg_source in ["rule", "default"]:
                        bg_value = current_styles[bg_prop]["value"]
                        if bg_source == "default":
                            # Skip ancestors with only default backgrounds
                            skip_ancestor = True
                            break

                        # Does this ancestor already is indeterminate status
                        if (
                            current_styles[bg_prop].get("contrast_analysis")
                            == "indeterminate"
                        ):
                            return {
                                "value": None,
                                "source_element": current,
                                "contrast_analysis": "indeterminate",
                                "reason": "ancestor_has_background_image",
                                "original_background": current_styles[
                                    bg_prop
                                ].get("original_background", bg_value),
                            }

                        # Skip None values and continue searching
                        if bg_value is None:
                            continue  # Continue to next property

                        # Check if this background contains a raster image
                        if contains_raster_image(bg_value):
                            return {
                                "value": None,
                                "source_element": current,
                                "contrast_analysis": "indeterminate",
                                "reason": "ancestor_has_background_image",
                                "original_background": bg_value,
                            }

                        # Found explicit background
                        bg_items = current_styles[bg_prop].items()
                        return {
                            "value": bg_value,
                            "source_element": current,
                            "contrast_analysis": "determinable",
                            # Copy metadata from ancestor
                            **{
                                metadata_key: metadata_value
                                for metadata_key, metadata_value in bg_items
                                if metadata_key not in ["value"]
                            },
                        }

            # If we flagged this ancestor to skip, move to next ancestor
            if skip_ancestor:
                current = current.parent
                continue  # ✅ Now this continues to next ancestor

        current = current.parent

    # No ancestor background found, use default
    return {
        "value": DEFAULT_GLOBAL_BACKGROUND,
        "source_element": None,
        "contrast_analysis": "determinable",
        "source": "default",
    }


def extract_gradient_contrast_color(background_value: str) -> str:
    """
    Extract representative color from gradient for contrast analysis.

    Args:
        background_value (str): CSS gradient value (e.g.,
            'linear-gradient(red, blue)').

    Returns:
        str: Representative color for contrast analysis, or None if no
            color found.
    """
    # Add None check
    if background_value is None:
        return None

    # Strategy: Use the final color in gradient (most visible for reading)
    # This handles: linear-gradient(red, blue) -> blue
    #              radial-gradient(center, red, blue) -> blue

    # Find all colors in gradient
    color_pattern = r"(#[a-f0-9]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)|"
    color_pattern += r"hsl\([^)]+\)|hsla\([^)]+\)|[a-z]+)"
    colors = re.findall(color_pattern, background_value, re.I)

    if colors:
        # Use last color (end of gradient)
        return colors[-1]

    return None
