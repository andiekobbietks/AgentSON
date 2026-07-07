Feature: Cross-session provenance
  session_id / parent_session_id / branched_from_entry exist to prevent
  cross-session content blending (the original AI Studio failure) and to
  make lineage reconstructable.

  Scenario: Every produced session has a unique id
    When I import the same ChatGPT export twice to different outputs
    Then both outputs carry an "id"
    And the ids identify their source deterministically per documented policy

  Scenario: Branched import records its parent
    Given a ChatGPT export containing conversation branches
    When I import with "--all-branches"
    Then branched content carries "branched_from_entry" references

  Scenario: Provenance fields survive a render round-trip
    Given a session with parent_session_id set
    When I render it to md and html
    Then the lineage information is present in the rendered output

  Scenario: Two different source sessions never blend
    Given two distinct source conversations imported in one run
    Then no output file contains entries from both sources

  Scenario: parent_session_id references are well-formed
    Given all files in "examples/"
    Then every non-null parent_session_id is a string matching the id format

  Scenario: Dogfood session demonstrates real provenance
    When I validate "examples/dogfood-session-2026-07-06.agentson"
    Then its provenance fields are populated per the dogfooding session
