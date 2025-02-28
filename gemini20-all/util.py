
from datetime import datetime
import datetime
import re


def fuzzy_date_to_date(fuzzy_date_string):
    """
    Converts fuzzy date strings like "today", "tomorrow", "yesterday", "day before yesterday" to exact datetime objects.

    Args:
      fuzzy_date_string: The fuzzy date string to convert.  Case-insensitive.

    Returns:
      A datetime object representing the date, or None if the input is not recognized.
    """

    fuzzy_date_string = fuzzy_date_string.lower()

    today = datetime.datetime.today()  # Use datetime.datetime for datetime objects

    if fuzzy_date_string == "today":
        return today
    elif fuzzy_date_string == "tomorrow":
        return today + datetime.timedelta(days=1)
    elif fuzzy_date_string == "yesterday":
        return today - datetime.timedelta(days=1)
    elif fuzzy_date_string == "day before yesterday":
        return today - datetime.timedelta(days=2)
    elif fuzzy_date_string == "next week":
        return today + datetime.timedelta(days=(7 - today.weekday()))
    elif fuzzy_date_string == "last week":
        return today - datetime.timedelta(days=(today.weekday() + 7))
    else:
        # Attempt to handle "n days ago" or "n days from now" using regex
        match = re.match(r"(\d+)\s+days?\s+(ago|from now)", fuzzy_date_string)
        if match:
            num_days = int(match.group(1))
            direction = match.group(2)
            if direction == "ago":
                return today - datetime.timedelta(days=num_days)
            elif direction == "from now":
                return today + datetime.timedelta(days=num_days)
        return None


# Example Usage:
# print(fuzzy_date_to_date("today"))
# print(fuzzy_date_to_date("Tomorrow"))  # Case-insensitive
# print(fuzzy_date_to_date("yesterday"))
# print(fuzzy_date_to_date("Day before yesterday"))
# print(fuzzy_date_to_date("5 days ago"))
# print(fuzzy_date_to_date("10 days from now"))
# print(fuzzy_date_to_date("invalid date"))
# print(fuzzy_date_to_date("next week"))
# print(fuzzy_date_to_date("last week"))