# Windows Boot Problems

## Overview
Boot problems range from a black screen with no activity to Windows starting but failing partway with a recovery error. Causes include a loose or failing drive, corrupted boot files, a bad driver or update, or incorrect firmware (BIOS/UEFI) settings. The Windows Recovery Environment (WinRE) provides safe repair tools that do not erase your data.

## Common symptoms
- The PC powers on but shows a black screen or a manufacturer logo that never progresses.
- An error such as "Operating system not found," "Bootmgr is missing," or `INACCESSIBLE_BOOT_DEVICE`.
- Windows reaches a spinning dots screen then restarts in a loop.
- The **Automatic Repair** or **Recovery** screen appears.

## Diagnostic questions
- Does the PC show any logo or lights, or is it completely dark?
- Is there an error message, and what does it say exactly?
- Did it start after a power loss, update, new hardware, or firmware change?
- Can you reach the Recovery or Advanced Startup screen?
- Have you added or moved any internal drives recently?

## Step-by-step fixes

### Rule out the simple causes
1. Confirm the monitor is on and the correct input is selected; try a different cable or port. A "no boot" is sometimes just no display signal.
2. Remove all USB drives, external disks, and memory cards, then restart. The PC may be trying to boot from the wrong device.
3. For a desktop, check that the power supply switch is on and reseat the power cable. For a laptop, charge it and try again.

### Use Automatic Repair
4. If the PC fails to boot twice, Windows usually opens **Automatic Repair**. Choose **Advanced options** to reach WinRE. You can also force it by holding the power button to interrupt boot three times.
5. In WinRE, select **Troubleshoot > Advanced options > Startup Repair** and let it attempt an automatic fix.

### Undo recent changes
6. If problems began after an update or driver, use **Advanced options > Uninstall Updates** or **System Restore** to roll back to a working state. System Restore keeps your personal files.
7. Try **Startup Settings > Safe Mode** (option 4). If Windows boots in Safe Mode, a driver or startup item is the cause; remove the recent addition.

### Repair boot files from the command line
> **Warning:** The commands below modify boot configuration. They are standard repair steps, but run them only after Startup Repair has failed, and do not run `/rebuildbcd` carelessly on multi-boot systems.

8. Open **Advanced options > Command Prompt** and run, one at a time:
   ```
   bootrec /scanos
   bootrec /fixmbr
   bootrec /fixboot
   bootrec /rebuildbcd
   ```
9. Check the system drive for errors (replace C: if Windows is on another letter in WinRE):
   ```
   chkdsk C: /f
   ```

### Check firmware settings
> **Warning:** BIOS/UEFI changes can make the system unbootable if set wrong. Note each setting before changing it and change only one at a time.

10. Enter firmware setup (usually Del, F2, F10, or F12 at power-on). Confirm the correct drive is first in the boot order and that the drive is detected. If the drive is missing, power down and reseat its cables.

## When to seek professional help
- The drive is not detected in firmware even after reseating cables (possible drive failure).
- You see errors pointing to disk hardware, or the drive makes clicking noises.
- Repairs fail and you do not have a recent backup of important files; a technician can often recover data before any reinstall.
