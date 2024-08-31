import os
import random
import subprocess
import signal
import requests
import re
from bs4 import BeautifulSoup

# ===============================
# Configuration: API Keys, Paths, and Credentials
# ===============================
img4k_api_url = 'https://img4k.net/api/1/upload'
img4k_api_key = 'img4k.net api key'

#TVDB
api_key = '*'
pin = '*'

filelist_username = '*'
filelist_password = '*'

qbittorrent_url = 'http://localhost:8089'
qbittorrent_username = '*'
qbittorrent_password = '*'

mediainfo_path = r"F:\FLUP\mediainfo\mediainfo.exe"
ffmpeg_path = r"ffmpeg"

# ===============================
# Function Definitions
# ===============================

# Function to delete specific files from the current directory.
def delete_files():
    extensions_to_delete = ['.txt', '.torrent', '.png']
    directory = os.getcwd()

    def delete_file(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            pass

    for filename in os.listdir(directory):
        if any(filename.endswith(ext) for ext in extensions_to_delete):
            file_path = os.path.join(directory, filename)
            delete_file(file_path)
delete_files()

# Kill FFmpeg process
def kill_ffmpeg_processes():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ffmpeg.exe'], stdout=subprocess.PIPE, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if 'ffmpeg.exe' in line:
            pid = int(line.split()[1])
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"FFmpeg process PID {pid} has been killed.")
            except OSError:
                print(f"Error killing FFmpeg PID {pid}.")
kill_ffmpeg_processes()

# Input direct path to file (.mkv) or folder to be uploaded
input_path = input("Input folder or mkv file path to upload: ")
if os.path.isfile(input_path) and input_path.endswith('.mkv'):
    mkv_files = [os.path.basename(input_path)]
    file_location = os.path.dirname(input_path)
elif os.path.isdir(input_path):
    file_location = input_path
    files = os.listdir(file_location)
    mkv_files = [file for file in files if file.endswith('.mkv')]
else:
    print("Invalid path.")
    exit()

if not mkv_files:
    print("No mkv files in this path.")
    exit()

selected_file = random.choice(mkv_files)
mediainfo_command = [mediainfo_path, os.path.join(file_location, selected_file)]
mediainfo_output = subprocess.check_output(mediainfo_command, encoding='utf-8').strip()

with open("mediainfo.txt", "w", encoding="utf-8") as output_file:
    output_file.write(mediainfo_output)

#print("File mediainfo.txt created")

duration_in_seconds = 0
for line in mediainfo_output.split('\n'):
    if "Duration" in line:
        duration_str = line.split(":")[1].strip()
        if 'h' in duration_str and 'min' in duration_str:
            hours = int(duration_str.split('h')[0].strip())
            minutes = int(duration_str.split('h')[1].split('min')[0].strip())
            duration_in_seconds = (hours * 3600) + (minutes * 60)
        elif 'min' in duration_str and 's' in duration_str:
            minutes = int(duration_str.split('min')[0].strip())
            seconds = int(duration_str.split('min')[1].split('s')[0].strip())
            duration_in_seconds = (minutes * 60) + seconds
        elif 'min' in duration_str:
            minutes = int(duration_str.split('min')[0].strip())
            duration_in_seconds = minutes * 60
        elif 's' in duration_str:
            seconds = int(duration_str.split('s')[0].strip())
            duration_in_seconds = seconds

if duration_in_seconds == 0:
    print("I couldn't determine the duration of the video.")
    exit()

screenshot_dir = os.getcwd()
screenshot_times = sorted(random.sample(range(0, duration_in_seconds), 3))
screenshot_filenames = []

for idx, time in enumerate(screenshot_times):
    screenshot_filename = os.path.join(screenshot_dir, f"screenshot_{idx + 1}.png")
    ffmpeg_command = [
        ffmpeg_path,
        '-ss', str(time),
        '-i', os.path.join(file_location, selected_file),
        '-frames:v', '1',
        '-q:v', '2',
        '-an',
        '-sn',
        screenshot_filename
    ]
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate(input=b'\n\n')
    screenshot_filenames.append(screenshot_filename)

#print("Screenshots saved")

uploaded_image_urls = []
for screenshot_filename in screenshot_filenames:
    with open(screenshot_filename, 'rb') as img_file:
        response = requests.post(
            img4k_api_url,
            data={'key': img4k_api_key, 'format': 'json'},
            files={'source': img_file}
        )
        if response.status_code == 200:
            response_data = response.json()
            if response_data['status_code'] == 200:
                # Accesează url_short pentru image_url și medium.url pentru medium_url
                image_url = response_data['image']['url_short']  # Folosește url_short pentru image_url
                medium_url = response_data['image']['medium']['url']  # Păstrează medium_url
                uploaded_image_urls.append((image_url, medium_url))
            else:
                print(f"Error while uploading saved screenshots: {response_data['error']['message']}")
        else:
            print(f"API error: {response.status_code}")

#print("Screenshots uploaded to img4k.net")

with open("images.txt", "w") as file:
    bbcode = ' '.join([f"[url={image_url}][img={medium_url}][/url]" for image_url, medium_url in uploaded_image_urls])
    file.write(bbcode)

#print("BBCode links saved in images.txt")

# Scrapping mediainfo
def extract_detail(pattern, text):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else 'N/A'

def extract_info(filename):
    with open(filename, 'r', encoding="utf-8") as file:
        data = file.read()

    info = {
        'General': {},
        'Video': {},
        'Audio': [],
        'Subtitles': []
    }

    # General section
    info['General']['Container'] = extract_detail(r'Container\s*:\s*(.+)', data)
    info['General']['Duration'] = extract_detail(r'Duration\s*:\s*(.+)', data)
    info['General']['File size'] = extract_detail(r'File size\s*:\s*(.+)', data)

    # Video section
    info['Video']['Format'] = extract_detail(r'Format\s*:\s*(.+)', data)
    info['Video']['Format profile'] = extract_detail(r'Format profile\s*:\s*(.+)', data)
    info['Video']['Scan type'] = extract_detail(r'Scan type\s*:\s*(.+)', data)
    info['Video']['Width'] = extract_detail(r'Width\s*:\s*(.+)', data)
    info['Video']['Height'] = extract_detail(r'Height\s*:\s*(.+)', data)
    info['Video']['Bit rate'] = extract_detail(r'Bit rate\s*:\s*(.+)', data)
    info['Video']['Frame rate'] = extract_detail(r'Frame rate\s*:\s*(.+)', data)
    info['Video']['HDR Format'] = extract_detail(r'HDR format\s*:\s*(.+)', data)

    # Audio section
    audio_matches = re.findall(r'Audio(?: #\d+)?\n(.*?)(?=\n(?:Audio|Text|$))', data, re.DOTALL)
    for audio_match in audio_matches:
        audio_info = {
            'Format': extract_detail(r'Format\s*:\s*(.+)', audio_match),
            'Commercial name': extract_detail(r'Commercial name\s*:\s*(.+)', audio_match),
            'Codec ID': extract_detail(r'Codec ID\s*:\s*(.+)', audio_match),
            'Channel(s)': extract_detail(r'Channel\(s\)\s*:\s*(.+)', audio_match),
            'Bit rate': extract_detail(r'Bit rate\s*:\s*(.+)', audio_match),
            'Language': extract_detail(r'Language\s*:\s*(.+)', audio_match),
            'Title': extract_detail(r'Title\s*:\s*(.+)', audio_match)
        }
        info['Audio'].append(audio_info)

    # Subtitles section, specifically targeting Text section
    subtitle_matches = re.findall(r'Text\n(?:ID\s*:\s*\d+\n)?(.*?)(?=\n(?:Audio|Text|Menu|$))', data, re.DOTALL)
    for subtitle_match in subtitle_matches:
        subtitle_language = extract_detail(r'Language\s*:\s*(.+)', subtitle_match)
        if subtitle_language:
            info['Subtitles'].append(subtitle_language)

    return info


# Creating description.txt
def create_description_txt(info, bbcode_images):
    # General section
    description = "[quote][pre][u]General[/u]\n"
    description += f"Container......: Matroska\n"
    if 'Duration' in info['General'] and info['General']['Duration'] != 'N/A':
        description += f"Duration.......: {info['General']['Duration']}\n"
    if 'File size' in info['General'] and info['General']['File size'] != 'N/A':
        description += f"Size...........: {info['General']['File size']}\n"

    # Video section
    description += "\n[u]Video[/u]\n"
    if 'Format' in info['Video'] and info['Video']['Format'] != 'N/A':
        description += f"Codec..........: {info['Video']['Format']}"
        if 'Format profile' in info['Video'] and info['Video']['Format profile'] != 'N/A':
            description += f" {info['Video']['Format profile']}"
        description += "\n"
    if 'Scan type' in info['Video'] and info['Video']['Scan type'] != 'N/A':
        description += f"Type...........: {info['Video']['Scan type']}\n"
    if 'HDR Format' in info['Video'] and info['Video']['HDR Format'] != 'N/A':
        description += f"HDR Format.....: {info['Video']['HDR Format']}\n"
    if 'Width' in info['Video'] and 'Height' in info['Video'] and info['Video']['Width'] != 'N/A' and info['Video'][
        'Height'] != 'N/A':
        width = re.sub(r'\D', '', info['Video']['Width'])
        height = re.sub(r'\D', '', info['Video']['Height'])
        description += f"Resolution.....: {width}x{height}\n"
    if 'Bit rate' in info['Video'] and info['Video']['Bit rate'] != 'N/A':
        bit_rate = re.sub(r'(?<=\d)\s+(?=\d)', '', info['Video']['Bit rate'])
        description += f"Bit rate.......: {bit_rate}\n"
    if 'Frame rate' in info['Video'] and info['Video']['Frame rate'] != 'N/A':
        description += f"Frame rate.....: {info['Video']['Frame rate']}\n"

    # Audio section
    for i, audio in enumerate(info['Audio']):
        if i == 0:
            description += "\n[u]Audio[/u]\n"
        else:
            description += f"\n[u]Audio #{i + 1}[/u]\n"
        if 'Format' in audio and audio['Format'] != 'N/A':
            description += f"Format.........: {audio['Format']}\n"
        if 'Commercial name' in audio and audio['Commercial name'] != 'N/A':
            description += f"Codec..........: {audio['Commercial name']}\n"
        elif 'Codec ID' in audio and audio['Codec ID'] != 'N/A':
            description += f"Codec..........: {audio['Codec ID']}\n"
        if 'Channel(s)' in audio and audio['Channel(s)'] != 'N/A':
            description += f"Channels.......: {audio['Channel(s)']}\n"
        if 'Bit rate' in audio and audio['Bit rate'] != 'N/A':
            bit_rate = re.sub(r'(?<=\d)\s+(?=\d)', '', audio['Bit rate'])
            description += f"Bit rate.......: {bit_rate}\n"
        if 'Language' in audio and audio['Language'] != 'N/A':
            description += f"Language.......: {audio['Language']}\n"
        if 'Title' in audio and audio['Title'] != 'N/A':
            description += f"Title..........: {audio['Title']}\n"

    # Subtitles section
    description += "\n[u]Subtitles[/u]\n"
    seen_languages = set()

    # Iterăm prin limbile din mediainfo și eliminăm duplicatele
    for language in info['Subtitles']:
        language = language.split('(')[0].strip().lower()  # Ignorăm detaliile între paranteze și normalizăm textul
        if language not in seen_languages:
            if language == 'romanian':
                description += "Language.......: [color=red]Romanian[/color]\n"
            else:
                description += f"Language.......: {language.capitalize()}\n"  # Capitalizăm pentru a păstra formatul original
            seen_languages.add(language)

    # Verificăm dacă există fișiere .srt în folder
    srt_files_present = any(file.endswith('.srt') for file in os.listdir(file_location))

    # Dacă există fișiere .srt, adăugăm "Romanian" cu formatul special, doar dacă nu a fost deja adăugată
    if srt_files_present and 'romanian' not in seen_languages:
        description += "Language.......: [color=red]Romanian[/color]\n"
        seen_languages.add('romanian')

    description = description.rstrip("\n") + "[/pre][/quote]\n"
    description += "[b][color=red]SCREENS:[/color][/b]\n"
    description += bbcode_images

    with open("description.txt", "w", encoding="utf-8") as file:
        file.write("[center]" + description + "[/center]")

    #print("File description.txt created")

info = extract_info("mediainfo.txt")

# Reading images.txt
with open("images.txt", "r", encoding="utf-8") as file:
    bbcode_images = file.read().strip()

# Updating description.txt
create_description_txt(info, bbcode_images)

# Input IMDb link from user
imdb_url = input("IMDb link: ")

# Extract IMDb ID from the URL
imdb_id_match = re.search(r'(tt\d+)', imdb_url)
if imdb_id_match:
    imdb_id = imdb_id_match.group(1)  # Extract the first capturing group, the ID without '/'
else:
    print("Invalid IMDb link.")
    exit()

# Fetch data from local API
local_api_url = f"https://imdb.luvbb.me/{imdb_id}"
response = requests.get(local_api_url)
if response.status_code != 200:
    print(f"Failed to fetch data from {local_api_url}. Status code: {response.status_code}")
    exit()

# Parse the JSON response
data = response.json()

# Extract genres
genres = data.get('Genres', [])

# Limit the genres to the top three
top_genres = genres[:3]

# Save the genres in genres.txt
with open("genres.txt", "w", encoding="utf-8") as genres_file:
    genres_file.write(", ".join(top_genres))

# Save the IMDb link in imdb.txt
with open("imdb.txt", "w", encoding="utf-8") as imdb_file:
    imdb_file.write(f"[url=https://www.imdb.com/title/{imdb_id}/][img=https://filelist.io/styles/images/imdb.png][/url]")

# Pasul 1: Obține un token de acces
def get_token(api_key, pin):
    url = "https://api4.thetvdb.com/v4/login"
    headers = {"Content-Type": "application/json"}
    data = {
        "apikey": api_key,
        "pin": pin
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["token"]
    else:
        raise Exception("Unable to get token: " + response.text)

# Pasul 2: Preia datele despre serial folosind IMDb ID și returnează ID-ul TVDB
def get_series_by_imdb_id(imdb_id, token):
    url = f"https://api4.thetvdb.com/v4/search/remoteid/{imdb_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        series_data = response.json()
        if series_data['status'] == 'success' and 'data' in series_data:
            return series_data['data'][0]['series']['id']
        else:
            return None  # Nu s-a găsit un serial, returnăm None
    else:
        return None  # Nu s-a putut face request-ul, returnăm None

# Pasul 3: Preia lista de artwork-uri pentru un serial folosind ID-ul TVDB
def get_series_artworks(series_id, token):
    url = f"https://api4.thetvdb.com/v4/series/{series_id}/extended"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Asigurăm că returnează un dicționar
    else:
        raise Exception("Unable to retrieve artworks: " + response.text)

banner_found = False  # Initialize the banner_found variable

try:
    # Obține tokenul de acces
    token = get_token(api_key, pin)

    # Preia ID-ul TVDB folosind IMDb ID
    tvdb_id = get_series_by_imdb_id(imdb_id, token)

    if tvdb_id:
        # Afișează ID-ul TVDB
        print(f"TVDB ID for IMDb ID {imdb_id}: {tvdb_id}")

        # Preia lista de artwork-uri pentru serial folosind ID-ul TVDB
        artworks_data = get_series_artworks(tvdb_id, token)

        # Verificăm dacă există date în răspuns
        if 'artworks' in artworks_data['data']:
            # Caută primul banner de tip 1 (Banner)
            for artwork in artworks_data['data']['artworks']:
                if artwork['type'] == 1:
                    banner_url = artwork['image']
                    tvdb_link = f"https://thetvdb.com/?tab=series&id={tvdb_id}"

                    # Formatarea textului pentru banner.txt
                    banner_text = f"[img]{banner_url}[/img]"
                    tvdb_text = f"[url={tvdb_link}][img=https://filelist.io/styles/images/tvdb.png][/url]"

                    # Salvează rezultatele în fișierele banner.txt și tvdb.txt
                    with open("banner.txt", "w") as banner_file:
                        banner_file.write(banner_text)

                    with open("tvdb.txt", "w") as tvdb_file:
                        tvdb_file.write(tvdb_text)

                    # Printează rezultatele
                    print("First Banner URL:", banner_url)
                    print("TVDB Link:", tvdb_link)

                    banner_found = True  # Set banner_found to True when a banner is found
                    break  # Oprește căutarea după ce găsești primul banner
        else:
            print("No artwork data available.")
    else:
        print(f"No TVDB ID found for IMDb ID {imdb_id}.")

except Exception as e:
    print(e)

# Read the content of description.txt
with open("description.txt", "r", encoding="utf-8") as description_file:
    description_content = description_file.read()

# Read the content of imdb.txt
with open("imdb.txt", "r", encoding="utf-8") as imdb_file:
    imdb_content = imdb_file.read().strip()

# Read the content of tvdb.txt
with open("tvdb.txt", "r", encoding="utf-8") as tvdb_file:
    tvdb_content = tvdb_file.read().strip()

# Add banner content only if the banner was found
if banner_found:
    # Read the content of banner.txt
    with open("banner.txt", "r", encoding="utf-8") as banner_file:
        banner_content = banner_file.read().strip()

    # Find the position to insert the new content (after the [center] tag)
    insert_position = description_content.find("[center]") + len("[center]")

    # Create the new content
    new_content = (description_content[:insert_position] + "" + banner_content + "\n" + "\n" +
                   imdb_content + " " + tvdb_content + "\n\n" + description_content[insert_position:])
else:
    # Find the position to insert the new content (after the [center] tag)
    insert_position = description_content.find("[center]") + len("[center]")

    # Create the new content without banner
    new_content = (description_content[:insert_position] + "" + "\n" +
                   imdb_content + " " + tvdb_content + "\n\n" + description_content[insert_position:])

# Updating description.txt
with open("description.txt", "w", encoding="utf-8") as description_file:
    description_file.write(new_content)

print("description.txt updated")


# Create .torrent file
def get_total_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def select_piece_size(total_size):
    size_gib = total_size / (1024 ** 3)  # Convertim în GiB
    if size_gib < 4:
        return "2 MiB"
    elif size_gib < 8:
        return "4 MiB"
    elif size_gib < 16:
        return "8 MiB"
    else:
        return "16 MiB"

def create_torrent(input_path):
    total_size = get_total_size(input_path)
    piece_size = select_piece_size(total_size)

    if os.path.isfile(input_path) or os.path.isdir(input_path):
        output_file = os.path.join(os.getcwd(),
                                   os.path.basename(input_path.rstrip('/\\')).replace('.mkv', '') + ".torrent")
        command = [
            'torrenttools', 'create', input_path,
            '--piece-size', piece_size,
            '--output', output_file
        ]

        subprocess.run(command)

# Go
create_torrent(input_path)

# Login
login_url = 'https://filelist.io/login.php'
takelogin_url = 'https://filelist.io/takelogin.php'
upload_url = 'https://filelist.io/takeupload.php'
edit_url = 'https://filelist.io/takeedit.php'
download_base_url = 'https://filelist.io/download.php?id='


username = filelist_username
password = filelist_password


qbittorrent_url = qbittorrent_url
qbittorrent_username = qbittorrent_username
qbittorrent_password = qbittorrent_password


session = requests.Session()

def login(session):
    login_page = session.get(login_url)
    soup = BeautifulSoup(login_page.text, 'html.parser')
    validator = soup.find('input', {'name': 'validator'})['value']

    login_data = {
        'username': username,
        'password': password,
        'validator': validator,
        'unlock': '1'
    }
    login_response = session.post(takelogin_url, data=login_data)
    return login_response


login_response = login(session)

if 'logout' in login_response.text or login_response.url != takelogin_url:
    print('Auth to FileList OK')
else:
    print('Auth to Filelist Failed')
    print(login_response.text)
    exit()

# Locate the torrent file in the current directory
torrent_file_path = None
for file in os.listdir('.'):
    if file.endswith('.torrent'):
        torrent_file_path = file
        break

if not torrent_file_path:
    print('No .torrent file found in the current directory.')
    exit()

title = os.path.basename(torrent_file_path).replace('.torrent', '')

# Prompt user to select the category
print("Category:\n1. Anime\n2. Desene\n3. Seriale 4K\n4. Seriale HD\n5. Seriale SD")
category_options = {
    '1': '24', '2': '15', '3': '27', '4': '21', '5': '23'
}
category_choice = input("Input category value: ").strip()
category_value = category_options.get(category_choice, '21')  # Default to 'Seriale HD' if invalid choice

with open("genres.txt", "r", encoding="utf-8") as file:
    genre = file.read().strip()
with open("description.txt", "r", encoding="utf-8") as file:
    description = file.read().strip()
with open("mediainfo.txt", "r", encoding="utf-8") as file:
    mediainfo = file.read().strip()

# Extract IMDb ID from the description if available
imdb_id_match = re.search(r'tt(\d+)', description)
imdb_id = imdb_id_match.group(1) if imdb_id_match else ''

# Prepare the upload payload and files
upload_payload = {
    'name': title,
    'type': category_value,
    'description': genre,
    'descr': description,
    'nfo': mediainfo,
    'imdbid': imdb_id,
    'freeleech': '1'
}

files = {
    'file': (os.path.basename(torrent_file_path), open(torrent_file_path, 'rb'))
}

# Perform the upload
upload_response = session.post(upload_url, data=upload_payload, files=files)

# Check if upload was successful
if 'success' in upload_response.text.lower():
    print('Torrent uploaded successfully')
else:
    print('Failed to upload torrent')
    print(upload_response.text)
    exit()

torrent_id_match = re.search(r'download\.php\?id=(\d+)', upload_response.text)
if torrent_id_match:
    torrent_id = torrent_id_match.group(1)
    #print(f'Torrent ID: {torrent_id}')

    torrent_url = f'{download_base_url}{torrent_id}'
    response = session.get(torrent_url)
    if response.status_code == 200:
        torrent_filename = f'{torrent_id}.torrent'
        with open(torrent_filename, 'wb') as torrent_file:
            torrent_file.write(response.content)
        #print(f'Torrent file downloaded: {torrent_filename}')

        save_path = os.path.dirname(input_path)
        #print(f'Save path set to: {save_path}')

        with open(torrent_filename, 'rb') as torrent_file:
            files = {'torrents': torrent_file}
            data = {
                'savepath': save_path,
                'autoTMM': 'false',
                'paused': 'false',
                'root_folder': 'true' if os.path.isdir(input_path) else 'false',
                'dlLimit': '0',
                'upLimit': '0',
                'sequentialDownload': 'false',
                'firstLastPiecePrio': 'false'
            }

            login_data = {'username': qbittorrent_username, 'password': qbittorrent_password}
            session.post(f'{qbittorrent_url}/api/v2/auth/login', data=login_data)

            upload_response = session.post(f'{qbittorrent_url}/api/v2/torrents/add', files=files, data=data)
            if upload_response.status_code == 200 or 'Ok' in upload_response.text:
                print(f'Torrent added to qBittorrent')
            else:
                print(f'Failed to add torrent to qBittorrent: {upload_response.text}')

        # Start of the editing process
        edit_url = f'https://filelist.io/edit.php?id={torrent_id}'

        edit_page = session.get(edit_url)
        soup = BeautifulSoup(edit_page.text, 'html.parser')

        form_data = {}
        form = soup.find('form')

        # Collect all form fields and only modify `visible`
        for input_tag in form.find_all('input'):
            input_name = input_tag.get('name')
            if input_tag['type'] == 'checkbox':
                if input_name == 'visible':
                    form_data[input_name] = '1'
                elif input_tag.has_attr('checked'):
                    form_data[input_name] = input_tag['value']
            elif input_name:
                form_data[input_name] = input_tag.get('value', '')

        for textarea_tag in form.find_all('textarea'):
            form_data[textarea_tag['name']] = textarea_tag.get_text()

        for select_tag in form.find_all('select'):
            selected_option = select_tag.find('option', selected=True)
            if selected_option:
                form_data[select_tag['name']] = selected_option['value']

        edit_button = form.find('input', {'type': 'submit', 'value': 'Edit!'})

        if edit_button:
            if 'name' in edit_button.attrs:
                form_data[edit_button['name']] = edit_button['value']
            else:
                form_data['submit'] = edit_button['value']

        # Submit the form to `takeedit.php`
        takeedit_url = f'https://filelist.io/takeedit.php'
        edit_response = session.post(takeedit_url, data=form_data)
