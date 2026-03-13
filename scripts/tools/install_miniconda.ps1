$installer = Join-Path $env:USERPROFILE "Downloads\Miniconda3-latest-Windows-x86_64.exe"
Write-Output "Downloading Miniconda installer to: $installer"
Invoke-WebRequest -Uri "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe" -OutFile $installer
Write-Output "Running Miniconda silent installer..."
$installDir = Join-Path $env:USERPROFILE "Miniconda3"
Start-Process -FilePath $installer -ArgumentList "/InstallationType=JustMe","/AddToPath=0","/RegisterPython=0","/S","/D=$installDir" -Wait
Write-Output "Miniconda installer finished; installed to: $installDir"
