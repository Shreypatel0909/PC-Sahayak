# Diagnostic Questions by Category

## Overview
Good troubleshooting starts with good questions. This file gives the first questions the assistant should ask for each problem category, with suggested multiple-choice answers to keep replies quick and precise. Ask one or two at a time, start broad, and use the answers to narrow toward the right guide. Always capture the exact error text early.

## Universal first questions
- When did the problem start?
  - Just now / after a recent change / it has been getting worse / it has always done this
- Did anything change right before it started?
  - A Windows update / new software / new hardware / a settings or firmware change / nothing I know of
- Is there an exact error message or code?
  - Yes, I can read it out / there is a code / no message / not sure where to look
- Is the device a laptop or a desktop?
  - Laptop / desktop / all-in-one / not sure

## Boot problems
- What happens when you press the power button?
  - Nothing at all / lights and fans but no display / a logo that never progresses / it reaches a recovery or repair screen / it restarts in a loop
- Is there an error on screen?
  - "Operating system not found" / "Bootmgr is missing" / a stop code / a spinning dots screen / no text
- Can you reach the Advanced Startup or Recovery menu?
  - Yes / no / not sure what that is
- Did you recently add or move an internal drive or change firmware settings?
  - Yes / no / not sure

## Performance and slowness
- Is the whole system slow or only certain apps?
  - Everything / only one or two apps / only the web browser / only during heavy tasks
- When is it slow?
  - All the time / only at startup / after running a while / only under load
- Which resource is highest in Task Manager?
  - CPU / Memory / Disk / Network / I have not checked
- Is the system drive a solid-state drive or an older spinning hard drive?
  - SSD / HDD / not sure
- How full is the system drive?
  - Plenty free / fairly full / nearly full / not sure

## Network and internet
- How is the device connected?
  - Wi-Fi / Ethernet cable / mobile hotspot / not connected
- Do other devices on the same network work?
  - Yes, others are fine / no, all are affected / only this device is affected / no other devices to test
- What does the taskbar network icon show?
  - Connected with internet / connected, no internet / not connected / an error
- Does it fail for all websites or only some?
  - All sites / only some sites / only certain apps / intermittent
- Did it stop suddenly or degrade over time?
  - Sudden / gradual / comes and goes

## Hardware
- What hardware seems affected?
  - Display / sound / keyboard or mouse / a USB or external device / internal drive / cooling and temperature / memory
- Does the device make any unusual noise?
  - Loud fans / clicking or grinding / beeping at startup / no unusual noise
- Does it work on another port, cable, or computer?
  - Works elsewhere / fails everywhere / cannot test / not applicable
- Is it too hot or shutting down on its own?
  - Runs hot and loud / shuts off suddenly / seems normal temperature / not sure
- Was the hardware recently added, moved, or overclocked?
  - Newly added / recently moved / overclocked / nothing changed

## Software and applications
- Is it one application or several?
  - Just one app / a few related apps / many unrelated apps / the whole system
- When does it fail?
  - Fails to launch / crashes on startup / crashes during a specific action / freezes randomly
- Is it an install, an update, or a running problem?
  - Cannot install it / an update broke it / it was working and now crashes / never worked
- Did it start after an app update or a Windows update?
  - After an app update / after a Windows update / after new hardware or drivers / nothing changed
- Is there an error message or code?
  - Yes / a code number / no message / it just closes

## Routing the user
- One app affected → application crashes guide.
- Many apps or whole system unstable → consider memory, disk, and driver guides.
- No display or no startup → boot problems guide.
- Connected but no websites → DNS errors guide; no connection at all → no internet connection guide.
- Hot, loud, or sudden shutdowns → overheating guide.
- Device not recognized → peripheral and USB guide.

## Reminder
After gathering answers, follow the safe troubleshooting principles: start with reversible checks, change one thing at a time, back up before any risky step, and gate destructive actions behind clear warnings.
