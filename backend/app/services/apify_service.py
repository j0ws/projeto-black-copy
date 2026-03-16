import os
from apify_client import ApifyClient

def scrape_tiktok_profile(profile_url: str, max_videos: int = 5):
    """
    Função principal que interage com o Apify.
    Gasta créditos, usar com a devida autorização financeira.
    """
    # Obter token de ambiente
    apify_token = os.environ.get("APIFY_API_TOKEN", "sua_chave_real")
    client = ApifyClient(apify_token)

    print(f"[APIFY_SERVICE] Executando chamada REAL e tarifada no Apify para: {profile_url}")
    
    # Preparar a entrada (input) para o Actor do Apify
    run_input = {
        "profiles": [profile_url],
        "resultsPerPage": max_videos,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
    }

    try:
        run = client.actor("clockwork/tiktok-profile-scraper").call(run_input=run_input)
        
        # Obter os resultados do Run Dataset
        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append(item)
            
        print(f"[APIFY_SERVICE] Extração concluída. {len(items)} itens obtidos.")
        return items
    except Exception as e:
        print(f"[APIFY_SERVICE] Erro fatal ao chamar Apify: {str(e)}")
        raise e
