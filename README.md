# FLUP - Semi-Automatic Torrent Uploader for FileList.io

![FLUP Logo](https://github.com/user-attachments/assets/f947a7ae-a0d3-452b-a9e7-4f6f7bae7204)

## 🌟 Overview

**FLUP is a semi-automated uploader for FileList.io, designed to streamline the process of uploading torrents for movies and TV shows in any format and category**

## 🛠️ Prerequisites

1. **Install Python Dependencies**

   ```sh
   pip install -r requirements.txt

2. **Download FFMpeg** -> [FFMpeg](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z)

   Unzip this file by using any file archiver such as Winrar or 7z.

   Rename the extracted folder to ffmpeg and move it into the root of C: drive.

   Now, run cmd as an administrator and set the environment path variable for ffmpeg by running the following command:

   ```sh
   setx /m PATH "C:\ffmpeg\bin;%PATH%"

3. **Install Windows MSI torrenttools from** [HERE](https://github.com/fbdtemme/torrenttools/releases)

4. **Install** [VLC](https://www.videolan.org/vlc/download-windows.html)

5. **Configure qBitorrent Web UI using this image as example:**

<details>
   <summary>Click to see the image</summary>

  ![359194253-071c56f5-1780-40cd-9862-20b4a0b4601c](https://github.com/user-attachments/assets/e8f6c1dd-0e85-4539-a23d-ea7cc84b64da)

</details>

## ⚙️ Configuration: API Keys, Paths, and Credentials

**Before using FLUP, it's essential to configure the API keys, paths, and credentials to ensure everything operates smoothly. These configurations are located at the top of each script file (`BD.py`, `Movie.py`, `TV.py`).**

## 🚀 Running the script in CMD
`python BD.py`
`python TV.py`
`python Movie.py`

| 🚀 python BD.py | 🚀 python TV.py | 🚀 python Movie.py |
| ------ | ------ | --------- |
| ➡️ Filme Blu-ray | ➡️ Anime | ➡️ Anime |
| ➡️ Filme 4k Blu-ray | ➡️ Desene | ➡️ Desene |
| ✖️ | ➡️ Seriale 4k | ➡️ Filme 4k |
| ✖️ | ➡️ Seriale HD | ➡️ Filme HD |
| ✖️ | ➡️ Seriale SD | ➡️ Filme HD-RO |
| ✖️ | ✖️ | ➡️ Filme SD |
