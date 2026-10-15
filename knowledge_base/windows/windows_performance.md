# Windows Performance and Slowness

## Overview
A slow PC is usually caused by too many background programs, low free disk space, insufficient memory for the workload, or a drive that is failing or heavily fragmented (on older hard drives). Performance issues are almost always fixable with safe adjustments. Identify what resource is maxed out before changing anything.

## Common symptoms
- The system takes a long time to boot or reach a usable desktop.
- Apps open slowly or freeze; typing lags.
- The fan runs constantly and the PC feels hot.
- The disk or CPU sits near 100% in Task Manager.
- Everything slows down when many browser tabs or apps are open.

## Diagnostic questions
- Is the whole system slow, or only specific apps?
- Is it slow all the time or only after running a while?
- How much RAM is installed, and how full is the system drive?
- Is the drive a solid-state drive (SSD) or an older spinning hard drive (HDD)?
- Did slowness start after installing something or after an update?

## Step-by-step fixes

### Find the bottleneck
1. Open **Task Manager** (`Ctrl+Shift+Esc`) and view the **Processes** tab sorted by CPU, Memory, and Disk. Note which resource is pinned and which process is responsible.
2. Check the **Startup apps** tab (or **Settings > Apps > Startup**) and disable programs you do not need at boot. This speeds up startup safely.

### Free resources
3. Free disk space: aim for at least 10-15% free on the system drive. Use **Settings > System > Storage** and **Storage Sense** to clear temporary files, caches, and the Recycle Bin.
4. Close unused browser tabs and background apps. A browser with many tabs is a common memory hog.
5. Restart the PC. Uptime of many days lets memory leaks and stuck processes build up.

### Housekeeping
6. Uninstall software you no longer use via **Settings > Apps > Installed apps**.
7. Scan for malware with **Windows Security > Virus & threat protection**. Hidden malware can consume CPU and network.
8. Install pending updates, including driver updates, from **Settings > Windows Update**.

### Drive maintenance
9. For an older hard drive, run **Defragment and Optimize Drives** (`dfrgui`). For an SSD, the same tool runs the correct TRIM optimization automatically. Do not manually defragment an SSD.
10. Check drive health in an elevated terminal:
    ```
    chkdsk /scan
    ```

### Adjust for performance
> **Warning:** The power plan and visual-effect changes below are safe and reversible, but note the original setting before changing it.

11. Set **Settings > System > Power** to **Balanced** or **Best performance** (on laptops this reduces battery life).
12. Reduce animations: search "Adjust the appearance and performance of Windows" and select **Adjust for best performance** or disable individual effects.

### When slowness points to hardware
13. If memory is consistently full under normal use, adding RAM is the most effective upgrade. If an old HDD is the bottleneck, moving to an SSD gives the largest real-world improvement.

## When to seek professional help
- Drive health tools report reallocated sectors or SMART warnings; back up immediately and consult a technician.
- The PC overheats and throttles despite cleaning dust and checking fans.
- Performance does not improve after cleanup and the hardware appears healthy.
