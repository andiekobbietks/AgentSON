Feature: agentson export and list

  Scenario: Export requires --tool
    When I run "agentson export"
    Then the command exits nonzero with a usage message

  Scenario: Libre export requires --input
    When I run "agentson export --tool libre"
    Then the command exits nonzero naming the missing input

  Scenario: Export with --all writes files that validate
    Given a tool environment with at least one real session available
    When I run "agentson export --tool opencode --all --output /tmp/exp"
    Then every written file validates against "spec/v1.json"

  Scenario: List respects --limit
    Given more sessions exist than the limit
    When I run "agentson list --tool opencode --limit 2"
    Then at most 2 sessions are listed

  Scenario: List with no sessions available exits cleanly
    Given an environment with no sessions for the tool
    When I run "agentson list --tool minimax"
    Then the command exits 0 with an empty-state message, no traceback
