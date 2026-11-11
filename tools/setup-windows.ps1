# Red Herrings - Windows forensics toolkit setup
# Installs the free tools the Red Herrings cases use, via winget where possible.
# Run in an elevated PowerShell:  powershell -ExecutionPolicy Bypass -File setup-windows.ps1
# It installs only free, redistributable tools and prints links for the few
# that must be downloaded by hand (their licenses do not allow bundling).

$ErrorActionPreference = "Continue"

function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Write-Host "== Red Herrings toolkit setup (Windows) ==" -ForegroundColor Cyan
if (-not (Have winget)) {
  Write-Host "winget was not found. Install 'App Installer' from the Microsoft Store, then re-run this script." -ForegroundColor Yellow
  exit 1
}

# id = winget package id, name = friendly label
$pkgs = @(
  @{ id = "SleuthKit.Autopsy";                        name = "Autopsy (disk analysis)" },
  @{ id = "WiresharkFoundation.Wireshark";            name = "Wireshark (packet captures)" },
  @{ id = "DBBrowserForSQLite.DBBrowserForSQLite";    name = "DB Browser for SQLite (mobile/browser DBs)" },
  @{ id = "Mozilla.Thunderbird";                      name = "Thunderbird (email/mbox/.eml)" },
  @{ id = "Notepad++.Notepad++";                      name = "Notepad++ (text/log viewing)" },
  @{ id = "jqlang.jq";                                name = "jq (JSON: cloud audit logs)" },
  @{ id = "7zip.7zip";                                name = "7-Zip (archives)" },
  @{ id = "Microsoft.DotNet.DesktopRuntime.10";       name = ".NET 10 Desktop Runtime (Eric Zimmerman's tools)" },
  @{ id = "Python.Python.3.12";                       name = "Python 3.12 (Volatility 3)" }
)

foreach ($p in $pkgs) {
  Write-Host ("Installing {0} ..." -f $p.name) -ForegroundColor Green
  winget install --id $($p.id) -e --silent --accept-source-agreements --accept-package-agreements
}

# Volatility 3 (memory) once Python is present.
Write-Host "Installing Volatility 3 ..." -ForegroundColor Green
$py = if (Have py) { "py -m pip" } elseif (Have python) { "python -m pip" } else { $null }
if ($py) {
  Invoke-Expression "$py install --upgrade pip volatility3"
} else {
  Write-Host "Python not on PATH yet. Open a new terminal after install and run:  py -m pip install volatility3" -ForegroundColor Yellow
}

# Eric Zimmerman's tools (Prefetch, LNK, jump lists, registry, EVTX, timelines).
Write-Host "Fetching Eric Zimmerman's tools to C:\EZ ..." -ForegroundColor Green
try {
  New-Item -ItemType Directory -Force -Path "C:\EZ" | Out-Null
  Invoke-WebRequest -Uri "https://raw.githubusercontent.com/EricZimmerman/Get-ZimmermanTools/master/Get-ZimmermanTools.ps1" -OutFile "C:\EZ\Get-ZimmermanTools.ps1"
  Push-Location "C:\EZ"; & ".\Get-ZimmermanTools.ps1" -Dest "C:\EZ"; Pop-Location
} catch {
  Write-Host "Could not auto-fetch EZ tools. Get them from https://ericzimmerman.github.io/ (unzip to C:\EZ)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "== Download by hand (licenses do not allow bundling/scripted install) ==" -ForegroundColor Cyan
Write-Host "  FTK Imager   https://www.exterro.com/digital-forensics-software/ftk-imager"
Write-Host "  Chainsaw     https://github.com/WithSecureLabs/chainsaw/releases (EVTX threat hunting)"
Write-Host "  ALEAPP       https://github.com/abrignoni/ALEAPP/releases (Android)"
Write-Host "  iLEAPP       https://github.com/abrignoni/iLEAPP/releases (iPhone)"
Write-Host ""
Write-Host "Done. See the tool-to-case mapping at https://redherrings.app/tools.html" -ForegroundColor Cyan
