# No Internet Connection

## Overview
"No internet" can mean the PC has no network link at all, or it is connected to the local network but cannot reach the wider internet. Pinpointing where the chain breaks, the PC, the router, or the provider, makes the fix obvious. Most cases are resolved by restarting equipment and refreshing the PC's network configuration.

## Common symptoms
- A globe or "No internet access" icon in the taskbar.
- Connected to Wi-Fi or Ethernet but web pages will not load.
- Some apps work while others fail.
- All devices in the home lose internet at the same time.
- Pages load very slowly or time out.

## Diagnostic questions
- Is the PC connected by Wi-Fi or Ethernet cable?
- Do other devices on the same network have internet?
- Does the taskbar show connected-but-no-internet, or not connected at all?
- Did it stop working suddenly, and did anything change?
- Can you reach the router's status page or the provider's app?

## Step-by-step fixes

### Locate the break in the chain
1. Check whether other devices have internet. If none do, the problem is the router or the provider, not this PC, so skip to restarting the router.
2. Look at the taskbar icon: "No internet, secured" means connected to the local network but not reaching out; "Not connected" means no link at all.

### Restart the equipment
3. Restart the PC first.
4. Power-cycle the modem and router: unplug both, wait about 30 seconds, plug the modem in first and let it fully come online, then the router. This clears the majority of whole-home outages.

### Check the physical link
5. For Ethernet, confirm the cable is firmly seated at both ends and the port lights are active. Try a different cable or port.
6. For Wi-Fi, confirm you are joined to the right network and the signal is adequate.

### Refresh the PC's configuration
7. Open an elevated terminal and run:
   ```
   ipconfig /release
   ipconfig /renew
   ipconfig /flushdns
   ```
8. Test connectivity in layers to see where it fails:
   ```
   ping 127.0.0.1
   ping 192.168.1.1
   ping 8.8.8.8
   ping www.example.com
   ```
   If the numeric address (`8.8.8.8`) works but the name does not, the problem is DNS; see the DNS errors guide.

### Use built-in repair tools
9. Run **Settings > System > Troubleshoot > Other troubleshooters > Network and Internet**.
10. Confirm the adapter is enabled and obtaining an address automatically under **Settings > Network & internet > Advanced network settings**.

### Rule out software blocks
> **Warning:** Only disable security software briefly for testing and re-enable it immediately afterward. Never browse with protection off.

11. A misconfigured VPN, proxy, or firewall can block all traffic. Disconnect any VPN and check **Settings > Network & internet > Proxy** is set to automatic unless your network requires otherwise.

### Reset the network stack (last resort)
> **Warning:** This removes saved Wi-Fi networks and VPN settings. Note credentials first.

12. Run, then restart:
    ```
    netsh winsock reset
    netsh int ip reset
    ```

## When to seek professional help
- All devices stay offline after power-cycling the modem and router; contact the internet service provider to check for an outage or line fault.
- The modem shows error lights that do not clear.
- The Ethernet port or adapter appears physically faulty.
