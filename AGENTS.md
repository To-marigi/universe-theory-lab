# Repository instructions

## Research-source preservation

When internet pages, papers, datasets, or external technical documentation materially inform
work in this repository:

1. Search `references/sources.json`, `references/manifest.json`, `references/text/`, and
   `references/notes/` before repeating online research.
2. Save a legally accessible, version-specific local copy under `references/papers/` when
   practical. Never bypass authentication, subscriptions, or access controls.
3. Add its bibliography, exact URL, retrieval date, local filename, use, and claim boundary to
   `references/sources.json`.
4. Run `scripts/archive_references.py` to validate PDFs, refresh SHA-256 hashes, and create
   searchable text. If `pypdf` is unavailable, use `--skip-text` and record the limitation.
5. Add a concise research note when interpretation or scientific judgment affects implementation.
6. Do not overwrite an older paper version with a newer one. Preserve both with explicit version
   names.
7. Treat extracted text as a search aid; verify equations, figures, and page layout in the PDF.
8. Keep source claims, independent project derivations, and unresolved gaps explicitly separate.
