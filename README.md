# ComicMerge

A simple and efficient Python tool with a graphical interface to merge multiple comic book archives (.cbz, .cbr) into a single, sequentially ordered .cbz file. It automatically handles natural sorting for numbers and extracts nested folders correctly.

## Features

* Supports both **.cbz** (ZIP) and **.cbr** (RAR) formats.
* Graphical file picker and save dialog using **Tkinter**.
* Natural sorting for chapters and volumes, ensuring proper chapter ordering.
* Automatically detects system UnRAR or 7-Zip tools for archive extraction.

## Prerequisites

For **.cbr** file support, ensure you have one of the following tools installed on your system:
* **WinRAR** (with `UnRAR.exe`)
* **7-Zip** (`7z.exe`)
* **UnRAR** utility added to your system PATH.

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/comic-merge.git](https://github.com/your-username/comic-merge.git)
   cd comic-merge
