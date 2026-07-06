# PowerShell script to check project status
$ErrorActionPreference = "Stop"

# Check if we're in a git repository
if (Test-Path .git) {
    Write-Host "Git repository found" -ForegroundColor Green
    
    # Check git status
    $status = git status --porcelain
    if ($status) {
        Write-Host "Uncommitted changes:" -ForegroundColor Yellow
        Write-Host $status
    } else {
        Write-Host "Working tree clean" -ForegroundColor Green
    }
    
    # Check recent commits
    Write-Host "Recent commits:" -ForegroundColor Cyan
    git log --oneline -5
    
    # Check tags
    Write-Host "Tags:" -ForegroundColor Cyan
    git tag --list | Select-Object -First 10
    
    # Check remote tracking
    Write-Host "Remote branches:" -ForegroundColor Cyan
    git branch -r
} else {
    Write-Host "Not a git repository" -ForegroundColor Red
}

# Check project files
Write-Host "Project files:" -ForegroundColor Cyan
$keyFiles = @(\"README.md\", \"pyproject.toml\", \"CHANGELOG.md\", \"LICENSE\", \"PRD.md\")
foreach ($file in $keyFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file" -ForegroundColor Red
    }
}

# Check license file
Write-Host "License content:" -ForegroundColor Cyan
if (Test-Path \"LICENSE\") {
    $license = Get-Content -Path \"LICENSE\" -First 5
    Write-Host $license
}

# Check CHANGELOG
Write-Host "Latest CHANGELOG entry:" -ForegroundColor Cyan
if (Test-Path \"CHANGELOG.md\") {
    $latest = Select-String -Path \"CHANGELOG.md\" -Pattern \"^## v0\.1\.0\" -Context 5 -SimpleMatch
    if ($latest) {
        Write-Host $latest
    } else {
        Write-Host \"## v0.1.0 not found\" -ForegroundColor Yellow
    }
}
