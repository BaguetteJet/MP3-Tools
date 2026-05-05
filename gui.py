import os
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from clean import update_mp3

def select_file():
    clear_output()
    path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
    if path:
        path_var.set(path)
        on_path_change
        preview_btn.config(state="normal")

def select_folder():
    clear_output()
    path = filedialog.askdirectory()
    if path:
        path_var.set(path)
        on_path_change
        preview_btn.config(state="normal")

def preview():
    path = path_var.get()
    comment = comment_var.get()

    apply_btn.config(state="disabled")
    
    clear_output()

    output_action.config(text=f"Previewing possible changes to {count_var.get()} file(s):\n-> {path}\n")

    if not path:
        messagebox.showerror("Error", "No MP3 file or folder selected.")
        return
    
    update_mp3(path, comment, False)
    apply_btn.config(state="normal")

def apply():
    path = path_var.get()
    comment = comment_var.get()

    output_action.config(text=f"Applying changes to {count_var.get()} file(s):\n-> {path}\n")

    if not path:
        messagebox.showerror("Error", "No file selected.")
        return
    
    if not messagebox.askyesno("Confirm", f"Apply changes to {count_var.get()} file(s)?"):
        return
    
    on_path_change
    
    update_mp3(path, comment, True)
    output_action.config( text=f"Successfully applied changes to {count_var.get()} file(s):\n-> {path}")

def clear_comments():
    comment_var.set(" <<< clear all comment data >>> ")

def get_mp3_count(path):
    if not path:
        return 0
    if os.path.isfile(path):
        return 1 if path.lower().endswith(".mp3") else 0
    if os.path.isdir(path):
        return sum(1 for f in os.listdir(path) if f.lower().endswith(".mp3"))
    return 0

def on_path_change(*args):
    path = path_var.get()
    count = get_mp3_count(path)
    
    clear_output()

    preview_btn.config(state="disabled")
    apply_btn.config(state="disabled")

    if path:
        count_var.set(count)
        preview_btn.config(state="normal" if count > 0 else "disabled")
        output_action.config( text=f"Selected {count} file(s):\n-> {path}")
    else:
        count_var.set(0)
        preview_btn.config(state="disabled")
        output_action.config(text="")

def clear_output():
    output.config(state="normal")
    output.delete("1.0", tk.END)
    output.config(state="disabled")


# --- Window ---
root = tk.Tk()
root.title("Python MP3 Cleaner - Baguette_Jet 2026")

# Center window
window_width = 900
window_height = 500

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))

root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# --- Variables ---
path_var = tk.StringVar()
comment_var = tk.StringVar(value="")
count_var = tk.IntVar()

path_var.trace_add("write", on_path_change) # disable preview button until path

# --- UI Layout ---
frame = tk.Frame(root)
frame.pack(padx=10, pady=10, fill="both", expand=True)

# Folder input
tk.Label(frame, text="Select MP3 file or folder path").pack(anchor="w")
folder_frame = tk.Frame(frame)
folder_frame.pack(fill="x")
tk.Entry(folder_frame, textvariable=path_var).pack(side="left", fill="x", expand=True)

# Browse buttons
button_frame1 = tk.Frame(frame)
button_frame1.pack(anchor="w", pady=5)
tk.Button(button_frame1, text="Browse Files", command=select_file).pack(side="left", padx=1)
tk.Button(button_frame1, text="Browse Folders", command=select_folder).pack(side="left", padx=1)

# Comment input
comment_frame = tk.Frame(frame)
comment_frame.pack(fill="x", pady=(10, 0))
tk.Label(comment_frame, text="Comment (optional): ").pack(side="left")
tk.Entry(comment_frame, textvariable=comment_var).pack(side="left", fill="x", expand=True)
tk.Button(comment_frame, text="Clear Comments", command=clear_comments).pack(side="left", padx=1)

# Action Buttons
button_frame2 = tk.Frame(frame)
button_frame2.pack(pady=10)

preview_btn = tk.Button(button_frame2, text="Preview", command=preview, state="disabled")
preview_btn.pack(side="left", padx=5)

apply_btn = tk.Button(button_frame2, text="Apply", command=apply, state="disabled")
apply_btn.pack(side="left", padx=5)

# Info label
output_action = tk.Label(frame, text="", anchor="w", justify="left", height=2)
output_action.pack(fill="both")

# Scrollable output
output = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=15)
output.pack(fill="both", expand=True)
output.config(state="disabled")

# Show print() in output text box
class StdoutRedirector:
    def write(self, text):
        output.config(state="normal")
        output.insert(tk.END, text)
        output.see(tk.END) # auto scroll
        output.config(state="disabled")
        output.update_idletasks() # update live

    def flush(self):
        pass  # required for compatibility

sys.stdout = StdoutRedirector()

# Run
root.mainloop()