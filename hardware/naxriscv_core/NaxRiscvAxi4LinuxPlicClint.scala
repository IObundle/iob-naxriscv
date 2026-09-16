// SPDX-FileCopyrightText: 2025 IObundle
//
// SPDX-License-Identifier: MIT

package naxriscv.platform.asic

import naxriscv.{Config, NaxRiscv}
import naxriscv.compatibility.{CombRamBlackboxer, EnforceSyncRamPhase, MemReadDuringWriteHazardPhase, MemReadDuringWritePatcherPhase, MultiPortWritesSymplifier}
import naxriscv.debug.EmbeddedJtagPlugin
import naxriscv.fetch.FetchCachePlugin
import naxriscv.lsu.DataCachePlugin
import naxriscv.lsu2.Lsu2Plugin
import naxriscv.prediction.{BtbPlugin, GSharePlugin}
import naxriscv.utilities.DocPlugin
import spinal.core._
import spinal.lib._
import spinal.lib.eda.bench.Rtl

import spinal.lib.bus.amba4.axi.{Axi4ReadOnly, Axi4SpecRenamer}
import spinal.lib.bus.amba4.axilite.AxiLite4SpecRenamer
import naxriscv.misc.PrivilegedPlugin
import naxriscv.fetch.PcPlugin

object NaxRiscvAxi4LinuxPlicClint extends App{
  var ramBlocks = "inferred"
  var regFileFakeRatio = 1
  var withLsu = true // Add Load/Store Unit
  var withIoFf = false // Add a Flip-Flops to the IO
  var withRfLatchRam = true // Use Latch RAM for the Register File
  var blackBoxCombRam = false

  assert(new scopt.OptionParser[Unit]("NaxAsicGen") {
    help("help").text("prints this usage text")
    opt[Int]("regfile-fake-ratio") action { (v, c) => regFileFakeRatio = v }
    opt[Unit]("no-lsu") action { (v, c) => withLsu = false }
    opt[Unit]("io-ff") action { (v, c) => withIoFf = true }
    opt[Unit]("no-rf-latch-ram") action { (v, c) => withRfLatchRam = false }
    opt[Unit]("bb-comb-ram") action { (v, c) => blackBoxCombRam = true }
  }.parse(args, Unit).nonEmpty)


  LutInputs.set(4)
  def plugins = {
    // By default Nax is configured for 32-bit RV (xlen=32).
    // Nax always supports the following RV32 extensions: IM
    // Using the default configuration, it also supports Nax the following RV32 extensions: ASU
    // By modifying the config, it is also possible to enable the following extensions: FDC
    // With current config, it is using: rv32imasu
    val l = Config.plugins(
      resetVector = null, // Setting to null will cause externalResetVector to be an input port
      asic = false, // Target is an ASIC implementation (not FPGA); enables ASIC-specific optimizations
      withRfLatchRam = withRfLatchRam, // Whether to use latch-based RAM for the register file (vs SRAM macros)
      withRdTime = false, // Disable 'read time' CSR support (e.g. cycle counter read timing)
      aluCount    = 1, // Number of integer ALU execution units (arithmetic logic units)
      decodeCount = 1, // Number of instructions decoded simultaneously per cycle
      debugTriggers = 4, // Number of debug trigger hardware units for breakpoints/watchpoints
      withDedicatedLoadAgu = false, // Disable dedicated Load Address Generation Unit separate from ALU
      withRvc = true, // Enable RISC-V Compressed Instruction (RVC) extension support (extension C)
      withLoadStore = withLsu, // Enable Load/Store Unit plugin (memory access handling) (extension A)
      withMmu = withLsu, // Enable Memory Management Unit for virtual memory (depends on LSU)
      withPerfCounters = false, // Disable performance counters hardware // Disabled because throws errors with AXI4 dbus for some reason
      withDebug = false, // Disable debug hardware support
      withEmbeddedJtagTap = false, // Disable embedded JTAG TAP controller for external debug
      jtagTunneled = false, // Disable tunneling JTAG through other interfaces
      withFloat = false, // Disable single-precision floating point instruction support (extension F)
      withDouble = false, // Disable double-precision floating point instruction support (extension D)
      withLsu2 = true, // Enable secondary Load/Store Unit for increased memory parallelism
      lqSize = 8, // Size of Load Queue (buffer for tracking in-flight load instructions)
      sqSize = 8, // Size of Store Queue (buffer for tracking in-flight store instructions)
      dispatchSlots = 8, // Number of instruction dispatch slots available per cycle
      robSize = 16, // Size of Reorder Buffer (number of instructions tracked for out-of-order commit)
      branchCount = 4, // Number of branch instructions that can be tracked in flight
      mmuSets = 4, // Number of MMU sets (associativity) for page table translation caching
      regFileFakeRatio = regFileFakeRatio, // Controls ratio for fake register file replication (implementation-specific optimization)
      // withCoherency = true, // Enable cache/memory coherency extensions
      ioRange = null, // Setting to null will cause ioRange and ioSize to be input ports
      memRange = _ => True, // By default CPU only allows memory addresses above 0x80000000. This change allows it to access entire address space as memory.
      fetchRange = _ => True, // By default CPU disallows fetching instructions from ioRange. This change allows it to access entire address space to fetch instructions.

      // Full config and their default values (for reference)
      // resetVector : BigInt = 0x80000000l,  // CPU reset start address (default 0x80000000)
      // withRdTime : Boolean = true,          // Enable reading precise time CSR support
      // ioRange    : UInt => Bool = _(31 downto 28) === 0x1,  // Address range predicate for IO devices
      // memRange   : UInt => Bool = _(31),   // Address range predicate for main memory
      // fetchRange : UInt => Bool = _(31 downto 28) =/= 0x1, // Address range predicate for fetch memory
      // aluCount : Int = 2,                   // Number of integer ALUs (execution units)
      // decodeCount : Int = 2,                // Number of instructions decoded per cycle
      // withRvc : Boolean = false,            // Enable/disable support for compressed (16-bit) RISC-V instructions (extension C)
      // withMmu : Boolean = true,             // Enable/disable memory management unit (virtual memory)
      // withPerfCounters : Boolean = true,   // Enable performance counters (cycle, instructions, etc.)
      // withSupervisor : Boolean = true,     // Enable supervisor privilege mode (extension S)
      // withUser : Boolean = true,            // Enable user privilege mode (extension U)
      // withDistributedRam : Boolean = true, // Use distributed RAM for register files or caches
      // xlen : Int = 32,                      // CPU register width (32-bit or 64-bit)
      // withLoadStore : Boolean = true,      // Enable load/store unit (memory operations)
      // withDedicatedLoadAgu : Boolean = false, // Use dedicated load address generation unit separate from ALU
      // withDebug : Boolean = false,          // Enable debug support features
      // withEmbeddedJtagTap : Boolean = false,// Include embedded JTAG TAP controller for debugging
      // withEmbeddedJtagInstruction : Boolean = false, // Include embedded JTAG instruction support
      // jtagTunneled : Boolean = false,      // Enable tunneling of JTAG over other interfaces
      // debugTriggers : Int = 0,              // Number of hardware debug trigger units
      // branchCount : Int = 16,               // Number of branch instructions tracked simultaneously
      // withFloat  : Boolean = false,         // Enable single-precision floating point instructions (extension F)
      // withDouble : Boolean = false,         // Enable double-precision floating point instructions (extension D)
      // withLsu2: Boolean = true,             // Enable secondary load/store unit for parallel memory ops (extension A)
      // keepMulInput: Boolean = true,         // Preserve multiplier input values (debug or verification use)
      // keepMulOutput: Boolean = true,        // Preserve multiplier output values (debug or verification use)
      // lqSize : Int = 16,                    // Load queue size (in-flight loads tracked)
      // sqSize : Int = 16,                    // Store queue size (in-flight stores tracked)
      // simulation : Boolean = GenerationFlags.simulation, // Flag indicating simulation mode
      // sideChannels : Boolean = false,       // Enable side channel countermeasures or tracking
      // dispatchSlots : Int = 32,             // Number of slots for instruction dispatch per cycle
      // robSize : Int = 64,                   // Size of the reorder buffer (out-of-order tracking capacity)
      // withCoherency : Boolean = false,      // Enable cache/memory coherency extensions
      // hartId : Int = 0,                    // Hardware thread ID (for multi-core or multi-hart systems)
      // asic : Boolean = false,               // Target ASIC implementation rather than FPGA
      // withRfLatchRam : Boolean = false,    // Use latch-based RAM for register file implementation
      // mmuSets : Int = 32,                  // Number of MMU sets (associativity) in TLB
      // regFileFakeRatio : Int = 1,          // Ratio used in fake register file optimization
    )

    l.foreach{
      case p : EmbeddedJtagPlugin => p.debugCd.load(ClockDomain.current.copy(reset = Bool().setName("debug_reset")))
      case _ =>
    }

    ramBlocks match {
      case "inferred" => l.foreach {
        case p: FetchCachePlugin => p.wayCount = 1; p.cacheSize = 256; p.fetchDataWidth = 32; p.memDataWidth = 32
        case p: DataCachePlugin => p.wayCount = 1; p.cacheSize = 256; p.memDataWidth = 32
        case p: BtbPlugin => p.entries = 8
        case p: GSharePlugin => p.memBytes = 32
        case p: Lsu2Plugin => p.hitPedictionEntries = 64
        case _ =>
      }
    }
    l
  }

  var spinalConfig = ramBlocks match {
    case "inferred" => SpinalConfig()
  }

  if(blackBoxCombRam) spinalConfig.memBlackBoxers += new CombRamBlackboxer()

  def gen = {
    val cpu = new NaxRiscv(plugins)
    cpu.setDefinitionName("NaxRiscvAxi4LinuxPlicClint")
    // CPU modifications to be an Avalon one
    cpu.rework {
      for (plugin <- cpu.plugins) plugin match {
        // Convert IBus to Axi4
        case plugin: FetchCachePlugin => {
          val native = plugin.mem.setAsDirectionLess //Unset IO properties of mem bus
          val axi = master(native.toAxi4())
              .setName("iBusAxi")
              .addTag(ClockDomainTag(ClockDomain.current)) //Specify a clock domain to the ibus (used by QSysify)
          Axi4SpecRenamer(axi)
        }
        // Convert DBus to Axi4
        case plugin: DataCachePlugin => {
          val native = plugin.mem.setAsDirectionLess //Unset IO properties of mem bus
          val axi = master(native.toAxi4())
              .setName("dBusAxi")
              .addTag(ClockDomainTag(ClockDomain.current)) //Specify a clock domain to the dbus (used by QSysify)
          Axi4SpecRenamer(axi)
        }
        // Convert PBus to Axi4
        case plugin: Lsu2Plugin => {
          val native = plugin.peripheralBus.setAsDirectionLess //Unset IO properties of peripheral bus
          val axi = master(native.toAxiLite4())
              .setName("pBus")
              .addTag(ClockDomainTag(ClockDomain.current)) //Specify a clock domain to the dbus (used by QSysify)
          AxiLite4SpecRenamer(axi)
        }
        case _ =>
      }
    }
    cpu
  }

  // Generate with simulation in mind (initialize memories).
  spinalConfig.includeSimulation.generateVerilog(if(withIoFf) Rtl.ffIo(gen) else gen)
//  spinalConfig.generateVerilog(new StreamFifo(UInt(4 bits), 256).setDefinitionName("nax"))
}
