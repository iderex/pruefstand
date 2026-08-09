# A package rather than a bare directory, because `unittest discover -s harness`
# skips a directory that is not one. Without this file the engine part of the
# gate would collect nothing here, and a part that collected nothing is the
# failure `gate.py` was written to refuse.
