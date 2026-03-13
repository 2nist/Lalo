$ErrorActionPreference = 'Stop'
$inst = "$env:TEMP\Miniconda3-latest-Windows-x86_64.exe"
if (-not (Test-Path $inst)) {
    Write-Host "Downloading Miniconda installer to $inst"
    Invoke-WebRequest -Uri "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe" -OutFile $inst -UseBasicParsing
} else {
    Write-Host "Installer already present: $inst"
}
Write-Host "Running silent installer..."
Start-Process -FilePath $inst -ArgumentList "/S","/InstallationType=JustMe","/AddToPath=0","/RegisterPython=0","/D=$env:USERPROFILE\Miniconda3" -Wait
$conda = Join-Path $env:USERPROFILE "Miniconda3\condabin\conda.bat"
if (-not (Test-Path $conda)) { Write-Host "ERROR: conda not found after install"; exit 2 }
Write-Host "Initializing conda for PowerShell"
& $conda init powershell
Write-Host "Creating conda env 'lalo' with required packages (this may take several minutes)"
& $conda create -n lalo -c conda-forge python=3.10 msaf librosa scikit-learn mir_eval numpy scipy joblib -y
$py = Join-Path $env:TEMP "conda_import_test.py"
@"
import msaf, sklearn, mir_eval, librosa, numpy
print('IMPORT_OK', msaf.__version__, sklearn.__version__, mir_eval.__version__, librosa.__version__, numpy.__version__)
"@ | Out-File -FilePath $py -Encoding utf8
Write-Host "Running import test in 'lalo'"
& $conda run -n lalo python $py
Remove-Item $py -Force
Write-Host "Done."