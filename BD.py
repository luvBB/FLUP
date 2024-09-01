import os
import random
import subprocess
import signal
import requests
import re
import glob
from bs4 import BeautifulSoup
from config import *

# ===============================
# Let's Go!
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

# Input direct path to Blu-ray folder to be uploaded
input_path = input("Input folder path to Blu-ray: ")
if not os.path.isdir(input_path):
    print("Invalid path.")
    exit()

# Run BDInfoCLI to find the main playlist and generate report
report_output_dir = os.getcwd()
full_report_path = os.path.join(report_output_dir, "fullreport.txt")
summary_report_path = os.path.join(report_output_dir, "summary.txt")

# List playlist
command_list = [bdinfo_path, "-l", input_path]
result = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

playlists = []
for line in result.stdout.splitlines():
    if ".MPLS" in line:
        playlist_file = line.split()[2]
        playlists.append(playlist_file)

if not playlists:
    print("No playlists found.")
    exit()

first_playlist = playlists[0]
#print(f"First playlist found: {first_playlist}")

# Run BDInfo on first playlist
command_scan = [bdinfo_path, "-m", first_playlist, input_path, report_output_dir]
subprocess.run(command_scan, check=True)

# Looking for the generated raport as text file
generated_report_file = None
for file in os.listdir(report_output_dir):
    if file.endswith(".txt"):
        generated_report_file = file
        break

if not generated_report_file:
    print("Not any report found.")
    exit()

generated_report_path = os.path.join(report_output_dir, generated_report_file)

# Rename report to fullreport.txt
os.rename(generated_report_path, full_report_path)

# Read fullreport.txt and extract "QUICK SUMMARY:"
with open(full_report_path, 'r', encoding='utf-8') as full_report:
    lines = full_report.readlines()

quick_summary_found = False
summary_lines = []

for line in lines:
    if "QUICK SUMMARY:" in line:
        quick_summary_found = True
    if quick_summary_found:
        summary_lines.append(line)

# Saving "QUICK SUMMARY:" in summary.txt
if summary_lines:
    with open(summary_report_path, 'w', encoding='utf-8') as summary_report:
        summary_report.writelines(summary_lines)
    print(f"Summary report saved in {summary_report_path}")
else:
    print("Section 'QUICK SUMMARY:' not found in fullsummary.txt.")
    exit()

# Find the largest .m2ts file from BDMV\STREAM
stream_dir = os.path.join(input_path, "BDMV", "STREAM")
largest_m2ts_file = None
largest_size = 0

for file in os.listdir(stream_dir):
    if file.endswith(".m2ts"):
        file_path = os.path.join(stream_dir, file)
        file_size = os.path.getsize(file_path)
        if file_size > largest_size:
            largest_size = file_size
            largest_m2ts_file = file_path

if not largest_m2ts_file:
    print(r"Not any .m2ts file in BDMV\STREAM.")
    exit()

# Use mediainfo to get the lenght of .m2ts file
mediainfo_command = [mediainfo_path, '--Inform=Video;%Duration%', largest_m2ts_file]
mediainfo_output = subprocess.run(mediainfo_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

try:
    duration_in_ms = int(mediainfo_output.stdout.strip())
    duration_in_seconds = duration_in_ms // 1000
except ValueError:
    print("Can't get lenght of .m2ts file.")
    print(mediainfo_output.stdout)
    exit()

print(f"File {largest_m2ts_file} have a lenght of {duration_in_seconds} seconds.")

skip_time = 10 * 60

valid_duration_in_seconds = duration_in_seconds - 2 * skip_time

if valid_duration_in_seconds <= 0:
    raise ValueError("Video-ul este prea scurt pentru a sări primele și ultimele 10 minute.")

screenshot_times = sorted(random.sample(range(0, valid_duration_in_seconds), 3))
screenshot_times = [time + skip_time for time in screenshot_times]

valid_duration_in_seconds = duration_in_seconds - 2 * skip_time

if valid_duration_in_seconds <= 0:
    raise ValueError("Video-ul este prea scurt pentru a sări primele și ultimele 10 minute.")

screenshot_times = sorted(random.sample(range(0, valid_duration_in_seconds), 3))
screenshot_times = [time + skip_time for time in screenshot_times]

screenshot_filenames = []

for idx, time in enumerate(screenshot_times):
    screenshot_filename = os.path.join(report_output_dir, f"screenshot_{idx+1}.png")
    vlc_command = [
        vlc_path,
        '-I', 'dummy',
        '--avcodec-hw=none',
        largest_m2ts_file,
        "--video-filter=scene",
        "--vout=dummy",
        "--no-audio",
        "--no-sub-autodetect-file",
        "--scene-ratio=99999",
        f"--scene-prefix=screenshot_{idx+1}_",
        f"--scene-path={report_output_dir}",
        f"--start-time={time}",
        f"--stop-time={time + 2}",
        "vlc://quit"
    ]
    result = subprocess.run(vlc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Failed to save screenshot: {screenshot_filename}")
        print(f"VLC Output:\n{result.stdout}")
        print(f"VLC Error Output:\n{result.stderr}")
    else:

        expected_screenshot_path = os.path.join(report_output_dir, f"screenshot_{idx+1}_00001.png")
        if os.path.exists(expected_screenshot_path):
            os.rename(expected_screenshot_path, screenshot_filename)
            screenshot_filenames.append(screenshot_filename)
        else:
            print(f"Expected screenshot {expected_screenshot_path} not found.")

print("Screenshots saved.")

# Upload screenshots to img4k.net
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
                image_url = response_data['image']['url_short']
                medium_url = response_data['image']['medium']['url']
                uploaded_image_urls.append((image_url, medium_url))
            else:
                print(f"Error while uploading saved screenshots: {response_data['error']['message']}")
        else:
            print(f"API error: {response.status_code}")

print("Screenshots uploaded to img4k.net")

with open("images.txt", "w") as file:
    bbcode = ' '.join([f"[url={image_url}][img={medium_url}][/url]" for image_url, medium_url in uploaded_image_urls])
    file.write(bbcode)

print("BBCode links saved in images.txt")

# Create description.txt using summary.txt instead of mediainfo.txt
def create_description_txt(summary_file, bbcode_images):
    with open(summary_file, "r", encoding="utf-8") as file:
        summary_content = file.read().strip()

    # Initialize the description with [quote][pre] and directly append formatted content
    description = "[quote][pre]"

    # Skip "QUICK SUMMARY:" line and do formatting
    formatted_summary = []
    lines = summary_content.splitlines()
    for line in lines:
        if "QUICK SUMMARY:" in line:
            continue
        elif line.startswith("Disc Title"):
            formatted_summary.append(f"[b][color=#2980b9]Disc Title[/color][/b]    : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Disc Label"):
            formatted_summary.append(f"[b][color=#2980b9]Disc Label[/color][/b]    : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Disc Size"):
            formatted_summary.append(f"[b][color=#2980b9]Disc Size[/color][/b]     : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Protection"):
            formatted_summary.append(f"[b][color=#2980b9]Protection[/color][/b]    : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Playlist"):
            formatted_summary.append(f"[b][color=#2980b9]Playlist[/color][/b]      : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Size"):
            formatted_summary.append(f"[b][color=#2980b9]Size[/color][/b]          : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Length"):
            formatted_summary.append(f"[b][color=#2980b9]Length[/color][/b]        : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Total Bitrate"):
            formatted_summary.append(f"[b][color=#2980b9]Total Bitrate[/color][/b] : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Video"):
            formatted_summary.append(f"[b][color=#2980b9]Video[/color][/b]         : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Audio"):
            formatted_summary.append(f"[b][color=#2980b9]Audio[/color][/b]         : {line.split(':', 1)[1].strip()}")
        elif line.startswith("Subtitle"):
            formatted_summary.append(f"[b][color=#2980b9]Subtitle[/color][/b]      : {line.split(':', 1)[1].strip()}")
        elif line.startswith("* Subtitle"):
            formatted_summary.append(f"[b][color=#2980b9]* Subtitle[/color][/b]    : {line.split(':', 1)[1].strip()}")
        elif line.startswith("* Audio"):
            formatted_summary.append(f"[b][color=#2980b9]* Audio[/color][/b]       : {line.split(':', 1)[1].strip()}")
        else:
            formatted_summary.append(line.strip())

    # Ensure no leading/trailing whitespace
    formatted_summary_text = "\n".join(formatted_summary).lstrip()

    # Add the formatted content to the description
    description += formatted_summary_text + "[/pre][/quote]\n"

    # Append the screenshots section
    description += "[b][color=red]SCREENS:[/color][/b]\n"
    description += bbcode_images

    # Write the final description to a file
    with open("description.txt", "w", encoding="utf-8") as file:
        file.write("[center]" + description + "[/center]")

# Read the BBCode images
with open("images.txt", "r") as file:
    bbcode_images = file.read().strip()

# Create the description
create_description_txt(summary_report_path, bbcode_images)

with open("images.txt", "r") as file:
    bbcode_images = file.read().strip()

create_description_txt(summary_report_path, bbcode_images)

# Input IMDb link from user
imdb_url = input("IMDb link: ")

# Extract IMDb ID from the URL
imdb_id_match = re.search(r'(tt\d+)', imdb_url)
if imdb_id_match:
    imdb_id = imdb_id_match.group(1)  # Extrage primul grup de capturare, adică ID-ul fără /
else:
    print("Invalid IMDb link.")
    exit()

local_api_url = f"https://imdb.luvbb.me/{imdb_id}"

# Realizează cererea GET la URL-ul local
response = requests.get(local_api_url)
if response.status_code != 200:
    print(f"Failed to fetch data from {local_api_url}. Status code: {response.status_code}")
    exit()

# Parsează răspunsul JSON
data = response.json()

# Debugging: Afișează JSON-ul returnat pentru a verifica structura
#print("JSON data received:", data)

# Extrage genurile din JSON
genres = []
if data and 'Genres' in data:  # Verifică existența cheii 'Genres' cu majusculă
    genres = data['Genres']    # Extrage valoarea asociată

# Debugging: Afișează genurile extrase
#print("Genres extracted:", genres)

# Limitează genurile la primele 3
top_genres = genres[:3]

# Salvarea genurilor în genres.txt
with open("genres.txt", "w", encoding="utf-8") as genres_file:
    genres_file.write(", ".join(top_genres))

# Salvarea link-ului IMDb în imdb.txt
with open("imdb.txt", "w", encoding="utf-8") as imdb_file:
    imdb_file.write(f"[url=https://www.imdb.com/title/{imdb_id}/][img=https://filelist.io/styles/images/imdb.png][/url]")

#print("IMDb link and genres saved.")

# Read the content of description.txt
with open("description.txt", "r", encoding="utf-8") as description_file:
    description_content = description_file.read()

# Read imdb.txt
with open("imdb.txt", "r", encoding="utf-8") as imdb_file:
    imdb_content = imdb_file.read().strip()

# Working IMDb
imdb_url_match = re.search(r'\[url=(https://www\.imdb\.com/title/tt\d+/)\]\[img=.*?\[/url\]', imdb_content)

if imdb_url_match:
    imdb_url = imdb_url_match.group(1)
    imdb_content = f'[url={imdb_url}[][/url]'

insert_position = description_content.find("[center]") + len("[center]")

new_content = (description_content[:insert_position] + "" +
               imdb_content + "\n" + description_content[insert_position:])

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

        print(f"Succesfully .torrent file created -> {output_file}")

        # Rename .torrent file?
        rename_torrent_file(output_file)
    else:
        print("Invalid path")

def rename_torrent_file(torrent_file):
    user_input = input("Rename .torrent? (Y/N): ").strip().lower()

    if user_input == 'y':
        new_name = input("Input new .torrent name (without extension): ").strip()
        new_output_file = os.path.join(os.getcwd(), new_name + ".torrent")
        os.rename(torrent_file, new_output_file)
        print(f"Renamed to -> {new_output_file}")
    else:
        print("Going further!")

# Go
create_torrent(input_path)

#Login
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
    print('Auth to FileList Failed')
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
print("Category:\n1. Filme Blu-ray\n2. Filme 4k Blu-ray")
category_options = {
    '1': '20', '2': '26'
}
category_choice = input("Input category value: ").strip()
category_value = category_options.get(category_choice, '21')  # Default to 'Seriale HD' if invalid choice

with open("genres.txt", "r", encoding="utf-8") as file:
    genre = file.read().strip()
with open("description.txt", "r", encoding="utf-8") as file:
    description = file.read().strip()
with open("summary.txt", "r", encoding="utf-8") as file:
    summary = file.read().strip()

# Extract IMDb ID from the description if available
imdb_id_match = re.search(r'tt(\d+)', description)
imdb_id = imdb_id_match.group(1) if imdb_id_match else ''

# Prepare the upload payload and files
upload_payload = {
    'name': title,
    'type': category_value,
    'description': genre,
    'descr': description,
    'nfo': summary,
    'imdbid': imdb_id,
    'freeleech': '1' if input("FreeLeech? (Y/N): ").strip().lower() == 'y' else '0'
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
    print(f'Torrent ID: {torrent_id}')

    torrent_url = f'{download_base_url}{torrent_id}'
    response = session.get(torrent_url)
    if response.status_code == 200:
        torrent_filename = f'{torrent_id}.torrent'
        with open(torrent_filename, 'wb') as torrent_file:
            torrent_file.write(response.content)
        print(f'Torrent file downloaded: {torrent_filename}')

        save_path = os.path.dirname(input_path)
        print(f'Save path set to: {save_path}')

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


        edit_url = f'https://filelist.io/edit.php?id={torrent_id}'

        edit_page = session.get(edit_url)
        soup = BeautifulSoup(edit_page.text, 'html.parser')

        form_data = {}
        form = soup.find('form')  # Assuming there's only one form on the page

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
