import re
from pathlib import Path

src = Path("vein_launcher/presentation/webui/src")
pat = re.compile(r"[\u4e00-\u9fff][^\n]*")
left = {}
for f in sorted(src.glob("*.tsx")) + sorted(src.glob("*.ts")):
    for m in pat.finditer(f.read_text(encoding="utf-8")):
        s = m.group(0).strip()
        if s:
            left.setdefault(s[:80], f.name)
for s in sorted(left):
    print(f"{left[s]}\t{s}")
print("REMAIN", len(left))
