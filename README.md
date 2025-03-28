[![Documentation Status](https://readthedocs.org/projects/qilingframework/badge/?version=latest)](https://docs.qiling.io)
[![Downloads](https://pepy.tech/badge/qiling)](https://pepy.tech/project/qiling)
[![Chat on Telegram](https://img.shields.io/badge/Chat%20on-Telegram-brightgreen.svg)](https://t.me/qilingframework)

---

<p align="center">
<img width="150" height="150" src="https://raw.githubusercontent.com/qilingframework/qiling/master/docs/qiling2_logo_small.png">
</p>

[Qiling's use case, blog and related work](https://github.com/qilingframework/qiling/issues/134)

Qiling is an advanced binary emulation framework, with the following features:

- Emulate multi-platforms: Windows, macOS, Linux, Android, BSD, UEFI, DOS, MBR.
- Emulate multi-architectures: 8086, X86, X86_64, ARM, ARM64, MIPS, RISC-V, PowerPC.
- Support multiple file formats: PE, Mach-O, ELF, COM, MBR.
- Support Windows Driver (.sys), Linux Kernel Module (.ko) & macOS Kernel (.kext) via [Demigod](https://groundx.io/demigod/).
- Emulates & sandbox code in an isolated environment.
- Provides a fully configurable sandbox.
- Provides in-depth memory, register, OS level and filesystem level API.
- Fine-grain instrumentation: allows hooks at various levels
  (instruction/basic-block/memory-access/exception/syscall/IO/etc.)
- Provides virtual machine level API such as saving and restoring the current execution state.
- Supports cross architecture and platform debugging capabilities.
- Built-in debugger with reverse debugging capability.
- Allows dynamic hot patch on-the-fly running code, including the loaded library.
- True framework in Python, making it easy to build customized security analysis tools on top.

Qiling also made its way to various international conferences.

2022:
- [Black Hat, EU](https://www.blackhat.com/eu-22/arsenal/schedule/#reversing-mcu-with-firmware-emulation-29553)
- [Black Hat, MEA](https://blackhatmea.com/node/724)

2021:
- [Black Hat, USA](https://www.blackhat.com/us-21/arsenal/schedule/index.html#bringing-the-x-complete-re-experience-to-smart-contract-24119)
- [Hack In The Box, Amsterdam](https://conference.hitb.org/hitbsecconf2021ams/sessions/when-qiling-framework-meets-symbolic-execution/)
- [Black Hat, Asia](https://www.blackhat.com/asia-21/arsenal/schedule/index.html#qiling-smart-analysis-for-smart-contract-22643)

2020:
- [Black Hat, Europe](https://www.blackhat.com/eu-20/arsenal/schedule/index.html#qiling-framework-deep-dive-into-obfuscated-binary-analysis-21781)
- [Black Hat, USA](https://www.blackhat.com/us-20/arsenal/schedule/index.html#qiling-framework-from-dark-to-dawn-----enlightening-the-analysis-of-the-most-mysterious-iot-firmware--21062)
- [Black Hat, USA (Demigod)](https://www.blackhat.com/us-20/briefings/schedule/#demigod-the-art-of-emulating-kernel-rootkits-20009)
- [Black Hat, Asia](https://www.blackhat.com/asia-20/arsenal/schedule/index.html#qiling-lightweight-advanced-binary-analyzer-19245)
- [Hack In The Box, Lockdown 001](https://conference.hitb.org/lockdown-livestream/)
- [Hack In The Box, Lockdown 002](https://conference.hitb.org/hitb-lockdown002/virtual-labs/virtual-lab-qiling-framework-learn-how-to-build-a-fuzzer-based-on-a-1day-bug/)
- [Hack In The Box, Cyberweek](https://cyberweek.ae/2020/lab-qiling-framework/)
- [Nullcon](https://nullcon.net/website/goa-2020/speakers/kaijern-lau.php)
    
2019:

- [DEFCON, USA](https://www.defcon.org/html/defcon-27/dc-27-demolabs.html#QiLing)
- [Hitcon](https://hitcon.org/2019/CMT/agenda)
- [Zeronights](https://zeronights.ru/report-en/qiling-io-advanced-binary-emulation-framework/)


Qiling is backed by [Unicorn Engine](http://www.unicorn-engine.org).

Visit our [website](https://www.qiling.io) for more information.

---
#### License

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

---

#### Qiling vs. other Emulators

There are many open-source emulators, but two projects closest to Qiling
are [Unicorn](http://www.unicorn-engine.org) & [QEMU user mode](https://qemu.org).
This section explains the main differences of Qiling against them.

##### Qiling vs. Unicorn engine

Built on top of Unicorn, but Qiling & Unicorn are two different animals.

- Unicorn is just a CPU emulator, so it focuses on emulating CPU instructions,
  that can understand emulator memory.
  Beyond that, Unicorn is not aware of higher level concepts, such as dynamic
  libraries, system calls, I/O handling or executable formats like PE, Mach-O
  or ELF. As a result, Unicorn can only emulate raw machine instructions,
  without Operating System (OS) context.
- Qiling is designed as a higher level framework, that leverages Unicorn to
  emulate CPU instructions, but can understand OS: it has executable format
  loaders (for PE, Mach-O & ELF currently), dynamic linkers (so we can
  load & relocate shared libraries), syscall & IO handlers. For this reason,
  Qiling can run executable binary without requiring its native OS.

##### Qiling vs. QEMU user mode

QEMU user mode does a similar thing to our emulator, that is, to emulate whole
executable binaries in a cross-architecture way. 
However, Qiling offers some important differences against QEMU user mode:

- Qiling is a true analysis framework,
  that allows you to build your own dynamic analysis tools on top (in Python).
  Meanwhile, QEMU is just a tool, not a framework.
- Qiling can perform dynamic instrumentation, and can even hot patch code at
  runtime. QEMU does neither.
- Not only working cross-architecture, Qiling is also cross-platform.
  For example, you can run Linux ELF file on top of Windows.
  In contrast, QEMU user mode only runs binary of the same OS, such as Linux
  ELF on Linux, due to the way it forwards syscall from emulated code to
  native OS.
- Qiling supports more platforms, including Windows, macOS, Linux & BSD. QEMU
  user mode can only handle Linux & BSD.

---

#### Installation

Please see [setup guide](https://docs.qiling.io/en/latest/install/) file for how to install Qiling Framework.

---

#### Examples

The example below shows how to use Qiling framework in the most
straightforward way to emulate a Windows executable.

```python
from qiling import Qiling

if __name__ == "__main__":
    # initialize Qiling instance, specifying the executable to emulate and the emulated system root.
    # note that the current working directory is assumed to be Qiling home
    ql = Qiling([r'examples/rootfs/x86_windows/bin/x86_hello.exe'], r'examples/rootfs/x86_windows')

    # start emulation
    ql.run()
```

- The following example shows how a Windows crackme may be patched dynamically
  to make it always display the “Congratulation” dialog.

```python
from qiling import Qiling

def force_call_dialog_func(ql: Qiling):
    # get DialogFunc address from current stack frame
    lpDialogFunc = ql.stack_read(-8)

    # setup stack memory for DialogFunc
    ql.stack_push(0)
    ql.stack_push(1001)     # IDS_APPNAME
    ql.stack_push(0x111)    # WM_COMMAND
    ql.stack_push(0)

    # push return address
    ql.stack_push(0x0401018)

    # resume emulation from DialogFunc address
    ql.arch.regs.eip = lpDialogFunc


if __name__ == "__main__":
    # initialize Qiling instance
    ql = Qiling([r'rootfs/x86_windows/bin/Easy_CrackMe.exe'], r'rootfs/x86_windows')

    # NOP out some code
    ql.patch(0x004010B5, b'\x90\x90')
    ql.patch(0x004010CD, b'\x90\x90')
    ql.patch(0x0040110B, b'\x90\x90')
    ql.patch(0x00401112, b'\x90\x90')

    # hook at an address with a callback
    ql.hook_address(force_call_dialog_func, 0x00401016)
    ql.run()
```

The below YouTube video shows how the above example works.

#### Emulating ARM router firmware on Ubuntu x64 host

Qiling Framework hot-patches and emulates an ARM router's `/usr/bin/httpd` on
an x86_64 Ubuntu host.

[![Qiling Tutorial: Emulating and Fuzz ARM router firmware](https://github.com/qilingframework/theme.qiling.io/blob/master/source/img/fuzzer.jpg?raw=true)](https://www.youtube.com/watch?v=e3_T3KLh2NU)

#### Qiling's IDA Pro Plugin: Instrument and Decrypt Mirai's Secret

This video demonstrates how Qiling's IDA Pro plugin can make IDA Pro run with
Qiling instrumentation engine.

[![Qiling's IDA Pro Plugin: Instrument and Decrypt Mirai's Secret](http://img.youtube.com/vi/ZWMWTq2WTXk/0.jpg)](http://www.youtube.com/watch?v=ZWMWTq2WTXk)

#### GDB server with IDA Pro demo

Solving a simple CTF challenge with Qiling Framework and IDA Pro

[![Solving a simple CTF challenge with Qiling Framework and IDA Pro](https://i.ytimg.com/vi/SPjVAt2FkKA/0.jpg)](https://www.youtube.com/watch?v=SPjVAt2FkKA)


#### Emulating MBR

Qiling Framework emulates MBR

[![Qiling DEMO: Emulating MBR](https://github.com/qilingframework/theme.qiling.io/blob/master/source/img/mbr.png?raw=true)](https://github.com/qilingframework/theme.qiling.io/blob/master/source/img/mbr.png?raw=true)

---

#### Qltool

Qiling also provides a friendly tool named `qltool` to quickly emulate shellcode & executable binaries.

With qltool, easy execution can be performed:


With shellcode:

```
$ ./qltool code --os linux --arch arm --format hex -f examples/shellcodes/linarm32_tcp_reverse_shell.hex
```

With binary file:

```
$ ./qltool run -f examples/rootfs/x8664_linux/bin/x8664_hello --rootfs  examples/rootfs/x8664_linux/
```

With binary and GDB debugger enabled:

```
$ ./qltool run -f examples/rootfs/x8664_linux/bin/x8664_hello --gdb 127.0.0.1:9999 --rootfs examples/rootfs/x8664_linux
```

With code coverage collection (UEFI only for now):

```
$ ./qltool run -f examples/rootfs/x8664_efi/bin/TcgPlatformSetupPolicy --rootfs examples/rootfs/x8664_efi --coverage-format drcov --coverage-file TcgPlatformSetupPolicy.cov
```

With JSON output (Windows, mainly):

```
$ ./qltool run -f examples/rootfs/x86_windows/bin/x86_hello.exe --rootfs  examples/rootfs/x86_windows/ --console False --json
```
---


#### Contact

Get the latest info from our website https://www.qiling.io

Contact us at email info@qiling.io,
via Twitter [@qiling_io](https://twitter.com/qiling_io).

---

#### Core developers, Key Contributors and etc.

Please refer to [CREDITS.md](https://github.com/qilingframework/qiling/blob/dev/CREDITS.md).
