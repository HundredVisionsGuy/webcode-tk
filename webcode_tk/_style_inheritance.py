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
