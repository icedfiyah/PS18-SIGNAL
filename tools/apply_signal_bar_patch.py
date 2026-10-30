#!/usr/bin/env python3
"""Adds a 3-bar signal indicator left of the battery icon. Run from repo root,
AFTER tools/apply_rx_screen_patch.py. Idempotent: skips files already patched."""
import sys

D = "examples/companion_radio/ui-new/"

def patch(path, marker, edits):
    s = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    if marker in s:
        print("already patched:", path); return
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            sys.exit(f"ERROR: anchor found {n} times (need 1) in {path}:\n{old}")
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
    print("patched", path)

if "onPacketRx" not in open(D + "UITask.h", encoding="utf-8").read():
    sys.exit("ERROR: run tools/apply_rx_screen_patch.py first")

# --- icons.h: 8x8 'X' bitmap
patch(D + "icons.h", "no_signal_icon", [(
"// small power plug, 8x8px, shown next to the battery icon once fully charged\n",
"// small X, 8x8px, drawn in the signal slot when there are 0 bars / stale / no data\n"
"static const uint8_t no_signal_icon[] = {\n"
"  0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81\n"
"};\n\n"
"// small power plug, 8x8px, shown next to the battery icon once fully charged\n")])

# --- UITask.h: timeout define, last-rx timestamp, accessor
patch(D + "UITask.h", "getSignalBars", [
("#endif\n\nclass UITask : public AbstractUITask {\n",
"#endif\n\n"
"#ifndef SIGNAL_STALE_MILLIS\n"
"  #define SIGNAL_STALE_MILLIS 600000UL   // no packet for 10 min -> 0 bars\n"
"#endif\n\n"
"class UITask : public AbstractUITask {\n"),
("  int _rx_count = 0;   // valid entries\n",
 "  int _rx_count = 0;   // valid entries\n  uint32_t _rx_last_ms = 0;  // millis() of last received packet\n"),
("  bool getRxHistory(int idx, float& snr, float& rssi) const;\n",
 "  bool getRxHistory(int idx, float& snr, float& rssi) const;\n"
 "  uint8_t getSignalBars() const;   // 0..3 from avg SNR of the RX history\n"),
])

# --- UITask.cpp: record time, compute bars, draw
patch(D + "UITask.cpp", "getSignalBars", [
("  if (_rx_count < UI_RX_HISTORY_SIZE) _rx_count++;\n}\n",
"""  if (_rx_count < UI_RX_HISTORY_SIZE) _rx_count++;
  _rx_last_ms = millis();
}

uint8_t UITask::getSignalBars() const {
  if (_rx_count == 0) return 0;
  if ((uint32_t)(millis() - _rx_last_ms) > SIGNAL_STALE_MILLIS) return 0;
  float sum = 0;
  for (int i = 0; i < _rx_count; i++) sum += _rx_snr[i];
  float avg = sum / _rx_count;
  if (avg > 5.0f) return 3;
  if (avg > 0.0f) return 2;
  if (avg > -5.0f) return 1;
  return 0;
}
"""),
("    // while charging, show a bolt (or a plug once full) just left of the battery,\n",
"""    // signal indicator: 3 bars (24x10) directly left of the battery, or an X at 0 bars
    int sigX = iconX - 24 - 4;
    {
      uint8_t bars = _task->getSignalBars();
      display.setColor(UIColor::title_txt);
      if (bars == 0) {
        display.drawXbm(sigX + 8, iconY + 1, no_signal_icon, 8, 8);
      } else {
        static const int barH[3] = {4, 7, 10};
        for (int b = 0; b < 3; b++) {
          int bx = sigX + b * 9;
          int by = iconY + 10 - barH[b];
          if (b < bars) display.fillRect(bx, by, 6, barH[b]);
          else          display.drawRect(bx, by, 6, barH[b]);
        }
      }
    }

    // while charging, show a bolt (or a plug once full) just left of the battery,
"""),
("      display.drawXbm(iconX - 9, iconY + 1, symbol, 8, 8);\n",
 "      display.drawXbm(sigX - 9, iconY + 1, symbol, 8, 8);\n"),
("      display.drawXbm(iconX - (charging ? 18 : 9), iconY + 1, muted_icon, 8, 8);\n",
 "      display.drawXbm(sigX - (charging ? 18 : 9), iconY + 1, muted_icon, 8, 8);\n"),
])
