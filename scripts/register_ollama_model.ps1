param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelName = "assamese-chatbot"
$modelTag = "$modelName`:latest"
$modelFile = Join-Path $projectRoot "Modelfile"
$gguf = Join-Path $projectRoot "models\assamese-q4_k_m.gguf"
$ollama = Get-Command ollama -ErrorAction SilentlyContinue

if (-not $ollama) {
    throw "Ollama is not installed or not on PATH. Install/update it from https://ollama.com/download, then reopen PowerShell."
}
if (-not (Test-Path -LiteralPath $gguf)) {
    throw "Local quantized model not found: $gguf. Run .\scripts\convert_merged_model.ps1 -Execute first."
}
if (-not (Test-Path -LiteralPath $modelFile)) {
    throw "Modelfile not found: $modelFile"
}

$baseUrl = if ($env:OLLAMA_BASE_URL) { $env:OLLAMA_BASE_URL.TrimEnd("/") } else { "http://localhost:11434" }
try {
    $uri = [Uri]$baseUrl
    if ($uri.Scheme -ne "http" -or -not $uri.IsLoopback) {
        throw "OLLAMA_BASE_URL must use local HTTP."
    }
    $tags = Invoke-RestMethod -Uri "$baseUrl/api/tags" -TimeoutSec 5 -MaximumRedirection 0
} catch {
    throw "Ollama API is unavailable at $baseUrl. Start Ollama and retry. $($_.Exception.Message)"
}

$existing = @($tags.models | Where-Object { $_.name -eq $modelTag -or $_.name -eq $modelName })
if ($existing.Count -gt 0 -and -not $Force) {
    throw "Model '$modelTag' already exists. To replace it intentionally, rerun with -Force."
}

Push-Location -LiteralPath $projectRoot
try {
    Write-Host "Registering the local merged GGUF as $modelTag..."
    & $ollama.Source create $modelName -f $modelFile
    if ($LASTEXITCODE -ne 0) {
        throw "ollama create failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

$show = Invoke-RestMethod -Method Post -Uri "$baseUrl/api/show" -ContentType "application/json" -Body (@{ model = $modelTag; verbose = $true } | ConvertTo-Json) -TimeoutSec 30
if ([string]::IsNullOrWhiteSpace([string]$show.template)) {
    throw "Ollama registered the model, but /api/show returned no chat template. Do not invent a template; inspect the source chat_template.jinja and GGUF metadata before using this model."
}
$registeredArchitecture = $show.details.family
if ($registeredArchitecture -and $registeredArchitecture -notin @("granite", "granitemoe", "granitehybrid")) {
    throw "Unexpected Ollama model family '$registeredArchitecture'; refusing to treat it as the intended Granite conversion."
}
Write-Host "Registered model: $modelTag; Ollama architecture family: $registeredArchitecture"
Write-Host "Embedded chat template is present; Modelfile does not override it."

$testBody = @{
    model = $modelTag
    messages = @(@{ role = "user"; content = "নমস্কাৰ! আপুনি কেনে আছে?" })
    stream = $false
    think = $false
    options = @{ num_ctx = 512; num_predict = 96; temperature = 0.1 }
} | ConvertTo-Json -Depth 8
$testResult = Invoke-RestMethod -Method Post -Uri "$baseUrl/api/chat" -ContentType "application/json" -Body $testBody -TimeoutSec 300
if (-not $testResult.message -or [string]::IsNullOrWhiteSpace([string]$testResult.message.content)) {
    throw "Ollama model registered, but the Assamese API smoke test returned an empty response."
}
if ($testResult.done -eq $false) {
    throw "Ollama model registered, but its API smoke-test response reports done=false."
}
Write-Host "Local /api/chat smoke test returned a nonempty response (done=$($testResult.done), reason=$($testResult.done_reason))."
Write-Host "Response language/quality is not verified by this deployment smoke test; the application keeps its existing validator."
