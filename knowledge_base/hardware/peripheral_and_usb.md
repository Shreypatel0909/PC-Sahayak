# Peripherals and USB Devices

## Overview
Keyboards, mice, printers, webcams, external drives, and other USB devices can fail to work due to a loose connection, a missing or broken driver, a power issue, or a disabled port. Most peripheral problems are solved with simple reconnection and driver steps before any hardware is suspected.

## Common symptoms
- A device is not recognized, or Windows reports "USB device not recognized."
- A mouse or keyboard stops responding intermittently.
- An external drive does not appear in File Explorer.
- A printer shows offline or jobs stick in the queue.
- A device works on one port but not another.

## Diagnostic questions
- Which device, and how does it connect (USB-A, USB-C, Bluetooth)?
- Does it work on another port, cable, or computer?
- Did it ever work, or is this a new device?
- Was there a recent Windows update or driver change?
- Is the device self-powered or does it draw power from the port?

## Step-by-step fixes

### Start with the physical basics
1. Unplug and firmly re-plug the device. Try a different USB port, ideally one directly on the PC rather than a hub.
2. Swap the cable if possible. A failing cable is a very common and easily missed cause.
3. For a device that needs more power (external hard drive, some webcams), connect it directly to the PC or use a powered hub.
4. For wireless devices, replace or recharge the batteries and re-pair via **Settings > Bluetooth & devices**.

### Software and driver checks
5. Restart the PC. This clears many temporary port and driver glitches.
6. Open **Device Manager** (`devmgmt.msc`) and look for the device. A yellow exclamation mark indicates a driver problem.
7. Right-click the device and choose **Update driver**, then **Scan for hardware changes** from the Action menu.

### Reset the device entry
> **Warning:** Uninstalling a device removes its driver; Windows normally reinstalls it on reconnect, but have the vendor driver available for specialized hardware.

8. If a device misbehaves, right-click it in Device Manager, choose **Uninstall device**, then unplug and replug it (or restart) so Windows reinstalls it cleanly.

### Power management
9. Some ports power down to save energy. In Device Manager, expand **Universal Serial Bus controllers**, open each **USB Root Hub > Properties > Power Management**, and clear **Allow the computer to turn off this device to save power** for troublesome devices.

### Printer-specific steps
10. Open **Settings > Bluetooth & devices > Printers & scanners**, select the printer, and run its troubleshooter. Clear a stuck queue by restarting the Print Spooler in an elevated terminal:
    ```
    net stop spooler
    net start spooler
    ```
11. Confirm the printer is set as default and is not in **Use Printer Offline** mode.

### Storage device not appearing
12. Open **Disk Management** (`diskmgmt.msc`). If an external drive appears without a drive letter, right-click it and assign one. Do not format a drive that holds data you need.

## When to seek professional help
- The device fails on multiple ports, cables, and computers (likely a faulty device).
- USB ports stop working across the whole system, suggesting a motherboard or controller fault.
- Specialized hardware requires drivers that are no longer available.
