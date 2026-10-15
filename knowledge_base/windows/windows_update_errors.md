# Windows Update Errors

## Overview
Windows Update can fail for many reasons: a corrupted download cache, low disk space, damaged system files, or a service that is not running. Most update failures are recoverable with safe, built-in tools and do not require reinstalling the operating system. Work through the checks below in order, starting with the least invasive.

## Common symptoms
- An update downloads but fails to install, then rolls back on restart.
- A specific error code appears (for example `0x80070002`, `0x800f0922`, `0x80073712`, `0x80240034`).
- The update is stuck at a percentage for a very long time.
- "We couldn't complete the updates. Undoing changes."
- Updates repeatedly reappear after being installed.

## Diagnostic questions
- What exact error code or message is shown?
- Is a single update failing, or do all updates fail?
- How much free space is on the system drive (usually C:)?
- Did the problem start after installing new software or hardware?
- Is the device connected to a metered or restricted network?
- Is this a work or school device that might be managed by an administrator?

## Step-by-step fixes

### Start with safe checks
1. Confirm an internet connection and that the clock date/time is correct. An incorrect clock can break update validation.
2. Open **Settings > Update & Security > Windows Update** (Windows 11: **Settings > Windows Update**) and choose **Check for updates** again. Transient server issues often clear on a retry.
3. Free up disk space. Updates need several gigabytes free. Open **Settings > System > Storage** and remove temporary files.
4. Restart the PC and try the update once more. A pending restart can block new installs.

### Run the built-in troubleshooter
5. Go to **Settings > Update & Security > Troubleshoot > Additional troubleshooters > Windows Update** and run it. This resets common update components automatically.

### Repair system files
6. Open an elevated terminal (right-click **Start > Terminal (Admin)** or **Command Prompt (Admin)**) and run a system file check:
   ```
   sfc /scannow
   ```
7. If issues remain, repair the component store, then re-run the file check:
   ```
   DISM /Online /Cleanup-Image /RestoreHealth
   sfc /scannow
   ```
   These commands are safe and non-destructive; they only repair OS files.

### Reset the Windows Update cache
> **Warning:** The following stops services and deletes the download cache. It is reversible (Windows rebuilds the cache) but should only be used if the steps above did not help. Close other apps first.

8. In the elevated terminal, stop the update services, rename the cache folders, then restart the services:
   ```
   net stop wuauserv
   net stop bits
   ren %windir%\SoftwareDistribution SoftwareDistribution.old
   ren %windir%\System32\catroot2 catroot2.old
   net start wuauserv
   net start bits
   ```
9. Return to Windows Update and check for updates again.

### Install a specific update manually
10. If one named update keeps failing, note its **KB number** and download the matching package from the official Microsoft Update Catalog, then run it. Confirm you pick the build and architecture (x64/ARM64) that match your system.

## When to seek professional help
- The same error persists after a component reset and file repair.
- Errors reference failing disk hardware or repeated boot failures.
- The device is managed by an organization; contact the IT administrator rather than overriding policy.
