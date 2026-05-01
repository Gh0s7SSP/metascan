#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║        METASCAN - Metadata Tool      ║
║  Scan & Strip metadata from file     ║
║  by 4y0ubyyyy                        ║
╚══════════════════════════════════════╝
Usage:
  python metascan.py scan <file_or_dir>
  python metascan.py strip <file_or_dir>
  python metascan.py scan <file> --export report.json
"""

import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

# ─── FILE TYPE MAPPING ──────────────────────────────────────────────────────
IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".heic"}
PDF_EXTS    = {".pdf"}
OFFICE_EXTS = {".docx", ".xlsx", ".pptx"}
AUDIO_EXTS  = {".mp3", ".flac", ".ogg", ".m4a", ".wav", ".aac"}
VIDEO_EXTS  = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}


# ─── SCANNERS ───────────────────────────────────────────────────────────────

def scan_image(path: Path) -> dict:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS

    meta = {}
    try:
        img = Image.open(path)
        meta["Format"] = img.format
        meta["Mode"] = img.mode
        meta["Size"] = f"{img.width}x{img.height}"

        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    gps = {}
                    for gps_id, gps_val in value.items():
                        gps[GPSTAGS.get(gps_id, gps_id)] = str(gps_val)
                    meta["GPS"] = gps
                elif isinstance(value, bytes):
                    meta[str(tag)] = value.hex()
                else:
                    meta[str(tag)] = str(value)
    except Exception as e:
        meta["Error"] = str(e)
    return meta


def scan_pdf(path: Path) -> dict:
    from pypdf import PdfReader

    meta = {}
    try:
        reader = PdfReader(str(path))
        info = reader.metadata
        if info:
            for key, val in info.items():
                clean_key = key.lstrip("/")
                meta[clean_key] = str(val)
        meta["Pages"] = str(len(reader.pages))
        meta["Encrypted"] = str(reader.is_encrypted)
    except Exception as e:
        meta["Error"] = str(e)
    return meta


def scan_docx(path: Path) -> dict:
    from docx import Document

    meta = {}
    try:
        doc = Document(str(path))
        cp = doc.core_properties
        fields = [
            "author", "created", "description", "identifier",
            "keywords", "language", "last_modified_by", "modified",
            "revision", "subject", "title", "version"
        ]
        for f in fields:
            val = getattr(cp, f, None)
            if val:
                meta[f.replace("_", " ").title()] = str(val)
    except Exception as e:
        meta["Error"] = str(e)
    return meta


def scan_xlsx(path: Path) -> dict:
    from openpyxl import load_workbook

    meta = {}
    try:
        wb = load_workbook(str(path), read_only=True)
        cp = wb.properties
        fields = [
            "creator", "lastModifiedBy", "created", "modified",
            "title", "description", "subject", "keywords",
            "category", "contentStatus", "revision", "version"
        ]
        for f in fields:
            val = getattr(cp, f, None)
            if val:
                meta[f] = str(val)
        wb.close()
    except Exception as e:
        meta["Error"] = str(e)
    return meta


def scan_pptx(path: Path) -> dict:
    from pptx import Presentation

    meta = {}
    try:
        prs = Presentation(str(path))
        cp = prs.core_properties
        fields = [
            "author", "created", "description", "keywords",
            "language", "last_modified_by", "modified",
            "revision", "subject", "title", "version"
        ]
        for f in fields:
            val = getattr(cp, f, None)
            if val:
                meta[f.replace("_", " ").title()] = str(val)
    except Exception as e:
        meta["Error"] = str(e)
    return meta


def scan_audio(path: Path) -> dict:
    import mutagen

    meta = {}
    try:
        audio = mutagen.File(str(path), easy=True)
        if audio:
            for key, val in audio.items():
                meta[key] = ", ".join(val) if isinstance(val, list) else str(val)
            if hasattr(audio, "info"):
                info = audio.info
                if hasattr(info, "length"):
                    meta["Duration"] = f"{info.length:.1f}s"
                if hasattr(info, "bitrate"):
                    meta["Bitrate"] = f"{info.bitrate} kbps"
                if hasattr(info, "sample_rate"):
                    meta["Sample Rate"] = f"{info.sample_rate} Hz"
    except Exception as e:
        meta["Error"] = str(e)
    return meta


def scan_video(path: Path) -> dict:
    meta = {}
    try:
        from hachoir.parser import createParser
        from hachoir.metadata import extractMetadata

        parser = createParser(str(path))
        if parser:
            with parser:
                extracted = extractMetadata(parser)
                if extracted:
                    for item in extracted.exportPlaintext():
                        if ":" in item:
                            k, v = item.split(":", 1)
                            meta[k.strip().lstrip("-").strip()] = v.strip()
    except Exception as e:
        meta["Error"] = str(e)
    return meta


# ─── STRIPPERS ──────────────────────────────────────────────────────────────

def strip_image(path: Path) -> bool:
    from PIL import Image
    try:
        img = Image.open(path)
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        clean.save(str(path))
        return True
    except Exception as e:
        console.print(f"  [red]Error stripping {path.name}: {e}[/red]")
        return False


def strip_pdf(path: Path) -> bool:
    from pypdf import PdfReader, PdfWriter
    try:
        reader = PdfReader(str(path))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({})
        with open(str(path), "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        console.print(f"  [red]Error stripping {path.name}: {e}[/red]")
        return False


def strip_docx(path: Path) -> bool:
    from docx import Document
    try:
        doc = Document(str(path))
        cp = doc.core_properties
        cp.author = ""
        cp.last_modified_by = ""
        cp.title = ""
        cp.subject = ""
        cp.description = ""
        cp.keywords = ""
        cp.category = ""
        cp.comments = ""
        doc.save(str(path))
        return True
    except Exception as e:
        console.print(f"  [red]Error stripping {path.name}: {e}[/red]")
        return False


def strip_xlsx(path: Path) -> bool:
    from openpyxl import load_workbook
    try:
        wb = load_workbook(str(path))
        cp = wb.properties
        cp.creator = ""
        cp.lastModifiedBy = ""
        cp.title = ""
        cp.description = ""
        cp.subject = ""
        cp.keywords = ""
        cp.category = ""
        cp.revision = None
        wb.save(str(path))
        return True
    except Exception as e:
        console.print(f"  [red]Error stripping {path.name}: {e}[/red]")
        return False


def strip_pptx(path: Path) -> bool:
    from pptx import Presentation
    try:
        prs = Presentation(str(path))
        cp = prs.core_properties
        cp.author = ""
        cp.last_modified_by = ""
        cp.title = ""
        cp.subject = ""
        cp.description = ""
        cp.keywords = ""
        prs.save(str(path))
        return True
    except Exception as e:
        console.print(f"  [red]Error stripping {path.name}: {e}[/red]")
        return False


def strip_audio(path: Path) -> bool:
    import mutagen
    try:
        audio = mutagen.File(str(path))
        if audio:
            audio.delete()
            audio.save()
        return True
    except Exception as e:
        console.print(f"  [red]Error stripping {path.name}: {e}[/red]")
        return False


# ─── DISPATCH ───────────────────────────────────────────────────────────────

def get_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:  return "image"
    if ext in PDF_EXTS:    return "pdf"
    if ext in OFFICE_EXTS:
        if ext == ".docx":  return "docx"
        if ext == ".xlsx":  return "xlsx"
        if ext == ".pptx":  return "pptx"
    if ext in AUDIO_EXTS:  return "audio"
    if ext in VIDEO_EXTS:  return "video"
    return "unsupported"


def scan_file(path: Path) -> dict | None:
    ftype = get_file_type(path)
    scanners = {
        "image": scan_image,
        "pdf":   scan_pdf,
        "docx":  scan_docx,
        "xlsx":  scan_xlsx,
        "pptx":  scan_pptx,
        "audio": scan_audio,
        "video": scan_video,
    }
    if ftype == "unsupported":
        return None
    return scanners[ftype](path)


def strip_file(path: Path) -> bool:
    ftype = get_file_type(path)
    strippers = {
        "image": strip_image,
        "pdf":   strip_pdf,
        "docx":  strip_docx,
        "xlsx":  strip_xlsx,
        "pptx":  strip_pptx,
        "audio": strip_audio,
    }
    if ftype == "unsupported":
        console.print(f"  [yellow]Skipping unsupported file: {path.name}[/yellow]")
        return False
    if ftype == "video":
        console.print(f"  [yellow]Video stripping not supported: {path.name}[/yellow]")
        return False
    return strippers[ftype](path)


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    all_exts = IMAGE_EXTS | PDF_EXTS | OFFICE_EXTS | AUDIO_EXTS | VIDEO_EXTS
    return [f for f in target.rglob("*") if f.is_file() and f.suffix.lower() in all_exts]


# ─── DISPLAY ────────────────────────────────────────────────────────────────

TYPE_COLORS = {
    "image": "cyan",
    "pdf":   "red",
    "docx":  "blue",
    "xlsx":  "green",
    "pptx":  "magenta",
    "audio": "yellow",
    "video": "bright_magenta",
}

RISK_FIELDS = {
    "GPS", "GPSLatitude", "GPSLongitude", "GPSAltitude",
    "Author", "Creator", "Producer", "LastModifiedBy",
    "Last Modified By", "Last_modified_by", "author",
    "Make", "Model", "Software", "DateTime", "DateTimeOriginal"
}

def display_meta(path: Path, meta: dict):
    ftype = get_file_type(path)
    color = TYPE_COLORS.get(ftype, "white")

    table = Table(box=box.SIMPLE_HEAVY, show_header=True,
                  header_style="bold white", expand=False)
    table.add_column("Field", style=f"bold {color}", min_width=22)
    table.add_column("Value", style="white", min_width=40, overflow="fold")

    risky_found = []

    def add_rows(d: dict, prefix=""):
        for k, v in d.items():
            label = f"{prefix}{k}"
            is_risky = any(r.lower() in label.lower() for r in RISK_FIELDS)
            if isinstance(v, dict):
                add_rows(v, prefix=f"{k} › ")
            else:
                if is_risky:
                    risky_found.append(label)
                    table.add_row(f"⚠  {label}", f"[bold red]{v}[/bold red]")
                else:
                    table.add_row(f"   {label}", v)

    add_rows(meta)

    risk_tag = f" [bold red]({len(risky_found)} sensitive fields)[/bold red]" if risky_found else " [green](clean)[/green]"
    title = f"[bold {color}]{path.name}[/bold {color}] [{ftype.upper()}]{risk_tag}"
    console.print(Panel(table, title=title, border_style=color))


# ─── MENU HELPERS ────────────────────────────────────────────────────────────

def ask(prompt: str, choices: list[str]) -> str:
    """Show numbered choices and return the selected number string."""
    while True:
        console.print(f"\n[bold cyan]{prompt}[/bold cyan]")
        for i, c in enumerate(choices, 1):
            console.print(f"  [bold white]{i}.[/bold white] {c}")
        raw = input("\n  › ").strip()
        if raw in [str(i) for i in range(1, len(choices) + 1)]:
            return raw
        console.print("[red]  Invalid choice, try again.[/red]")


def ask_path(prompt: str) -> Path | None:
    """Ask for a file or folder path, return None to go back."""
    console.print(f"\n[bold cyan]{prompt}[/bold cyan]")
    console.print("  [dim](type 'back' to return to menu)[/dim]")
    raw = input("  › ").strip()
    if raw.lower() == "back":
        return None
    p = Path(raw)
    if not p.exists():
        console.print(f"[red]  Path not found: {raw}[/red]")
        return None
    return p


def clear():
    os.system("clear")


def banner():
    console.print(Panel(
        "[bold green]███╗   ███╗███████╗████████╗ █████╗ ███████╗ ██████╗ █████╗ ███╗  ██╗[/bold green]\n"
        "[bold green]████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗ ██║[/bold green]\n"
        "[bold green]██╔████╔██║█████╗     ██║   ███████║███████╗██║     ███████║██╔██╗██║[/bold green]\n"
        "[bold green]██║╚██╔╝██║██╔══╝     ██║   ██╔══██║╚════██║██║     ██╔══██║██║╚████║[/bold green]\n"
        "[bold green]██║ ╚═╝ ██║███████╗   ██║   ██║  ██║███████║╚██████╗██║  ██║██║ ╚███║[/bold green]\n"
        "[bold green]╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚══╝ by 4y0ubyyyy[/bold green]\n\n"
        "  [dim]Metadata Scanner & Stripper  •  Images · PDFs · Office · Audio · Video[/dim]",
        border_style="green",
        padding=(0, 2),
    ))


# ─── ACTIONS ─────────────────────────────────────────────────────────────────

def action_scan():
    target = ask_path("Enter the path to a file or folder to scan:")
    if target is None:
        return

    files = collect_files(target)
    if not files:
        console.print("[yellow]  No supported files found.[/yellow]")
        input("\n  Press Enter to continue...")
        return

    console.print(Panel(
        f"[bold green]SCANNING[/bold green] — [cyan]{len(files)}[/cyan] file(s) found",
        border_style="green"
    ))

    report = {}
    for f in files:
        meta = scan_file(f)
        if meta is None:
            continue
        display_meta(f, meta)
        report[str(f)] = {"type": get_file_type(f), "metadata": meta}

    console.print(f"\n[dim]Scanned {len(report)} file(s) at {datetime.now().strftime('%H:%M:%S')}[/dim]")

    choice = ask("What do you want to do next?", [
        "Export results to JSON report",
        "Back to main menu",
    ])
    if choice == "1":
        default_name = f"metascan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        console.print(f"\n[bold cyan]Save report as:[/bold cyan] [dim](Enter for '{default_name}')[/dim]")
        name = input("  › ").strip() or default_name
        out = Path(name)
        out.write_text(json.dumps(report, indent=2, default=str))
        console.print(f"\n[bold green]✔[/bold green] Report saved → [cyan]{out.resolve()}[/cyan]")
        input("\n  Press Enter to continue...")


def action_strip():
    target = ask_path("Enter the path to a file or folder to strip:")
    if target is None:
        return

    files = collect_files(target)
    if not files:
        console.print("[yellow]  No supported files found.[/yellow]")
        input("\n  Press Enter to continue...")
        return

    # Show what will be affected
    console.print(f"\n  Found [cyan]{len(files)}[/cyan] file(s):")
    for f in files[:10]:
        console.print(f"    [dim]•[/dim] {f.name}")
    if len(files) > 10:
        console.print(f"    [dim]... and {len(files) - 10} more[/dim]")

    choice = ask("Choose strip mode:", [
        "Strip with backup  [dim](safe — keeps originals)[/dim]",
        "Strip without backup  [dim](permanent — no undo)[/dim]",
        "Cancel",
    ])

    if choice == "3":
        return

    backup = choice == "1"

    if backup:
        backup_dir = target.parent / f"{target.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if target.is_dir():
            shutil.copytree(str(target), str(backup_dir))
        else:
            backup_dir.mkdir(exist_ok=True)
            shutil.copy2(str(target), str(backup_dir / target.name))
        console.print(f"\n  [dim]Backup saved → {backup_dir}[/dim]")

    console.print(Panel(
        f"[bold red]STRIPPING[/bold red] — Removing metadata from [cyan]{len(files)}[/cyan] file(s)",
        border_style="red"
    ))

    ok, fail = 0, 0
    for f in files:
        console.print(f"  Stripping [cyan]{f.name}[/cyan]...", end=" ")
        if strip_file(f):
            console.print("[green]✔[/green]")
            ok += 1
        else:
            fail += 1

    console.print(f"\n[bold]Done:[/bold] [green]{ok} stripped[/green]   [red]{fail} failed/skipped[/red]")
    input("\n  Press Enter to continue...")


def action_help():
    console.print(Panel(
        "[bold]Supported file types:[/bold]\n\n"
        "  [cyan]Images[/cyan]   .jpg  .jpeg  .png  .tiff  .webp  .heic\n"
        "  [red]PDF[/red]      .pdf\n"
        "  [blue]Word[/blue]     .docx\n"
        "  [green]Excel[/green]    .xlsx\n"
        "  [magenta]PowerPt[/magenta]  .pptx\n"
        "  [yellow]Audio[/yellow]    .mp3  .flac  .ogg  .m4a  .wav\n"
        "  [bright_magenta]Video[/bright_magenta]    .mp4  .mkv  .avi  .mov  (read-only)\n\n"
        "[bold]What gets detected:[/bold]\n\n"
        "  ⚠  GPS coordinates, device make/model, software used\n"
        "  ⚠  Author name, last modified by, revision history\n"
        "  ⚠  Creation & modification timestamps\n\n"
        "[bold]Strip mode:[/bold]\n\n"
        "  Removes all sensitive metadata in-place.\n"
        "  Use [green]'with backup'[/green] to keep originals safe.",
        title="[bold white]Help & Info[/bold white]",
        border_style="dim",
    ))
    input("\n  Press Enter to continue...")


# ─── MAIN LOOP ────────────────────────────────────────────────────────────────

def main():
    while True:
        clear()
        banner()

        choice = ask("What do you want to do?", [
            "🔍  Scan file / folder   [dim](view metadata)[/dim]",
            "🧹  Strip file / folder  [dim](remove metadata)[/dim]",
            "❓  Help",
            "🚪  Exit",
        ])

        if choice == "1":
            clear()
            action_scan()
        elif choice == "2":
            clear()
            action_strip()
        elif choice == "3":
            clear()
            action_help()
        elif choice == "4":
            console.print("\n[dim]Bye go hack the world lol 👋[/dim]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
