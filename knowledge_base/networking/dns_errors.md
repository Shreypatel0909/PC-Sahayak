# DNS Errors

## Overview
DNS (Domain Name System) translates website names like `example.com` into the numeric addresses computers use. When DNS fails, the PC often has a working connection but cannot open websites by name. A telltale sign is that a numeric address pings successfully while the site name does not. Fixes are safe and focus on clearing the cache and choosing a reliable resolver.

## Common symptoms
- "DNS server not responding" or `DNS_PROBE_FINISHED_NXDOMAIN` in the browser.
- Websites will not load by name, but a direct numeric address works.
- Some sites load while others fail.
- Pages load on one device but not another on the same network.

## Diagnostic questions
- Does a numeric address such as `8.8.8.8` ping while names fail?
- Do all sites fail, or only some?
- Does the problem affect every device or just this PC?
- Is a VPN, proxy, or custom DNS configured?
- Did it start after changing network settings?

## Step-by-step fixes

### Confirm it is really DNS
1. Open an elevated terminal and compare a numeric ping with a name ping:
   ```
   ping 8.8.8.8
   ping www.example.com
   ```
   If the first succeeds and the second fails with a resolution error, DNS is the problem.

### Clear the DNS cache
2. Flush the resolver cache and retry:
   ```
   ipconfig /flushdns
   ```
3. Renew the address lease as well:
   ```
   ipconfig /release
   ipconfig /renew
   ```

### Restart and test another browser
4. Restart the PC and the router. A stale router DNS cache is a common cause.
5. Try a different browser or an incognito window to rule out a browser-specific cache.

### Set a reliable DNS server
> **Warning:** Note the current DNS settings before changing them so you can revert. Use automatic (DHCP) settings on managed or workplace networks unless told otherwise.

6. Go to **Settings > Network & internet**, open the active connection, choose **Edit** next to DNS server assignment, set it to **Manual**, enable IPv4, and enter a well-known public resolver such as `8.8.8.8` and `8.8.4.4`, or `1.1.1.1` and `1.0.0.1`.
7. Flush the cache again after changing it:
   ```
   ipconfig /flushdns
   ```

### Rule out interference
> **Warning:** Re-enable any security software immediately after a brief test. Do not browse with protection disabled.

8. Disconnect any VPN or proxy, which may override DNS. Check **Settings > Network & internet > Proxy** is set correctly.
9. Confirm a "secure DNS" or DNS-over-HTTPS setting inside the browser is not conflicting with the system resolver; temporarily set it to match the system.

### Check the hosts file
> **Warning:** The hosts file can block or redirect sites. Edit it only if you understand the entries, and back it up first.

10. Unexpected entries in `C:\Windows\System32\drivers\etc\hosts` can block specific sites. Review it and remove suspicious lines only if you know what they do.

## When to seek professional help
- DNS fails on all devices even with a public resolver set, suggesting a router or provider issue.
- You suspect malware has altered DNS or the hosts file; run a full security scan and consult a professional.
- The provider's DNS is persistently unreliable and changing it does not help.
