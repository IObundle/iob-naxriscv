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

import spinal.lib.misc.AxiLite4Clint
import spinal.lib.misc.plic.AxiLite4Plic
import spinal.lib.bus.amba4.axi.{Axi4ReadOnly, Axi4SpecRenamer}
import spinal.lib.bus.amba4.axilite.AxiLite4SpecRenamer
import naxriscv.misc.PrivilegedPlugin

object NaxRiscvAxi4LinuxPlicClint extends App{
  var ramBlocks = "inferred"
  var regFileFakeRatio = 1
  var withLsu = true // Add Load/Store Unit
  var withIoFf = false // Add a Flip-Flops to the IO
  var withRfLatchRam = true // Add a RAM to the Register File
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
    val l = Config.plugins(
      asic = true,
      withRfLatchRam = withRfLatchRam,
      withRdTime = false,
      aluCount    = 1,
      decodeCount = 1,
      debugTriggers = 4,
      withDedicatedLoadAgu = false,
      withRvc = false,
      withLoadStore = withLsu,
      withMmu = withLsu,
      withPerfCounters = false, // Disabled because throws errors with AXI4 dbus for some reason
      withDebug = false,
      withEmbeddedJtagTap = false,
      jtagTunneled = false,
      withFloat = false,
      withDouble = false,
      withLsu2 = true,
      lqSize = 8,
      sqSize = 8,
      dispatchSlots = 8,
      robSize = 16,
      branchCount = 4,
      mmuSets = 4,
      regFileFakeRatio = regFileFakeRatio,
      //      withCoherency = true,
      ioRange = a => a(31 downto 28) === 0x1// || !a(12)//(a(5, 6 bits) ^ a(12, 6 bits)) === 51
    )

    l.foreach{
      case p : EmbeddedJtagPlugin => p.debugCd.load(ClockDomain.current.copy(reset = Bool().setName("debug_reset")))
      case _ =>
    }

    ramBlocks match {
      case "inferred" => l.foreach {
        case p: FetchCachePlugin => p.wayCount = 1; p.cacheSize = 256; p.memDataWidth = 64
        case p: DataCachePlugin => p.wayCount = 1; p.cacheSize = 256; p.memDataWidth = 64
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
    val cpu = new NaxRiscv(plugins){
        val clintCtrl = new AxiLite4Clint(1, bufferTime = false)
        val plicCtrl = new AxiLite4Plic(
          sourceCount = 31,
          targetCount = 2
        )

        val clint = clintCtrl.io.bus.toIo()
        val plic = plicCtrl.io.bus.toIo()
        val plicInterrupts = in Bits(32 bits)
        plicCtrl.io.sources := plicInterrupts >> 1

        AxiLite4SpecRenamer(clint)
        AxiLite4SpecRenamer(plic)
    }
    cpu.setDefinitionName("NaxRiscvAxi4LinuxPlicClint")
    // CPU modifications to be an Avalon one
    cpu.rework {
      for (plugin <- cpu.plugins) plugin match {
        case plugin: FetchCachePlugin => {
          val native = plugin.mem.setAsDirectionLess //Unset IO properties of mem bus
          val axi = master(native.resizer(32).toAxi4())
              .setName("iBusAxi")
              .addTag(ClockDomainTag(ClockDomain.current)) //Specify a clock domain to the ibus (used by QSysify)
          Axi4SpecRenamer(axi)
        }
        case plugin: DataCachePlugin => {
          val native = plugin.mem.setAsDirectionLess //Unset IO properties of mem bus
          val axi = master(native.resizer(32).toAxi4())
              .setName("dBusAxi")
              .addTag(ClockDomainTag(ClockDomain.current)) //Specify a clock domain to the dbus (used by QSysify)
          Axi4SpecRenamer(axi)
        }
        case plugin: PrivilegedPlugin => {
          // Interrupt connections based on NaxRiscvBmbGenerator.scala and CsrPlugin of VexRiscvAxi4LinuxPlicClint.scala 
          plugin.io.int.machine.external setAsDirectionLess() := cpu.plicCtrl.io.targets(0)       // external interrupts from PLIC
          plugin.io.int.machine.timer  setAsDirectionLess() := cpu.clintCtrl.io.timerInterrupt(0)  // timer interrupts from CLINT
          plugin.io.int.machine.software  setAsDirectionLess() := cpu.clintCtrl.io.softwareInterrupt(0) // software interrupts from CLINT
          if (plugin.p.withSupervisor) plugin.io.int.supervisor.external  setAsDirectionLess() := cpu.plicCtrl.io.targets(1) // supervisor external interrupts from PLIC
          plugin.io.rdtime  setAsDirectionLess() := cpu.clintCtrl.io.time // time register from CLINT
        }
        case _ =>
      }
    }
    cpu
  }

  spinalConfig.generateVerilog(if(withIoFf) Rtl.ffIo(gen) else gen)
//  spinalConfig.generateVerilog(new StreamFifo(UInt(4 bits), 256).setDefinitionName("nax"))
}
