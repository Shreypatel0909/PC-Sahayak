# Wi-Fi Troubleshooting

## Overview
Wi-Fi problems include not seeing any networks, failing to connect to a known network, or connecting with no usable internet. Causes range from a disabled adapter or airplane mode, to a weak signal, a wrong password, a driver issue, or a router that needs restarting. Work from the simplest checks outward.

## Common symptoms
- No networks appear in the Wi-Fi list.
- The PC connects but shows "No internet, secured."
- Frequent disconnects or very slow, unstable speeds.
- "Can't connect to this network" when joining.
- Wi-Fi works on other devices but not this PC.

## Diagnostic questions
- Do other devices on the same network work normally?
- Does the PC see any networks at all, or just fail to connect to one?
- Does it fail everywhere or only at a certain distance from the router?
- Did it work before, and did anything change (update, password, new router)?
- Is this a known home network or a public/managed one?

## Step-by-step fixes

### Quick checks first
1. Confirm **Airplane mode** is off and Wi-Fi is on in the **Quick Settings** panel (click the network icon in the taskbar).
2. Make sure the physical Wi-Fi switch or function-key toggle on a laptop is enabled.
3. Move closer to the router to rule out a weak signal, then retry.
4. Toggle Wi-Fi off and on, and try **Forget** then rejoin the network, re-entering the password carefully.

### Restart the chain
5. Restart the PC. Then, if other devices are also affected, restart the router/modem by powering it off for 30 seconds and back on.

### Use Windows tools
6. Run the network troubleshooter: **Settings > System > Troubleshoot > Other troubleshooters > Network and Internet** (or **Network Adapter**).
7. Check the adapter is enabled in **Settings > Network & internet > Advanced network settings**; enable it if it is off.

### Refresh the connection from the command line
8. Open an elevated terminal and release/renew the address and reset the resolver cache:
   ```
   ipconfig /release
   ipconfig /renew
   ipconfig /flushdns
   ```
9. View saved networks and signal details if needed:
   ```
   netsh wlan show interfaces
   ```

### Driver and adapter reset
10. In **Device Manager**, expand **Network adapters**, right-click the Wi-Fi adapter, and choose **Update driver**. If it recently stopped working after an update, try **Roll Back Driver**.
11. Reinstall cleanly if needed: right-click the adapter, **Uninstall device**, then restart so Windows reinstalls it.

### Reset the network stack (last resort)
> **Warning:** A network reset removes all saved Wi-Fi networks and VPN settings, which you will need to set up again. Note your Wi-Fi password first.

12. If nothing else works, use **Settings > Network & internet > Advanced network settings > Network reset**, or run in an elevated terminal:
    ```
    netsh winsock reset
    netsh int ip reset
    ```
    Restart afterward.

## When to seek professional help
- No Wi-Fi networks appear even after driver reinstall (possible hardware or antenna fault).
- The adapter is missing from Device Manager entirely.
- All devices lose internet and restarting the router does not help; contact the internet service provider.
