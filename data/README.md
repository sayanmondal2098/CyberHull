# CyberHull dataset

`final_merged.json` contains the original 1,674 records: 204 legitimate and 1,470
phishing. It is tracked directly in Git, so a clone of this repository includes
it without Git LFS. Local training uses `--data data/final_merged.json`.

## Download it again

From the repository root, run this PowerShell snippet. It downloads from the
dataset snapshot in this repository at a fixed revision, checks the original SHA-256,
and only then places the file at `data/final_merged.json`. A failed download or
checksum check leaves any existing dataset untouched.

```powershell
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force data | Out-Null
$datasetUrl = 'https://raw.githubusercontent.com/sayanmondal2098/CyberHull/16c74a5/final_merged.json'
$expectedHash = '1a5275096c5f1130a2666a04e23ecc8542329c66cf50dd7fe063f90fddd372f4'
$downloadPath = Join-Path (Resolve-Path data).Path 'final_merged.json.download'
Invoke-WebRequest -Uri $datasetUrl -OutFile $downloadPath
if ((Get-FileHash -LiteralPath $downloadPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
    throw 'Dataset checksum mismatch. The existing dataset has not been replaced.'
}
Move-Item -LiteralPath $downloadPath -Destination data/final_merged.json -Force
```

[Direct dataset download](https://raw.githubusercontent.com/sayanmondal2098/CyberHull/16c74a5/final_merged.json).

Expected size: **26,967,679 bytes**. SHA-256:

```text
1a5275096c5f1130a2666a04e23ecc8542329c66cf50dd7fe063f90fddd372f4
```

The download URL uses the earlier verified snapshot, where the file was still at
repository root. Save it under `data/` for the current project layout. If the download
fails, retain the verified local copy. Do not substitute synthetic demonstration
data for this file.

## Verify and train

```powershell
Get-FileHash data/final_merged.json -Algorithm SHA256
git check-attr filter -- data/final_merged.json
New-Item -ItemType Directory -Force results/runs | Out-Null
.\.venv\Scripts\python.exe -m cyberhull train --data data/final_merged.json --model results/runs/real-model.json --output results/runs/real-metrics.json
```

The Git `filter` attribute should be `unset`. Commit this file with normal Git
commands; it does not need an LFS upload. Notebook setup resolves inputs from
the project root and also reads `data/final_merged.json`.
