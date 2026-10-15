# Application Crashes and Freezes

## Overview
When a single application crashes, freezes, or fails to open, the cause is usually specific to that app: a corrupted install, incompatible settings, a damaged user profile for the app, an outdated version, or a conflict with another program or driver. System-wide instability points elsewhere (memory, disk, drivers). Start by confirming whether it is one app or many.

## Common symptoms
- An app closes unexpectedly, sometimes with "has stopped working."
- The app window turns white and shows "Not responding."
- The app will not launch at all, or crashes on startup.
- Crashes happen when opening a specific file or using a specific feature.
- Only one program is affected while the rest of the system is fine.

## Diagnostic questions
- Is it one application or several?
- Does it crash on launch, after a while, or during a specific action?
- Did it start after an update to the app or to Windows?
- Does it crash with every file or only certain ones?
- Is there an error message or code?

## Step-by-step fixes

### Confirm the scope
1. Note whether other applications run normally. If many apps crash, treat it as a system issue (check memory, disk, and drivers) rather than an app issue.

### Basic resets
2. Close the app fully, including background instances via **Task Manager > Processes** (select it and **End task**), then reopen it.
3. Restart the PC to clear temporary conflicts and locked files.
4. Make sure Windows and the app are both fully updated.

### Give it a clean run
5. Try **Run as administrator** (right-click the app) if it needs elevated rights for certain features.
6. If the app has a compatibility option, right-click it, open **Properties > Compatibility**, and run the compatibility troubleshooter. This mainly helps older software.

### Reset the app's state
> **Warning:** Clearing an app's cache or settings reverts your preferences for that app. Note or export important settings first; this does not delete your documents.

7. Clear the app's cache or reset its settings if it offers that option. For modern Windows apps, use **Settings > Apps > Installed apps > (app) > Advanced options > Repair**, then **Reset** if repair does not help.
8. If a specific add-on, plugin, or extension was recently added, disable it and test.

### Investigate the cause
9. Open **Event Viewer** (`eventvwr.msc`) and check **Windows Logs > Application** for an error logged at the crash time. The faulting module named there often identifies the culprit.
10. Test whether a specific file triggers it. If one document crashes the app but others do not, that file may be corrupted.

### Repair or reinstall
> **Warning:** Back up any data stored inside the app before reinstalling. Uninstalling can remove app-specific data.

11. Use the app's built-in **Repair** option if available (via **Installed apps > Modify/Repair**).
12. If repair fails, uninstall and reinstall the app from the official source. For a stubborn case, remove leftover settings folders only if you know where they are and have backed them up.

## When to seek professional help
- Many unrelated apps crash, pointing to hardware or system corruption that deeper diagnostics should address.
- The app still crashes after a clean reinstall; contact the software vendor's support with the Event Viewer details.
- Crashes coincide with blue screens, which should be investigated as a system fault.
