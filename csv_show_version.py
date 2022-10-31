import sys

version = 0.9
min_python_version = {"major": 3, "minor": 6, "micro": 0}
current_python_version = {"major": sys.version_info.major, "minor": sys.version_info.minor,
                          "micro": sys.version_info.micro}


def version_check():
    fail = ((current_python_version["major"] < min_python_version["major"]) or
            (current_python_version["major"] == min_python_version["major"] and current_python_version["minor"] <
             min_python_version[
                 "minor"]) or
            (current_python_version["major"] == min_python_version["major"] and current_python_version["minor"] ==
             min_python_version[
                 "minor"] and current_python_version["micro"] < min_python_version["micro"]))
    ok = not fail
    return ok


