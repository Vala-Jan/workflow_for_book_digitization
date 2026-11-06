r"""
jpg2pdf - slozi JPEG skeny dvojstran (Bookeye 3) z datumove slozky do jednoho PDF
(1 sken = 1 stranka A4).

    workspace\
    +-- tool\    jpg2pdf.bat + jpg2pdf.py
    +-- log\     runner_RRRR-MM-DD_HHMMSS.txt (auditni log, jeden soubor na spusteni)
    +-- scans\
        +-- 2026-10-14\   skeny -> 2026-10-14.pdf

Razeni podle cisla v nazvu (REFERENCE00001, REFERENCE00002, REFERENCE00004 ...).
Chybejici cisla v rade se jen zapisou do logu.
"""

import datetime as dt
import getpass
import hashlib
import platform
import re
import sys
import time
import traceback
from importlib.metadata import version as pkg_version
from pathlib import Path

import img2pdf
import pikepdf  # instaluje se s img2pdf; slouzi ke kontrole vysledneho PDF
from PIL import Image, UnidentifiedImageError

VERSION = "1.2.2"

# Nastaveni
PAGE_SIZE_MM = (210, 297)   # A4; sken na sirku dostane stranku na sirku
BORDER_MM = 1               # okraj stranky v mm

WORKSPACE = Path(__file__).resolve().parent.parent
SCANS_DIR = WORKSPACE / "scans"
LOG_DIR = WORKSPACE / "log"
START = dt.datetime.now()
RUN_ID = f"{START:%Y%m%d-%H%M%S}"
LOG_FILE = LOG_DIR / f"runner_{START:%Y-%m-%d_%H%M%S}.txt"
n = 1
while LOG_FILE.exists():  # dve spusteni ve stejne sekunde -> kazde vlastni ID a soubor
    n += 1
    RUN_ID = f"{START:%Y%m%d-%H%M%S}-{n}"
    LOG_FILE = LOG_DIR / f"runner_{START:%Y-%m-%d_%H%M%S}-{n}.txt"


def audit(level: str, msg: str, console=None) -> None:
    """Pripise do logu radek 'cas | ID behu | uroven | zprava'.

    console: None = nic nevypsat, True = vypsat msg, text = vypsat tento text.
    """
    if console:
        print(msg if console is True else console)
    stamp = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    stamp = f"{stamp[:-2]}:{stamp[-2:]}"  # 2026-10-15 11:52:00 +02:00
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for line in msg.splitlines():
            f.write(f"{stamp} | {RUN_ID} | {level:<8} | {line}\n")


def file_info(path: Path) -> str:
    """Velikost a SHA-256 otisk souboru pro audit."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return f"{path.stat().st_size} B | sha256={h.hexdigest()}"


def name_key(path: Path):
    """Prirozene razeni: cisla v nazvu se porovnavaji jako cisla (REF2 < REF10)."""
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", path.stem.lower())]


def log_gaps(paths) -> int:
    """Zapise chybejici cisla v rade. Vrati pocet souboru, jejichz nazev nekonci cislem."""
    nums, no_number = set(), 0
    for p in paths:
        m = re.search(r"\d+$", p.stem)
        if m:
            nums.add(int(m.group()))
        else:
            no_number += 1
            audit("VAROVANI", f"NAZEV {p.name} nekonci cislem", console=f"  VAROVANI: {p.name} nekonci cislem")
    if nums:
        missing = sorted(set(range(min(nums), max(nums) + 1)) - nums)
        text = ", ".join(map(str, missing)) if missing else "zadna"
        audit("INFO", f"RADA {min(nums)}-{max(nums)} | chybejici cisla: {text}",
              console=f"  Chybejici cisla: {text}")
    return no_number


class SkipScan(Exception):
    """Sken nejde pouzit; text vyjimky je duvod pro log."""


def scan_details(path: Path) -> str:
    """Zkontroluje sken a vrati udaje pro audit, nepouzitelny soubor -> SkipScan."""
    if path.stat().st_size == 0:
        raise SkipScan("prazdny soubor (0 B) - nedokonceny prenos?")
    try:
        with Image.open(path) as im:
            fmt, (width, height) = im.format, im.size
            dpi = im.info.get("dpi")
            im.verify()
    except UnidentifiedImageError:
        raise SkipScan("soubor neni obrazek - poskozeny nebo jen prejmenovany")
    except Exception as e:
        raise SkipScan(f"soubor nelze precist ({type(e).__name__}: {e})")
    if fmt != "JPEG":
        raise SkipScan(f"soubor neni JPEG, ale {fmt}")

    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime)
    dpi_text = "x".join(str(round(d)) for d in dpi) if dpi else "-"
    return f"{file_info(path)} | soubor={mtime:%Y-%m-%d %H:%M:%S} | px={width}x{height} | dpi={dpi_text}"


def find_jpegs(folder: Path):
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg")),
                  key=name_key)


def build_pdf(paths, out_path: Path) -> None:
    """JPEGy se vkladaji bez prekodovani."""
    mm = img2pdf.mm_to_pt
    layout = img2pdf.get_layout_fun(
        pagesize=(mm(PAGE_SIZE_MM[0]), mm(PAGE_SIZE_MM[1])),
        border=(mm(BORDER_MM), mm(BORDER_MM)),
        fit=img2pdf.FitMode.into,
        auto_orient=True,
    )
    out_path.write_bytes(img2pdf.convert([str(p) for p in paths], layout_fun=layout,
                                         rotation=img2pdf.Rotation.ifvalid))


def ask_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} (Y/N): ").strip().lower()
        if answer in ("y", "a", "ano"):
            return True
        if answer in ("n", "ne"):
            return False


def choose_folder():
    folders = sorted((p for p in SCANS_DIR.glob("*")
                      if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)), reverse=True)
    if not folders:
        audit("VAROVANI", f"Ve slozce {SCANS_DIR} neni zadna slozka RRRR-MM-DD.", console=True)
        return None

    print(f"Slozky v {SCANS_DIR}:")
    for i, f in enumerate(folders, 1):
        flag = "   [PDF uz existuje]" if (f / f"{f.name}.pdf").exists() else ""
        print(f"  {i:>2}) {f.name}   {len(find_jpegs(f))} skenu{flag}")
    print("   0) Konec")

    while True:
        choice = input("\nVyberte cislo slozky: ").strip()
        if choice == "0":
            audit("UZIVATEL", "VYBER 0 = konec")
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(folders):
            folder = folders[int(choice) - 1]
            audit("UZIVATEL", f"VYBER {choice} = {folder}")
            return folder


def process_folder(folder: Path) -> str:
    """Zpracuje slozku a vrati stav: OK / OK S VAROVANIM / ZRUSENO / CHYBA."""
    t0 = time.monotonic()
    scans, skipped = [], 0

    def result(status: str) -> str:
        audit("CHYBA" if status == "CHYBA" else "INFO",
              f"VYSLEDEK {folder.name} | stav={status} | skenu={len(scans)} | preskoceno={skipped} | "
              f"trvani={time.monotonic() - t0:.0f} s")
        return status

    audit("INFO", f"SLOZKA {folder}", console=f"\n=== Slozka: {folder} ===")
    if not folder.is_dir():
        audit("CHYBA", "SLOZKA neexistuje nebo to neni slozka", console=True)
        return result("CHYBA")

    # Vstupy (uz serazene podle nazvu)
    files = find_jpegs(folder)
    audit("INFO", f"VSTUP nalezeno souboru .jpg/.jpeg: {len(files)}")
    print("Poradi skenu:")
    for p in files:
        try:
            details = scan_details(p)
        except SkipScan as e:
            skipped += 1
            audit("VAROVANI", f"PRESKOCENO {p.name} | {p.stat().st_size} B | duvod: {e}",
                  console=f"  VAROVANI: preskakuji {p.name} - {e}")
            continue
        scans.append(p)
        audit("INFO", f"VSTUP str={len(scans)} | {p.name} | {details}",
              console=f"  {len(scans):>3}. {p.name}")
    if not scans:
        audit("CHYBA", "VSTUP ve slozce neni zadny pouzitelny JPEG", console=True)
        return result("CHYBA")
    no_number = log_gaps(scans)

    # Rozhodnuti uzivatele
    out_path = folder / f"{folder.name}.pdf"
    overwrite = out_path.exists()
    if overwrite:
        modified = dt.datetime.fromtimestamp(out_path.stat().st_mtime)
        audit("VAROVANI", f"EXISTUJICI PDF {out_path.name} | {file_info(out_path)} | "
                          f"zmeneno={modified:%Y-%m-%d %H:%M:%S} | bude prepsano",
              console=f"\nPOZOR: {out_path.name} uz existuje a bude prepsano.")
    if not ask_yes_no(f"\nVytvorit {out_path.name} ({len(scans)} stran)?"):
        audit("UZIVATEL", "ODPOVED N (nevytvaret)")
        return result("ZRUSENO")
    audit("UZIVATEL", f"ODPOVED Y (vytvorit{', prepsat' if overwrite else ''})")

    # Vystup a kontrola
    try:
        build_pdf(scans, out_path)
    except PermissionError:
        audit("CHYBA", f"VYSTUP {out_path.name} nelze zapsat - je otevrene v jinem programu?", console=True)
        return result("CHYBA")

    with pikepdf.open(out_path) as pdf:
        pages = len(pdf.pages)
    audit("INFO", f"VYSTUP {out_path} | {pages} stran | {file_info(out_path)}",
          console=f"HOTOVO: {out_path}  ({pages} stran, {out_path.stat().st_size / 1024 / 1024:.1f} MB)")
    if pages != len(scans):
        audit("CHYBA", f"KONTROLA pocet stran ({pages}) != pocet skenu ({len(scans)})", console=True)
        return result("CHYBA")
    audit("INFO", f"KONTROLA pocet stran = pocet skenu ({pages}) - OK")

    return result("OK S VAROVANIM" if skipped or no_number else "OK")


def main() -> None:
    audit("INFO", f"START jpg2pdf {VERSION} | uzivatel={getpass.getuser()} | pc={platform.node()} | "
                  f"rezim={'pretazeni slozky' if len(sys.argv) > 1 else 'dvojklik'}")
    audit("INFO", f"PROSTREDI python={platform.python_version()} | img2pdf={pkg_version('img2pdf')} | "
                  f"pillow={pkg_version('pillow')} | pikepdf={pkg_version('pikepdf')} | os={platform.platform()}")
    audit("INFO", f"NASTAVENI workspace={WORKSPACE} | scans={SCANS_DIR} | "
                  f"stranka={PAGE_SIZE_MM[0]}x{PAGE_SIZE_MM[1]} mm | okraj={BORDER_MM} mm | razeni=nazev")

    results = []
    try:
        if len(sys.argv) > 1:
            results.append(process_folder(Path(sys.argv[1]).resolve()))
        else:
            while (folder := choose_folder()) is not None:
                results.append(process_folder(folder))
                more = ask_yes_no("\nZpracovat dalsi slozku?")
                audit("UZIVATEL", f"DALSI SLOZKA {'Y' if more else 'N'}")
                if not more:
                    break
                print()
    except KeyboardInterrupt:
        audit("CHYBA", "PRERUSENO uzivatelem (Ctrl+C)", console="\nPreruseno.")
        results.append("PRERUSENO")
    except Exception as e:
        audit("CHYBA", f"NECEKANA CHYBA {type(e).__name__}: {e}", console=True)
        audit("CHYBA", traceback.format_exc())
        results.append("CHYBA")
    finally:
        audit("INFO", f"KONEC zpracovano slozek={len(results)} | stavy: {', '.join(results) or '-'} | "
                      f"trvani={(dt.datetime.now() - START).total_seconds():.0f} s")


if __name__ == "__main__":
    main()
