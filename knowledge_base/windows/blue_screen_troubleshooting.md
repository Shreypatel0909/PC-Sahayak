# Blue Screen (BSOD) Troubleshooting

## Overview
A blue screen (also called a stop error) is Windows halting to protect itself after an unexpected fault, usually from a driver, hardware problem, or corrupted system file. The on-screen stop code is the most useful clue. Many blue screens are one-time events; recurring ones follow a pattern that points to the cause.

## Common symptoms
- A full-screen error with a sad face, a QR code, and a stop code such as `IRQL_NOT_LESS_OR_EQUAL`, `PAGE_FAULT_IN_NONPAGED_AREA`, `SYSTEM_SERVICE_EXCEPTION`, or `CRITICAL_PROCESS_DIED`.
- The PC restarts suddenly, sometimes in a loop.
- Crashes cluster around a specific action (gaming, plugging in a device, waking from sleep).
- A driver file name (ending in `.sys`) is shown on the screen.

## Diagnostic questions
- What is the exact stop code and any file name shown?
- Does it happen randomly or during a specific activity?
- Did it begin after new hardware, a driver update, or a Windows update?
- How often does it occur, and can you reach the desktop at all?
- Have you recently overclocked the CPU, GPU, or memory?

## Step-by-step fixes

### Capture the clues first
1. Write down the **stop code** and any `.sys` file name. Search the stop code to narrow the category (memory, driver, disk).
2. Open **Event Viewer** (`eventvwr.msc`) and look under **Windows Logs > System** for red Error entries at the crash time.

### Reverse recent changes
3. If the crashes started after a recent change, undo it: uninstall the new driver in **Device Manager**, roll back a driver (right-click the device > **Properties > Driver > Roll Back Driver**), or remove newly added hardware.
4. If overclocked, return to stock speeds. Instability from aggressive overclocks is a common cause.

### Repair system files and check the disk
5. In an elevated terminal, run:
   ```
   sfc /scannow
   DISM /Online /Cleanup-Image /RestoreHealth
   ```
6. Schedule a disk check for the next restart:
   ```
   chkdsk /f
   ```

### Test memory
7. Run **Windows Memory Diagnostic** (`mdsched.exe`) and let it test on restart. Memory errors frequently cause stop codes like `PAGE_FAULT_IN_NONPAGED_AREA`.

### If Windows will not start
8. Boot into **Safe Mode** (hold Shift while clicking Restart, then **Troubleshoot > Advanced options > Startup Settings > Restart > 4**). If it is stable in Safe Mode, a driver or startup app is the likely cause.
9. Use **System Restore** (**Advanced options > System Restore**) to return to a point before the crashes began.

### Advanced: read the crash dump
> **Warning:** Updating or reinstalling drivers and editing startup items can affect stability. Note what you change so you can reverse it.

10. Crash details are saved to `C:\Windows\Minidump`. A free dump-reading tool can identify the faulting driver so you can update or remove exactly that component.

## When to seek professional help
- Memory or disk tests report errors (hardware likely needs replacement).
- Blue screens continue after clean drivers, file repair, and memory tests pass.
- The system will not stay running long enough to troubleshoot.
