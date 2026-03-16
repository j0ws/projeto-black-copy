import yt_dlp
import os
import re
from datetime import datetime, timedelta
from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

TMP_DIR = os.path.join(os.getcwd(), "tmp_downloads")
os.makedirs(TMP_DIR, exist_ok=True)

def search_youtube_videos(query: str, max_results: int = 10, filter_time: str = None, channel_name: str = None):
    """
    Search YouTube videos using yt-dlp with optional filters.
    filter_time options: '24h', '30d'
    """
    search_query = query
    if channel_name:
        search_query += f" channel:{channel_name}"

    ydl_opts = {
        'skip_download': True,
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
    }

    # Add date filters if requested (yt-dlp format: YYYYMMDD)
    if filter_time:
        now = datetime.now()
        if filter_time == '24h':
            date_filter = (now - timedelta(days=1)).strftime('%Y%m%d')
        elif filter_time == '30d':
            date_filter = (now - timedelta(days=30)).strftime('%Y%m%d')
        else:
            date_filter = None

        if date_filter:
            ydl_opts['dateafter'] = date_filter
            # Date filtering in yt-dlp search requires retrieving full info usually,
            # but ytsearch passes the query to Youtube. Youtube understands `after:YYYY-MM-DD` in query string sometimes
            search_query += f" after:{(now - timedelta(days=1 if filter_time=='24h' else 30)).strftime('%Y-%m-%d')}"

    # Use ytsearch syntax
    final_query = f"ytsearch{max_results}:{search_query}"

    results = []
    try:
        print(f"[MINER_API] Searching YouTube for: '{final_query}'")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dict_info = ydl.extract_info(final_query, download=False)
            if 'entries' in dict_info:
                for entry in dict_info['entries']:
                    if not entry: continue
                    # Fallback view_count/like_count if unavailable in flat extraction
                    results.append({
                        "id": entry.get('id'),
                        "url": entry.get('url'),
                        "title": entry.get('title'),
                        "duration": entry.get('duration'),
                        "view_count": entry.get('view_count', 0),
                        "like_count": entry.get('like_count', 0),
                        "channel": entry.get('uploader')
                    })
    except Exception as e:
        print(f"[ERROR-YT-DLP] Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search YouTube: {str(e)}")
        
    return results

def get_youtube_highlights(video_url: str, query_word: str):
    """
    Fetches the transcript and finds the exact timestamps where the keyword is spoken.
    """
    video_id = None
    
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
    if match:
        video_id = match.group(1)
    else:
        raise HTTPException(status_code=400, detail="Could not identify YouTube ID from URL.")

    print(f"[MINER_HIGHLIGHTS] Fetching subtitles for {video_id} searching '{query_word}'")
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'pt-BR', 'en'])
        
        matches = []
        target_word = query_word.lower()
        
        for block in transcript:
            text = block['text'].lower()
            if target_word in text:
                start_time = float(block['start'])
                duration = float(block['duration'])
                end_time = start_time + duration
                
                matches.append({
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "text": block['text'],
                    "video_id": video_id
                })
                
        return {"total_matches": len(matches), "highlights": matches}

    except Exception as e:
        print(f"[MINER_HIGHLIGHTS] Transcript not available: {e}")
        return {"total_matches": -1, "error": "Transcript unavailable for this video.", "highlights": []}

def download_video_clip(video_url: str, start_time: float, end_time: float, output_name: str):
    """
    Downloads ONLY the selected slice using yt-dlp + ffmpeg under the hood.
    Hard limit constraint: 20 seconds maximum.
    """
    if (end_time - start_time) > 20:
        raise HTTPException(status_code=400, detail="Security Constraint: Clip cannot exceed 20 seconds.")

    output_path = os.path.join(TMP_DIR, f"{output_name}.mp4")
    
    def _format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    
    str_start = _format_time(start_time)
    str_end = _format_time(end_time)
    section_arg = f"*{str_start}-{str_end}"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'download_sections': [section_arg],
        'force_keyframes_at_cuts': True, 
        'quiet': True,
        'no_warnings': True,
    }

    try:
        print(f"[MINER_CLIPPER] Slicing {video_url} from {str_start} to {str_end}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if os.path.exists(output_path):
            return output_path
        else:
            raise Exception("File was not generated on filesystem.")
            
    except Exception as e:
        print(f"[ERROR-CLIPPER] yt-dlp engine failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error packing clip: {str(e)}")

def mock_tiktok_search(query: str):
    """
    Mock response for TikTok platform search until official Apify integration is rebuilt for v2.0
    """
    return [
        {
            "id": "mock_tk_01",
            "url": "https://www.tiktok.com/@healthguru/video/72000001",
            "title": f"The secret behind {query}",
            "duration": 45,
            "view_count": 1200000,
            "like_count": 85000,
            "channel": "healthguru"
        },
        {
            "id": "mock_tk_02",
            "url": "https://www.tiktok.com/@fitness_pro/video/72000002",
            "title": f"{query} transformed my life",
            "duration": 30,
            "view_count": 800000,
            "like_count": 45000,
            "channel": "fitness_pro"
        }
    ]
