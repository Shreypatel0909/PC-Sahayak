# Software Installation Errors

## Overview
Installations fail for a handful of common reasons: insufficient permissions, a corrupted or incomplete download, missing prerequisites (runtimes or frameworks), leftover files from a previous version, or not enough disk space. Most are fixed without drastic measures by verifying the installer and clearing the way for a clean install.

## Common symptoms
- An installer errors out partway with a code or "installation failed" message.
- "You need administrator permission" or a blocked installer.
- The installer hangs or closes with no message.
- A previous version blocks the new one.
- "Another installation is already in progress."

## Diagnostic questions
- What exact error message or code appears?
- Where did the installer come from, and is it from the official source?
- Is there enough free disk space for the install?
- Was an earlier version of this software installed before?
- Does installing as administrator change the result?

## Step-by-step fixes

### Verify the installer and environment
1. Confirm the download is complete and from the official source. Re-download if the file size looks wrong or the download was interrupted.
2. Check free disk space in **File Explorer > This PC**; clear space if low.
3. Restart the PC to clear any pending operations, then try again. "Another installation in progress" often clears after a restart.

### Run with the right permissions
> **Warning:** Only run installers from sources you trust. Granting administrator rights lets an installer change the whole system.

4. Right-click the installer and choose **Run as administrator**.
5. If a security prompt blocks it, confirm the publisher is legitimate before allowing it.

### Clear previous versions and leftovers
6. Uninstall any older version via **Settings > Apps > Installed apps** before installing the new one.
7. If an uninstall itself fails, use the official uninstaller or the vendor's cleanup tool rather than deleting folders manually.

### Install missing prerequisites
8. Many apps need a specific runtime or framework. Read the error for a named component and install the official prerequisite, then retry.
9. Make sure Windows itself is up to date via **Settings > Windows Update**, as some installers require recent components.

### Repair the system if the installer service fails
10. If errors mention the installer service, repair system files in an elevated terminal:
    ```
    sfc /scannow
    DISM /Online /Cleanup-Image /RestoreHealth
    ```

### Rule out interference
> **Warning:** Disable security software only briefly for a test and re-enable it right after. Never leave protection off.

11. Antivirus or controlled-folder settings can block installers. Temporarily disable them to test, then re-enable immediately.
12. Try a clean boot (via `msconfig` or **Settings > Apps > Startup**) so background software does not interfere, then install.

### Review the installer log
13. Many installers write a log in the temporary folder (`%temp%`). The last lines usually name the exact failure to guide the next step.

## When to seek professional help
- The installer repeatedly fails with the same error after all steps and a clean boot.
- System file repair itself cannot complete.
- The software vendor's support should be contacted for product-specific error codes.
