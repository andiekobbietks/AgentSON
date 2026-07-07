Feature: copilot_chat reader — including path traversal regression
  A real path-traversal vulnerability was found and fixed here (verified
  with a live reproduction). These scenarios keep it fixed.

  Scenario: Path traversal in session-derived filenames is blocked
    Given a copilot chat export whose session name contains "../../etc/passwd"
    When the reader converts it with output directory "/tmp/safe"
    Then no file is written outside "/tmp/safe"
    And the command exits without writing to a traversed path

  Scenario: Absolute path injection is blocked
    Given a copilot chat export whose session name contains "/etc/cron.d/evil"
    When the reader converts it with output directory "/tmp/safe"
    Then no file is written outside "/tmp/safe"

  Scenario: Model and provider fields come from the export, not hardcoded
    Given a real copilot chat export declaring its model and provider
    When the reader converts it
    Then the output tool/model fields match the export's declared values
    # Pins the hardcoded-fields fix from the CodeRabbit review round.

  Scenario: Real reference export converts and validates
    Given a real copilot chat export
    When the reader converts it
    Then the output validates against "spec/v1.json"

  Scenario: Hostile filename characters are sanitized
    Given a session name containing null bytes and newline characters
    When the reader converts it
    Then the written filename contains neither
