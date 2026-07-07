Feature: agentson search
  cli/main.py defines cmd_search TWICE (lines ~259 and ~423); the later
  definition wins. These scenarios pin the surviving behavior so removing
  the dead one is provably safe.

  Scenario: Search finds a known term in the examples directory
    When I run "agentson search agentson --dir examples"
    Then the command exits 0
    And stdout lists at least one matching file

  Scenario: Search with no matches exits cleanly
    When I run "agentson search zzz-no-such-term-zzz --dir examples"
    Then the command exits 0
    And stdout indicates zero matches without a traceback

  Scenario: Search only inspects .agentson files
    Given a directory containing both .agentson and .json files with the term
    When I search that directory
    Then only .agentson files are reported

  Scenario: Search in a nonexistent directory fails cleanly
    When I run "agentson search term --dir /no/such/dir"
    Then the command exits nonzero without a Python traceback

  Scenario: Duplicate cmd_search removal is behavior-neutral
    Given the output of "agentson search agentson --dir examples" today
    When the dead cmd_search definition is removed
    Then the output is byte-identical
