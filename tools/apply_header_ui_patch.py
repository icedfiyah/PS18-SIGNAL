import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
if "PS18 header layout" in s:
    print("already patched"); sys.exit(0)

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit("FAILED: expected exactly one match for:\n" + old)
    s = s.replace(old, new)

rep("    int iconWidth = 24;\n", "    int iconWidth = 20;   // PS18 header layout: was 24\n")
rep("    int sigX = iconX - 24 - 4;\n", "    int sigX = iconX - 21 - 4;   // 3 bars x 3 px at 9 px pitch\n")
rep("display.drawXbm(sigX + 8, iconY + 1, no_signal_icon, 8, 8);",
    "display.drawXbm(sigX + 6, iconY + 1, no_signal_icon, 8, 8);")
rep("""          if (b < bars) display.fillRect(bx, by, 6, barH[b]);
          else          display.drawRect(bx, by, 6, barH[b]);
""", """          if (b < bars) display.fillRect(bx, by, 3, barH[b]);   // lit bars only
""")
rep("""    int uptimeX = display.width() - uptimeWidth - 2;
    int uptimeY = iconY + iconHeight + 1;
""", """    (void)uptimeWidth;
    int uptimeX = 0;
    int uptimeY = 2;
""")
rep("""    char filtered_name[sizeof(_node_prefs->node_name)];
    display.translateUTF8ToBlocks(filtered_name, _node_prefs->node_name, sizeof(filtered_name));
    display.setCursor(0, 2);
    display.print(filtered_name);
""", "")
rep("""    int x = 5;  // Left-aligned dots
    for (uint8_t i = 0; i < HomePage::Count; i++, x += 10) {
""", """    // dots spread evenly across the width, 5 px side margins
    for (uint8_t i = 0; i < HomePage::Count; i++) {
      int x = 5 + (i * (display.width() - 12)) / (HomePage::Count - 1);
""")
s = s.replace('#include "icons.h"\n', '#include "icons.h"\n// PS18 header layout patch applied\n', 1)
open(p, "w", encoding="utf-8").write(s)
print("patched OK")
