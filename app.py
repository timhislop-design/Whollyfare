"""
app.py — WhollyFare repo root entry point.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠  DO NOT use this file as the Streamlit entrypoint.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The correct Streamlit main file is:

    ui/Home.py

  ● Locally:      streamlit run ui/Home.py
  ● Streamlit Cloud → Settings → Main file path → ui/Home.py

Running app.py directly breaks st.page_link() / st.switch_page()
because Streamlit builds its multipage registry relative to the
main script's directory. With app.py as the entry, it looks for
pages/ at the repo root instead of ui/pages/.

There is nothing else in this file — point Streamlit at ui/Home.py.
"""

import sys
from pathlib import Path

print(
    "\n[WhollyFare] ⚠  Run Streamlit from the correct entry point:\n"
    "    streamlit run ui/Home.py\n"
    "or set Main file path = 'ui/Home.py' in Streamlit Cloud settings.\n",
    file=sys.stderr,
)

raise SystemExit(
    "Wrong entry point. Use:  streamlit run ui/Home.py"
)
