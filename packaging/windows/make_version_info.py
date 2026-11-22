"""Write a PyInstaller version resource so the Windows .exe carries its name,
publisher and version (shown in Properties > Details, and required by most
code-signing services).

    python packaging/windows/make_version_info.py 1.2.3 build/version_info.txt
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

COMPANY = "adityabhalsod"
PRODUCT = "Offline Video Converter"
EXE = "OfflineVideoConverter.exe"

TEMPLATE = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={nums},
    prodvers={nums},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', {company!r}),
        StringStruct('FileDescription', {product!r}),
        StringStruct('FileVersion', {version!r}),
        StringStruct('InternalName', 'OfflineVideoConverter'),
        StringStruct('LegalCopyright', 'Copyright (c) {company}. Apache License 2.0.'),
        StringStruct('OriginalFilename', {exe!r}),
        StringStruct('ProductName', {product!r}),
        StringStruct('ProductVersion', {version!r}),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def numeric(version: str) -> tuple[int, int, int, int]:
    """1.2.3-beta.1 -> (1, 2, 3, 0); Windows only allows four integers."""
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not m:
        return (0, 0, 0, 0)
    return (int(m[1]), int(m[2]), int(m[3]), 0)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    version, out = argv
    text = TEMPLATE.format(nums=numeric(version), company=COMPANY, product=PRODUCT, version=version, exe=EXE)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
