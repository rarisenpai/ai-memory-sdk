AI Memory SDK (Python)

This directory contains the Python package for the AI Memory SDK.

For usage and high-level docs, see the repository root README.md.

Quick install locally (editable):

1. From this folder:

   uv pip install -e .

2. Run offline unit tests for the context API:

   uv run pytest -q tests/test_context.py

3. Or run an example (requires LETTA_API_KEY set for networked calls):

   uv run python ../../examples/subject.py
