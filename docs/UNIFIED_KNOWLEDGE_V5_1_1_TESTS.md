# Unified Knowledge v5.1.1 Portable Tests

Run:
`python -m unittest discover -s recovery/unified-knowledge-v5_1_1 -p "test_*.py" -v`

The verifier resolves stale recorded paths by SHA-256 only inside the package's own `library_source/`.
