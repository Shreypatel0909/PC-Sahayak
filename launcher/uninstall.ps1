# PC-Sahayak uninstaller (run through "Uninstall PC-Sahayak.bat").
#
# Removes what PC-Sahayak set up on this computer, asking before anything that
# holds your data. Keep this file ASCII-only: Windows PowerShell 5.1 reads
# scripts as ANSI.

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
$Host.UI.RawUI.WindowTitle = 'Uninstall PC-Sahayak'
$StateDir = Join-Path $Root '.sahayak'

function Say([string]$Text, [string]$Color = 'Gray') { Write-Host $Text -ForegroundColor $Color }

function Ask([string]$Question) {
    while ($true) {
        $a = Read-Host "$Question [Y/N]"
        if ($a -match '^\s*[Yy]') { return $true }
        if ($a -match '^\s*[Nn]') { return $false }
    }
}

function Remove-IfPresent([string]$Relative, [string]$Label) {
    $p = Join-Path $Root $Relative
    if (Test-Path -LiteralPath $p) {
        Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $p) { Say "  Could not fully remove $Label ($Relative). Close any program using it and try again." Yellow }
        else { Say "  Removed $Label" }
    }
}

Write-Host ''
Write-Host '  Uninstall PC-Sahayak' -ForegroundColor White
Write-Host ''
Say 'This removes what PC-Sahayak installed in this folder:'
Say '  - its Python environment (.venv) and interface build files'
Say '  - the search index of the knowledge base'
Say '  - the desktop shortcut, if one was created'
Say '  - the network access code (old share links stop working)'
Say 'You will be asked separately about your saved chats, your API key, and'
Say 'any programs (Python, Node.js) that the launcher installed.'
Write-Host ''
if (-not (Ask 'Continue?')) { Say 'Nothing was changed.'; Start-Sleep -Seconds 2; exit 0 }

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

# 1. Stop PC-Sahayak if it is running from this folder.
$running = Get-PcSahayakProcesses
foreach ($proc in $running) {
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    Say '  Stopped the running PC-Sahayak server'
}
Start-Sleep -Milliseconds 500

# 2. Installed files.
Write-Host ''
Say 'Removing installed files...' Cyan
Remove-IfPresent '.venv' 'the Python environment'
Remove-IfPresent 'web\node_modules' 'the interface packages'
Remove-IfPresent 'web\dist' 'the built interface'
Remove-IfPresent 'data\index' 'the knowledge-base index'
Remove-IfPresent '.pytest_cache' 'test cache'
Get-ChildItem -LiteralPath $Root -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }

# 3. Desktop shortcut.
$shortcuts = @()
$recorded = Join-Path $StateDir 'shortcut.txt'
if (Test-Path -LiteralPath $recorded) { $shortcuts += (Get-Content -LiteralPath $recorded | Where-Object { $_ }) }
$shortcuts += Join-Path ([Environment]::GetFolderPath('Desktop')) 'PC-Sahayak.lnk'
$shell = New-Object -ComObject WScript.Shell
foreach ($lnk in ($shortcuts | Select-Object -Unique)) {
    if (Test-Path -LiteralPath $lnk) {
        $target = $shell.CreateShortcut($lnk).TargetPath
        if ($target -and $target.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $lnk -Force
            Say '  Removed the desktop shortcut'
        }
    }
}

# 3b. Firewall rules added for network mode.
$rulesFile = Join-Path $StateDir 'firewall-rules.txt'
if (Test-Path -LiteralPath $rulesFile) {
    $rules = @(Get-Content -LiteralPath $rulesFile | Where-Object { $_ } | Select-Object -Unique |
        Where-Object { Get-NetFirewallRule -DisplayName $_ -ErrorAction SilentlyContinue })
    if ($rules.Count) {
        Write-Host ''
        if (Ask 'Remove the Windows Firewall rule added for network mode? Windows will ask for administrator permission') {
            $names = ($rules | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ','
            try {
                Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -WindowStyle Hidden `
                    -ArgumentList @('-NoProfile', '-Command', "Remove-NetFirewallRule -DisplayName $names")
            } catch { }
            if (-not ($rules | Where-Object { Get-NetFirewallRule -DisplayName $_ -ErrorAction SilentlyContinue })) { Say '  Removed the firewall rule' }
            else { Say '  The firewall rule was not removed. You can delete it in Windows Defender Firewall > Advanced settings.' Yellow }
        }
    }
}

# 3c. Networks the launcher switched from Public to Private.
$madePrivate = Join-Path $StateDir 'networks-made-private.txt'
if (Test-Path -LiteralPath $madePrivate) {
    $nets = @(Get-Content -LiteralPath $madePrivate | Where-Object { $_ } | Select-Object -Unique)
    if ($nets.Count) {
        Write-Host ''
        $list = ($nets | ForEach-Object { "'" + $_ + "'" }) -join ', '
        if (Ask "The launcher set $list to Private. Set it back to Public? Windows will ask for administrator permission") {
            $cmd = ($nets | ForEach-Object { "Set-NetConnectionProfile -Name '" + $_.Replace("'", "''") + "' -NetworkCategory Public -ErrorAction SilentlyContinue" }) -join '; '
            try { Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList @('-NoProfile', '-Command', $cmd) } catch { }
            Say '  Done. You can check it in Settings > Network & internet.'
        }
    }
}

# 4. Your data (asked separately).
Write-Host ''
$chats = Join-Path $Root 'data\conversations'
$uploads = Join-Path $Root 'data\uploads'
if ((Test-Path -LiteralPath $chats) -or (Test-Path -LiteralPath $uploads)) {
    if (Ask 'Delete your saved chats and screenshots too?') {
        Remove-IfPresent 'data\conversations' 'saved chats'
        Remove-IfPresent 'data\uploads' 'saved screenshots'
    } else { Say '  Kept your saved chats (data\conversations).' }
}
if (Test-Path -LiteralPath (Join-Path $Root '.env')) {
    if (Ask 'Delete your Groq API key (the .env file)?') { Remove-IfPresent '.env' 'the API key file' }
    else { Say '  Kept the .env file.' }
}

# 5. Programs the launcher installed (Python / Node.js), never anything else.
$installedList = Join-Path $StateDir 'installed-by-launcher.txt'
if ((Test-Path -LiteralPath $installedList) -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    foreach ($entry in (Get-Content -LiteralPath $installedList | Where-Object { $_ } | Select-Object -Unique)) {
        $id, $name = $entry.Split('|', 2)
        Write-Host ''
        Say "The launcher installed $name. Other programs on this computer may use it too."
        if (Ask "Uninstall $name?") {
            & winget uninstall -e --id $id
            if ($LASTEXITCODE -eq 0) { Say "  Uninstalled $name" } else { Say "  $name could not be uninstalled. Remove it from Settings > Apps if you want." Yellow }
        }
    }
}
Remove-IfPresent '.sahayak' 'launcher settings'

# 6. Optionally remove the whole program folder.
Write-Host ''
Say 'PC-Sahayak has been uninstalled. Its program files are still in:' Green
Say "  $Root"
Write-Host ''
Say 'You can also delete that whole folder now. This removes the program files for good.' Yellow
$confirm = Read-Host 'Type DELETE to remove the folder, or press Enter to keep it'
if ($confirm -ceq 'DELETE') {
    # The folder can't be deleted while this script runs from it, so a separate
    # window waits a moment and then removes it.
    $cmd = "/c timeout /t 3 /nobreak >nul & rmdir /s /q `"$Root`""
    Start-Process -FilePath 'cmd.exe' -ArgumentList $cmd -WindowStyle Hidden -WorkingDirectory $env:TEMP
    Say 'The folder will be removed in a few seconds.'
    Start-Sleep -Seconds 1
    exit 0
}
Say 'Kept the folder. Run "Start PC-Sahayak.bat" any time to set it up again.'
Write-Host ''
Read-Host 'Press Enter to close this window' | Out-Null
