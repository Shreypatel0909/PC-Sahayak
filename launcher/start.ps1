# PC-Sahayak launcher (run through "Start PC-Sahayak.bat").
#
# Checks that everything PC-Sahayak needs is present, offers to install what is
# missing (asking first every time), starts the server and opens the browser.
# With -Network ("Start PC-Sahayak (network).bat") other devices on the local
# network can use it too, through a share link that carries an access code.
# Keep this file ASCII-only: Windows PowerShell 5.1 reads scripts as ANSI.

param([int]$Port = 8000, [switch]$Network)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
$Host.UI.RawUI.WindowTitle = 'PC-Sahayak'

# Launcher bookkeeping: what it installed, so the uninstaller can offer to remove it.
$StateDir = Join-Path $Root '.sahayak'
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
$DistIndex = Join-Path $Root 'web\dist\index.html'

function Say([string]$Text, [string]$Color = 'Gray') { Write-Host $Text -ForegroundColor $Color }
function Step([string]$Text) { Write-Host ''; Write-Host "> $Text" -ForegroundColor Cyan }

function Ask([string]$Question) {
    while ($true) {
        $a = Read-Host "$Question [Y/N]"
        if ($a -match '^\s*[Yy]') { return $true }
        if ($a -match '^\s*[Nn]') { return $false }
    }
}

function Stop-WithMessage([string]$Text) {
    Write-Host ''
    Write-Host $Text -ForegroundColor Red
    Write-Host ''
    Read-Host 'Press Enter to close this window' | Out-Null
    exit 1
}

function Update-PathFromRegistry {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Test-Winget { return [bool](Get-Command winget -ErrorAction SilentlyContinue) }

function Install-WithWinget([string]$Id, [string]$Name) {
    Say "Installing $Name with winget. Windows may ask for permission..."
    & winget install -e --id $Id --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { return $false }
    Add-Content -LiteralPath (Join-Path $StateDir 'installed-by-launcher.txt') -Value "$Id|$Name"
    Update-PathFromRegistry
    return $true
}

function Test-PcSahayak([int]$P) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$P/api/meta" -UseBasicParsing -TimeoutSec 2
        return $r.Content -match 'starter_suggestions'
    } catch { return $false }
}

function Test-PortFree([int]$P) {
    $busy = Get-NetTCPConnection -LocalPort $P -State Listen -ErrorAction SilentlyContinue
    return -not $busy
}

# A Python 3.11-3.13 interpreter, as @{ Exe; Args } or $null.
function Find-Python {
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in '3.13', '3.12', '3.11') { $candidates += @{ Exe = 'py'; Args = @("-$v") } }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += @{ Exe = 'python'; Args = @() } }
    foreach ($v in '313', '312', '311') {
        $p = Join-Path $env:LOCALAPPDATA "Programs\Python\Python$v\python.exe"
        if (Test-Path -LiteralPath $p) { $candidates += @{ Exe = $p; Args = @() } }
    }
    foreach ($c in $candidates) {
        try {
            $ver = & $c.Exe @($c.Args + @('-c', 'import sys; print("%d.%d" % sys.version_info[:2])')) 2>$null
            if ($LASTEXITCODE -eq 0 -and "$ver".Trim() -match '^3\.(11|12|13)$') { return $c }
        } catch { }
    }
    return $null
}

function Test-PythonPackages {
    if (-not (Test-Path -LiteralPath $VenvPython)) { return $false }
    & $VenvPython -c 'import fastapi, uvicorn, multipart, groq, numpy, yaml, dotenv, pydantic' 2>$null
    return $LASTEXITCODE -eq 0
}

function Get-FileHashText([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Get-NodeMajor {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { return 0 }
    try {
        $v = (& node --version) -replace '^v', ''
        return [int]($v.Split('.')[0])
    } catch { return 0 }
}

function Get-GroqKey {
    foreach ($file in @('.env', '.streamlit\secrets.toml')) {
        $p = Join-Path $Root $file
        if (Test-Path -LiteralPath $p) {
            foreach ($line in Get-Content -LiteralPath $p) {
                if ($line -match '^\s*GROQ_API_KEY\s*=\s*"?([^"#\s]+)') {
                    $k = $Matches[1]
                    if ($k -and $k -notin @('your_api_key_here', 'changeme')) { return $k }
                }
            }
        }
    }
    return $null
}

function Set-GroqKey([string]$Key) {
    $envFile = Join-Path $Root '.env'
    if (-not (Test-Path -LiteralPath $envFile)) {
        $example = Join-Path $Root '.env.example'
        if (Test-Path -LiteralPath $example) { Copy-Item -LiteralPath $example -Destination $envFile }
        else { Set-Content -LiteralPath $envFile -Value '' -Encoding ASCII }
    }
    $lines = @(Get-Content -LiteralPath $envFile)
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*#?\s*GROQ_API_KEY\s*=') { $lines[$i] = "GROQ_API_KEY=$Key"; $found = $true }
    }
    if (-not $found) { $lines += "GROQ_API_KEY=$Key" }
    Set-Content -LiteralPath $envFile -Value $lines -Encoding ASCII
}

# Is the PC-Sahayak already running on this port older than the code on disk?
# (e.g. started before an update) Old servers can break a newer interface.
function Test-ServerOutdated([int]$P) {
    $local = ''
    $init = Select-String -LiteralPath (Join-Path $Root 'pc_helper\__init__.py') -Pattern '__version__\s*=\s*"([^"]+)"' -ErrorAction SilentlyContinue
    if ($init) { $local = $init.Matches[0].Groups[1].Value }
    try { $running = [string](Invoke-RestMethod -Uri "http://127.0.0.1:$P/api/meta" -TimeoutSec 3).version } catch { $running = '' }
    if ($local -and $running -ne $local) { return $true }
    $owner = Get-NetTCPConnection -LocalPort $P -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess
    if (-not $owner) { return $false }
    try { $started = (Get-Process -Id $owner -ErrorAction Stop).StartTime } catch { return $false }
    $newest = Get-ChildItem -LiteralPath (Join-Path $Root 'api'), (Join-Path $Root 'pc_helper') -Recurse -File -Filter '*.py' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    return [bool]($newest -and $newest.LastWriteTime -gt $started)
}

# PC-Sahayak server processes from this folder. On Windows the .venv python.exe is a
# small launcher that starts the real interpreter, so match on the parent too.
function Get-PcSahayakProcesses {
    $all = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue)
    $byId = @{}
    foreach ($proc in $all) { $byId[[int]$proc.ProcessId] = $proc }
    $isOurs = { param($path) [bool]($path -and $path.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase)) }
    return @($all | Where-Object {
        $parent = $byId[[int]$_.ParentProcessId]
        $_.CommandLine -match 'api\.main:app' -and ((& $isOurs $_.ExecutablePath) -or ($parent -and (& $isOurs $parent.ExecutablePath)))
    })
}

function Stop-PcSahayakServer {
    Get-PcSahayakProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}

# Is the running copy shared on the network? (share links are only reported to this PC)
function Test-SharedOnNetwork([int]$P) {
    try { $urls = (Invoke-RestMethod -Uri "http://127.0.0.1:$P/api/meta" -TimeoutSec 3).share_urls } catch { return $false }
    return [bool]($urls -and @($urls).Count -gt 0)
}

# Access code for network mode: kept between runs so share links keep working.
function Get-AccessCode {
    $file = Join-Path $StateDir 'access-code'
    if (Test-Path -LiteralPath $file) {
        $saved = (Get-Content -LiteralPath $file -Raw).Trim()
        if ($saved.Length -ge 8) { return $saved }
    }
    $alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    $bytes = New-Object byte[] 10
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $code = -join ($bytes | ForEach-Object { $alphabet[$_ % $alphabet.Length] })
    Set-Content -LiteralPath $file -Value $code -Encoding ASCII
    return $code
}

# IPv4 addresses other devices can reach (adapters with a default gateway first).
function Get-LanAddresses {
    $withGateway = @(Get-NetIPConfiguration -ErrorAction SilentlyContinue |
        Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
        ForEach-Object { $_.IPv4Address.IPAddress })
    if ($withGateway.Count) { return $withGateway | Select-Object -Unique }
    return @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.InterfaceAlias -notmatch 'vEthernet|Loopback|VirtualBox|VMware|WSL' } |
        ForEach-Object { $_.IPAddress }) | Select-Object -Unique
}

# Let other devices reach the port. Windows hides a PC on networks marked Public, so
# offer to mark a trusted network Private, plus a firewall rule for private networks
# only. Both happen in one administrator prompt.
function Confirm-NetworkAccess([int]$P) {
    $rule = "PC-Sahayak (TCP $P)"
    $hasRule = [bool](Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue)
    $public = @(Get-NetConnectionProfile -ErrorAction SilentlyContinue |
        Where-Object { $_.NetworkCategory -eq 'Public' -and $_.IPv4Connectivity -ne 'Disconnected' })
    if (-not $public.Count -and $hasRule) { return }

    $commands = @()
    if ($public.Count) {
        $names = ($public | ForEach-Object { "'" + $_.Name + "'" }) -join ', '
        Say "Windows has your network $names set to Public, which stops other devices from connecting to this PC." Yellow
        Say 'If this is your home or work network, set it to Private.' Yellow
        if (-not (Ask "Set $names to Private and let PC-Sahayak through the firewall? Windows will ask for administrator permission")) {
            Say 'OK, the network stays Public, so other devices will probably not be able to connect.' Yellow
            return
        }
        foreach ($n in $public) { $commands += "Set-NetConnectionProfile -InterfaceIndex $($n.InterfaceIndex) -NetworkCategory Private" }
    } else {
        Say "Windows Firewall may block other devices from reaching port $P." Yellow
        if (-not (Ask 'Let PC-Sahayak through the firewall on private networks? Windows will ask for administrator permission')) {
            Say 'Skipped. If Windows shows a firewall prompt, choose Allow.' Yellow
            return
        }
    }
    if (-not $hasRule) {
        $commands += "New-NetFirewallRule -DisplayName '$rule' -Direction Inbound -Protocol TCP -LocalPort $P -Profile Private -Action Allow | Out-Null"
    }
    try {
        Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList @('-NoProfile', '-Command', ($commands -join '; '))
    } catch {
        Say 'Administrator permission was not given, so nothing was changed.' Yellow
        return
    }
    foreach ($n in $public) {
        $now = Get-NetConnectionProfile -InterfaceIndex $n.InterfaceIndex -ErrorAction SilentlyContinue
        if ($now -and $now.NetworkCategory -eq 'Private') {
            Add-Content -LiteralPath (Join-Path $StateDir 'networks-made-private.txt') -Value $n.Name
            Say "Network '$($n.Name)' is now Private." Green
        } else {
            Say "Network '$($n.Name)' could not be changed. Set it to Private in Settings > Network & internet > Wi-Fi." Yellow
        }
    }
    if (-not $hasRule) {
        if (Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue) {
            Add-Content -LiteralPath (Join-Path $StateDir 'firewall-rules.txt') -Value $rule
            Say 'Firewall rule added.' Green
        } else {
            Say 'The firewall rule was not added. If Windows shows a firewall prompt, choose Allow.' Yellow
        }
    }
}

# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '  PC-Sahayak' -ForegroundColor White
Write-Host '  Windows PC troubleshooting assistant' -ForegroundColor DarkGray

# 0. Already running? Open it, unless it is an outdated copy that should be restarted.
if (Test-PcSahayak $Port) {
    Say ''
    $restart = $false
    if (Test-ServerOutdated $Port) {
        Say 'An older copy of PC-Sahayak is still running from before an update.' Yellow
        $restart = Ask 'Restart it with the current version?'
    } elseif ($Network -and -not (Test-SharedOnNetwork $Port)) {
        Say 'PC-Sahayak is already running, but only for this computer.' Yellow
        $restart = Ask 'Restart it so other devices on your network can use it?'
    }
    if ($restart) {
        Stop-PcSahayakServer
    } else {
        Say "PC-Sahayak is already running. Opening http://127.0.0.1:$Port ..." Green
        Start-Process "http://127.0.0.1:$Port/"
        Start-Sleep -Seconds 2
        exit 0
    }
}

# 1. Python + packages
Step 'Checking Python and its packages'
$needPackages = -not (Test-PythonPackages)
$reqHash = Get-FileHashText (Join-Path $Root 'requirements.txt')
$hashFile = Join-Path $StateDir 'requirements.sha256'
if (-not $needPackages -and (Test-Path -LiteralPath $hashFile) -and ((Get-Content -LiteralPath $hashFile -Raw).Trim() -ne $reqHash)) {
    $needPackages = $true   # requirements.txt changed since the last install
}

if ($needPackages) {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        $py = Find-Python
        if (-not $py) {
            Say 'Python 3.11, 3.12 or 3.13 is needed but was not found.' Yellow
            if (-not (Test-Winget)) {
                Start-Process 'https://www.python.org/downloads/'
                Stop-WithMessage "Install Python 3.12 from python.org (tick 'Add python.exe to PATH'), then open PC-Sahayak again."
            }
            if (-not (Ask 'Install Python 3.12 now?')) { Stop-WithMessage 'PC-Sahayak cannot run without Python.' }
            if (-not (Install-WithWinget 'Python.Python.3.12' 'Python 3.12')) { Stop-WithMessage 'Python could not be installed. Install Python 3.12 from python.org, then try again.' }
            $py = Find-Python
            if (-not $py) { Stop-WithMessage 'Python was installed, but Windows has not picked it up yet. Close this window and open PC-Sahayak again.' }
        }
        Say 'PC-Sahayak needs its own Python environment and packages (about 150 MB, a few minutes, needs internet).' Yellow
        if (-not (Ask 'Install them now?')) { Stop-WithMessage 'PC-Sahayak cannot run without its packages.' }
        Say 'Creating the Python environment...'
        & $py.Exe @($py.Args + @('-m', 'venv', (Join-Path $Root '.venv')))
        if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'Could not create the Python environment (.venv).' }
    } else {
        Say 'Some Python packages are missing or out of date.' Yellow
        if (-not (Ask 'Install them now? (needs internet)')) { Stop-WithMessage 'PC-Sahayak cannot run without its packages.' }
    }
    Say 'Installing packages. This can take a few minutes...'
    & $VenvPython -m pip install --disable-pip-version-check -q --upgrade pip
    & $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $Root 'requirements.txt')
    if ($LASTEXITCODE -ne 0 -or -not (Test-PythonPackages)) { Stop-WithMessage 'Package installation failed. Check your internet connection, then try again.' }
}
Set-Content -LiteralPath $hashFile -Value $reqHash -Encoding ASCII
Say 'Python is ready.' Green

# 2. The interface (React app, built once with Node.js)
Step 'Checking the interface'
$webSrc = Join-Path $Root 'web\src'
$stale = $false
if (Test-Path -LiteralPath $DistIndex) {
    $built = (Get-Item -LiteralPath $DistIndex).LastWriteTime
    $newer = Get-ChildItem -LiteralPath $webSrc -Recurse -File | Where-Object { $_.LastWriteTime -gt $built } | Select-Object -First 1
    $stale = [bool]$newer
}
$needBuild = (-not (Test-Path -LiteralPath $DistIndex)) -or ($stale -and (Get-NodeMajor) -ge 18)

if ($needBuild) {
    if ((Get-NodeMajor) -lt 18) {
        Say 'The interface needs to be built once, which requires Node.js 18 or newer.' Yellow
        if (-not (Test-Winget)) {
            Start-Process 'https://nodejs.org/en/download'
            Stop-WithMessage 'Install Node.js (LTS) from nodejs.org, then open PC-Sahayak again.'
        }
        if (-not (Ask 'Install Node.js LTS now?')) { Stop-WithMessage 'PC-Sahayak cannot build its interface without Node.js.' }
        if (-not (Install-WithWinget 'OpenJS.NodeJS.LTS' 'Node.js LTS')) { Stop-WithMessage 'Node.js could not be installed. Install it from nodejs.org, then try again.' }
        if ((Get-NodeMajor) -lt 18) { Stop-WithMessage 'Node.js was installed, but Windows has not picked it up yet. Close this window and open PC-Sahayak again.' }
    }
    if ($stale) { Say 'The interface code has changed since it was last built. Rebuilding...' }
    elseif (-not (Ask 'Build the PC-Sahayak interface now? (about 1-2 minutes, needs internet the first time)')) {
        Stop-WithMessage 'PC-Sahayak cannot open without its interface.'
    }
    Push-Location -LiteralPath (Join-Path $Root 'web')
    try {
        if (-not (Test-Path -LiteralPath 'node_modules')) {
            Say 'Downloading interface packages...'
            & npm ci --no-audit --no-fund
            if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'Downloading the interface packages failed. Check your internet connection, then try again.' }
        }
        Say 'Building the interface...'
        & npm run build
        if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'Building the interface failed. See the messages above.' }
    } finally { Pop-Location }
}
Say 'Interface is ready.' Green

# 3. Groq API key
Step 'Checking the Groq API key'
if (-not (Get-GroqKey)) {
    Say 'PC-Sahayak uses Groq for its answers. You need a free API key from https://console.groq.com/keys' Yellow
    if (Ask 'Open the Groq website to get a key?') { Start-Process 'https://console.groq.com/keys' }
    $key = (Read-Host 'Paste your Groq API key here (or press Enter to skip for now)').Trim()
    if ($key) {
        Set-GroqKey $key
        Say 'Key saved to the .env file in the PC-Sahayak folder.' Green
    } else {
        Say 'Skipped. PC-Sahayak will open, but it cannot answer until a key is added.' Yellow
    }
} else {
    Say 'API key found.' Green
}

# 4. Desktop shortcut (asked once)
$askedFile = Join-Path $StateDir 'shortcut-asked'
if (-not (Test-Path -LiteralPath $askedFile)) {
    Set-Content -LiteralPath $askedFile -Value 'yes' -Encoding ASCII
    if (Ask 'Create a PC-Sahayak shortcut on your desktop?') {
        $lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'PC-Sahayak.lnk'
        $shell = New-Object -ComObject WScript.Shell
        $s = $shell.CreateShortcut($lnk)
        $s.TargetPath = Join-Path $Root 'Start PC-Sahayak.bat'
        $s.WorkingDirectory = $Root
        $s.IconLocation = (Join-Path $Root 'launcher\PC-Sahayak.ico') + ',0'
        $s.Description = 'Start PC-Sahayak'
        $s.Save()
        Set-Content -LiteralPath (Join-Path $StateDir 'shortcut.txt') -Value $lnk -Encoding UTF8
        Say 'Shortcut created.' Green
    }
}

# 5. Start the server and open the browser
Step 'Starting PC-Sahayak'
$p = $Port
while (-not (Test-PortFree $p)) {
    $p++
    if ($p -gt $Port + 20) { Stop-WithMessage "Ports $Port to $($Port + 20) are all in use. Close some programs, then try again." }
}
if ($p -ne $Port) { Say "Port $Port is busy, using $p instead." Yellow }

$bindHost = '127.0.0.1'
$shareUrls = @()
$env:PC_SAHAYAK_ACCESS_CODE = ''
$env:PC_SAHAYAK_SHARE_URLS = ''
if ($Network) {
    Step 'Sharing on your local network'
    Say 'Other devices on your Wi-Fi or network will be able to use PC-Sahayak through a share link.'
    Say 'Anyone with the link can see and delete its chats, and their questions use your Groq API key.' Yellow
    Say 'Only do this on a network you trust (for example your home Wi-Fi).' Yellow
    if (Ask 'Share PC-Sahayak on this network?') {
        $addresses = @(Get-LanAddresses)
        if (-not $addresses.Count) {
            Say 'No network connection was found, so PC-Sahayak will run on this computer only.' Yellow
        } else {
            $code = Get-AccessCode
            $shareUrls = @($addresses | ForEach-Object { "http://$($_):$p/?access=$code" })
            $env:PC_SAHAYAK_ACCESS_CODE = $code
            $env:PC_SAHAYAK_SHARE_URLS = $shareUrls -join ','
            $bindHost = '0.0.0.0'
            Confirm-NetworkAccess $p
        }
    } else {
        Say 'OK, PC-Sahayak will run on this computer only.'
    }
}

$server = Start-Process -FilePath $VenvPython -ArgumentList @('-m', 'uvicorn', 'api.main:app', '--host', $bindHost, '--port', "$p", '--log-level', 'warning') `
    -WorkingDirectory $Root -NoNewWindow -PassThru
$null = $server.Handle   # keep a handle so the exit code can be read later

Say 'Loading the knowledge base (the first start can take a minute)...'
$ready = $false
for ($i = 0; $i -lt 240; $i++) {
    if ($server.HasExited) { break }
    if (Test-PcSahayak $p) { $ready = $true; break }
    Start-Sleep -Milliseconds 500
}
if (-not $ready) {
    if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
    Stop-WithMessage 'PC-Sahayak did not start. See the messages above for the reason.'
}

$url = "http://127.0.0.1:$p/"
Start-Process $url
Write-Host ''
Write-Host "  PC-Sahayak is running at $url" -ForegroundColor Green
if ($shareUrls.Count) {
    Write-Host ''
    Write-Host '  Other devices on your network can open:' -ForegroundColor Cyan
    foreach ($u in $shareUrls) { Write-Host "    $u" -ForegroundColor White }
    Write-Host '  (The same link is in PC-Sahayak under Settings.) If a device cannot connect, make sure' -ForegroundColor DarkGray
    Write-Host '  this network is set to Private in Windows Settings > Network & internet.' -ForegroundColor DarkGray
    Write-Host ''
}
Write-Host '  Keep this window open while you use it. To stop PC-Sahayak, use the power button in the app,' -ForegroundColor DarkGray
Write-Host '  close this window, or press Ctrl+C.' -ForegroundColor DarkGray
Write-Host ''
$server.WaitForExit()
if ($server.ExitCode -eq 0) {
    Write-Host ''
    Write-Host '  PC-Sahayak was closed. This window will close by itself.' -ForegroundColor Green
    Start-Sleep -Seconds 2
    exit 0
}
Stop-WithMessage "PC-Sahayak stopped unexpectedly (exit code $($server.ExitCode)). See the messages above."
