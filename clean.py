import re
import os
from mutagen.id3 import ID3, ID3NoHeaderError, COMM

# Winodws/Linux filename cleaner
def clean_string(name:str) -> str:
    # remove forbidden characters
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', name)

    # remove trailing spaces or periods
    name = name.rstrip(' .')

    # reserved device names (case‑insensitive)
    if re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])', name):
        name += '_'

    # prevent empty filename
    return name or '_'

def update_filename(file_path:str, title:str, artists:str) -> str:
    if not title or not artists:
        return file_path

    root = os.path.dirname(file_path)
    file = os.path.basename(file_path)
    _, ext = os.path.splitext(file) # .mp3

    filename_artist = artists.split(",")[0].split("/")[0].strip() # get only first artist
    filename_title = title

    base_name = f"{filename_artist} - {filename_title}{ext}"
    base_name = clean_string(base_name) # to ensure valid filename

    new_path = os.path.join(root, base_name)

    if file_path != new_path:

        counter = 1
        final_path = new_path

        while os.path.exists(final_path):
            final_path = os.path.join(root, f"{base_name} ({counter}){ext}")
            counter += 1

        print(f"  FILENAME -> \"{os.path.basename(final_path)}\"")
        return final_path

    return file_path

def update_comment(new_comment:str, old_comment:str) -> str:
    if new_comment == " <<< clear all comment data >>> ":
        return ""
    
    if not new_comment:
        return old_comment
        
    if old_comment.startswith(new_comment):
        return old_comment
    
    if old_comment:
        new_comment = f"{new_comment} | {old_comment}"

    print(f"  COMMENT  -> \"{new_comment}\"")
    return new_comment

def update_mp3(path:str, new_comment:str, modify:bool):
    if os.path.isfile(path):
        files_to_process = [(os.path.dirname(path), [], [os.path.basename(path)])]
    else:
        files_to_process = os.walk(path)

    count = 1
    for root, _, files in files_to_process:
        for file in files:
            if not file.lower().endswith(".mp3"):
                continue

            file_path = os.path.join(root, file)
            print(f"\n{'─' * 70}")
            print(f"#{count} File: \"{file}\"")
            print(f"{'─' * 70}")

            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                print("  (no ID3 tags found)")
                continue

            # ── Read all tags into variables ───────────────────────────────────────
            title   = str(audio.get("TIT2", ""))
            artists = str(audio.get("TPE1", ""))
            album   = str(audio.get("TALB", ""))
            year    = str(audio.get("TDRC", ""))
            track   = str(audio.get("TRCK", ""))
            genre   = str(audio.get("TCON", ""))

            comments = audio.getall("COMM")
            comment = ""
            for c in comments:
                if c.lang == "eng" and c.text:
                    comment = c.text[0]
                    break
            else:
                if comments and comments[0].text:
                    comment = comments[0].text[0]

            # ── Print ──────────────────────────────────────────────────────────────
            print(f"  Title:   {title}")
            print(f"  Artist:  {artists}")
            print(f"  Album:   {album}")
            print(f"  Year:    {year}")
            print(f"  Track:   {track}")
            print(f"  Genre:   {genre}")
            print(f"  Comment: {comment}")
            print("\n")

            # ── Edit values ───────────────────────────────────────────────────────

            new_file_path = update_filename(file_path, title, artists)
            comment = update_comment(new_comment, comment) 

            # ── Save back (edit values above before this line) ────────────────────
            if title:   audio["TIT2"].text = [title]
            if artists: audio["TPE1"].text = [artists]
            if album:   audio["TALB"].text = [album]
            if year:    audio["TDRC"].text = [year]
            if track:   audio["TRCK"].text = [track]
            if genre:   audio["TCON"].text = [genre]
            if comment:
                audio.delall("COMM")  # remove old comment
                audio.add(COMM(encoding=3, lang='eng', desc='', text=comment))

            if modify:
                audio.save(file_path, v2_version=3) # update tags
                os.rename(file_path, new_file_path) # rename

            count+=1
    return


