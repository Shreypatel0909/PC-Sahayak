# Storage and Disk Problems

## Overview
Storage problems show up as slow performance, files that will not open, errors during saves, or a drive that disappears entirely. Causes include a failing drive, loose cables, corrupted file systems, or simply a full disk. Because data loss is a real risk, the first priority with any suspected failing drive is to back up important files before troubleshooting.

## Common symptoms
- Files fail to open, disappear, or report corruption errors.
- The system freezes with the disk at 100% in Task Manager.
- A drive is missing from File Explorer or shows as unformatted.
- Clicking, grinding, or repeated spin-up noises from a spinning hard drive.
- "Low disk space" warnings or inability to save new files.

## Diagnostic questions
- Is one specific drive affected or the whole system?
- Is it a solid-state drive (SSD) or a spinning hard drive (HDD)?
- Are important files on it backed up elsewhere?
- Did the problem appear suddenly or worsen over time?
- Does the drive make any unusual noise?

## Step-by-step fixes

> **Warning:** If you suspect the drive is failing, back up your important files first. Running repair tools on a dying drive can make data harder to recover. If the drive is making mechanical noises, stop and seek recovery help.

### Check space and health first
1. In **File Explorer > This PC**, check free space on each drive. If a drive is nearly full, free space via **Settings > System > Storage** before anything else.
2. Check SMART health in an elevated terminal:
   ```
   wmic diskdrive get model,status
   ```
   A status other than "OK," or vendor tools reporting reallocated sectors, signals impending failure.

### Verify connections
> **Warning:** Power off, unplug, and discharge static before opening a desktop. Skip on laptops where this is impractical.

3. For a desktop with a missing or intermittent internal drive, reseat the data and power cables, or try a different cable and port.

### Repair the file system
4. Scan a drive for errors first (read-only, safe):
   ```
   chkdsk C: /scan
   ```
5. If errors are found and the data is backed up, schedule a full repair. This can take a long time and may be destructive to already-corrupted files:
   ```
   chkdsk C: /f /r
   ```
   Replace C: with the affected drive letter. The `/r` option also checks for bad sectors.

### Handle a drive that shows as unformatted
> **Warning:** Do not format or initialize a drive that contains data you need. Formatting erases it. If the data matters, use recovery tools or a professional first.

6. Open **Disk Management** (`diskmgmt.msc`) to see whether the drive appears. If it shows as unallocated but held important data, do not format it; pursue data recovery instead.

### Address a slow but healthy drive
7. For an older HDD, run **Optimize Drives** (`dfrgui`) to defragment. For an SSD, the same tool runs TRIM. Never manually defragment an SSD.
8. Update the storage controller driver and confirm firmware is current from the drive maker's utility.

## When to seek professional help
- SMART or vendor tools report the drive is failing.
- The drive clicks, grinds, or disappears intermittently.
- Important data is on a drive that no longer mounts; a recovery specialist offers the best chance before any repair attempt.
