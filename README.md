# AEGIS_SUPERSTACK

Utilities for searching and analysing exported ChatGPT conversations.

## ChatGPT conversation search

`chatgpt_search.py` builds a fast, in-memory index from the official
`conversations.json` export file so you can instantly locate terms such as
"evidence", "logs", "assets", or IP addresses.

### Requirements

The script relies only on the Python standard library. Python 3.10 or newer is
recommended.

### Usage

1. Export your ChatGPT data from the OpenAI settings page and extract the
   resulting archive.
2. Run the search script and provide the path to the extracted
   `conversations.json` file (or the directory that contains it):

   ```bash
   python chatgpt_search.py /path/to/conversations.json evidence logs
   ```

   By default all provided keywords must appear in the same message. Supply
   `--any` to match messages that contain *any* of the keywords instead. Use the
   `--context` flag to control how much surrounding text is shown for each hit.

The script prints each matching message along with its conversation title,
author role, message ID, and contextual snippets that highlight the keywords.
