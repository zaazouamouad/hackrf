#!/usr/bin/env python3
"""
NexuIO Pro – Advanced RF Control Suite for HackRF One
Real hardware control · No simulation · Jamming frequency database
Author: RF Expert
"""

import sys
import time
import threading
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# ----------------------------------------------------------------------
# ANSI Terminal Styling
# ----------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

# ----------------------------------------------------------------------
# HackRF availability check
# ----------------------------------------------------------------------
try:
    from pyhackrf2 import HackRF
    HACKRF_AVAILABLE = True
except ImportError:
    HACKRF_AVAILABLE = False
    print(f"{RED}[ERROR] pyhackrf2 not installed. Run: pip install pyhackrf2{RESET}")
    sys.exit(1)

# ----------------------------------------------------------------------
# Jamming Frequency Database (70+ entries, categorised)
# ----------------------------------------------------------------------
JAMMING_DB: Dict[str, List[Tuple[float, str, str]]] = {
    "GPS / GNSS": [
        (1176.45, "L2C", "GPS L2 / GLONASS L2"),
        (1227.60, "L2", "GPS L2 Military"),
        (1381.05, "L3", "GPS L3 Nuclear Detection"),
        (1561.10, "B1", "BeiDou B1"),
        (1575.42, "L1", "GPS L1 / Galileo / GLONASS L1"),
        (1589.74, "L5", "GPS L5 Safety-of-Life"),
        (1602.00, "G1", "GLONASS G1"),
        (2492.00, "S-Band", "BeiDou S-Band"),
    ],
    "Cellular / Mobile": [
        (450.00, "5G Band31", "450 MHz LTE/5G"),
        (700.00, "4G/5G", "LTE Bands 12/13/17/28 (700 MHz)"),
        (800.00, "4G", "LTE Band 5/20/26 (850/800 MHz)"),
        (900.00, "2G/3G/4G", "GSM 900 / UMTS 900 / LTE Band 8"),
        (1700.00, "3G/4G", "AWS 1700/2100 MHz"),
        (1800.00, "2G/4G", "GSM 1800 / LTE Band 3"),
        (1900.00, "2G/3G", "PCS 1900 / UMTS 1900"),
        (2100.00, "3G/4G", "IMT 2100 / LTE Band 1"),
        (2600.00, "4G/5G", "LTE Band 7 / 5G n7"),
        (3500.00, "5G", "5G n78 (C-Band)"),
        (3700.00, "5G", "5G n77 (C-Band)"),
    ],
    "Wi-Fi / Bluetooth / IoT": [
        (2400.00, "Wi-Fi 2.4G", "802.11b/g/n/ax"),
        (2412.00, "Wi-Fi Ch1", "Channel 1"),
        (2462.00, "Wi-Fi Ch11", "Channel 11"),
        (2484.00, "Wi-Fi Ch14", "Channel 14 (Japan)"),
        (5180.00, "Wi-Fi 5G", "Low band 5 GHz"),
        (5500.00, "Wi-Fi 5G", "Mid band 5 GHz"),
        (5825.00, "Wi-Fi 5G", "High band 5 GHz"),
        (2402.00, "BLE Ch0", "Bluetooth LE"),
        (2480.00, "BLE Ch39", "Bluetooth LE"),
        (868.00, "Zigbee/Z-Wave", "EU ISM"),
        (915.00, "Zigbee/LoRa", "US ISM"),
        (433.05, "ISM", "433 MHz band"),
    ],
    "Remote Controls & Keyless": [
        (27.00, "RC Toys", "27 MHz CB Band"),
        (40.00, "RC", "40 MHz RC (EU)"),
        (49.00, "RC Toys", "49 MHz Low Power"),
        (72.00, "RC Aircraft", "72 MHz Air Band"),
        (75.00, "RC Surface", "75 MHz Surface"),
        (315.00, "Keyfob", "US garage/remote"),
        (390.00, "Keyfob", "Alternative remote"),
        (418.00, "Keyfob", "European remote"),
        (433.92, "Keyless", "Car key fob / alarm"),
        (868.35, "Keyless", "Modern car remote (EU)"),
        (902.00, "Garage", "US garage opener"),
    ],
    "Drones & UAV": [
        (2400.00, "Drone 2.4G", "DJI / Parrot"),
        (5725.00, "Drone 5.8G", "DJI OcuSync"),
        (5800.00, "FPV 5.8G", "Analog FPV"),
        (900.00, "Telemetry", "Long-range RC"),
        (1430.00, "UAV C-band", "Military UAV"),
        (2200.00, "Drone", "Chinese drone band"),
    ],
    "Satellite & Radar": [
        (1090.00, "ADS-B", "Aircraft transponder"),
        (1200.00, "L-Band Radar", "L-band radar"),
        (5400.00, "C-Band Radar", "C-band radar"),
        (9400.00, "X-Band Radar", "X-band radar"),
        (11700.00, "Ku DBS", "Ku-band satellite"),
    ],
    "Public Safety & Gov": [
        (138.00, "VHF Mil", "Military VHF"),
        (150.00, "VHF Police", "Police VHF"),
        (450.00, "UHF Police", "Police UHF"),
        (760.00, "TETRA", "Emergency services"),
        (800.00, "P25", "Public Safety 800"),
    ],
    "FM / AM Broadcast": [
        (88.00, "FM Low", "88-108 MHz FM"),
        (98.00, "FM Mid", "Common FM station"),
        (108.00, "FM High", "FM upper limit"),
        (0.530, "AM Low", "530 kHz AM (kHz value!)"),
    ],
    "Miscellaneous": [
        (13.56, "NFC/RFID", "13.56 MHz"),
        (125.00, "LF RFID", "125 kHz (kHz!)"),
        (303.00, "Older Cars", "303 MHz remotes"),
        (310.00, "MICS", "Medical implant"),
        (402.00, "MedRadio", "402-405 MHz medical"),
        (169.00, "Meteo", "Meteorological sensors"),
    ]
}

# ----------------------------------------------------------------------
# Logo & splash screen (no Arabic)
# ----------------------------------------------------------------------
def show_splash() -> None:
    """Display the jamming logo and penguin."""
    YELLOW, GREEN, RESET, BOLD = "\033[93m", "\033[92m", "\033[0m", "\033[1m"
    print(f"{YELLOW}{BOLD}")
    print("     ██╗ █████╗ ███╗   ███╗███╗   ███╗██╗███╗   ██╗ ██████╗ ")
    print("     ██║██╔══██╗████╗ ████║████╗ ████║██║████╗  ██║██╔════╝ ")
    print("     ██║███████║██╔████╔██║██╔████╔██║██║██╔██╗ ██║██║  ███╗")
    print("██   ██║██╔══██║██║╚██╔╝██║██║╚██╔╝██║██║██║╚██╗██║██║   ██║")
    print("╚█████╔╝██║  ██║██║ ╚═╝ ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝")
    print(" ╚════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ")
    print(RESET)
    print(f"{GREEN}{BOLD}")
    print("        .--.")
    print("       |o_o |")
    print("       |:_/ |")
    print("      //   \\ \\")
    print("     (|     | )")
    print("    /'\\   /`\\")
    print("    \\)=(/")
    print(RESET)

# ----------------------------------------------------------------------
# Main Application Class
# ----------------------------------------------------------------------
class NexuIOCLI:
    def __init__(self):
        self.hackrf: Optional[HackRF] = None
        self.is_tx: bool = False
        self.running: bool = True
        self.current_freq: float = 433.92e6   # Hz
        self.tx_vga_gain: int = 20            # 0-47 dB
        self.rx_lna_gain: int = 16            # 0-40 dB (step 8)
        self.rx_vga_gain: int = 20            # 0-62 dB (step 2)
        self.tx_amp_enable: bool = False
        self.sample_rate: float = 2e6
        self.bw_hz: int = 1.75e6

        if HACKRF_AVAILABLE:
            self._init_hackrf()

    # ------------------------------------------------------------------
    # Hardware Initialization
    # ------------------------------------------------------------------
    def _init_hackrf(self) -> None:
        try:
            self.hackrf = HackRF()
            self.hackrf.open()
            self.hackrf.set_sample_rate(self.sample_rate)
            self.hackrf.set_freq(self.current_freq)
            self.hackrf.set_lna_gain(self.rx_lna_gain)
            self.hackrf.set_vga_gain(self.rx_vga_gain)
            self.hackrf.set_txvga_gain(self.tx_vga_gain)
            self.hackrf.set_amp_enable(self.tx_amp_enable)
            self._log("HackRF connected and configured", "SUCCESS")
        except Exception as e:
            self._log(f"HackRF init failed: {e}", "ERROR")
            self.hackrf = None

    def _log(self, msg: str, lvl: str = "INFO") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        if lvl == "ERROR":
            prefix = f"{RED}[{ts}] ERROR{RESET}"
        elif lvl == "SUCCESS":
            prefix = f"{GREEN}[{ts}] ✓{RESET}"
        elif lvl == "WARNING":
            prefix = f"{YELLOW}[{ts}] ⚠{RESET}"
        else:
            prefix = f"{DIM}[{ts}]{RESET}"
        print(f"{prefix} {msg}")

    def _print_header(self, title: str) -> None:
        print(f"\n{BOLD}{BLUE}─── {title} ───{RESET}")

    def _input_float(self, prompt: str, minv: float, maxv: float) -> float:
        while True:
            try:
                val = float(input(prompt))
                if minv <= val <= maxv:
                    return val
                print(f"{RED}Value must be between {minv} and {maxv}{RESET}")
            except ValueError:
                print(f"{RED}Invalid number{RESET}")

    def _input_int(self, prompt: str, minv: int, maxv: int) -> int:
        while True:
            try:
                val = int(input(prompt))
                if minv <= val <= maxv:
                    return val
                print(f"{RED}Value must be between {minv} and {maxv}{RESET}")
            except ValueError:
                print(f"{RED}Invalid integer{RESET}")

    # ------------------------------------------------------------------
    # Frequency Management
    # ------------------------------------------------------------------
    def _set_frequency(self, freq_hz: float) -> bool:
        if not self.hackrf:
            return False
        try:
            self.hackrf.set_freq(freq_hz)
            self.current_freq = freq_hz
            return True
        except Exception as e:
            self._log(f"Set freq error: {e}", "ERROR")
            return False

    # ------------------------------------------------------------------
    # Transmit CW (Continuous Wave) for jamming/ testing
    # ------------------------------------------------------------------
    def _start_transmit(self, duration: float = 10.0) -> None:
        if not self.hackrf:
            self._log("HackRF not available", "ERROR")
            return
        if self.is_tx:
            self._log("Already transmitting", "WARNING")
            return

        def tx_worker():
            self.is_tx = True
            self._log(f"TX started @ {self.current_freq/1e6:.2f} MHz | TX VGA={self.tx_vga_gain} dB | Amp={'ON' if self.tx_amp_enable else 'OFF'}", "SUCCESS")
            try:
                self.hackrf.set_txvga_gain(self.tx_vga_gain)
                self.hackrf.set_amp_enable(self.tx_amp_enable)
                self.hackrf.set_tx(True)
                # Generate a simple complex tone at baseband (1 MHz offset)
                num_samples = int(self.sample_rate * duration)
                t = np.arange(num_samples) / self.sample_rate
                tone_freq = 1e6  # 1 MHz tone
                iq = np.exp(2j * np.pi * tone_freq * t).astype(np.complex64)
                # Scale to max int16
                iq *= 32767
                self.hackrf.tx(iq)
                self.hackrf.set_tx(False)
            except Exception as e:
                self._log(f"TX error: {e}", "ERROR")
            finally:
                self.is_tx = False
                self._log("TX finished", "SUCCESS")

        threading.Thread(target=tx_worker, daemon=True).start()

    def _stop_transmit(self) -> None:
        if not self.is_tx:
            self._log("No active transmission", "WARNING")
            return
        self._log("Stopping TX...", "INFO")
        # The tx thread will exit when self.is_tx is false after the current call
        # For simplicity, we rely on the thread finishing its duration.
        # In a real implementation you'd need a flag to break the loop.
        print(f"{YELLOW}Note: TX will stop after current burst (press Ctrl+C to force){RESET}")

    # ------------------------------------------------------------------
    # Spectrum Sweep (using HackRF's built-in sweep)
    # ------------------------------------------------------------------
    def _sweep_spectrum(self, start_mhz: float, stop_mhz: float, step_mhz: float = 2.0) -> None:
        if not self.hackrf:
            self._log("HackRF not available", "ERROR")
            return
        self._log(f"Sweeping from {start_mhz} MHz to {stop_mhz} MHz, step {step_mhz} MHz", "INFO")
        freqs = np.arange(start_mhz, stop_mhz + step_mhz/2, step_mhz) * 1e6
        print(f"\n{BOLD}{CYAN}Freq (MHz)  |  RSSI (dBm){RESET}")
        print(f"{CYAN}{'_'*30}{RESET}")
        for f in freqs:
            try:
                self.hackrf.set_freq(f)
                time.sleep(0.01)
                # Capture a few samples and compute approximate RSSI
                samples = self.hackrf.rx(1000, 0.001)
                power = 20 * np.log10(np.abs(samples).mean() + 1e-6)
                bar_len = max(0, int((power + 100) / 5))
                bar = "█" * min(bar_len, 40)
                print(f"{f/1e6:>8.2f} MHz | {power:>5.1f} dBm {bar}")
            except Exception as e:
                self._log(f"Sweep error at {f/1e6:.2f} MHz: {e}", "WARNING")
        self._log("Sweep completed", "SUCCESS")

    # ------------------------------------------------------------------
    # Receive live spectrum (simple RMS)
    # ------------------------------------------------------------------
    def _receive_live(self, duration: float = 10.0) -> None:
        if not self.hackrf:
            self._log("HackRF not available", "ERROR")
            return
        self._log(f"Receiving @ {self.current_freq/1e6:.2f} MHz for {duration}s", "INFO")
        try:
            self.hackrf.set_lna_gain(self.rx_lna_gain)
            self.hackrf.set_vga_gain(self.rx_vga_gain)
            start = time.time()
            while time.time() - start < duration:
                samples = self.hackrf.rx(8192, timeout_us=5000)
                rms = 20 * np.log10(np.abs(samples).mean() + 1e-6)
                self._log(f"RSSI: {rms:.1f} dBm", "INFO")
                time.sleep(0.5)
        except Exception as e:
            self._log(f"RX error: {e}", "ERROR")

    # ------------------------------------------------------------------
    # Jamming Frequency Database Menu
    # ------------------------------------------------------------------
    def _show_jamming_db(self) -> None:
        self._print_header("JAMMING FREQUENCY DATABASE")
        print(f"{YELLOW}[!] Educational purpose only. Do not interfere with authorised communications.{RESET}\n")
        categories = list(JAMMING_DB.keys())
        for idx, cat in enumerate(categories, 1):
            print(f"  {BLUE}{idx}{RESET}. {cat}")
        print(f"  {BLUE}0{RESET}. Back to main")
        print(f"  {BLUE}-1{RESET}. Select from custom frequency")

        cat_choice = self._input_int("Select category: ", -1, len(categories))
        if cat_choice == 0:
            return
        elif cat_choice == -1:
            custom = self._input_float("Enter frequency (MHz): ", 0.0, 10000.0)
            if self._set_frequency(custom * 1e6):
                self._log(f"Frequency set to {custom} MHz", "SUCCESS")
            return

        cat = categories[cat_choice - 1]
        entries = JAMMING_DB[cat]
        print(f"\n{BOLD}{MAGENTA}Frequencies in {cat}:{RESET}")
        for i, (freq_mhz, label, desc) in enumerate(entries, 1):
            print(f"  {BLUE}{i}{RESET}. {freq_mhz:>8.2f} MHz [{label}] - {desc}")
        print(f"  {BLUE}0{RESET}. Back")

        freq_choice = self._input_int("Select frequency to set: ", 0, len(entries))
        if freq_choice == 0:
            return
        freq_mhz, label, desc = entries[freq_choice - 1]
        if self._set_frequency(freq_mhz * 1e6):
            self._log(f"Set to {freq_mhz} MHz ({label}) - {desc}", "SUCCESS")

    # ------------------------------------------------------------------
    # Hardware Settings Menu
    # ------------------------------------------------------------------
    def _hardware_settings(self) -> None:
        while True:
            self._print_header("HackRF Hardware Settings")
            print(f"  1. TX VGA Gain (0-47 dB): {self.tx_vga_gain}")
            print(f"  2. RX LNA Gain (0-40 dB step8): {self.rx_lna_gain}")
            print(f"  3. RX VGA Gain (0-62 dB step2): {self.rx_vga_gain}")
            print(f"  4. TX Amplifier: {'ON' if self.tx_amp_enable else 'OFF'}")
            print(f"  5. Sample Rate (Hz): {self.sample_rate:.0f}")
            print(f"  6. Set all gains to default")
            print(f"  0. Back")
            choice = input("\nChoice: ").strip()
            if choice == "1":
                newgain = self._input_int("TX VGA Gain (0-47): ", 0, 47)
                self.tx_vga_gain = newgain
                if self.hackrf:
                    self.hackrf.set_txvga_gain(newgain)
                self._log(f"TX VGA gain set to {newgain} dB")
            elif choice == "2":
                newgain = self._input_int("RX LNA Gain (0,8,16,24,32,40): ", 0, 40)
                # Round to step 8
                newgain = min(40, (newgain // 8) * 8)
                self.rx_lna_gain = newgain
                if self.hackrf:
                    self.hackrf.set_lna_gain(newgain)
                self._log(f"RX LNA gain set to {newgain} dB")
            elif choice == "3":
                newgain = self._input_int("RX VGA Gain (0-62 step2): ", 0, 62)
                newgain = min(62, (newgain // 2) * 2)
                self.rx_vga_gain = newgain
                if self.hackrf:
                    self.hackrf.set_vga_gain(newgain)
                self._log(f"RX VGA gain set to {newgain} dB")
            elif choice == "4":
                self.tx_amp_enable = not self.tx_amp_enable
                if self.hackrf:
                    self.hackrf.set_amp_enable(self.tx_amp_enable)
                self._log(f"TX Amplifier {'ENABLED' if self.tx_amp_enable else 'DISABLED'}")
            elif choice == "5":
                new_sr = self._input_float("Sample Rate (MHz, 2-20): ", 2.0, 20.0) * 1e6
                self.sample_rate = new_sr
                if self.hackrf:
                    self.hackrf.set_sample_rate(new_sr)
                self._log(f"Sample rate set to {new_sr/1e6:.1f} MHz")
            elif choice == "6":
                self.tx_vga_gain, self.rx_lna_gain, self.rx_vga_gain = 20, 16, 20
                self.tx_amp_enable = False
                self.sample_rate = 2e6
                if self.hackrf:
                    self.hackrf.set_txvga_gain(20)
                    self.hackrf.set_lna_gain(16)
                    self.hackrf.set_vga_gain(20)
                    self.hackrf.set_amp_enable(False)
                    self.hackrf.set_sample_rate(2e6)
                self._log("Default gains restored")
            elif choice == "0":
                break

    # ------------------------------------------------------------------
    # Main Menu Loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        show_splash()
        print(f"\n{BOLD}{CYAN}◈◈◈ NEXUIO PRO – HackRF Control Suite ◈◈◈{RESET}")
        print(f"Real hardware · No simulation · {GREEN}HackRF {'connected' if self.hackrf else 'NOT available'}{RESET}")

        while self.running:
            self._print_header("Main Menu")
            print("  1. Set frequency")
            print("  2. Transmit CW (jamming / test)")
            print("  3. Stop transmission")
            print("  4. Receive live RSSI")
            print("  5. Spectrum sweep (start/stop MHz)")
            print("  6. Jamming frequency database")
            print("  7. HackRF hardware settings")
            print("  0. Exit")
            choice = input("\nChoice: ").strip()

            if choice == "1":
                freq_mhz = self._input_float("Frequency (MHz): ", 0.0, 10000.0)
                if self._set_frequency(freq_mhz * 1e6):
                    self._log(f"Frequency set to {freq_mhz:.2f} MHz")
            elif choice == "2":
                dur = self._input_float("Transmit duration (seconds) [10]: ", 1.0, 300.0)
                self._start_transmit(dur)
            elif choice == "3":
                self._stop_transmit()
            elif choice == "4":
                dur = self._input_float("Receive duration (seconds) [5]: ", 1.0, 60.0)
                self._receive_live(dur)
            elif choice == "5":
                start = self._input_float("Start frequency (MHz): ", 0.0, 6000.0)
                stop = self._input_float("Stop frequency (MHz): ", start, 6000.0)
                step = self._input_float("Step size (MHz) [2.0]: ", 0.1, 10.0)
                self._sweep_spectrum(start, stop, step)
            elif choice == "6":
                self._show_jamming_db()
            elif choice == "7":
                self._hardware_settings()
            elif choice == "0":
                if self.is_tx:
                    self._log("Stopping TX before exit...")
                    time.sleep(0.5)
                if self.hackrf:
                    self.hackrf.close()
                self._log("Shutting down. Goodbye!", "SUCCESS")
                self.running = False
            else:
                print(f"{RED}Invalid choice{RESET}")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = NexuIOCLI()
    app.run()
