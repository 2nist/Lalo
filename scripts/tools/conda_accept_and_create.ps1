$ErrorActionPreference='Stop'
$conda = Join-Path $env:USERPROFILE "Miniconda3\condabin\conda.bat"
if (-not (Test-Path $conda)) { Write-Host "ERROR: conda not found at $conda"; exit 2 }
Write-Host "Accepting Miniconda channel Terms of Service..."
& $conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
& $conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
& $conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2
Write-Host "Creating conda env 'lalo'..."
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