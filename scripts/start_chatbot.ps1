$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelName = "assamese-q4-k-m"
$baseUrl = if ($env:LLAMA_CPP_BASE_URL) { $env:LLAMA_CPP_BASE_URL.TrimEnd("/") } else { "http://127.0.0.1:8081" }
$contextSize = 1024
$parallelRequests = 1
$batchSize = 32
$microBatchSize = 16
$gpuLayers = 0
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$modelPath = Join-Path $projectRoot "models\assamese-corrected-q4_k_m.gguf"
$llamaRoot = Join-Path $projectRoot "tools\llama.cpp-bin-b12032"
$serverPath = Join-Path $llamaRoot "llama-server.exe"
$ggufPython = Join-Path $projectRoot "tools\llama.cpp\gguf-py"
$ggufCheck = Join-Path $PSScriptRoot "check_gguf_model.py"
$logsDirectory = Join-Path $projectRoot "logs"
$serverProcess = $null
$streamlitProcess = $null
$startedServer = $false
$startedStreamlit = $false

function Test-LocalApiUri([string]$Address) {
    $parsed = [Uri]$Address
    if ($parsed.Scheme -ne "http" -or -not $parsed.IsLoopback -or $parsed.AbsolutePath -ne "/") {
        throw "LLAMA_CPP_BASE_URL must be a local HTTP loopback URL such as http://127.0.0.1:8081."
    }
}

function Get-LoadedModelId([string]$Address) {
    $models = Invoke-RestMethod -Uri "$Address/v1/models" -TimeoutSec 5 -MaximumRedirection 0
    if (-not $models.data) {
        return $null
    }
    foreach ($entry in $models.data) {
        if ($entry.id -eq $modelName) {
            return $entry.id
        }
    }
    return $null
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Project virtual environment is missing. Run .\scripts\check_setup.ps1 first."
}
if (-not (Test-Path -LiteralPath $modelPath)) {
    throw "Fine-tuned GGUF not found: $modelPath. The app will not fall back to another model."
}
if (-not (Test-Path -LiteralPath $serverPath)) {
    throw "Bundled llama.cpp server is missing: $serverPath."
}
if (-not (Test-Path -LiteralPath $ggufCheck)) {
    throw "GGUF metadata validator not found: $ggufCheck."
}
$operatingSystem = Get-CimInstance Win32_OperatingSystem
$availableMemoryGiB = $operatingSystem.FreePhysicalMemory / 1MB
if ($availableMemoryGiB -lt 3) {
    throw "Only $([math]::Round($availableMemoryGiB, 2)) GiB of physical RAM is available. Close memory-heavy applications yourself and retry when at least 3 GiB is free."
}
Test-LocalApiUri $baseUrl

Set-Location -LiteralPath $projectRoot
& $venvPython $ggufCheck --model $modelPath --gguf-python $ggufPython
if ($LASTEXITCODE -ne 0) {
    throw "GGUF metadata validation failed; refusing to start inference."
}

try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 3 -MaximumRedirection 0
    $loadedModel = Get-LoadedModelId $baseUrl
    if ($health.status -eq "ok" -and $loadedModel -eq $modelName) {
        Write-Host "Using the already-running llama.cpp server and model '$modelName'."
    } else {
        throw "Another service is listening on $baseUrl without the expected model alias '$modelName'. Stop that service or choose another LLAMA_CPP_BASE_URL."
    }
} catch [System.Net.WebException] {
    $healthUnavailable = $true
} catch {
    if ($_.Exception.Message -like "*No connection could be made*" -or $_.Exception.Message -like "*actively refused*") {
        $healthUnavailable = $true
    } else {
        throw
    }
}

if ($healthUnavailable) {
    if (Get-NetTCPConnection -LocalPort $([Uri]$baseUrl).Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $(([Uri]$baseUrl).Port) is occupied, but it is not the expected llama.cpp server. No existing process was stopped."
    }
    New-Item -ItemType Directory -Path $logsDirectory -Force | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $stdoutLog = Join-Path $logsDirectory "llama-server-$stamp.stdout.log"
    $stderrLog = Join-Path $logsDirectory "llama-server-$stamp.stderr.log"
    $port = ([Uri]$baseUrl).Port
    $serverArguments = "--model `"$modelPath`" --ctx-size $contextSize --n-gpu-layers $gpuLayers --threads 4 --threads-batch 2 --batch-size $batchSize --ubatch-size $microBatchSize --parallel $parallelRequests --alias $modelName --host 127.0.0.1 --port $port --no-webui --jinja"
    Write-Host "Starting the local fine-tuned GGUF with llama.cpp (CPU inference, context $contextSize, batch $batchSize, micro-batch $microBatchSize, parallel $parallelRequests)."
    $serverProcess = Start-Process `
        -FilePath $serverPath `
        -ArgumentList $serverArguments `
        -WorkingDirectory $llamaRoot `
        -PassThru `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog
    $startedServer = $true

    $serverReady = $false
    try {
        for ($attempt = 0; $attempt -lt 240; $attempt++) {
            if ($serverProcess.HasExited) {
                $logTail = if (Test-Path $stderrLog) { (Get-Content $stderrLog -Tail 60) -join "`n" } else { "(no server stderr log)" }
                throw "llama.cpp exited during model loading with code $($serverProcess.ExitCode). Log: $stderrLog`n$logTail"
            }
            try {
                $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 2 -MaximumRedirection 0
                $loadedModel = Get-LoadedModelId $baseUrl
                if ($health.status -eq "ok" -and $loadedModel -eq $modelName) {
                    $serverReady = $true
                    break
                }
            } catch {
                Start-Sleep -Seconds 2
            }
        }
        if (-not $serverReady) {
            $logTail = if (Test-Path $stderrLog) { (Get-Content $stderrLog -Tail 60) -join "`n" } else { "(no server stderr log)" }
            throw "llama.cpp did not load the expected model within 8 minutes. Log: $stderrLog`n$logTail"
        }
    } catch {
        if ($startedServer -and $serverProcess -and -not $serverProcess.HasExited) {
            Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
        }
        throw
    }
    Write-Host "The exact local GGUF is loaded and healthy at $baseUrl."
}

try {
    $env:LLAMA_CPP_BASE_URL = $baseUrl
    $env:LLAMA_CPP_MODEL = $modelName
    New-Item -ItemType Directory -Path $logsDirectory -Force | Out-Null
    $appStamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $appStdoutLog = Join-Path $logsDirectory "streamlit-$appStamp.stdout.log"
    $appStderrLog = Join-Path $logsDirectory "streamlit-$appStamp.stderr.log"
    $streamlitProcess = Start-Process `
        -FilePath $venvPython `
        -ArgumentList "-m streamlit run app.py --server.address=127.0.0.1 --server.headless=true" `
        -WorkingDirectory $projectRoot `
        -PassThru `
        -RedirectStandardOutput $appStdoutLog `
        -RedirectStandardError $appStderrLog
    $startedStreamlit = $true

    $appReady = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($streamlitProcess.HasExited) {
            $logTail = if (Test-Path $appStderrLog) { (Get-Content $appStderrLog -Tail 40) -join "`n" } else { "(no Streamlit stderr log)" }
            throw "Streamlit exited during startup with code $($streamlitProcess.ExitCode). Log: $appStderrLog`n$logTail"
        }
        try {
            $page = Invoke-WebRequest -Uri "http://127.0.0.1:8501/_stcore/health" -TimeoutSec 2 -MaximumRedirection 0
            if ($page.StatusCode -eq 200) {
                $appReady = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $appReady) {
        throw "Streamlit did not become ready at http://127.0.0.1:8501. Log: $appStderrLog"
    }

    Write-Host "Chatbot ready at http://127.0.0.1:8501"
    Write-Host "Inference engine: llama.cpp CPU; model: $modelName"
    Write-Host "Press Ctrl+C or close this window to stop the chatbot and its llama.cpp server."
    Start-Process "http://127.0.0.1:8501"
    Wait-Process -Id $streamlitProcess.Id
} finally {
    if ($startedStreamlit -and $streamlitProcess -and -not $streamlitProcess.HasExited) {
        Stop-Process -Id $streamlitProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($startedServer -and $serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
