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
$f16Output = Join-Path $modelsDir "assamese-f16.gguf"
$q4Output = Join-Path $modelsDir "assamese-q4_k_m.gguf"
$prepareScript = Join-Path $PSScriptRoot "prepare_merged_model_for_gguf.py"

$pythonCommand = $null
if (-not $PythonExecutable) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python was not found. Use a Python installation with PyTorch, Transformers, and safetensors."
    }
    $PythonExecutable = $pythonCommand.Source
}
if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    throw "Python executable not found: $PythonExecutable"
}
if (-not (Test-Path -LiteralPath $converter)) {
    throw "Pinned llama.cpp converter not found at $converter. Reinstall the official b12032 source checkout."
}
if (-not (Test-Path -LiteralPath $quantizer)) {
    throw "Official Windows llama-quantize binary not found at $quantizer."
}
if (-not (Select-String -LiteralPath (Join-Path $llamaCppDir "conversion\granite.py") -Pattern 'GraniteMoeHybridForCausalLM' -Quiet)) {
    throw "The selected llama.cpp converter does not register GraniteMoeHybridForCausalLM; conversion is blocked."
}

Write-Host "llama.cpp revision: $(& git -C $llamaCppDir rev-parse --short HEAD)"

if (-not (Test-Path -LiteralPath $modelsDir)) {
    New-Item -ItemType Directory -Path $modelsDir | Out-Null
}
$prepareOutput = & $PythonExecutable $prepareScript --source $sourceModel --staging $stagingModel
if ($LASTEXITCODE -ne 0) {
    throw "Merged-model preflight/staging failed. Original weights were not modified."
}
Write-Host $prepareOutput

$ram = Get-CimInstance Win32_OperatingSystem
$availableRamGiB = [math]::Round($ram.FreePhysicalMemory / 1MB, 2)
$totalRamGiB = [math]::Round($ram.TotalVisibleMemorySize / 1MB, 2)
$driveLetter = (Split-Path -Qualifier $modelsDir).TrimEnd(":")
$freeDiskGiB = [math]::Round((Get-PSDrive -Name $driveLetter).Free / 1GB, 2)
Write-Host "Available RAM: $availableRamGiB GiB / $totalRamGiB GiB total; free disk: $freeDiskGiB GiB"
Write-Host "Required outputs: intermediate FP16 GGUF (~6.4 GiB) plus Q4_K_M GGUF (~2.2 GiB)."
Write-Host "Conversion stages a config-only normalization: all 40 layers are full attention and the safetensors index contains no Mamba/SSM tensors. Original shard files are hard-linked read-only."

if (-not $Execute) {
    Write-Host "Preflight complete. No model weights were loaded and no conversion was started."
    Write-Host "When at least 3 GiB RAM is available, run .\scripts\convert_merged_model.ps1 -Execute"
    exit 0
}
if ($availableRamGiB -lt 3) {
    throw "Only $availableRamGiB GiB RAM is currently available. Close Ollama and memory-heavy apps, then retry. Conversion was not started."
}
if ($freeDiskGiB -lt 20) {
    throw "At least 20 GiB free disk is required for conversion and quantization; found $freeDiskGiB GiB."
}
if ((Test-Path -LiteralPath $f16Output) -or (Test-Path -LiteralPath $q4Output)) {
    throw "A conversion output already exists. This script refuses to overwrite GGUF files."
}

$dependencyCheck = & $PythonExecutable -c "import torch, transformers, safetensors; print('torch=' + torch.__version__ + ' transformers=' + transformers.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "Converter Python must have working torch, transformers, and safetensors imports."
}
Write-Host "Converter Python: $PythonExecutable"
Write-Host $dependencyCheck

$started = Get-Date
Write-Host "Converting the local merged checkpoint to FP16 GGUF..."
& $PythonExecutable $converter $stagingModel --outfile $f16Output --outtype f16
if ($LASTEXITCODE -ne 0) {
    throw "llama.cpp HF-to-GGUF conversion failed with exit code $LASTEXITCODE. No quantization or Ollama registration was attempted."
}
Write-Host "Quantizing the converted local model to Q4_K_M..."
& $quantizer --max-buffer-size 512 $f16Output $q4Output Q4_K_M
if ($LASTEXITCODE -ne 0) {
    throw "llama-quantize failed with exit code $LASTEXITCODE. The FP16 intermediate is preserved."
}

$duration = (Get-Date) - $started
Get-Item $f16Output,$q4Output | Select-Object FullName,Length
Write-Host "Conversion and quantization completed in $([math]::Round($duration.TotalMinutes, 1)) minutes."
Write-Host "Original merged_model files were not edited. Next: .\scripts\register_ollama_model.ps1"
