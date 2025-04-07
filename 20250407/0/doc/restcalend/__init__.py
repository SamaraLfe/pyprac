"""
restcalend Module
================

This module provides functionality to generate a reStructuredText (reST) table for a given month's calendar,
where the 1st day of the month is assumed to be a Monday.

Example usage:
    >>> from restcalend import restmonth
    >>> print(restmonth(2024, 4))
    .. table:: April 2024

        == == == == == == ==
        Mo Tu We Th Fr Sa Su
        == == == == == == ==
         1  2  3  4  5  6  7
         8  9 10 11 12 13 14
        15 16 17 18 19 20 21
        22 23 24 25 26 27 28
        29 30
        == == == == == == ==
"""

import calendar


def restmonth(year, month):
    """
    Generate a reStructuredText table for a given month's calendar.

    Args:
        year (int): The year of the calendar.
        month (int): The month of the calendar (1-12).

    Returns:
        str: A string containing the reST table for the month.

    Note:
        Assumes the 1st day of the month is a Monday.
    """
    month_name = calendar.month_name[month]
    table = f".. table:: {month_name} {year}\n\n"
    table += "    == == == == == == ==\n"
    table += "    Mo Tu We Th Fr Sa Su\n"
    table += "    == == == == == == ==\n"

    # Generate days (assuming 1st is Monday)
    days = calendar.monthrange(year, month)[1]
    week = []
    for day in range(1, days + 1):
        week.append(f"{day:2}")
        if len(week) == 7 or day == days:
            table += "    " + " ".join(week) + " " * (7 - len(week)) * 2 + "\n"
            week = []
    table += "    == == == == == == =="
    return table