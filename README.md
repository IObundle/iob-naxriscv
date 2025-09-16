<!--
SPDX-FileCopyrightText: 2025 IObundle

SPDX-License-Identifier: MIT
-->

# iob-naxriscv
This repository contains the hardware necessary to integrate the NaxRiscv CPU on IOb-SoC.

## Requirements
- scala sbt: instructions of how to download can be found in https://www.scala-sbt.org/download.html;

This repository also provides the `shell.nix` file that can be used with [nix-shell](https://nixos.org/download.html#nix-install-linux) to create an environment with all the necessary tools, including sbt.
Run `nix-shell` from the root of the repository to create the environment.

## Makefile Targets
- naxriscv: build the Verilog RTL NaxRiscv CPU core.
- clean-all: do all of the cleaning above

## Makefile Variables
- CPU: by default it has the value `NaxRiscvAxi4LinuxPlicClint`. However, the value could be any of the CPUs present in the NaxRiscv platform directory (`submodules/NaxRiscv/src/main/scala/naxriscv/platform/`).

## Example:
To generate a new NaxRiscv.v simply do:
- `make naxriscv`
