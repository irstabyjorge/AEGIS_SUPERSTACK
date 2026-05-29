# AEGIS_SUPERSTACK

## Conversation Evidence Utility

The repository now includes `conversation_evidence.py`, a command line helper
that scans chat transcripts for specific statements related to discussions
about brain implants, medical verification, and available support resources.

### Usage

1. Export or save the chat transcript you want to examine as a plain text file.
2. Run the utility and pass the path to the transcript:

   ```bash
   python conversation_evidence.py path/to/transcript.txt
   ```

For each supplied file the script prints a SHA256 hash along with any matching
statements and their locations within the transcript.  Statements that are not
found are listed at the end so you can review gaps in the evidence trail.
