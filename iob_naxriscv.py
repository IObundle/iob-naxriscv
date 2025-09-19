# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT

import os
import shutil


def setup(py_params_dict):
    # Each generated cpu verilog module must have a unique name due to different python parameters (can't have two differnet verilog modules with same name).
    assert "name" in py_params_dict, print(
        "Error: Missing name for generated naxriscv module."
    )

    params = {
        "reset_addr": 0x00000000,
        "uncached_start_addr": 0x00000000,
        "uncached_size": 2**32,
    }

    # Update params with values from py_params_dict
    for param in py_params_dict:
        if param in params:
            params[param] = py_params_dict[param]

    attributes_dict = {
        "name": py_params_dict["name"],
        "version": "0.1",
        "generate_hw": True,
        "confs": [
            {
                "name": "AXI_ID_W",
                "descr": "AXI ID bus width",
                "type": "P",
                "val": 0,
                "min": 0,
                "max": 32,
            },
            {
                "name": "AXI_ADDR_W",
                "descr": "AXI address bus width",
                "type": "P",
                "val": 0,
                "min": 0,
                "max": 32,
            },
            {
                "name": "AXI_DATA_W",
                "descr": "AXI data bus width",
                "type": "P",
                "val": 0,
                "min": 0,
                "max": 32,
            },
            {
                "name": "AXI_LEN_W",
                "descr": "AXI burst length width",
                "type": "P",
                "val": 0,
                "min": 0,
                "max": 4,
            },
        ],
        "ports": [
            {
                "name": "clk_en_rst_s",
                "descr": "Clock, clock enable and reset",
                "signals": {"type": "iob_clk"},
            },
            {
                "name": "rst_i",
                "descr": "Synchronous reset",
                "signals": [
                    {
                        "name": "rst_i",
                        "descr": "CPU synchronous reset",
                        "width": "1",
                    },
                ],
            },
            {
                "name": "i_bus_m",
                "descr": "CPU instruction bus",
                "signals": {
                    "type": "axi",
                    "prefix": "ibus_",
                    "ID_W": "AXI_ID_W",
                    "ADDR_W": "AXI_ADDR_W",
                    "DATA_W": "AXI_DATA_W",
                    "LEN_W": "AXI_LEN_W",
                    "LOCK_W": 1,
                },
            },
            {
                "name": "d_bus_m",
                "descr": "CPU data bus",
                "signals": {
                    "type": "axi",
                    "prefix": "dbus_",
                    "ID_W": "AXI_ID_W",
                    "ADDR_W": "AXI_ADDR_W",
                    "DATA_W": "AXI_DATA_W",
                    "LEN_W": "AXI_LEN_W",
                    "LOCK_W": 1,
                },
            },
            {
                "name": "clint_cbus_s",
                "descr": "CLINT CSRs bus",
                "signals": {
                    "type": "iob",
                    "prefix": "clint_",
                    "ADDR_W": 16,
                },
            },
            {
                "name": "plic_cbus_s",
                "descr": "PLIC CSRs bus",
                "signals": {
                    "type": "iob",
                    "prefix": "plic_",
                    "ADDR_W": 22,
                },
            },
            {
                "name": "plic_interrupts_i",
                "descr": "PLIC interrupts",
                "signals": [
                    {
                        "name": "plic_interrupts_i",
                        "descr": "PLIC interrupts",
                        "width": "32",
                    },
                ],
            },
        ],
        "wires": [
            {
                "name": "cpu_reset",
                "descr": "cpu reset signal",
                "signals": [
                    {"name": "cpu_reset", "width": "1"},
                ],
            },
            {
                "name": "dbus_int",
                "descr": "Internal cached data bus",
                "signals": {
                    "type": "axi",
                    "prefix": "dbus_int_",
                    "ID_W": "AXI_ID_W",
                    "ADDR_W": "AXI_ADDR_W",
                    "DATA_W": "AXI_DATA_W",
                    "LEN_W": "AXI_LEN_W",
                    "LOCK_W": 1,
                },
            },
            {
                "name": "pbus_axil_int",
                "descr": "Internal uncached AXI-Lite peripheral bus",
                "signals": {
                    "type": "axil",
                    "prefix": "pbus_int_",
                    "ADDR_W": "AXI_ADDR_W",
                    "DATA_W": "AXI_DATA_W",
                },
            },
            {
                "name": "pbus_axi_int",
                "descr": "Internal uncached AXI peripheral bus",
                "signals": {
                    "type": "axi",
                    "prefix": "pbus_int_",
                    "ID_W": "AXI_ID_W",
                    "ADDR_W": "AXI_ADDR_W",
                    "DATA_W": "AXI_DATA_W",
                    "LEN_W": "AXI_LEN_W",
                    "LOCK_W": 1,
                },
            },
            {
                "name": "clint_cbus_axil",
                "descr": "CLINT CSRs bus",
                "signals": {
                    "type": "axil",
                    "prefix": "clint_",
                    "ADDR_W": 16,
                    "DATA_W": "AXI_DATA_W",
                },
            },
            {
                "name": "plic_cbus_axil",
                "descr": "PLIC CSRs bus",
                "signals": {
                    "type": "axil",
                    "prefix": "plic_",
                    "ADDR_W": 22,
                    "DATA_W": "AXI_DATA_W",
                },
            },
            {
                "name": "unused_signals",
                "signals": [
                    {"name": "dbus_araddr_ignore_bit", "width": "1"},
                    {"name": "dbus_awaddr_ignore_bit", "width": "1"},
                ],
            },
        ],
        "subblocks": [
            {
                "core_name": "iob_iob2axil",
                "instance_name": "clint_iob2axil",
                "instance_description": "Convert IOb to AXI lite for CLINT",
                "parameters": {
                    "AXIL_ADDR_W": 16,
                    "AXIL_DATA_W": "AXI_DATA_W",
                },
                "connect": {
                    "iob_s": "clint_cbus_s",
                    "axil_m": "clint_cbus_axil",
                },
            },
            {
                "core_name": "iob_iob2axil",
                "instance_name": "plic_iob2axil",
                "instance_description": "Convert IOb to AXI lite for PLIC",
                "parameters": {
                    "AXIL_ADDR_W": 22,
                    "AXIL_DATA_W": "AXI_DATA_W",
                },
                "connect": {
                    "iob_s": "plic_cbus_s",
                    "axil_m": "plic_cbus_axil",
                },
            },
            {
                "core_name": "iob_axil2axi",
                "instance_name": "pbus_axil2axi",
                "instance_description": "Convert AXI-Lite to AXI for peripheral bus",
                "parameters": {
                    "AXI_ID_W": "AXI_ID_W",
                    "AXI_ADDR_W": "AXI_ADDR_W",
                    "AXI_DATA_W": "AXI_DATA_W",
                    "AXI_LEN_W": "AXI_LEN_W",
                    "AXI_LOCK_W": 1,
                },
                "connect": {
                    "axil_s": "pbus_axil_int",
                    "axi_m": "pbus_axi_int",
                },
            },
            {
                "core_name": "iob_axi_merge",
                "name": "iob_naxriscv_dbus_axi_merge",
                "instance_name": "dbus_axi_merge",
                "instance_description": "Merge internal data and peripheral buses into a single data bus",
                "addr_w": 33,  # Each subordinate has -1 address bit (32 bits each). Manager has 33 bits (1 ignored).
                "lock_w": 1,
                "parameters": {
                    "ID_W": "AXI_ID_W",
                    "LEN_W": "AXI_LEN_W",
                },
                "num_subordinates": 2,
                "connect": {
                    "clk_en_rst_s": "clk_en_rst_s",
                    "reset_i": "rst_i",
                    "s_0_s": "dbus_int",
                    "s_1_s": "pbus_axi_int",
                    "m_m": (
                        "d_bus_m",
                        [
                            # Ignore most significant address bit (we only use 32 bits)
                            "{dbus_araddr_ignore_bit, dbus_axi_araddr_o}",
                            "{dbus_awaddr_ignore_bit, dbus_axi_awaddr_o}",
                        ],
                    ),
                },
            },
        ],
        "snippets": [
            {
                "verilog_code": """
   wire [7:0] ibus_axi_arlen_int;
   wire [7:0] dbus_int_axi_arlen_int;
   wire [7:0] dbus_int_axi_awlen_int;


   // Instantiation of NaxRiscv, Plic, and Clint
   NaxRiscvAxi4LinuxPlicClint CPU (
      // CLINT
      .clint_awvalid(clint_axil_awvalid),
      .clint_awready(clint_axil_awready),
      .clint_awaddr(clint_axil_awaddr),
      .clint_awprot(3'd0),
      .clint_wvalid(clint_axil_wvalid),
      .clint_wready(clint_axil_wready),
      .clint_wdata(clint_axil_wdata),
      .clint_wstrb(clint_axil_wstrb),
      .clint_bvalid(clint_axil_bvalid),
      .clint_bready(clint_axil_bready),
      .clint_bresp(clint_axil_bresp),
      .clint_arvalid(clint_axil_arvalid),
      .clint_arready(clint_axil_arready),
      .clint_araddr(clint_axil_araddr),
      .clint_arprot(3'd0),
      .clint_rvalid(clint_axil_rvalid),
      .clint_rready(clint_axil_rready),
      .clint_rdata(clint_axil_rdata),
      .clint_rresp(clint_axil_rresp),
      // PLIC
      .plic_awvalid(plic_axil_awvalid),
      .plic_awready(plic_axil_awready),
      .plic_awaddr(plic_axil_awaddr),
      .plic_awprot(3'd0),
      .plic_wvalid(plic_axil_wvalid),
      .plic_wready(plic_axil_wready),
      .plic_wdata(plic_axil_wdata),
      .plic_wstrb(plic_axil_wstrb),
      .plic_bvalid(plic_axil_bvalid),
      .plic_bready(plic_axil_bready),
      .plic_bresp(plic_axil_bresp),
      .plic_arvalid(plic_axil_arvalid),
      .plic_arready(plic_axil_arready),
      .plic_araddr(plic_axil_araddr),
      .plic_arprot(3'd0),
      .plic_rvalid(plic_axil_rvalid),
      .plic_rready(plic_axil_rready),
      .plic_rdata(plic_axil_rdata),
      .plic_rresp(plic_axil_rresp),
      .plicInterrupts(plic_interrupts_i),
"""
                + f"""
      // Configuration ports
      .externalResetVector(32'h{params["reset_addr"]:x}),
      .ioStartAddr(32'h{params["uncached_start_addr"]:x}),
      .ioSize(32'h{params["uncached_size"]:x}),
"""
                + """
      // Instruction Bus
      .iBusAxi_arvalid(ibus_axi_arvalid_o),
      .iBusAxi_arready(ibus_axi_arready_i),
      .iBusAxi_araddr(ibus_axi_araddr_o),
      //.iBusAxi_arid(ibus_axi_arid_o), // Not available
      .iBusAxi_arlen(ibus_axi_arlen_int),
      .iBusAxi_arsize(ibus_axi_arsize_o),
      .iBusAxi_arburst(ibus_axi_arburst_o),
      //.iBusAxi_arlock(ibus_axi_arlock_o), // Not available
      //.iBusAxi_arcache(ibus_axi_arcache_o), // Not available
      //.iBusAxi_arqos(ibus_axi_arqos_o), // Not available
      .iBusAxi_arprot(),
      .iBusAxi_rvalid(ibus_axi_rvalid_i),
      .iBusAxi_rready(ibus_axi_rready_o),
      .iBusAxi_rdata(ibus_axi_rdata_i),
      //.iBusAxi_rid(ibus_axi_rid_i), // Not available
      .iBusAxi_rresp(ibus_axi_rresp_i),
      .iBusAxi_rlast(ibus_axi_rlast_i),
      // (Cached) Data Bus
      .dBusAxi_awvalid(dbus_int_axi_awvalid),
      .dBusAxi_awready(dbus_int_axi_awready),
      .dBusAxi_awaddr(dbus_int_axi_awaddr),
      .dBusAxi_awid(dbus_int_axi_awid),
      .dBusAxi_awlen(dbus_int_axi_awlen_int),
      .dBusAxi_awsize(dbus_int_axi_awsize),
      .dBusAxi_awburst(dbus_int_axi_awburst),
      //.dBusAxi_awlock(dbus_int_axi_awlock), // Not available
      //.dBusAxi_awcache(dbus_int_axi_awcache), // Not available
      //.dBusAxi_awqos(dbus_int_axi_awqos), // Not available
      .dBusAxi_awprot(),
      .dBusAxi_wvalid(dbus_int_axi_wvalid),
      .dBusAxi_wready(dbus_int_axi_wready),
      .dBusAxi_wdata(dbus_int_axi_wdata),
      .dBusAxi_wstrb(dbus_int_axi_wstrb),
      .dBusAxi_wlast(dbus_int_axi_wlast),
      .dBusAxi_bvalid(dbus_int_axi_bvalid),
      .dBusAxi_bready(dbus_int_axi_bready),
      .dBusAxi_bid(dbus_int_axi_bid),
      .dBusAxi_bresp(dbus_int_axi_bresp),
      .dBusAxi_arvalid(dbus_int_axi_arvalid),
      .dBusAxi_arready(dbus_int_axi_arready),
      .dBusAxi_araddr(dbus_int_axi_araddr),
      .dBusAxi_arid(dbus_int_axi_arid),
      .dBusAxi_arlen(dbus_int_axi_arlen_int),
      .dBusAxi_arsize(dbus_int_axi_arsize),
      .dBusAxi_arburst(dbus_int_axi_arburst),
      //.dBusAxi_arlock(dbus_int_axi_arlock), // Not available
      //.dBusAxi_arcache(dbus_int_axi_arcache), // Not available
      //.dBusAxi_arqos(dbus_int_axi_arqos), // Not available
      .dBusAxi_arprot(),
      .dBusAxi_rvalid(dbus_int_axi_rvalid),
      .dBusAxi_rready(dbus_int_axi_rready),
      .dBusAxi_rdata(dbus_int_axi_rdata),
      .dBusAxi_rid(dbus_int_axi_rid),
      .dBusAxi_rresp(dbus_int_axi_rresp),
      .dBusAxi_rlast(dbus_int_axi_rlast),
      // (Uncached) Peripheral Bus
      .pBus_awvalid(pbus_int_axil_awvalid),
      .pBus_awready(pbus_int_axil_awready),
      .pBus_awaddr(pbus_int_axil_awaddr),
      .pBus_awprot(),
      .pBus_wvalid(pbus_int_axil_wvalid),
      .pBus_wready(pbus_int_axil_wready),
      .pBus_wdata(pbus_int_axil_wdata),
      .pBus_wstrb(pbus_int_axil_wstrb),
      .pBus_bvalid(pbus_int_axil_bvalid),
      .pBus_bready(pbus_int_axil_bready),
      .pBus_bresp(pbus_int_axil_bresp),
      .pBus_arvalid(pbus_int_axil_arvalid),
      .pBus_arready(pbus_int_axil_arready),
      .pBus_araddr(pbus_int_axil_araddr),
      .pBus_arprot(),
      .pBus_rvalid(pbus_int_axil_rvalid),
      .pBus_rready(pbus_int_axil_rready),
      .pBus_rdata(pbus_int_axil_rdata),
      .pBus_rresp(pbus_int_axil_rresp),
      // Clock and Reset
      .clk(clk_i),
      .reset(cpu_reset)
  );



   assign cpu_reset = rst_i | arst_i;

   // Unused ibus write signals
   assign ibus_axi_awvalid_o = 1'b0;
   assign ibus_axi_awaddr_o = {AXI_ADDR_W{1'b0}};
   assign ibus_axi_awid_o = 1'b0;
   assign ibus_axi_awlen_o = {AXI_LEN_W{1'b0}};
   assign ibus_axi_awsize_o = {3{1'b0}};
   assign ibus_axi_awburst_o = {2{1'b0}};
   assign ibus_axi_awlock_o = 1'b0;
   assign ibus_axi_awcache_o = {4{1'b0}};
   assign ibus_axi_awqos_o = {4{1'b0}};
   assign ibus_axi_wvalid_o = 1'b0;
   assign ibus_axi_wdata_o = {AXI_DATA_W{1'b0}};
   assign ibus_axi_wstrb_o = {AXI_DATA_W / 8{1'b0}};
   assign ibus_axi_wlast_o = 1'b0;
   assign ibus_axi_bready_o = 1'b0;

   // Unused AXI signals
   assign ibus_axi_arid_o = 'b0;
   assign ibus_axi_arlock_o = 'b0;
   assign ibus_axi_arcache_o = 'b0;
   assign ibus_axi_arqos_o = 'b0;
   // ibus_axi_rid_i // Unused input
   assign dbus_int_axi_awlock = 'b0;
   assign dbus_int_axi_awcache = 'b0;
   assign dbus_int_axi_awqos = 'b0;
   assign dbus_int_axi_arlock = 'b0;
   assign dbus_int_axi_arcache = 'b0;
   assign dbus_int_axi_arqos = 'b0;

   generate
      if (AXI_LEN_W < 8) begin : gen_if_less_than_8
         assign ibus_axi_arlen_o = ibus_axi_arlen_int[AXI_LEN_W-1:0];
         assign dbus_int_axi_arlen = dbus_int_axi_arlen_int[AXI_LEN_W-1:0];
         assign dbus_int_axi_awlen = dbus_int_axi_awlen_int[AXI_LEN_W-1:0];
      end else begin : gen_if_equal_8
         assign ibus_axi_arlen_o = ibus_axi_arlen_int;
         assign dbus_int_axi_arlen = dbus_int_axi_arlen_int;
         assign dbus_int_axi_awlen = dbus_int_axi_awlen_int;
      end
   endgenerate
"""
            }
        ],
    }

    if py_params_dict.get("py2hwsw_target", "") == "setup":
        build_dir = py_params_dict.get("build_dir")
        # Disable linter for `NaxRiscvAxi4LinuxPlicClint.v` source.
        os.makedirs(f"{build_dir}/hardware/lint/verilator", exist_ok=True)
        with open(f"{build_dir}/hardware/lint/verilator_config.vlt", "a") as file:
            file.write(
                f"""
// Lines generated by {os.path.basename(__file__)}
lint_off -file "*/NaxRiscvAxi4LinuxPlicClint.v"
"""
            )
        # Copy CPU memory initialization binaries to build directory
        os.makedirs(f"{build_dir}/hardware/simulation", exist_ok=True)
        os.makedirs(f"{build_dir}/hardware/fpga", exist_ok=True)
        mem_bin_dir = f"{os.path.dirname(__file__)}/hardware/init_mems"
        bin_files = os.listdir(mem_bin_dir)
        for file in bin_files:
            # copy binaries to simulation directory
            shutil.copyfile(
                f"{mem_bin_dir}/{file}", f"{build_dir}/hardware/simulation/{file}"
            )
            # symlink binaries in fpga directory as well
            os.symlink(
                f"../simulation/{file}",
                f"{build_dir}/hardware/fpga/{file}",
            )

    return attributes_dict
