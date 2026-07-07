Feature: agentson import chatgpt
  Regression suite built from the three real v0.1.0 bugs plus core behavior.

  Scenario: Module is importable at all (v0.1.0 IndentationError regression)
    When I run "python -c 'import importers.chatgpt'"
    Then the command exits 0

  Scenario: Import a real ChatGPT export
    When I run "agentson import chatgpt examples/chatgpt_export.json --output /tmp/out"
    Then the command exits 0
    And a file matching "/tmp/out/chatgpt_*.agentson" exists
    And that file validates against "spec/v1.json"

  Scenario: Null message node does not crash (v0.1.0 _detect_model regression)
    Given a ChatGPT export fixture containing a node with a null "message"
    When I import it
    Then the command exits 0
    And no Python traceback is printed

  Scenario: Entry count is reported and non-zero for a real export
    When I run "agentson import chatgpt examples/chatgpt_export.json --output /tmp/out"
    Then stdout contains "Entries:"
    And the reported entry count is greater than 0

  Scenario: All-branches flag includes branched turns
    When I import "examples/chatgpt_full_export.json" with "--all-branches"
    And I import the same file without "--all-branches"
    Then the all-branches output has greater than or equal entry count

  Scenario: Unknown import format exits nonzero with a clear error
    When I run "agentson import notachat something.json"
    Then the command exits with a nonzero status
    And stderr does not contain a Python traceback

  Scenario: Missing input file fails cleanly
    When I run "agentson import chatgpt /nonexistent/file.json"
    Then the command exits with a nonzero status
    And stderr does not contain a Python traceback

  Scenario: Output uses lowercase .agentson extension (ADR-011)
    When I import "examples/chatgpt_export.json" to "/tmp/out"
    Then the created filename ends with ".agentson"
    And no file ending in ".AgentSON" is created
