# Schedule auto-export of OpenCode sessions
# Run this script to set up a scheduled task

$taskName = "AgentSON Auto-Export"
$scriptPath = "C:\Users\LLM-Test\Documents\AgentSON\scripts\auto_export.py"
$pythonPath = "C:\Python312\python.exe"

# Create the action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "$scriptPath --output C:\Users\LLM-Test\Documents\AgentSON\examples"

# Create trigger (every hour)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Auto-export OpenCode sessions to .agentson format"

Write-Host "Scheduled task '$taskName' created successfully!"
Write-Host "The task will run every hour to export new sessions."
