"""Compatibility launcher for the PM GUI.

The old wizard silently downloaded HOT TM AOI/task files. That workflow is
intentionally retired: the PM-facing application now opens the official
endpoints and lets the user download/select the exact files being audited.
"""

import app


if __name__ == "__main__":
    app.App().mainloop()
