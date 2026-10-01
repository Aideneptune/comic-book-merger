import os
import sys
import shutil
import zipfile
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import rarfile
from typing import List, Callable

# Auto-detect UnRAR or 7-Zip for .cbr extraction
if shutil.which('unrar'):
    rarfile.UNRAR_TOOL = 'unrar'
elif shutil.which('7z'):
    rarfile.UNRAR_TOOL = '7z'
else:
    # Fallback to default Windows installation paths
    if os.path.exists(r"C:\Program Files\WinRAR\UnRAR.exe"):
        rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"
    elif os.path.exists(r"C:\Program Files\7-Zip\7z.exe"):
        rarfile.UNRAR_TOOL = r"C:\Program Files\7-Zip\7z.exe"

class ComicMerge:
    def __init__(self, output_name: str, comics_to_merge: List[str], log_callback: Callable[[str], None] = None):
        self.output_name = output_name
        if not self.output_name.endswith(".cbz"):
            self.output_name += ".cbz"
        
        self.comics_to_merge = [c for c in comics_to_merge if c != self.output_name]
        self.log_callback = log_callback

    def _log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(msg)

    def _extract_archive(self, file_name: str, destination: str):
        base_name = os.path.basename(file_name)
        output_dir = os.path.join(destination, os.path.splitext(base_name)[0])
        os.mkdir(output_dir)
        
        self._log(f'Unzipping: {base_name}')
        
        ext = os.path.splitext(file_name)[1].lower()
        if ext == '.cbz':
            with zipfile.ZipFile(file_name) as zip_file:
                zip_file.extractall(output_dir)
        elif ext == '.cbr':
            with rarfile.RarFile(file_name) as r_file:
                r_file.extractall(output_dir)

    @staticmethod
    def _remove_file(file_name: str):
        if os.path.exists(file_name):
            os.remove(file_name)

    @staticmethod
    def _find_temp_folder() -> str:
        base_dir = 'temp_merge'
        mod = 0
        temp_dir = base_dir
        while os.path.exists(temp_dir):
            mod += 1
            temp_dir = f"{base_dir}{mod}"
        return temp_dir

    def _extract_comics(self, temp_dir: str):
        for file_name in self.comics_to_merge:
            self._extract_archive(file_name, temp_dir)

        files_moved = 1
        extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        
        self._log('Renaming and structuring files...')
        for subdir_name in self.natsorted(extracted_dirs):
            comic_dir = os.path.join(temp_dir, subdir_name)
            
            for root, dirs, files in os.walk(comic_dir):
                dirs[:] = self.natsorted(dirs)
                for file_name in self.natsorted(files):
                    file_path = os.path.join(root, file_name)
                    ext = os.path.splitext(file_name)[1]
                    new_name = f"P{str(files_moved).rjust(5, '0')}{ext}"
                    
                    shutil.move(file_path, os.path.join(temp_dir, new_name))
                    files_moved += 1
                    
            shutil.rmtree(comic_dir)

    def _make_cbz_from_dir(self, temp_dir: str):
        self._log(f'Creating final archive: {os.path.basename(self.output_name)}')
        
        with zipfile.ZipFile(self.output_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            add_count = 0
            files_to_zip = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
            
            for file_name in self.natsorted(files_to_zip):
                file_path = os.path.join(temp_dir, file_name)
                zip_file.write(file_path, file_name)
                add_count += 1
                if add_count % 10 == 0:
                    self._log(f'Packing files: {add_count} added.')

    @staticmethod
    def natsorted(l: List[str]) -> List[str]:
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)
    
    def merge(self):
        try:
            self._remove_file(self.output_name)
            self._log('Starting merge process...')

            target_dir = os.path.dirname(self.output_name)
            if target_dir:
                os.chdir(target_dir)
                
            temp_dir = self._find_temp_folder()
            os.mkdir(temp_dir)

            self._extract_comics(temp_dir)
            self._make_cbz_from_dir(temp_dir)

            self._log('Cleaning up temporary files...')
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    selected_files = filedialog.askopenfilenames(
        title="Select .cbz or .cbr files to merge",
        filetypes=[("Comic Books", "*.cbz *.cbr"), ("All files", "*.*")]
    )

    if not selected_files:
        sys.exit(0)

    sorted_files = ComicMerge.natsorted(list(selected_files))

    output_filepath = filedialog.asksaveasfilename(
        title="Save merged comic as...",
        defaultextension=".cbz",
        filetypes=[("Comic Book Zip", "*.cbz")]
    )

    if not output_filepath:
        sys.exit(0)

    # Creating a Status Window
    progress_win = tk.Toplevel(root)
    progress_win.title("Working...")
    progress_win.geometry("400x120")
    progress_win.resizable(False, False)
    
    # Center alignment on the screen
    progress_win.update_idletasks()
    x = (progress_win.winfo_screenwidth() // 2) - (400 // 2)
    y = (progress_win.winfo_screenheight() // 2) - (120 // 2)
    progress_win.geometry(f"+{x}+{y}")
    status_label = tk.Label(progress_win, text="Starting...", font=("Arial", 10), wraplength=380)
    status_label.pack(expand=True, fill=tk.BOTH, pady=20)

    def update_status(msg: str):
        status_label.config(text=msg)
        root.update()

    merger = ComicMerge(output_filepath, sorted_files, log_callback=update_status)
    
    try:
        success = merger.merge()
        if success:
            progress_win.destroy()
            messagebox.showinfo("Success", f"Process completed!\nSaved to: {os.path.basename(output_filepath)}")
    except Exception as e:
        progress_win.destroy()
        messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
