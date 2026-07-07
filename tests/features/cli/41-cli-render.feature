Feature: agentson render

  Scenario: Render real session to markdown (default)
    When I run "agentson render examples/dogfood-session-2026-07-06.agentson"
    Then the command exits 0
    And stdout or the output file contains markdown headings

  Scenario: Render to html
    When I run "agentson render examples/mcp_demo.agentson --format html"
    Then the command exits 0
    And the output contains an html document structure

  Scenario: Render honors --output
    When I run "agentson render examples/mcp_demo.agentson --format md --output /tmp/r.md"
    Then "/tmp/r.md" exists and is non-empty

  Scenario: Every entry type renders without crashing
    Given a session containing one entry of every spec type
    When I render it in both formats
    Then both commands exit 0

  Scenario: Render rejects an invalid file cleanly
    Given a file that is valid JSON but not a valid session
    When I render it
    Then the command exits nonzero without a Python traceback

  Scenario: Rendered output does not execute embedded content
    Given a session whose answer text contains "<script>alert(1)</script>"
    When I render it to html
    Then the script content is escaped in the output
