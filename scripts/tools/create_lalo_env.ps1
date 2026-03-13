$conda = Join-Path $env:USERPROFILE "Miniconda3\Scripts\conda.exe"
if (-Not (Test-Path $conda)) { Write-Error "conda not found at $conda"; exit 1 }
Write-Output "Creating conda env 'lalo' with msaf and deps (this may take several minutes)..."
& $conda create -n lalo -c conda-forge python=3.10 msaf librosa scikit-learn mir_eval numpy scipy joblib -y
Write-Output "Verifying imports inside 'lalo'..."
$py = 'import msaf, sklearn, mir_eval, librosa, numpy; print("IMPORT_OK", msaf.__version__, sklearn.__version__, mir_eval.__version__, librosa.__version__, numpy.__version__)'
& $conda run -n lalo python -c $py
Write-Output "Environment create/verify finished."