import pandas as pd
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB
import os
from tqdm import tqdm
import time

# Read Excel file without headers
df = pd.read_excel('songs.xlsx', header=None, names=['Track', 'Artist'])  # Assign our own column names

# Function to download song from YouTube
def download_from_youtube(search_query, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'noplaylist': True,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search for the video
            search_url = f"ytsearch1:{search_query}"
            tqdm.write(f"Searching for: {search_url}")
            
            # Download directly
            ydl.download([search_url])
            
            # Check if file exists
            if os.path.exists(f"{output_path}.mp3"):
                tqdm.write(f"Successfully downloaded: {output_path}.mp3")
                return True
            else:
                tqdm.write(f"File not found after download: {output_path}.mp3")
                return False
                
    except Exception as e:
        tqdm.write(f"Error downloading {search_query}: {str(e)}")
        return False

# Function to embed metadata into MP3
def embed_metadata(file_path, title, artist, album):
    try:
        audio = MP3(file_path, ID3=ID3)
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        audio.tags.add(TALB(encoding=3, text=album))
        audio.save()
        print(f"Metadata embedded for {file_path}")
    except Exception as e:
        print(f"Error embedding metadata for {file_path}: {e}")

# Create a directory to save downloaded songs
download_dir = 'downloaded_songs'
os.makedirs(download_dir, exist_ok=True)

def sanitize_filename(filename):
    # Remove or replace characters that might cause issues
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename.strip()

# Main processing loop
total_songs = len(df)
for index, row in tqdm(df.iterrows(), total=total_songs, desc="Downloading songs", unit="song"):
    try:
        track_name = sanitize_filename(row['Track'])
        artist_name = sanitize_filename(row['Artist']) if pd.notna(row['Artist']) else ''
        
        # Create file name and search query
        if artist_name:
            search_query = f"{track_name} {artist_name}"
            output_file = os.path.join(download_dir, f"{artist_name} - {track_name}")
        else:
            search_query = track_name
            output_file = os.path.join(download_dir, f"{track_name}")
        
        # Check if file already exists
        if os.path.exists(f"{output_file}.mp3"):
            tqdm.write(f'Skipping (already exists): {output_file}.mp3')
            continue
        
        tqdm.write(f'Processing: {search_query}')
        
        # Download the song
        if download_from_youtube(search_query, output_file):
            time.sleep(1)  # Wait a bit longer before metadata
            if os.path.exists(f"{output_file}.mp3"):
                embed_metadata(f"{output_file}.mp3", track_name, artist_name or 'Unknown Artist', 'Unknown Album')
            else:
                tqdm.write(f"File not found for metadata embedding: {output_file}.mp3")
        else:
            tqdm.write(f"Failed to download: {search_query}")
            
        time.sleep(0.5)  # Add small delay between downloads
        
    except Exception as e:
        tqdm.write(f"Error processing {search_query}: {str(e)}")
        continue
