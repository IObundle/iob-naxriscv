<!--
SPDX-FileCopyrightText: 2025 IObundle

SPDX-License-Identifier: MIT
-->

# iob-naxriscv
This repository contains the hardware necessary to integrate the NaxRiscv CPU on IOb-SoC.

## Requirements
- scala sbt: instructions of how to download can be found in https://www.scala-sbt.org/download.html;

## Makefile Targets
- Naxriscv: build the Verilog RTL NaxRiscv CPU core.
- clean-all: do all of the cleaning above

## Makefile Variables
- CPU: by default it has the value `LinuxGen`. However, the value could be any of the CPUs present in the NaxRiscv demo directory (`submodules/NaxRiscv/src/main/scala/Naxriscv/demo`).

## Example:
To generate a new NaxRiscv.v simply do:
- `make Naxriscv CPU=LinuxGen`
