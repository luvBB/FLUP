import os
import random
import subprocess
import signal
import requests
import re
import sys
from bs4 import BeautifulSoup

# ===============================
# Configuration: API Keys, Paths, and Credentials
# ===============================
img4k_api_url = 'https://img4k.net/api/1/upload'
img4k_api_key = 'img4k.net api key'

filelist_username = '*'
filelist_password = '*'

qbittorrent_url = 'http://localhost:8089'
qbittorrent_username = '*'
qbittorrent_password = '*'

mediainfo_path = r"F:\FLUP\mediainfo\mediainfo.exe"
ffmpeg_path = r"ffmpeg"
