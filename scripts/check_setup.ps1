$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelName = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "assamese-chatbot:latest" }
$ollamaBaseUrl = if ($env:OLLAMA_BASE_URL) { $env:OLLAMA_BASE_URL.TrimEnd("/") } else { "http://localhost:11434" }

Write-Host "Checking the Assamese AI chatbot setup..."

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python was not found. Install Python 3.10 or newer, enable the Python PATH option, then rerun this script."
}
$pythonVersionText = python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0) {
    throw "Python was found but could not be started. Check the Python installation and PATH."
}
$pythonVersion = [version]$pythonVersionText
if ($pythonVersion -lt [version]"3.10") {
    throw "Python 3.10 or newer is required; found Python $pythonVersionText."
}
Write-Host "Python $pythonVersionText"

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating the project virtual environment..."
    python -m venv (Join-Path $projectRoot ".venv")
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Could not create .venv. Check that your Python installation includes the venv module."
}

Write-Host "Installing project dependencies into .venv..."
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed. Check your internet connection and rerun scripts\check_setup.ps1."
}

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Warning "Ollama is not installed or is not on PATH. Install it from https://ollama.com/download, then reopen PowerShell."
    Write-Host "After installing Ollama, create the local merged model with:"
    Write-Host "  .\scripts\register_ollama_model.ps1"
    exit 0
}

try {
    $apiUri = [Uri]$ollamaBaseUrl
    if ($apiUri.Scheme -ne "http" -or -not $apiUri.IsLoopback) {
        throw "OLLAMA_BASE_URL must use local HTTP."
    }
} catch {
    Write-Warning "OLLAMA_BASE_URL must be an HTTP loopback address such as http://localhost:11434."
    exit 0
}

try {
    $tags = Invoke-RestMethod -Uri "$ollamaBaseUrl/api/tags" -TimeoutSec 5 -MaximumRedirection 0
} catch {
    Write-Warning "Ollama is installed, but its local API is not reachable at $ollamaBaseUrl."
    Write-Host "Start the Ollama application and rerun this script."
    exit 0
}

$available = $false
foreach ($model in $tags.models) {
    if ($model.name -eq $modelName) {
        $available = $true
        break
    }
}
if ($available) {
    Write-Host "Ollama is running and model '$modelName' is installed."
} else {
    Write-Warning "Ollama is running, but model '$modelName' is not installed."
    Write-Host "Create the local merged model with:"
    Write-Host "  .\scripts\register_ollama_model.ps1"
}
