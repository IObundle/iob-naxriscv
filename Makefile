# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT

#PATHS
NAXRISCV_DIR ?= $(shell pwd)
NAX_HARDWARE_DIR:=$(NAXRISCV_DIR)/hardware
NAXRISCV_SRC_DIR:=$(NAX_HARDWARE_DIR)/src
NAX_SUBMODULES_DIR:=$(NAXRISCV_DIR)/submodules

# Rules
.PHONY: naxriscv clean-all qemu

CPU ?= NaxRiscvAxi4LinuxPlicClint
JDK_HOME := $(shell dirname $$(dirname $$(which java)))

# Primary targets
naxriscv:
	#mkdir -p $(NAX_SUBMODULES_DIR)/NaxRiscv/src/main/scala/naxriscv/platform/asic
	cp $(NAX_HARDWARE_DIR)/naxriscv_core/NaxRiscvAxi4LinuxPlicClint.scala $(NAX_SUBMODULES_DIR)/NaxRiscv/src/main/scala/naxriscv/platform/asic/
	cp $(NAX_HARDWARE_DIR)/naxriscv_core/PcPlugin.scala $(NAX_SUBMODULES_DIR)/NaxRiscv/src/main/scala/naxriscv/fetch/
	cp $(NAX_HARDWARE_DIR)/naxriscv_core/MmuPlugin.scala $(NAX_SUBMODULES_DIR)/NaxRiscv/src/main/scala/naxriscv/misc/
	# (Re-)try to apply these patches: https://github.com/SpinalHDL/NaxRiscv/issues/140#issuecomment-2725576402
	-make -C submodules/NaxRiscv install-core
	# Run sbt to build CPU and copy generated verilog to this repo
	cd submodules/NaxRiscv && \
	sbt -java-home $(JDK_HOME) "runMain naxriscv.platform.asic.$(CPU)" && \
	cp $(CPU).v $(NAXRISCV_SRC_DIR)/$(CPU).v

#
# Clean
#
clean-naxriscv:
	rm $(NAXRISCV_SRC_DIR)/$(CPU).v

clean-all: clean-naxriscv
