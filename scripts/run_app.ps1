$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$ollamaBaseUrl = if ($env:OLLAMA_BASE_URL) { $env:OLLAMA_BASE_URL.TrimEnd("/") } else { "http://localhost:11434" }
$modelName = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "assamese-chatbot:latest" }

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Error "Project environment not found. Run .\scripts\check_setup.ps1 first."
    exit 1
}

Set-Location -LiteralPath $projectRoot
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Warning "Ollama is not installed or not on PATH. The app will start, but local inference will not work."
} else {
    try {
        $apiUri = [Uri]$ollamaBaseUrl
        if ($apiUri.Scheme -ne "http" -or -not $apiUri.IsLoopback) {
            throw "OLLAMA_BASE_URL must use local HTTP."
        }
        $tags = Invoke-RestMethod -Uri "$ollamaBaseUrl/api/tags" -TimeoutSec 3 -MaximumRedirection 0
        $modelAvailable = $false
        foreach ($model in $tags.models) {
            if ($model.name -eq $modelName) {
                $modelAvailable = $true
                break
            }
        }
        if (-not $modelAvailable) {
            Write-Warning "Ollama is running, but '$modelName' is not installed. Run: .\scripts\register_ollama_model.ps1"
        }
    } catch {
        Write-Warning "Ollama's local API is unavailable or OLLAMA_BASE_URL is invalid. Start Ollama and verify the local URL; the app will still start."
    }
}

Write-Host "Starting the Assamese AI chatbot..."
& $venvPython -m streamlit run app.py --server.address=127.0.0.1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Streamlit exited with code $LASTEXITCODE. Check the messages above, verify .venv dependencies, and try .\scripts\check_setup.ps1."
    exit $LASTEXITCODE
}
