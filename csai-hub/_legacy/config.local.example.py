# Example local configuration file
# Copy this to config.local.py and customize for your setup
#
# This file is gitignored, so your local paths won't be committed

from pathlib import Path

# Set your materials paths here
# These can be directories (all supported files will be indexed)
# or specific files

MATERIALS_PATHS = [
    # Example: A folder with lecture PDFs
    Path.home() / "Documents" / "statistics" / "lectures",

    # Example: A folder with lecture transcripts
    Path.home() / "Documents" / "statistics" / "transcripts",

    # Example: A specific study guide file
    Path.home() / "Documents" / "statistics" / "STUDY_GUIDE.md",
]
