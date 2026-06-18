$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "data\mhealth" | Out-Null
$zip = "data\mhealth\mhealth_dataset.zip"
Invoke-WebRequest -Headers @{"User-Agent"="Mozilla/5.0"} `
    -Uri "https://cdn.uci-ics-mlr-prod.aws.uci.edu/319/mhealth%2Bdataset.zip" `
    -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath "data\mhealth" -Force

Write-Host "Downloaded and extracted UCI MHEALTH to data\mhealth"

