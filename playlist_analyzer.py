import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE PAGINA E CSS ---
st.set_page_config(page_title="Spotify Popularity Analyzer", layout="centered", page_icon="🎵")

# --- CARICAMENTO CREDENZIALI SICURO (STREAMLIT SECRETS) ---
try:
    SPOTIFY_CLIENT_ID = st.secrets["spotify"]["client_id"]
    SPOTIFY_CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
    credentials_ok = True
except:
    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None
    credentials_ok = False
    
# Custom CSS per lo stile Soundvertise (Viola/Azzurro/Scuro)
st.markdown("""
<style>
    /* VARIABILI COLORE AGGIORNATE */
    :root {
        --bg-color: #0b0c15; /* Sfondo principale */
        --card-bg: #161823;  /* Sfondo Card */
        --border-color: #2a2d3e; /* Bordo sottile */
        --accent-purple: #9d4edd; /* Viola principale */
        --accent-blue: #00bfff; /* Azzurro Neon */
        --accent-gradient: linear-gradient(90deg, #7b2cbf 0%, #00bfff 100%); /* Gradiente Bottone */
        --text-color: #ffffff;
        --text-secondary: #a0a0b0;
        --critical-low-color: #3b0764; /* NUOVO: Viola Ultra Scuro (0-19) */
        --low-score-color: #6a1a8c; /* Viola Scuro Intenso (20-39) */
        --duplicate-color: #ff9900; /* Arancione per i duplicati */
        --duplicate-row-bg: rgba(255, 153, 0, 0.1); /* Sfondo chiaro per la riga duplicata */
    }

    /* Stili Generali */
    [data-testid="stAppViewContainer"] { background-color: var(--bg-color); color: var(--text-color); }
    
    /* Input e Focus */
    .stTextInput > div > div > input { 
        background-color: var(--card-bg); 
        color: var(--text-color); 
        border: 1px solid var(--border-color); 
        border-radius: 8px;
        transition: border-color 0.3s;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-blue);
        box-shadow: 0 0 5px rgba(0, 191, 255, 0.5);
    }
    
    /* Stile Card con Ombreggiatura Profonda */
    .css-card { 
        background-color: var(--card-bg); 
        border: 1px solid var(--border-color); 
        border-radius: 12px; 
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7), 0 0 2px rgba(157, 78, 221, 0.2); 
    }
    
    /* Titolo H1 */
    h1 { 
        background: var(--accent-gradient); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-shadow: 0 0 20px rgba(157, 78, 221, 0.8);
    }
    
    /* Bottone Principale con Animazione */
    .stButton > button { 
        background: var(--accent-gradient); 
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(0, 191, 255, 0.7);
        transform: scale(1.02);
    }
    
    /* Score Display Generale (Colori per i range) */
    .score-badge-good { color: var(--accent-blue); font-size: 3.5rem; font-weight: bold; }
    .score-badge-bad { color: var(--accent-purple); font-size: 3.5rem; font-weight: bold; }

    /* Stile LISTA DETTAGLIO */
    .track-item-clean {
        display: grid;
        grid-template-columns: 50px auto minmax(130px, 160px);
        align-items: center;
        padding: 10px 0; 
        border-bottom: 1px solid #2a2d3e;
        transition: background-color 0.2s;
    }
    .track-item-clean.is-duplicate {
        background-color: var(--duplicate-row-bg);
        border-left: 5px solid var(--duplicate-color);
        padding-left: 10px;
    }
    .track-list-header {
        display: grid;
        grid-template-columns: 50px auto minmax(130px, 160px); 
        color: var(--accent-blue);
        font-weight: bold;
        padding: 0 0 10px 0;
        border-bottom: 2px solid var(--accent-purple);
        margin-bottom: 10px;
        font-size: 0.9rem;
    }
    
    .track-score-value-clean {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--text-color); 
        padding: 5px 10px;
        border-radius: 6px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.4); 
    }
    
    /* Colori del punteggio (Sfondo del numero - 5 sfumature) */
    .fill-excellent-bg { background-color: var(--accent-blue); } /* 90-100 */
    .fill-good-bg { background-color: #4a148c; } /* NUOVO: 60-89 */
    .fill-average-bg { background-color: var(--accent-purple); } /* 40-59 */
    .fill-low-bg { background-color: var(--low-score-color); } /* 20-39 */
    .fill-critical-bg { background-color: var(--critical-low-color); } /* 0-19 */

    /* Barra di Progresso Dettaglio */
    .score-bar-small {
        width: 80px; 
        height: 8px;
        background-color: #2a2d3e;
        border-radius: 4px;
        overflow: hidden;
        position: relative;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 4px;
        position: absolute;
        top: 0;
        left: 0;
    }

    /* Colori per il Riempimento Barra (Gradienti) */
    .bar-excellent { background: linear-gradient(90deg, #00bfff, #7b2cbf); }
    .bar-good { background: linear-gradient(90deg, #9d4edd, #4a148c); }
    .bar-average { background: linear-gradient(90deg, #b981f7, #9d4edd); }
    .bar-low { background: linear-gradient(90deg, #8c42a8, #6a1a8c); }
    .bar-critical { background: linear-gradient(90deg, #510a80, #3b0764); }
    
    .track-index { color: var(--accent-blue); }
    .low-track-name { color: var(--low-score-color); font-weight: bold; }
    .duplicate-name { color: var(--duplicate-color); font-style: italic; font-weight: bold; } 
    
    /* Score Badge Imponente (Effetto Ludopatia/Diagnosi) */
    .main-score-card {
        text-align: center;
        padding: 30px 20px;
        margin-bottom: 25px;
        background: linear-gradient(135deg, #161823 0%, #1a1c28 100%);
        border: 2px solid var(--accent-purple);
        box-shadow: 0 0 40px rgba(157, 78, 221, 0.3);
    }

    /* Barra di progresso per lo score medio */
    .main-score-bar-wrapper {
        width: 80%;
        margin: 10px auto 0 auto;
        height: 20px;
        background-color: #2a2d3e;
        border-radius: 10px;
        overflow: hidden;
    }
    .main-score-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }

</style>
""", unsafe_allow_html=True)

# --- FUNZIONE BACKEND UNIFICATA ---

def get_analysis_data(analysis_type, identifier, client_id, client_secret):
    """Esegue l'analisi unificata per Playlist o Artista."""
    
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    all_tracks_data = []
    track_identifiers = {} # Usato per rilevare duplicati (ID Spotify del brano)
    
    if analysis_type == "Playlist":
        # Pulizia URL per ottenere ID
        playlist_id = identifier.split("/")[-1].split("?")[0]
        
        try:
            # 1. Ottieni i metadati della playlist (nome, immagine)
            metadata = sp.playlist(playlist_id, fields='name,images')
            name = metadata['name']
            image_url = metadata['images'][0]['url'] if metadata['images'] else None

            # 2. Ottieni tutti gli elementi della playlist (gestione della paginazione)
            tracks_results = sp.playlist_items(playlist_id, fields='items.track.id,items.track.name,items.track.artists,items.track.popularity,next')
            tracks_list = []
            
            while tracks_results:
                tracks_list.extend(tracks_results['items'])
                tracks_results = sp.next(tracks_results)

            # 3. Processa tutti i brani
            for index, item in enumerate(tracks_list):
                track = item.get('track')
                if track and track.get('id'): 
                    track_id = track['id']
                    
                    # Rilevamento duplicati
                    is_duplicate = track_id in track_identifiers
                    if not is_duplicate:
                        track_identifiers[track_id] = True

                    all_tracks_data.append({
                        "position": index + 1,
                        "name": track['name'],
                        "artist": track['artists'][0]['name'],
                        "score": track['popularity'],
                        "is_duplicate": is_duplicate
                    })
        except Exception as e:
            return {"error": f"ID/URL Playlist non valido o errore API: {e}"}
                
    elif analysis_type == "Artista":
        artist_id = None
        
        # 1. Tentativo di estrarre l'ID da URL/URI
        if "spotify.com/artist/" in identifier:
            artist_id = identifier.split("/")[-1].split("?")[0]
        elif identifier.startswith("spotify:artist:"):
            artist_id = identifier.split(":")[-1]
        
        artist = None
        
        if artist_id:
            try:
                # Se abbiamo un ID valido, carichiamo i dettagli
                artist = sp.artist(artist_id)
            except Exception:
                # Se l'ID non è valido, si procede alla ricerca per nome
                artist_id = None 

        if not artist_id:
            # 2. Se l'ID non è stato trovato o non è valido, eseguiamo la ricerca per nome
            results = sp.search(q='artist:' + identifier, type='artist')
            items = results['artists']['items']
            if not items:
                return {"error": f"Artista non trovato con il nome o l'URL/ID fornito: {identifier}"}
            artist = items[0]
            artist_id = artist['id']
        
        # 3. Ottiene le top track dell'artista (non necessita paginazione, sono max 10)
        name = f"Top Tracks di {artist['name']}"
        image_url = artist['images'][0]['url'] if artist['images'] else None
        
        # Se l'artista è stato trovato, carica le tracce.
        top_tracks = sp.artist_top_tracks(artist_id)['tracks']
        
        for index, track in enumerate(top_tracks):
            if track:
                all_tracks_data.append({
                    "position": index + 1,
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "score": track['popularity'],
                    "is_duplicate": False # Non applicabile alle Top Tracks
                })

    # Calcolo della Popolarità Media
    total_pop = sum(t['score'] for t in all_tracks_data)
    avg_pop = int(total_pop / len(all_tracks_data)) if all_tracks_data else 0
    
    return {
        "name": name,
        "avg_pop": avg_pop,
        "all_tracks_data": all_tracks_data,
        "total_tracks": len(all_tracks_data),
        "image_url": image_url
    }
    
def _render_track_with_bar(track):
    """Helper function per il rendering del brano con barre sottili e numeri colorati, usando 5 sfumature."""
    score = track['score']
    
    # 1. Determinazione classi colore
    if score >= 90:
        score_class = 'fill-excellent-bg'
        bar_color = 'bar-excellent'
    elif score >= 60:
        score_class = 'fill-good-bg'
        bar_color = 'bar-good'
    elif score >= 40:
        score_class = 'fill-average-bg'
        bar_color = 'bar-average'
    elif score >= 20:
        score_class = 'fill-low-bg' 
        bar_color = 'bar-low'
    else:
        score_class = 'fill-critical-bg'
        bar_color = 'bar-critical'
        
    name_class = 'low-track-name' if score < 20 else ''
    
    artist_name = track['artist']
    song_name = track['name']
    
    duplicate_tag = " (DUPLICATO)" if track.get('is_duplicate') else ""
    duplicate_class = "duplicate-name" if track.get('is_duplicate') else name_class
    duplicate_row_class = "is-duplicate" if track.get('is_duplicate') else "" 
    
    bar_width = max(score, 3) # Larghezza minima per visualizzazione

    # Struttura HTML pulita (solo indice, nome e punteggio colorato)
    track_html = f"""
    <div class="track-item-clean {duplicate_row_class}">
        <span class="track-index">#{track['position']}</span>
        <div class="track-name-artist">
            <span class="{duplicate_class}">{song_name}{duplicate_tag}</span> <br> <i style='color:#a0a0b0'>{artist_name}</i>
        </div>
        <div class="score-container-detail">
            <div class="score-bar-small">
                <div class="score-bar-fill {bar_color}" style="width: {bar_width}%;"></div>
            </div>
            <span class="track-score-value-clean {score_class}">
                {score}
            </span>
        </div>
    </div>
    """
    return track_html

# --- UI COMPONENTS ---

st.title("PLAYLIST POPULARITY ANALYZER")
st.markdown("<p style='text-align: center;'>Analizza il punteggio di engagement di brani o artisti su Spotify.</p>", unsafe_allow_html=True)

# 1. Configurazione/Input Section
with st.container():
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Configuration")
    
    # Selettore Artista/Playlist
    analysis_type = st.radio(
        "Seleziona il tipo di analisi:",
        ("Playlist", "Artista"),
        horizontal=True
    )
    
    if analysis_type == "Playlist":
        placeholder = "🔗 Incolla qui l'URL della Playlist Spotify..."
    else:
        placeholder = "✍️ Inserisci il nome completo dell'Artista o l'URL Spotify..."
        
    identifier = st.text_input(placeholder)

    if not credentials_ok:
        st.error("🔒 **Errore:** Credenziali Spotify non trovate. Configura `secrets.toml`.")


    if 'data' not in st.session_state:
         st.session_state['data'] = None

    analyze_btn = st.button(f"🚀 Analizza {analysis_type} Popularity")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. Popularity Score Explanation (Collassabile)
with st.expander("📖 Clicca per Comprendere l'Indice di Popolarità"):
    st.markdown("""
    <div class="css-card" style="margin-top: 0; padding: 15px;">
        <p>L'**Indice di Popolarità** (Punteggio da 0 a 100) misura l'attuale rilevanza e l'engagement di un brano o artista su Spotify. Il punteggio è relativo, non assoluto, e si basa su diversi fattori chiave:</p>
        <ul style="list-style-type: disc; padding-left: 20px;">
            <li>**Frequenza di Streaming:** Il numero totale di ascolti recenti.</li>
            <li>**Tasso di Salvataggio:** Quante volte gli utenti aggiungono il contenuto alle loro librerie o playlist.</li>
            <li>**Tasso di Salto e Completezza:** Quanto spesso gli utenti ascoltano l'intero brano.</li>
        </ul>
        <p>Questo indice è vitale, poiché l'algoritmo di Spotify favorisce i contenuti con una maggiore popolarità relativa, migliorandone la scopribilità (discoverability).</p>
    </div>
    """, unsafe_allow_html=True)


# --- LOGIC EXECUTION AND RESULTS DISPLAY ---
if analyze_btn:
    if not credentials_ok:
        st.error("Per favore, configura Spotify Client ID e Secret in Streamlit Secrets.")
    elif not identifier:
        st.warning(f"Per favore, inserisci un ID o URL {analysis_type} valido.")
    else:
        with st.spinner(f"Analisi {analysis_type} e calcolo punteggio..."):
            
            analysis_data = get_analysis_data(analysis_type, identifier, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
            
            if "error" in analysis_data:
                st.error(f"Errore Spotify: {analysis_data['error']}")
            else:
                st.session_state['data'] = analysis_data
                st.rerun()

# 3. Results Display (NUOVA STRUTTURA: Score imponente + Artwork centrato)
if 'data' in st.session_state and st.session_state['data']:
    data = st.session_state['data']
    
    st.markdown(f"### 📈 Risultati Analisi per: {data['name']} ({data['total_tracks']} Tracks)")
    
    score_display = 'score-badge-good' if data['avg_pop'] >= 50 else 'score-badge-bad'
    avg_score = data['avg_pop']

    # Determina il colore e la larghezza della barra principale
    if avg_score >= 90:
        main_bar_color = 'linear-gradient(90deg, #00bfff, #7b2cbf)' # Excellent
    elif avg_score >= 60:
        main_bar_color = 'linear-gradient(90deg, #9d4edd, #4a148c)' # Good
    elif avg_score >= 40:
        main_bar_color = 'linear-gradient(90deg, #b981f7, #9d4edd)' # Average
    else:
        main_bar_color = 'linear-gradient(90deg, #8c42a8, #6a1a8c)' # Low/Critical

    # 3.1 Punteggio Medio (Card ad alto impatto)
    st.markdown('<div class="main-score-card">', unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center; margin-bottom: 0; color: var(--text-secondary);'>PUNTEGGIO POPOLARITÀ MEDIO FINALE</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; margin-top: 5px;' class='{score_display}'>{data['avg_pop']}/100</p>", unsafe_allow_html=True)
    
    # Barra di progresso dello score medio
    st.markdown(f"""
    <div class="main-score-bar-wrapper">
        <div class="main-score-fill" style="width: {avg_score}%; background: {main_bar_color};"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 3.2 Artwork Centrato sotto il Punteggio
    st.markdown('<div class="css-card" style="padding: 15px; text-align: center;">', unsafe_allow_html=True)
    if data['image_url']:
        # Mostra l'immagine centrata con una dimensione fissa moderna
        st.image(data['image_url'], width=250) 
    else:
        st.markdown("<p style='text-align:center;'>Artwork Non Trovato</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


    # 3.3 Low Popularity Tracks (< 20 Score)
    low_risk_tracks = [t for t in data['all_tracks_data'] if t['score'] < 20]
    
    st.markdown("### 📉 Low Popularity Tracks (Score < 20)") # TESTO AGGIORNATO
    
    if low_risk_tracks:
        st.warning(f"Trovati **{len(low_risk_tracks)}** brani con engagement estremamente basso. **Si suggerisce la Rimozione.**")
        st.markdown('<div class="css-card" style="max-height: 250px; overflow-y: auto;">', unsafe_allow_html=True)
        # Intestazioni per la lista a rischio
        st.markdown("""
        <div class="track-list-header">
            <span style="text-align: right;">POS.</span>
            <span style="margin-left: 10px;">SONG / ARTIST</span>
            <span style="text-align: right;">SCORE</span>
        </div>
        """, unsafe_allow_html=True)
        for track in low_risk_tracks:
            st.markdown(_render_track_with_bar(track), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("Nessun brano a bassa popolarità trovato (Score < 20). Ottima salute per la tua analisi!")

    # 3.4 Detailed Track Breakdown (All Tracks)
    st.markdown("### ⬇️ Dettaglio Completo Brani - Positions")
    st.markdown('<div class="css-card" style="max-height: 450px; overflow-y: auto;">', unsafe_allow_html=True)
    
    # Intestazioni per la lista completa
    st.markdown("""
    <div class="track-list-header">
        <span style="text-align: right;">POS.</span>
        <span style="margin-left: 10px;">SONG / ARTIST</span>
        <span style="text-align: right;">SCORE</span>
    </div>
    """, unsafe_allow_html=True)
    
    for track in data['all_tracks_data']:
        st.markdown(_render_track_with_bar(track), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
