$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "data\hydraulic" | Out-Null
$zip = "data\hydraulic\condition_monitoring_hydraulic_systems.zip"
Invoke-WebRequest -Headers @{"User-Agent"="Mozilla/5.0"} `
    -Uri "https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip" `
    -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath "data\hydraulic" -Force

Write-Host "Downloaded and extracted UCI Hydraulic Systems to data\hydraulic"

