import os
import shutil
import zipfile
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import rarfile
from typing import List

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
    def __init__(self, output_name: str, comics_to_merge: List[str], is_verbose: bool = True):
        self.output_name = output_name
        if not self.output_name.endswith(".cbz"):
            self.output_name += ".cbz"
        
        # Exclude the output file itself if selected by mistake
        self.comics_to_merge = [c for c in comics_to_merge if c != self.output_name]
        self.is_verbose = is_verbose

    def _log(self, msg: str):
        if self.is_verbose:
            print(msg)

    @staticmethod
    def _extract_archive(file_name: str, destination: str, verbose: bool):
        base_name = os.path.basename(file_name)
        output_dir = os.path.join(destination, os.path.splitext(base_name)[0])
        os.mkdir(output_dir)
        
        if verbose:
            print(f'Unzipping {base_name}')
        
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
            self._extract_archive(file_name, temp_dir, self.is_verbose)

        files_moved = 1
        extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        
        for subdir_name in self.natsorted(extracted_dirs):
            comic_dir = os.path.join(temp_dir, subdir_name)
            
            for root, dirs, files in os.walk(comic_dir):
                dirs[:] = self.natsorted(dirs)
                for file_name in self.natsorted(files):
                    file_path = os.path.join(root, file_name)
                    ext = os.path.splitext(file_name)[1]
                    new_name = f"P{str(files_moved).rjust(5, '0')}{ext}"
                    
                    self._log(f'Renaming & moving {file_name} to {new_name}')
                    shutil.move(file_path, os.path.join(temp_dir, new_name))
                    files_moved += 1
                    
            shutil.rmtree(comic_dir)

    def _make_cbz_from_dir(self, temp_dir: str):
        self._log(f'Initializing cbz {os.path.basename(self.output_name)}')
        
        with zipfile.ZipFile(self.output_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            self._log('Adding files to cbz...')
            add_count = 0
            
            files_to_zip = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
            
            for file_name in self.natsorted(files_to_zip):
                file_path = os.path.join(temp_dir, file_name)
                zip_file.write(file_path, file_name)
                add_count += 1
                if add_count % 10 == 0:
                    self._log(f'{add_count} files added.')

    @staticmethod
    def natsorted(l: List[str]) -> List[str]:
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)
    
    def merge(self):
        try:
            self._remove_file(self.output_name)
            self._log(f'Merging comics into file {self.output_name}')

            target_dir = os.path.dirname(self.output_name)
            if target_dir:
                os.chdir(target_dir)
                
            temp_dir = self._find_temp_folder()
            os.mkdir(temp_dir)

            self._extract_comics(temp_dir)
            self._make_cbz_from_dir(temp_dir)

            shutil.rmtree(temp_dir)
            self._log('\nSuccess!')
            messagebox.showinfo("Success", f"Comics successfully merged into:\n{self.output_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during merging:\n{str(e)}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    selected_files = filedialog.askopenfilenames(
        title="Select .cbz or .cbr files to merge",
        filetypes=[("Comic Books", "*.cbz *.cbr"), ("All files", "*.*")]
    )

    if not selected_files:
        exit()

    sorted_files = ComicMerge.natsorted(list(selected_files))

    output_filepath = filedialog.asksaveasfilename(
        title="Save merged comic as...",
        defaultextension=".cbz",
        filetypes=[("Comic Book Zip", "*.cbz")]
    )

    if not output_filepath:
        exit()

    merger = ComicMerge(output_filepath, sorted_files)
    merger.merge()
