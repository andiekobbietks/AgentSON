"""The canonical 12 primitives, in one place.

WHY: ADR-016 fixes the primitive set at 12 and makes the ontology the source
of truth. A list that lives only in a Markdown table cannot be checked by a
test, and a test that re-declares the list is a second place for it to
drift. This module is that one place, and the tests import it.

The order is the ontology's: coordination, execution, input.
"""

CANONICAL_PRIMITIVES = (
    # Coordination
    "stream-meta",
    "handoff",
    "presence",
    "capabilities",
    # Execution
    "action",
    "observation",
    "thought",
    "side-effect",
    "answer",
    # Input
    "user-query",
    "user-feedback",
    "system-event",
)

# The three types ADR-016 demoted to metadata. They are NOT primitives.
DEMOTED_TYPES = ("context", "querying", "title")
