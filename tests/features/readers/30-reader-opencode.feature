Feature: opencode reader
  Built around the v0.1.1 silent-reasoning-drop regression and the real
  sample already used by test_opencode_real_sample.py.

  Scenario: Reasoning parts are preserved, never silently dropped (v0.1.1 regression)
    Given an opencode session export containing reasoning parts
    When the opencode reader converts it
    Then every reasoning part appears as an entry in the output
    And no part types are dropped without an explicit warning

  Scenario: Real reference export converts and validates
    Given the real opencode sample used by the existing test suite
    When the reader converts it
    Then the output validates against "spec/v1.json"

  Scenario: Reader output matches shipped example shape
    When the reader converts the real sample
    Then the output's top-level keys match "examples/opencode_example.agentson"

  Scenario: Session with zero assistant turns
    Given an opencode session containing only user messages
    When the reader converts it
    Then the command exits 0 and output validates

  Scenario: Unknown part type is surfaced, not swallowed
    Given an opencode session containing an unrecognized part type
    When the reader converts it
    Then a warning names the unrecognized type
    And the entry is preserved or skipped per documented policy, not silently

  Scenario: Emitted entry types exist in the spec enum
    When the reader converts the real sample
    Then every entry "type" value is a member of the spec/v1.json enum
    # Pins the ADR-014 observation mismatch from the reader side.
