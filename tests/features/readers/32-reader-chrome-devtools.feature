Feature: chrome_devtools reader
  Context: Chrome 149 removed the native export button; DOM virtualisation
  can drop early turns from class-based scrapes. The reader must be honest
  about partial captures.

  Scenario: Real DevTools session converts and validates
    When the reader converts "examples/devtools_download_this_video_in_the_scene.agentson" source material
    Then the output validates against "spec/v1.json"

  Scenario: Partial capture is not silently presented as complete
    Given a DevTools capture missing early conversation turns
    When the reader converts it
    Then the output or stderr flags the capture as potentially partial

  Scenario: Code-execution turns become action entries with output
    Given a session where DevTools AI ran console code
    When the reader converts it
    Then each execution appears as an "action" entry carrying its output

  Scenario: Emitted entry types exist in the spec enum
    When the reader converts a real session
    Then every entry "type" is a member of the spec enum
