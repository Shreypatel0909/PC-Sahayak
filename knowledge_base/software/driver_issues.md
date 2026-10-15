# Driver Issues

## Overview
Drivers are the software that lets Windows talk to hardware such as graphics cards, network adapters, sound devices, and printers. A missing, outdated, corrupted, or wrong driver causes devices to stop working, perform poorly, or trigger crashes. Device Manager is the central tool, and most driver problems are fixed by updating, rolling back, or reinstalling cleanly.

## Common symptoms
- A device has a yellow exclamation mark in Device Manager.
- Hardware stops working after a Windows update.
- Poor performance, flickering display, no sound, or no network.
- Blue screens that name a `.sys` driver file.
- "This device cannot start (Code 10)" or similar error codes.

## Diagnostic questions
- Which device is affected, and what is its Device Manager status?
- Did the problem start after an update or a driver change?
- Is the device built in or an add-in/external component?
- Do you know the exact model so the correct driver can be found?
- Does the device work in Safe Mode?

## Step-by-step fixes

### Identify the problem device
1. Open **Device Manager** (`devmgmt.msc`) and look for any device with a warning icon. Right-click it and read **Properties > General** for the status and error code.

### Update the driver
2. Right-click the device and choose **Update driver > Search automatically**. Also check **Settings > Windows Update > Advanced options > Optional updates > Driver updates**.
3. For graphics, network, or specialized hardware, download the latest driver from the official hardware maker's site, matching your exact model and Windows version.

> **Warning:** Install drivers only from the device maker or Windows Update. Drivers from unknown sources can destabilize the system or carry malware. Avoid third-party "driver updater" utilities.

### Roll back a bad update
4. If the device broke right after a driver update, right-click it, choose **Properties > Driver > Roll Back Driver** to return to the previous working version.

### Reinstall cleanly
> **Warning:** Uninstalling removes the current driver. Have the replacement driver downloaded first, especially for network adapters, since you may lose internet to fetch it afterward.

5. Right-click the device, choose **Uninstall device**. If offered, tick **Delete the driver software for this device** only when you have a known-good replacement ready.
6. Restart the PC, or use **Action > Scan for hardware changes**, to let Windows reinstall the driver.

### Use Safe Mode when the driver blocks Windows
7. If a bad driver prevents normal startup, boot into **Safe Mode** (**Advanced options > Startup Settings > 4**) where Windows loads minimal drivers, then uninstall or roll back the problem driver from there.

### Verify after changes
8. Confirm the device no longer shows a warning in Device Manager and test its function.

## When to seek professional help
- No working driver exists for your Windows version (very old or unsupported hardware).
- The device still fails with correct, up-to-date drivers, suggesting a hardware fault.
- Repeated blue screens continue to name the same driver after clean reinstalls.
