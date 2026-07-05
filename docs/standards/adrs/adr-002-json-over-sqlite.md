# ADR-002: Why JSON Files Over SQLite Databases

**Status:** Accepted
**Date:** 04 July 2026
**Author:** Andrea Enning

---

## Context

Most AI coding agents store sessions in SQLite databases. SQLite is fast, reliable, and embedded. But it has problems for session portability:

- You can't email a SQLite database easily
- You can't diff it in git
- You can't drag-and-drop it into a viewer
- Different databases have different schemas

## Decision

Use plain JSON files (.AgentSON) instead of SQLite.

## Consequences

### Positive
- Files are human-readable
- Files can be emailed, shared, version-controlled
- A single `json.loads()` call parses the entire session
- Works in any language, any platform, any tool

### Negative
- No indexing (search requires loading the whole file)
- Large sessions produce large files
- No built-in concurrent access

### Neutral
- For large-scale search, the CLI can build indexes from files
- Supabase provides the indexed/cloud layer when needed
- The file format is the interchange layer; the database is the scale layer
