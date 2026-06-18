$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "data\pamap2" | Out-Null
$outerZip = "data\pamap2\pamap2.zip"
$innerZip = "data\pamap2\PAMAP2_Dataset.zip"
Invoke-WebRequest -Headers @{"User-Agent"="Mozilla/5.0"} `
    -Uri "https://archive.ics.uci.edu/static/public/231/pamap2+physical+activity+monitoring.zip" `
    -OutFile $outerZip
Expand-Archive -LiteralPath $outerZip -DestinationPath "data\pamap2" -Force
Expand-Archive -LiteralPath $innerZip -DestinationPath "data\pamap2" -Force

Write-Host "Downloaded and extracted UCI PAMAP2 to data\pamap2"

