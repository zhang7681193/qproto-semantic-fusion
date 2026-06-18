$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "data\gas_drift" | Out-Null

$zipPath = "data\gas_drift\gas_sensor_array_drift_dataset.zip"
if (-not (Test-Path $zipPath)) {
    Invoke-WebRequest `
        -Uri "https://archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip" `
        -OutFile $zipPath
}

if (-not (Test-Path "data\gas_drift\Dataset\batch1.dat")) {
    Expand-Archive -Path $zipPath -DestinationPath "data\gas_drift" -Force
}

Write-Host "Gas Sensor Array Drift dataset is ready under data\gas_drift"

