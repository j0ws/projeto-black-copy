import yt_dlp
import os
import re
import urllib.parse
from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

# Diretório base para depejos de downloads em /tmp (para não poluir o repo)
TMP_DIR = os.path.join(os.getcwd(), "tmp_downloads")
os.makedirs(TMP_DIR, exist_ok=True)

def search_youtube_videos(query: str, max_results: int = 10):
    """
    Usa o yt-dlp apenas para extração de metadados da pesquisa.
    """
    search_query = f"ytsearch{max_results}:{query}"
    ydl_opts = {
        'skip_download': True,
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
    }

    results = []
    try:
        print(f"[MINER_API] Pesquisando Youtube por: '{query}'")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dict_info = ydl.extract_info(search_query, download=False)
            if 'entries' in dict_info:
                for entry in dict_info['entries']:
                    if not entry: continue
                    # Filtrar apenas vídeos comuns (pode incluir Shorts dependendo do yt-dlp)
                    results.append({
                        "id": entry.get('id'),
                        "url": entry.get('url'),
                        "title": entry.get('title'),
                        "duration": entry.get('duration'),
                        "view_count": entry.get('view_count'),
                        "channel": entry.get('uploader')
                    })
    except Exception as e:
        print(f"[ERRO-YT-DLP] Falha na busca: {e}")
        raise HTTPException(status_code=500, detail=f"Falha na busca pelo YouTube: {str(e)}")
        
    return results

def get_youtube_highlights(video_url: str, query_word: str):
    """
    Puxa a transcrição do vídeo (se existir) e encontra a palavra-chave.
    Retorna uma lista de blocos de timestamp num raio de +- X segundos.
    """
    # Extrair video ID da URL
    video_id = None
    
    # regex basico pra "v=XXXX" ou "youtu.be/XXXX" ou "shorts/XXX"
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
    if match:
        video_id = match.group(1)
    else:
        raise HTTPException(status_code=400, detail="Não consegui identificar o ID do YouTube na URL enviada.")

    print(f"[MINER_HIGHLIGHTS] Puxando legendas para {video_id} buscando '{query_word}'")
    
    try:
        # A biblioteca exporta uma classe e dentro dela usamos o staticmethod \`get_transcript\`
        # Correção do erro "type object has no attribute 'get_transcript'"
        from youtube_transcript_api import YouTubeTranscriptApi
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
        print(f"[MINER_HIGHLIGHTS] Video sem legendas ou protegidas: {e}")
        return {"total_matches": -1, "error": "Transcrição indisponível ou vídeo sem legendas geradas.", "highlights": []}

def download_video_clip(video_url: str, start_time: int, end_time: int, output_name: str):
    """
    Usa a feature genial do yt-dlp de baixar _somente_ o trecho selecionado usando FFMPEG por trás.
    A API já prevê o uso do *start-end para passar o range de bytes sem fazer o full download.
    """
    # Limitação de Segurança de recortes (Máx 30 segs)
    if (end_time - start_time) > 30:
        raise HTTPException(status_code=400, detail="Limitação de Segurança: O recorte não pode exceder 30 segundos.")

    output_path = os.path.join(TMP_DIR, f"{output_name}.mp4")
    
    # O Pulo do Gato: download_sections pega EXATAMENTE O RECORTE.
    # Exemplo string de sections: "*00:00:15-00:00:25"
    
    # Formatação basica HH:MM:SS
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
        # Force Keyframes assegura precisão cortando via ffmpeg
        'force_keyframes_at_cuts': True, 
        'quiet': True,
        'no_warnings': True,
    }

    try:
        print(f"[MINER_CLIPPER] Recortando {video_url} de {str_start} a {str_end}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if os.path.exists(output_path):
            return output_path
        else:
            raise Exception("Falha: Arquivo não foi gerado no sistema de arquivos.")
            
    except Exception as e:
        print(f"[ERRO-CLIPPER] Falhou yt-dlp engine: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao empacotar clipe: {str(e)}")
