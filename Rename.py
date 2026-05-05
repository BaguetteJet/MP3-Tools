# --- DISCLAIMER: I made this utilizing GPT-5.
import os
import sys
import subprocess
import json
# --- Ensure mutagen is installed ---
try:
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3, COMM, ID3NoHeaderError
except ModuleNotFoundError:
    print("Mutagen not found — installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mutagen"])
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3, COMM, ID3NoHeaderError

# ===================== SETTINGS =====================
CONFIG_FILE = "config.json"
if not os.path.exists(CONFIG_FILE):
    print(f"ERROR: {CONFIG_FILE} not found. Please create it first.")
    sys.exit(1)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

folder_path = config.get("folder_path")

find_name = config.get("find_name", "")
replace_name = config.get("replace_name", "")
find_comment = config.get("find_comment", "")
replace_comment = config.get("replace_comment", "")

normalize_artist_in_filename = bool(config.get("normalize_artist_in_filename", False))
safe_mode = bool(config.get("safe_mode", True))

if not folder_path or not os.path.isdir(folder_path):
    print(f"ERROR: folder_path '{folder_path}' is invalid.")
    sys.exit(1)

# --- Show settings and confirm ---
print("Current settings loaded from config.json:")
print(f"  Folder Path:              {folder_path}")
print(f"  Find in filename:         '{find_name}'")
print(f"  Replace with:             '{replace_name}'")
print(f"  Find in comment:          '{find_comment}'")
print(f"  Replace with:             '{replace_comment}'")
print(f"  Normalize artist prefix:  {normalize_artist_in_filename}")
print(f"  Safe Mode:                {safe_mode}")
print("-" * 40)

choice = input("Proceed with these settings? (Y/N): ").strip().lower()
if choice != "y":
    print("Aborted by user.")
    sys.exit(0)
# =====================================================

def get_first_artist(file_path):
    """Return the first artist from ID3 TPE1 tag, or None if unavailable.

    ID3 tags commonly join multiple artists with '/', ';', or '\x00' (null byte).
    We split on all of them and return only the very first.
    """
    try:
        audio = ID3(file_path)
        tpe1_frames = audio.getall("TPE1")
        if tpe1_frames:
            raw = tpe1_frames[0].text[0]  # e.g. "Sam Smith/Kim Petras"
            # Replace all common delimiters with a single sentinel, then split once
            normalised = raw.replace("\x00", "/").replace(";", "/")
            first_artist = normalised.split("/")[0].strip()
            return first_artist if first_artist else None
    except ID3NoHeaderError:
        pass
    return None


def normalize_filename_with_artist(name_no_ext, artist):
    """
    Ensure the filename is formatted as "<ARTIST> - <SONG_NAME>".

    Handles three cases:
      1. "Song Name - Artist"   → artist is a suffix  → "Artist - Song Name"
      2. "Artist - Song Name"   → artist is a prefix  → unchanged
      3. "Song Name"            → artist is absent    → "Artist - Song Name"

    Returns the corrected name (without extension), or None if no change needed.
    """
    separator = " - "

    # Case 2: already correctly prefixed — nothing to do
    if name_no_ext.startswith(artist + separator):
        return None

    # Case 1: artist appears as a suffix → strip it and prepend
    if name_no_ext.endswith(separator + artist):
        song_name = name_no_ext[: -(len(separator) + len(artist))]
        return f"{artist}{separator}{song_name}"

    # Case 3: artist is absent entirely → prepend it
    return f"{artist}{separator}{name_no_ext}"


# --- Function to process each file ---
def process_file(file_path):
    filename = os.path.basename(file_path)
    name_no_ext, ext = os.path.splitext(filename)
    dir_path = os.path.dirname(file_path)
    changes = []

    # --- Normalize artist position in filename ---
    if normalize_artist_in_filename:
        first_artist = get_first_artist(file_path)
        if first_artist:
            corrected = normalize_filename_with_artist(name_no_ext, first_artist)
            if corrected:
                new_filename = corrected + ext
                new_path = os.path.join(dir_path, new_filename)
                changes.append(("filename (artist normalised)", filename, new_filename))
                if not safe_mode:
                    os.rename(file_path, new_path)
                    file_path = new_path
                    name_no_ext = corrected  # keep in sync for any further steps
                    filename = new_filename

    # --- Generic find/replace in filename ---
    if find_name and find_name in filename:
        new_filename = filename.replace(find_name, replace_name)
        new_path = os.path.join(dir_path, new_filename)
        changes.append(("filename", filename, new_filename))
        if not safe_mode:
            os.rename(file_path, new_path)
            file_path = new_path

    # --- Comment metadata check ---
    try:
        audio = ID3(file_path)
        for frame in audio.getall("COMM"):
            if find_comment in frame.text[0]:
                old_comment = frame.text[0]
                new_comment = old_comment.replace(find_comment, replace_comment)
                changes.append(("comment", old_comment, new_comment))
                if not safe_mode:
                    frame.text[0] = new_comment
                    audio.save(v2_version=3)  # save in ID3v2.3 for compatibility
    except ID3NoHeaderError:
        pass  # no metadata found, skip

    return changes

# --- Recursive scan ---
for root, _, files in os.walk(folder_path):
    for file in files:
        if file.lower().endswith(".mp3"):
            file_path = os.path.join(root, file)
            changes = process_file(file_path)
            for change_type, old, new in changes:
                print(f"[{change_type.upper()}] {old} → {new}")

if safe_mode:
    print("\nSAFE MODE ENABLED - No files were changed.")
    print("Set safe_mode = False in config.json to apply changes.")
else:
    print("\nChanges applied.")