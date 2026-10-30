#!/usr/bin/env python3
"""Adds a first-position SNR/RSSI history screen to the MeshCore companion UI.
Run from the repository root. Every anchor must match exactly once."""
import sys

def patch(path, edits):
    s = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            sys.exit(f"ERROR: anchor found {n} times (need 1) in {path}:\n{old}")
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
    print("patched", path)

D = "examples/companion_radio/"

patch(D + "MyMesh.h", [(
"      virtual void onRawDataRecv(mesh::Packet *pkt) { }\n",
"      virtual void onRawDataRecv(mesh::Packet *pkt) { }\n"
"      virtual void onPacketRx(float snr, float rssi) { }\n")])

patch(D + "MyMesh.cpp", [(
"void MyMesh::logRxRaw(float snr, float rssi, const uint8_t raw[], int len) {\n",
"void MyMesh::logRxRaw(float snr, float rssi, const uint8_t raw[], int len) {\n"
"  if (_listener) _listener->onPacketRx(snr, rssi);\n")])

patch(D + "ui-new/UITask.h", [
("class UITask : public AbstractUITask {\n",
"#ifndef UI_RX_HISTORY_SIZE\n"
"  #define UI_RX_HISTORY_SIZE 8\n"
"#endif\n\n"
"class UITask : public AbstractUITask {\n"
"  float _rx_snr[UI_RX_HISTORY_SIZE];\n"
"  float _rx_rssi[UI_RX_HISTORY_SIZE];\n"
"  int _rx_head = 0;    // next slot to write\n"
"  int _rx_count = 0;   // valid entries\n"),
("  void onControlDataRecv(const mesh::Packet* pkt) override;\n",
"  void onControlDataRecv(const mesh::Packet* pkt) override;\n"
"  void onPacketRx(float snr, float rssi) override;\n"
"  // idx 0 = newest. Returns false if no such entry.\n"
"  bool getRxHistory(int idx, float& snr, float& rssi) const;\n"),
])

patch(D + "ui-new/UITask.cpp", [
("  enum HomePage {\n    FIRST,\n",
 "  enum HomePage {\n    PACKETS,\n    FIRST,\n"),
("    if (_page == HomePage::FIRST) {\n",
"""    if (_page == HomePage::PACKETS) {
      display.setColor(UIColor::primary_txt);
      display.setTextSize(1);
      int y = 20;
      for (int i = 0; i < UI_RX_HISTORY_SIZE && y + 8 <= display.height(); i++, y += 11) {
        float snr, rssi;
        if (!_task->getRxHistory(i, snr, rssi)) break;
        snprintf(tmp, sizeof(tmp), "SNR %+.1f RSSI %d", snr, (int)(rssi >= 0 ? rssi + 0.5f : rssi - 0.5f));
        display.setCursor(0, y);
        display.print(tmp);
      }
      return 1000;   // live list: redraw every second while this page is open
    } else if (_page == HomePage::FIRST) {
"""),
])

# append implementations to end of UITask.cpp
p = D + "ui-new/UITask.cpp"
s = open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
add = """
// --- SNR/RSSI history (records every received packet; never wakes the display) ---
void UITask::onPacketRx(float snr, float rssi) {
  _rx_snr[_rx_head] = snr;
  _rx_rssi[_rx_head] = rssi;
  _rx_head = (_rx_head + 1) % UI_RX_HISTORY_SIZE;
  if (_rx_count < UI_RX_HISTORY_SIZE) _rx_count++;
}

bool UITask::getRxHistory(int idx, float& snr, float& rssi) const {
  if (idx < 0 || idx >= _rx_count) return false;
  int slot = (_rx_head - 1 - idx + 2 * UI_RX_HISTORY_SIZE) % UI_RX_HISTORY_SIZE;
  snr = _rx_snr[slot];
  rssi = _rx_rssi[slot];
  return true;
}
""".replace("\n", nl)
open(p, "w", encoding="utf-8", newline="").write(s.rstrip("\r\n") + nl + add)
print("patched", p, "(appended)")
