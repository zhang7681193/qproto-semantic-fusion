$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "data\uci_har" | Out-Null
New-Item -ItemType Directory -Force -Path "data\wdbc" | Out-Null
New-Item -ItemType Directory -Force -Path "data\mfeat" | Out-Null

$UciHarZip = "data\uci_har\uci_har.zip"
if (-not (Test-Path $UciHarZip)) {
    Invoke-WebRequest `
        -Uri "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip" `
        -OutFile $UciHarZip
}
if (-not (Test-Path "data\uci_har\UCI HAR Dataset")) {
    Expand-Archive -Path $UciHarZip -DestinationPath "data\uci_har" -Force
}

$WdbcPath = "data\wdbc\wdbc.data"
if (-not (Test-Path $WdbcPath)) {
    Invoke-WebRequest `
        -Uri "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data" `
        -OutFile $WdbcPath
}

$MfeatFiles = @("mfeat-mor", "mfeat-zer", "mfeat-fou", "mfeat-kar", "mfeat-fac", "mfeat-pix")
foreach ($Name in $MfeatFiles) {
    $OutPath = "data\mfeat\$Name"
    if (-not (Test-Path $OutPath)) {
        Invoke-WebRequest `
            -Uri "https://archive.ics.uci.edu/ml/machine-learning-databases/mfeat/$Name" `
            -OutFile $OutPath
    }
}

Write-Host "IF real datasets are ready."

