# 🔍 METASCAN
> Metadata Scanner & Stripper — find and remove hidden info from your files

---

## What is this?

Every file you create or share contains hidden **metadata** — things like:
- 📍 **GPS coordinates** embedded in photos taken on your phone
- 👤 **Your name** stored inside Word docs and PDFs
- 🖥️ **What software / device** you used to create a file
- 🕒 **Exact timestamps** of when you created or edited something

METASCAN lets you **see all of that** and **wipe it clean** before sharing files.

---

## Supported File Types

| Type | Extensions | Scan | Strip |
|------|-----------|------|-------|
| Images | `.jpg` `.jpeg` `.png` `.tiff` `.webp` `.heic` | ✅ | ✅ |
| PDF | `.pdf` | ✅ | ✅ |
| Word | `.docx` | ✅ | ✅ |
| Excel | `.xlsx` | ✅ | ✅ |
| PowerPoint | `.pptx` | ✅ | ✅ |
| Audio | `.mp3` `.flac` `.ogg` `.m4a` `.wav` | ✅ | ✅ |
| Video | `.mp4` `.mkv` `.avi` `.mov` `.wmv` | ✅ | ❌ |

---

## Requirements

- Python **3.10 or higher**
- pip

---

## Installation

**1. Clone or download the project**
```bash
git clone https://github.com/yourname/metascan.git
cd metascan
```

**2. Install dependencies**
```bash
pip install -r requirements.txt --break-system-packages
```

> ⚠️ The `--break-system-packages` flag is needed on **Ubuntu / Lubuntu / Debian** based systems.
> If you're on Windows or using a virtual environment, drop that flag.

**3. Run it**
```bash
python3 metascan.py
```

---

## Usage

Just launch it — no commands needed:

```
python3 metascan.py
```

You'll see a menu like this:

```
What do you want to do?
  1. 🔍  Scan file / folder   (view metadata)
  2. 🧹  Strip file / folder  (remove metadata)
  3. ❓  Help
  4. 🚪  Exit

  ›
```

Type a number and press Enter. That's it.

### Scanning
- Enter a file path or a folder path
- METASCAN will show all metadata found
- Sensitive fields (GPS, author, device info) are highlighted in **red** with a ⚠ warning
- After scanning you can export everything to a `.json` report

### Stripping
- Choose **with backup** (safe) or **without backup** (permanent)
- METASCAN removes all metadata in-place
- Works on single files or entire folders at once

---

## Example Output

```
╭─────────────── photo.jpg [IMAGE] (9 sensitive fields) ───────────────╮
│                                                                       │
│   Field                   Value                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│      Format               JPEG                                        │
│      Size                 4032x3024                                   │
│   ⚠  Make                 Apple                                       │
│   ⚠  Model                iPhone 13 Pro                               │
│   ⚠  GPS › GPSLatitude    (33.0, 34.0, 0.0)                          │
│   ⚠  GPS › GPSLongitude   (7.0, 36.0, 0.0)                           │
│   ⚠  DateTime             2024:03:15 14:32:01                         │
│                                                                       │
╰───────────────────────────────────────────────────────────────────────╯
```

After stripping:

```
╭──────────────── photo.jpg [IMAGE] (clean) ────────────────╮
│   Format    JPEG                                           │
│   Size      4032x3024                                      │
╰────────────────────────────────────────────────────────────╯
```

---

## Project Structure

```
metascan/
├── metascan.py        # Main script
├── requirements.txt   # Dependencies
└── README.md          # This file
```

---

## Troubleshooting

| Problem | Fix |
|--------|-----|
| `pip: command not found` | Use `pip3` instead |
| `externally-managed-environment` error | Add `--break-system-packages` to the pip command |
| `hachoir` install fails | Skip it — only needed for video scanning |
| `ModuleNotFoundError` | Re-run `pip install -r requirements.txt` |
| Permission denied on a file | Run with `sudo` or check file ownership |

---

## License

MIT — free to use, modify, and share.
made by 4y0ubyyyy 
