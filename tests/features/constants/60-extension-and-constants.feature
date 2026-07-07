Feature: Extension casing and constants (ADR-011)
  constants.py is the single source of truth for the extension and glob.

  Scenario: No code path produces a .AgentSON file
    When I run every importer and reader against its real fixture
    Then every produced filename ends with lowercase ".agentson"

  Scenario: Constants module is the only place the extension is spelled
    When I grep the package source for the extension string
    Then it appears only in constants.py (plus tests and docs)

  Scenario: Search glob comes from constants
    When I run "agentson search term --dir examples"
    Then the files inspected match the constants.py glob pattern

  Scenario: Mixed-case legacy files are still readable
    Given a legacy file named "old.AgentSON" with valid content
    When I attempt to read it via documented paths
    Then the behavior matches the documented ADR-011 migration policy
