# RAM (Memory) Troubleshooting

## Overview
System memory (RAM) problems cause crashes, blue screens, random restarts, corrupted files, and failures to boot. Faults come from a module that is seated loosely, a genuinely defective stick, incompatible modules, or unstable memory speed settings. Testing is non-destructive and should always come before replacing parts.

## Common symptoms
- Random blue screens, especially `MEMORY_MANAGEMENT` or `PAGE_FAULT_IN_NONPAGED_AREA`.
- The PC fails to boot and beeps, or the display stays blank.
- Apps crash or files become corrupted intermittently.
- Reported installed memory is less than what is physically fitted.
- Instability that appears only after enabling a memory speed profile.

## Diagnostic questions
- Do crashes happen randomly or under specific load?
- Did the problem start after adding or moving memory modules?
- How much RAM is installed, and how much does Windows report?
- Was a memory overclock or speed profile recently enabled?
- Are crashes reproducible, or completely random?

## Step-by-step fixes

### Confirm what the system sees
1. Open **Task Manager > Performance > Memory** to see total installed memory and current usage. Compare the reported total with what is physically installed.
2. If the reported amount is wrong, a module may be seated poorly or not detected.

### Run a memory test
3. Run **Windows Memory Diagnostic** (`mdsched.exe`) and allow it to test on restart. For a more thorough test, a dedicated bootable memory tester run for several passes is more reliable.
4. If a test reports errors, you very likely have a failing module or an unstable speed setting.

### Reset unstable speed settings
> **Warning:** Firmware (BIOS/UEFI) changes can prevent booting. Note the current values first and change one setting at a time.

5. If a memory overclock or speed profile is enabled, disable it so memory runs at its default speed, then retest. Many "bad RAM" cases are just an over-aggressive profile.

### Reseat and isolate modules
> **Warning:** Power off, unplug, and discharge static by touching a bare metal part of the case before touching components. For laptops, this may void a warranty or be impractical; skip if unsure.

6. For a desktop, open the case, remove each memory module, and reseat it firmly until the clips latch. Oxidized or loose contacts cause many intermittent faults.
7. If errors persist, test with one module at a time in a known-good slot. If one module passes alone and another fails, you have found the bad stick. If a single module fails in one slot but works in another, the slot may be the problem.

### Verify compatibility
8. When mixing modules, confirm they are supported by the motherboard and ideally matched in capacity and speed. Mismatched memory can run unstably or refuse to post.

## When to seek professional help
- A module consistently fails memory tests and needs replacement, and you are not comfortable opening the device.
- The motherboard memory slot appears faulty.
- The device is a laptop with soldered or hard-to-reach memory.
