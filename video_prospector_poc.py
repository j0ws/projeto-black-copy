import os
import json
import subprocess
import re
import glob
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import yt_dlp
from openai import OpenAI

# ==========================================
# MODELOS DE DADOS
# ==========================================
class VideoSegment(BaseModel):
    id: str = Field(description="ID sequencial do segmento original")
    start: float = Field(description="Tempo de início em segundos")
    end: float = Field(description="Tempo de fim em segundos")
    text: str = Field(description="Texto original transcrito")
    text_rewritten: Optional[str] = Field(description="Texto re-escrito para remover jargões ou atenuar o tom comercial", default=None)
    role: str = Field(description="Classificação da estrutura do roteiro: 'hook', 'body', 'cta', 'social_proof', 'demo', 'filler'")
    tone_label: str = Field(description="Rótulo da intenção. Ex: 'curiosity_gap', 'problem_statement', 'routine_benefit', 'testimonial_soft'")
    energy_score: float = Field(description="Nota de 0.0 a 1.0 indicando a força/energia da entonação e do texto")
    retention_potential: float = Field(description="Nota de 0.0 a 1.0 de potencial de manter a atenção do usuário no TikTok/Reels")
    risk_score: float = Field(description="Risco de compliance com ads networks (0.0=Seguríssimo, 1.0=Black Hat/Alto Risco)")
    compliance_flags: List[str] = Field(description="Motivos se o risco for alto: ['medical_claim', 'body_shaming', 'unrealistic_promise', 'none']", default=[])
    reasoning: str = Field(description="Descrição concisa explicando o raciocínio das variáveis atribuídas")

class SegmentList(BaseModel):
    segments: List[VideoSegment]

class ProductNiche(BaseModel):
    product_name: str = Field(description="Nome do produto analisado")
    product_category: str = Field(description="Categoria original providenciada pelos dados do Kalodata")
    identified_niches: List[str] = Field(description="Nichos relacionados em alta granularidade (ex: saude, fitness, suplementos, multivitaminicos, farmaceuticos, performance)")
    market_appeal: str = Field(description="Resumo do apelo comercial (o porquê o produto vende e qual a dor ele resolve)")

class ProductAnalysisList(BaseModel):
    analyzed_products: List[ProductNiche]

# Inicializar cliente da OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "SUA_CHAVE_AQUI"))

# ==========================================
# MÓDULO 0.A: KALODATA API (DESCOBERTA DE PRODUTOS DE PICO)
# ==========================================
def kalodata_get_peak_products(limit: int = 3) -> List[Dict[str, Any]]:
    print("\n[KALODATA: TRENDS] Mapeando Top Produtos em Pico de Faturamento (Global/US)...")
    mock_products = [
        {"id": "p_001", "name": "Maca Peruana Black Edition Premium", "category": "Dietary Supplements", "gmv": 350000},
        {"id": "p_002", "name": "Sérum Capilar Tônico de Crescimento Rápido", "category": "Personal Care", "gmv": 210000},
        {"id": "p_003", "name": "Creatina Monohidratada 100% Pura", "category": "Sports Nutrition", "gmv": 150000}
    ]
    for p in mock_products[:limit]:
        print(f"    -> [PRODUTO VIRAL] {p['name']} | Faturamento Diário: ${p['gmv']}")
    return mock_products[:limit]

def analyze_products_with_llm(products: List[Dict[str, Any]]) -> ProductAnalysisList:
    print("\n[*] INTELIGÊNCIA COMERCIAL LLM: Estratificando os produtos em nichos de mercado...")
    system_prompt = """
Você é um Estrategista Especializado em TikTok Shop e Marketing de Alta Performance.
Você receberá dados brutos de produtos com alto faturamento.
Sua missão é classificar cada produto em nichos de mercado (seja muito preciso: 'saude', 'fitness', 'suplementos', 'multivitaminicos', 'farmaceuticos', 'performance', etc).
Escreva também o 'market_appeal' de forma curta (qual dor ou ambição ele ataca de forma visceral).
Devolva RIGOROSAMENTE as respostas no formato da estrutura de dados solicitada.
    """
    user_prompt = f"Avalie esses produtos em pico para guiar nossa prospecção de criativos:\n{json.dumps(products, ensure_ascii=False, indent=2)}"
    
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        response_format=ProductAnalysisList,
        temperature=0.2
    )
    return response.choices[0].message.parsed

# ==========================================
# MÓDULO 0.B: KALODATA API (SIMULAÇÃO DE VÍDEOS VIRAIS POR PRODUTO/NICHO)
# ==========================================
def kalodata_get_top_videos(niche: str, product_name: str = "", min_gmv: int = 10000) -> List[Dict[str, Any]]:
    """
    Busca os criativos (vídeos) que de fato VENDERAM o produto no nicho.
    """
    print(f"\n[KALODATA: CRIATIVOS] Buscando os vídeos milionários do nicho '{niche}' (Produto: {product_name})...")
    
    # Mock de resposta da API do Kalodata
    mock_data = [
        {
            "id": "tk_vid_001",
            "platform": "tiktok",
            "url": "https://www.tiktok.com/@growth_saude/video/72000000001",
            "title": "Descobri o que destrói sua disposição aos 30 anos",
            "metrics": {
                "gmv_generated": 85000, 
                "views": 2500000,
                "sales_count": 1200
            },
            "creator": "growth_saude"
        }
    ]
    
    for v in mock_data:
        print(f"    -> [Viral Encontrado] '{v['title']}' | Vendeu: ${v['metrics']['gmv_generated']} | Views: {v['metrics']['views']}")
        
    return mock_data

# ==========================================
# MÓDULO 1.A: PROSPECTOR AVANÇADO (FILMOT + RAG LOCAL)
# ==========================================
def time_to_seconds(t_str: str) -> float:
    """Converte tempo no formato VTT 00:00:00.000 para segundos em float."""
    parts = t_str.replace(',', '.').split(':')
    sec = 0.0
    for p in parts:
        sec = sec * 60 + float(p)
    return sec

def find_keyword_in_subs(query_youtube: str, keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    1. Busca vídeos baseado na query
    2. Faz ingestão ultrarrápida apenas das legendas (.VTT)
    3. Faz uma varredura Lexical (Word Match) local (Fase B e C do seu Doc)
    """
    print(f"\n[*] PROSPECTOR AVANÇADO: Buscando canais/nicho: '{query_youtube}'")
    print(f"[*] ALVO LEXICAL: Procurando pela palavra chave: '{keyword}' nas legendas...\n")
    
    os.makedirs("temp_subs", exist_ok=True)
    # Limpa temp
    for f in glob.glob("temp_subs/*"):
        os.remove(f)
        
    search_query = f"ytsearch{max_results}:{query_youtube}"
    
    ydl_opts = {
        'skip_download': True,      # Ignora o MP4!
        'writeautomaticsub': True,  # VTT Autogerado
        'writesubtitles': True,     # VTT Manual
        'subtitleslangs': ['pt'],   
        'outtmpl': 'temp_subs/%(id)s.%(ext)s',
        'dumpjson': True,           # Para pegar os metadados dos canais
        'quiet': True,
        'no_warnings': True
    }

    candidates = []
    print(" -> Fase A e B: Descoberta e Ingestão de Legendas via yt-dlp...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            dict_info = ydl.extract_info(search_query, download=True) # download=True faz o pull dos .VTT
            if 'entries' in dict_info:
                for entry in dict_info['entries']:
                    if entry:
                        candidates.append({"id": entry.get('id'), "title": entry.get('title'), "url": entry.get('webpage_url')})
        except Exception as e:
            pass

    print(" -> Fase C: Hibridação e Full-Text Search Local (Estilo Filmot)...")
    matches = []
    
    for cand in candidates:
        vid_id = cand["id"]
        vtt_files = glob.glob(f"temp_subs/{vid_id}*.vtt")
        if not vtt_files:
            continue
            
        with open(vtt_files[0], 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        curr_start = 0.0
        curr_end = 0.0
        
        for line in lines:
            time_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if time_match:
                curr_start = time_to_seconds(time_match.group(1))
                curr_end = time_to_seconds(time_match.group(2))
            elif keyword.lower() in line.lower() and '<c>' not in line: # '<c>' ignora formatações sub-frames do YT
                clean_text = re.sub(r'<[^>]+>', '', line).strip()
                if clean_text:
                    # Fase D1: Expansão da Janela de Contexto (Buffer -10s / +15s)
                    start_window = max(0.0, curr_start - 10.0)
                    end_window = curr_end + 15.0
                    
                    matches.append({
                        "video_info": cand,
                        "matched_text": clean_text,
                        "exact_start": curr_start,
                        "exact_end": curr_end,
                        "window_start": start_window,
                        "window_end": end_window
                    })
                    print(f"    [+] MATCH ENCONTRADO!")
                    print(f"        Vídeo: {cand['title']}")
                    print(f"        Frase: '{clean_text}' (visto em {curr_start:.1f}s)")
                    print(f"        Janela ideal de Corte: {start_window:.1f}s até {end_window:.1f}s\n")
                    
    return matches

# ==========================================
# MÓDULO 1.B: INGESTÃO E EXTRAÇÃO DE ÁUDIO
# ==========================================
def download_video(url: str, output_path: str = "raw_video.mp4") -> str:
    print(f"\n[*] DOWNLOADER: Baixando vídeo bruto da URL: {url}")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

def download_partial_video(url: str, start_sec: float, end_sec: float, output_path: str = "raw_partial.mp4") -> str:
    """Fase D2: Download Cirúrgico (Apenas o range estrito encontrado)"""
    print(f"\n[*] EXTRAÇÃO CIRÚRGICA: Baixando apenas o trecho ({start_sec:.1f}s - {end_sec:.1f}s) do vídeo...")
    command = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-to", str(end_sec),
        "-i", url,     # O ffmpeg tem suporte nativo para ler streams https ou extraídos via yt-dlp
        "-c:v", "libx264", "-c:a", "aac",
        "-loglevel", "error", output_path
    ]
    
    # Para garantir sucesso, usamos o yt-dlp pra pegar o link do stream real m3u8
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'format': 'best'}) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info['url']
        
        command[4] = stream_url
        subprocess.run(command, check=True)
    except Exception as e:
        print(f"Falha de streaming parcial, baixando completo e cortando: {e}")
        dl_cmd = ["yt-dlp", "-f", "best", "-o", "temp_vid.mp4", url, "--quiet"]
        subprocess.run(dl_cmd)
        cmd2 = ["ffmpeg", "-y", "-i", "temp_vid.mp4", "-ss", str(start_sec), "-to", str(end_sec), output_path, "-loglevel", "error"]
        subprocess.run(cmd2)
        
    return output_path

def extract_audio(video_path: str, audio_path: str = "extracted_audio.mp3") -> str:
    print("[*] EXTRAÇÃO: Separando áudio do clipe de contexto...")
    command = ["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-loglevel", "error"]
    subprocess.run(command, check=True)
    return audio_path

# ==========================================
# MÓDULO 2: TRANSCRIÇÃO (WHISPER API COM TIMESTAMPS)
# ==========================================
def transcribe_audio(audio_path: str) -> List[Dict[str, Any]]:
    print("\n[*] TRANSCRIÇÃO HD: Repassando áudio filtrado para Whisper (Timestamps cravados)...")
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    
    raw_segments = []
    for i, seg in enumerate(transcript.segments):
        raw_segments.append({
            "id": f"seg_{i}", "start": seg['start'], "end": seg['end'], "text": seg['text'].strip()
        })
    return raw_segments

# ==========================================
# MÓDULO 3: TONE EDITOR (LABELING COM LLM)
# ==========================================
def analyze_and_label_segments(raw_segments: List[Dict[str, Any]]) -> SegmentList:
    print("\n[*] TONE EDITOR (Fase D3): Auditando Copy e Compliance no trecho extraído...")
    
    system_prompt = """
Você é o 'Tone Editor' IA, projetado para analisar e lapidar blocos de roteiro (segmentos transcritos de vídeo)
focados no nicho de **BEM-ESTAR/SAÚDE MASCULINA** para plataformas como Meta Ads e TikTok.

**REGRAS DE ANÁLISE E COPY (OBRIGATÓRIO):**
1. **ROLE & TONE**: Classifique as partes (ex: `hook`, `body`, `cta`) e o tom (`curiosity_gap`, `problem_statement`, `routine_benefit`, `cta_direct`).
2. **PRIORIZE**: Dores leves cotidianas, benefícios percebidos/plausíveis, linguagem de rotina e provas sociais moderadas.
3. **COMPLIANCE (TOLERÂNCIA ZERO):**
   - É PROIBIDO: Apelar para masculinidade frágil, humilhação corporal, promessas hormonais e resultados mágicos.
   - PALAVRAS-CHAVE ALTO RISCO: "cura", "trata", "reverte", "aumenta testosterona", "corpo perfeito", "rápido e fácil".
   - Se o trecho tiver qualquer um desses, suba o `risk_score` para > 0.8 e preencha `compliance_flags` detalhando o tipo de infração (ex: 'medical_claim').
4. **REESCRITA (TEXT_REWRITTEN):**
   - Se um trecho estiver com tom apelativo ("aumenta sua testosterona em 7 dias"), reescreva para ficar "white hat" e de bom tom ("apoio à sua rotina de autocuidado", "pensado para o bem-estar masculino com consistência").
   - Se for um 'hook' fraco, pode sugerir uma versão mais incisiva para retenção em 3 segundos.

Avalie os trechos, preencha as notas e devolva apenas as saídas estritamente estruturadas do JSON.
"""

    user_prompt = f"Aqui estão os segmentos brutos extraídos do vídeo base:\n{json.dumps(raw_segments, ensure_ascii=False, indent=2)}"

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        response_format=SegmentList,
        temperature=0.3
    )
    return response.choices[0].message.parsed

# ==========================================
# MÓDULO 4: GERADOR DE CORTES (EDIÇÃO ARTIFICIAL)
# ==========================================
def extract_best_clips(video_path: str, labeled_data: SegmentList, output_dir: str = "cortes"):
    print("\n[*] MOTOR DE EDIÇÃO: Recortando os melhores trechos via FFmpeg...")
    os.makedirs(output_dir, exist_ok=True)
    
    hooks = [seg for seg in labeled_data.segments if seg.role == 'hook' and seg.risk_score < 0.5 and seg.energy_score > 0.6]
    
    if not hooks:
        print("[!] Nenhum trecho com perfil de 'Hook Seguro' foi encontrado.")
        return
    
    for count, hook in enumerate(hooks):
        out_file = os.path.join(output_dir, f"hook_seguro_{count+1}.mp4")
        start_cut = max(0, hook.start - 0.2)
        end_cut = hook.end + 0.2
        
        print(f" -> Cortando: '{hook.text}' (Risco: {hook.risk_score})")
        
        cmd = [
            "ffmpeg", "-y", "-i", video_path, 
            "-ss", str(start_cut), "-to", str(end_cut),
            "-c:v", "libx264", "-c:a", "aac", "-preset", "ultrafast",
            "-loglevel", "error", out_file
        ]
        subprocess.run(cmd)

# ==========================================
# ORQUESTRADOR PRINCIPAL (POC)
# ==========================================
def main():
    print("=== BEM-VINDO AO PROSPECTOR v5 (KALODATA TRENDS ESPORTIVO + GPT) ===")
    
    # 0.A Buscar os produtos que são "Febre" Hoje
    produtos_de_pico = kalodata_get_peak_products(limit=2)
    
    # 0.B Fichamento dos Produtos usando LLM para entender o nicho (fitness, suplementos, etc)
    analise_estrategica = analyze_products_with_llm(produtos_de_pico)
    
    print("\n[+] Dossiê de Produtos (Kalodata + GPT):")
    for prod in analise_estrategica.analyzed_products:
        print(f"    📦 Produto: {prod.product_name}")
        print(f"       🧠 Nichos Detectados: {', '.join(prod.identified_niches)}")
        print(f"       🎯 Apelo de Venda (Dor/Desejo): {prod.market_appeal}")
        print("")
        
    # Vamos focar no nosso Campeão de Vendas da Pesquisa e usar o seu nicho primário
    produto_campeao = analise_estrategica.analyzed_products[0]
    nicho_alvo = produto_campeao.identified_niches[0]
    
    # 1. Integração Kalodata (Validação de Mercado via Analytics)
    # Procuramos o vídeo viral EXATO que fez esse produto decolar
    videos_virais = kalodata_get_top_videos(niche=nicho_alvo, product_name=produto_campeao.product_name, min_gmv=10000)
    
    if not videos_virais:
        print("[!] Nenhum vídeo viral com alta receita encontrado.")
        return
        
    video_top_1 = videos_virais[0]
    vid_url = video_top_1["url"]
    
    # 2. Fazemos o download silencioso e rápido do Vídeo da "Máquina de Vendas"
    video_file = download_video(vid_url, "viral_original.mp4")
    
    # 3. Transcrever com Whisper e Iniciar o Hacking de Roteiro
    audio_file = extract_audio(video_file, "viral_audio.mp3")
    raw_segments = transcribe_audio(audio_file)
    
    # 4. Manda pro Tone Editor "Guardão"
    # O LLM agora auditará o conteúdo que gerou $45k USD e o tornará seguro (Medical Claims).
    labeled_segments = analyze_and_label_segments(raw_segments)
    
    print(f"\n[+] Raio-X do Criativo Vencedor ({video_top_1['metrics']['gmv_generated']} em vendas):")
    for s in labeled_segments.segments:
        risco_tag = "\033[91m[BLOCK/ALTO RISCO]\033[0m" if s.risk_score >= 0.7 else "\033[92m[SEGURO]\033[0m"
        print(f"[{s.start:.1f}s - {s.end:.1f}s] Role: {s.role.upper():10} | {risco_tag} | {s.tone_label}")
        if s.text_rewritten and s.text_rewritten != s.text:
            print(f"    \033[94mReescrito ->\033[0m {s.text_rewritten}")
        print("")
    
    extract_best_clips(video_file, labeled_segments, output_dir="cortes_prontos")
    print("\n[*] PoC Finalizado. O prospector agora modela com base na receita (Kalodata)!")

if __name__ == "__main__":
    # main()
    pass
