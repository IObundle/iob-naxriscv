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
	# FIXME: Choose a .scala demo, include PLIC/CLINT, and copy to correct submodule directory.
	cp $(NAX_HARDWARE_DIR)/naxriscv_core/NaxRiscvAxi4LinuxPlicClint.scala $(NAX_SUBMODULES_DIR)/NaxRiscv/src/main/scala/naxriscv/demo/
	#cp $(NAX_HARDWARE_DIR)/naxriscv_core/MmuPlugin.scala $(NAX_SUBMODULES_DIR)/NaxRiscv/src/main/scala/naxriscv/plugin/
	cd submodules/NaxRiscv && \
	sbt -java-home $(JDK_HOME) "runMain naxriscv.demo.$(CPU)" && \
	cp $(CPU).v $(NAXRISCV_SRC_DIR)

#
# Clean
#
clean-naxriscv:
	rm $(NAXRISCV_SRC_DIR)/$(CPU).v

clean-all: clean-naxriscv
