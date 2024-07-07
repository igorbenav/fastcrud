def compute_offset(page: int, items_per_page: int) -> int:
    """Calculate the offset for pagination based on the given page number and items per page.

    The offset represents the starting point in a dataset for the items on a given page.
    For example, if each page displays 10 items and you want to display page 3, the offset will be 20,
    meaning the display should start with the 21st item.

    Args:
        page: The current page number. Page numbers should start from 1.
        items_per_page: The number of items to be displayed on each page.

    Returns:
        The calculated offset.

    Examples:
        >>> offset(1, 10)
        0
        >>> offset(3, 10)
        20
    """
    return (page - 1) * items_per_page
