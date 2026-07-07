Feature: minimax and antigravity readers

  Scenario: Minimax real sample converts and validates
    Given the fixture behind "examples/minimax_example.agentson"
    When the minimax reader converts it
    Then the output validates against "spec/v1.json"

  Scenario: Antigravity real sample converts and validates
    Given the fixture behind "examples/antigravity_example.agentson"
    When the antigravity reader converts it
    Then the output validates against "spec/v1.json"

  Scenario: Minimax emitted entry types exist in the spec enum
    When the minimax reader converts its real sample
    Then every entry "type" is a member of the spec enum

  Scenario: Antigravity emitted entry types exist in the spec enum
    When the antigravity reader converts its real sample
    Then every entry "type" is a member of the spec enum
