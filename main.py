import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('YOUTUBE_API_KEY')
playlist_id = os.getenv('PLAYLIST_ID')


def classify_title(title):

    """Esta função classifica um vídeo com base no título"""

    groups = [
        'Multimercados',
        'Renda Fixa',
        'Crédito Privado',
        'Ações',
        'CRIs',
        'KNRI11',
        'KFOF11',
        'KEVE11',
    ]

    title_lower = title.lower()
    for group in groups:
        if group.lower() in title_lower:
            return group
    return 'Outros'


def is_video_public(video_id):

    """Esta função verifica se um vídeo é público"""

    video_url = (
        f'https://www.googleapis.com/youtube/'
        f'v3/videos?part=status&id={video_id}&key={api_key}'
    )
    video_data = requests.get(video_url).json()
    if not video_data['items']:
        return False
    video_status = video_data['items'][0]['status']['privacyStatus']
    return video_status == 'public'


def get_video_stats(video_id):

    """Esta função obtém as estatísticas de um vídeo"""

    stats_url = (
        f'https://www.googleapis.com/youtube/'
        f'v3/videos?part=statistics&id={video_id}&key={api_key}'
    )

    stats_data = requests.get(stats_url).json()
    if not stats_data['items']:
        return None, None, None
    video_views = stats_data['items'][0]['statistics']['viewCount']
    video_likes = stats_data['items'][0]['statistics'].get(
        'likeCount', 'Não disponível'
    )
    video_comments = stats_data['items'][0]['statistics'].get(
        'commentCount', 'Não disponível'
    )
    return video_views, video_likes, video_comments


def fetch_youtube_data(api_key, playlist_id):

    """Esta função busca todos os dados necessários da API do YouTube"""

    playlist_url = (
        f'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&'
        f'maxResults=25&playlistId={playlist_id}&key={api_key}'
    )
    data = []
    page_token = ''

    while True:
        response = requests.get(playlist_url + f'&pageToken={page_token}')
        playlist_data = response.json()

        for item in playlist_data['items']:
            video_title = item['snippet']['title']
            video_id = item['snippet']['resourceId']['videoId']
            video_published_at = item['snippet']['publishedAt']

            if not is_video_public(video_id):
                continue  # pular o restante do loop

            # Agora sabemos que o vídeo é público, então pegue as estatísticas
            video_views, video_likes, video_comments = get_video_stats(
                video_id
            )

            # Tupla com os dados para a lista
            data.append(
                (
                    video_title,
                    video_views,
                    video_likes,
                    video_comments,
                    video_published_at,
                )
            )

        # Se 'nextPageToken' não estiver na resposta, chegamos na última página
        if 'nextPageToken' not in playlist_data:
            break

        page_token = playlist_data['nextPageToken']

    return data


def main():

    """Função principal que faz chamada as outras"""

    data = fetch_youtube_data(api_key, playlist_id)
    df = pd.DataFrame(
        data,
        columns=[
            'Título',
            'Visualizações',
            'Likes',
            'Comentários',
            'Data de publicação',
        ],
    )

    df['Grupo'] = df['Título'].apply(classify_title)

    new_df = df.to_excel('resultado.xlsx', index=False)


# Execute o ponto de entrada principal
if __name__ == '__main__':
    main()
