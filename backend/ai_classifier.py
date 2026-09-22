def classify_grievance(title, description):

    text = (title + " " + description).lower()

    if any(word in text for word in [
        "hostel",
        "room",
        "fan",
        "water",
        "mess",
        "warden"
    ]):
        return "Hostel"

    elif any(word in text for word in [
        "exam",
        "examination",
        "hall ticket",
        "result",
        "marks"
    ]):
        return "Examination"

    elif any(word in text for word in [
        "library",
        "book",
        "librarian"
    ]):
        return "Library"

    elif any(word in text for word in [
        "scholarship",
        "fee",
        "financial",
        "freeship"
    ]):
        return "Scholarship"

    elif any(word in text for word in [
        "class",
        "lecture",
        "faculty",
        "teacher",
        "attendance",
        "assignment"
    ]):
        return "Academic"

    elif any(word in text for word in [
        "building",
        "classroom",
        "bench",
        "electricity",
        "infrastructure"
    ]):
        return "Infrastructure"

    else:
        return "Other"