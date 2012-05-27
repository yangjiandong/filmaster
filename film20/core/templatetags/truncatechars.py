from django import template

register = template.Library()

def truncatechars(value, lenght):
    """
        truncate after a certain number of characters,
        if the last character is not space truncate at the next space
    """
    le = lenght
    value = value if value is not None else ''
    if len(value) > lenght:
        try:
            if value[le] == " ":
                return value[:le]
            else:
                while value[le] != " ":
                    le += 1
                else:
                    return value[:le]

        except IndexError:
            return value[:lenght]
    else:
        return value

register.filter(truncatechars)
