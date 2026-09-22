def detect_priority(title, description):

    text = (title + " " + description).lower()

    high_priority_words = [
        "emergency",
        "urgent",
        "danger",
        "unsafe",
        "harassment",
        "ragging",
        "fire",
        "accident",
        "no water",
        "no electricity",
        "security"
    ]

    medium_priority_words = [
        "not working",
        "problem",
        "issue",
        "delay",
        "broken",
        "complaint"
    ]

    for word in high_priority_words:
        if word in text:
            return "High"

    for word in medium_priority_words:
        if word in text:
            return "Medium"

    return "Low"