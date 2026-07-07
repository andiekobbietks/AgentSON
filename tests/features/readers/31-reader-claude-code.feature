Feature: claude_code reader

  Scenario: Complete real session converts and validates
    Given a complete real Claude Code session fixture
    When the reader converts it
    Then the output validates against "spec/v1.json"

  Scenario: Incomplete fixture is distinguishable from a reader bug
    Given the previously-incomplete fixture that caused the test_read_session failure
    When the reader processes it
    Then the failure mode names the fixture as incomplete
    # Encodes the lesson: the earlier failure was fixture, not reader.

  Scenario: Tool-use turns map to action entries
    Given a session where the agent invoked tools
    When the reader converts it
    Then each tool invocation appears as an "action" entry

  Scenario: Emitted entry types exist in the spec enum
    When the reader converts a real session
    Then every entry "type" is a member of the spec enum
