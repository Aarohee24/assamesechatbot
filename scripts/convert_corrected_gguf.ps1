param(
    [switch]$Execute,
    [string]$PythonExecutable = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceModel = Join-Path $projectRoot "merged_model"
$modelsDir = Join-Path $projectRoot "models"
$stagingModel = Join-Path $modelsDir "conversion-staging\merged_model"
$llamaCppDir = Join-Path $projectRoot "tools\llama.cpp"
$quantizer = Join-Path $projectRoot "tools\llama.cpp-bin-b12032\llama-quantize.exe"
$converter = Join-Path $llamaCppDir "convert_hf_to_gguf.py"
$prepareScript = Join-Path $PSScriptRoot "prepare_merged_model_for_gguf.py"
$ggufCheck = Join-Path $PSScriptRoot "check_gguf_model.py"
$ggufPython = Join-Path $llamaCppDir "gguf-py"
$f16Output = Join-Path $modelsDir "assamese-corrected-f16.gguf"
$q4Output = Join-Path $modelsDir "assamese-corrected-q4_k_m.gguf"

if (-not $PythonExecutable) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python was not found. Use an installation with PyTorch, Transformers, and safetensors."
    }
    $PythonExecutable = $pythonCommand.Source
}
if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    throw "Python executable not found: $PythonExecutable"
}
foreach ($requiredPath in @($sourceModel, $converter, $quantizer, $prepareScript, $ggufCheck, $ggufPython)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required local conversion input is missing: $requiredPath"
    }
}
if ((Test-Path -LiteralPath $f16Output) -or (Test-Path -LiteralPath $q4Output)) {
    throw "A corrected GGUF output already exists. This script refuses to overwrite either corrected output."
}

$prepareOutput = & $PythonExecutable $prepareScript --source $sourceModel --staging $stagingModel
if ($LASTEXITCODE -ne 0) {
    throw "Merged-model preflight/staging failed. Original weights were not modified."
}
Write-Host $prepareOutput

$driveLetter = (Split-Path -Qualifier $modelsDir).TrimEnd(":")
$freeDiskGiB = [math]::Round((Get-PSDrive -Name $driveLetter).Free / 1GB, 2)
$operatingSystem = Get-CimInstance Win32_OperatingSystem
$availableRamGiB = [math]::Round($operatingSystem.FreePhysicalMemory / 1MB, 2)
$totalRamGiB = [math]::Round($operatingSystem.TotalVisibleMemorySize / 1MB, 2)
Write-Host "Available RAM: $availableRamGiB GiB / $totalRamGiB GiB total; free disk: $freeDiskGiB GiB"
Write-Host "New outputs only: $f16Output and $q4Output. Existing GGUF files will not be changed."
Write-Host "The converter's metadata-only probe emitted architecture 'granite' with 8 KV heads on all 40 attention layers."

if (-not $Execute) {
    Write-Host "Preflight complete. No model tensors were converted or quantized."
    Write-Host "When at least 3 GiB RAM and 20 GiB free disk are available, run .\scripts\convert_corrected_gguf.ps1 -Execute"
    exit 0
}
if ($availableRamGiB -lt 3) {
    throw "Only $availableRamGiB GiB RAM is available. Close memory-heavy apps yourself and retry when at least 3 GiB is free. Conversion was not started."
}
if ($freeDiskGiB -lt 20) {
    throw "At least 20 GiB free disk is required for conversion and quantization; found $freeDiskGiB GiB."
}

$dependencyCheck = & $PythonExecutable -c "import torch, transformers, safetensors; print('torch=' + torch.__version__ + ' transformers=' + transformers.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "Converter Python must have working torch, transformers, and safetensors imports."
}
Write-Host "Converter Python: $PythonExecutable"
Write-Host $dependencyCheck

$sourceConfigHash = (Get-FileHash -LiteralPath (Join-Path $sourceModel "config.json") -Algorithm SHA256).Hash
$sourceShardHashes = @{}
foreach ($shard in @("model-00001-of-00002.safetensors", "model-00002-of-00002.safetensors")) {
    $sourceShardHashes[$shard] = (Get-FileHash -LiteralPath (Join-Path $sourceModel $shard) -Algorithm SHA256).Hash
}
$originalQ4Hash = (Get-FileHash -LiteralPath (Join-Path $modelsDir "assamese-q4_k_m.gguf") -Algorithm SHA256).Hash

$started = Get-Date
Write-Host "Converting the local staged checkpoint to a new FP16 Granite GGUF..."
& $PythonExecutable $converter --use-temp-file --outfile $f16Output --outtype f16 $stagingModel
if ($LASTEXITCODE -ne 0) {
    throw "FP16 GGUF conversion failed with exit code $LASTEXITCODE. Existing source and GGUF files were not overwritten."
}
if (-not (Test-Path -LiteralPath $f16Output) -or (Get-Item -LiteralPath $f16Output).Length -lt 5GB) {
    throw "The new FP16 GGUF is missing or unexpectedly small; refusing to quantize it."
}
& $PythonExecutable $ggufCheck --model $f16Output --gguf-python $ggufPython --expected-file-type 1
if ($LASTEXITCODE -ne 0) {
    throw "The new FP16 GGUF failed architecture/tensor validation; quantization was not attempted."
}

Write-Host "Quantizing the validated FP16 GGUF to a new Q4_K_M file..."
& $quantizer --max-buffer-size 512 $f16Output $q4Output Q4_K_M 4
if ($LASTEXITCODE -ne 0) {
    throw "Q4_K_M quantization failed with exit code $LASTEXITCODE. The FP16 intermediate is preserved."
}
& $PythonExecutable $ggufCheck --model $q4Output --gguf-python $ggufPython
if ($LASTEXITCODE -ne 0) {
    throw "The new Q4_K_M GGUF failed architecture/tensor validation. Existing model files were not overwritten."
}

if ((Get-FileHash -LiteralPath (Join-Path $sourceModel "config.json") -Algorithm SHA256).Hash -ne $sourceConfigHash) {
    throw "The original merged-model config changed during conversion."
}
foreach ($shard in $sourceShardHashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $sourceModel $shard) -Algorithm SHA256).Hash -ne $sourceShardHashes[$shard]) {
        throw "Original merged-model shard $shard changed during conversion."
    }
}
if ((Get-FileHash -LiteralPath (Join-Path $modelsDir "assamese-q4_k_m.gguf") -Algorithm SHA256).Hash -ne $originalQ4Hash) {
    throw "The pre-existing Q4_K_M GGUF changed during conversion."
}

$duration = (Get-Date) - $started
Get-Item -LiteralPath $f16Output, $q4Output | Select-Object FullName, Length
Write-Host "Corrected GGUF conversion and Q4_K_M quantization completed in $([math]::Round($duration.TotalMinutes, 1)) minutes."
Write-Host "Original merged checkpoint and existing assamese-q4_k_m.gguf verified unchanged."
