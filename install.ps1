# PowerShell script to install AgentSON
# Clear problematic files and install

# Remove problematic executable files
if (Test-Path 'C:\Python312\Scripts\agentson.exe') {
    Remove-Item 'C:\Python312\Scripts\agentson.exe' -Force -ErrorAction SilentlyContinue
}
if (Test-Path 'C:\Python312\Scripts\agentson.exe.deleteme') {
    Remove-Item 'C:\Python312\Scripts\agentson.exe.deleteme' -Force -ErrorAction SilentlyContinue
}

# Install the package
python -m pip install -e . --no-deps

# agentson_mcp — browser-driven capture (optional, see ADR-022 / ADR-023).
# Required only if you intend to run `agentson browser grab|tabs|list-tools`.
# Pinned to mcp-use 1.7.0 per ADR-022.
python -m pip install mcp-use==1.7.0

# Create a simple CLI access script
$cliScriptPath = 'C:\Users\LLM-Test\Documents\AgentSON\agentson_cli.py'
if (Test-Path $cliScriptPath -PathType Leaf) {
    Write-Host "AgentSON installation complete!" -ForegroundColor Green
    Write-Host "You can now run: python agentson_cli.py [command]" -ForegroundColor Yellow
} else {
    Write-Host "Installation may have issues" -ForegroundColor Red
}
