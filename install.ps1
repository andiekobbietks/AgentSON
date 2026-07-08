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

# Create a simple CLI access script
$cliScriptPath = 'C:\Users\LLM-Test\Documents\AgentSON\agentson_cli.py'
if (Test-Path $cliScriptPath -PathType Leaf) {
    Write-Host "AgentSON installation complete!" -ForegroundColor Green
    Write-Host "You can now run: python agentson_cli.py [command]" -ForegroundColor Yellow
} else {
    Write-Host "Installation may have issues" -ForegroundColor Red
}
