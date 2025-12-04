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
    /* Stili Generali */
    [data-testid="stAppViewContainer"] { background-color: #0b0c15; color: #ffffff; }
    .stTextInput > div > div > input { background-color: #161823; color: white; border: 1px solid #2a2d3e; border-radius: 8px; }
    
    /* Stile Card */
    .css-card { 
        background-color: #161823; 
        border: 1px solid #2a2d3e; 
        border-radius: 12px; 
        padding: 25px;
        margin-bottom: 20px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.5); 
    }
    
    /* Titolo H1 (Stile Neon Moderno) */
    h1 { 
        background: linear-gradient(90deg, #7b2cbf 0%, #00bfff 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-align: center; 
        font-weight: 800; 
        font-size: 3rem;
        margin-bottom: 20px;
        text-shadow: 0 0 15px rgba(157, 78, 221, 0.5); 
    }
    .stButton > button { 
        width: 100%; 
        background: linear-gradient(90deg, #7b2cbf 0%, #00bfff 100%); 
        color: white; 
        font-weight: bold; 
        border-radius: 8px; 
    }
    
    /* Score Display */
    .score-badge-good { color: #00bfff; font-size: 3.5rem; font-weight: bold; }
    .score-badge-bad { color: #ff4d4d; font-size: 3.5rem; font-weight: bold; }

    /* Stile per le barre di progresso */
    .track-bar-container {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        padding: 5px 0;
        border-bottom: 1px solid #2a2d3e;
    }
    .track-name-artist {
        width: 100%;
        font-size: 0.95rem;
    }
    .track-score-display-area {
        width: 50%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-left: 15px;
    }
    .track-score-value {
        font-size: 1.1rem;
        font-weight: bold;
        color: #ffffff; /* Punteggio sempre bianco (richiesta utente) */
        min-width: 40px;
        text-align: right;
    }
    .track-score-bar-wrapper {
        width: 80%;
        height: 18px;
        background-color: #2a2d3e; 
        border-radius: 9px;
        overflow: hidden;
        margin-left: 10px;
        position: relative;
    }
    .track-score-fill {
        height: 100%;
        border-radius: 9px;
        position: absolute;
        top: 0;
        left: 0;
    }
    /* Bar Colors (Viola/Azzurro) */
    .fill-high { background: linear-gradient(90deg, #9d4edd, #00bfff); } /* Ottimo: Viola a Azzurro */
    .fill-medium { background: linear-gradient(90deg, #7b2cbf, #9d4edd); } /* Medio: Viola */
    .fill-low { background: linear-gradient(90deg, #cc0000, #ff4d4d); } /* Critico: Rosso */
    
    .track-index { 
        color: #00bfff; /* Azzurro per la posizione */
        font-weight: bold; 
        margin-right: 15px; 
        min-width: 35px; 
        text-align: right; 
        font-size: 1.1rem;
    }
    .low-track-name { color: #ff4d4d; font-weight: bold; }
    
    /* Stile Collapsible */
    .expander-header {
        background-color: #161823; 
        border: 1px solid #2a2d3e;
        border-radius: 12px;
        padding: 10px 20px;
        color: #00bfff; 
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE BACKEND UNIFICATA ---

def get_analysis_data(analysis_type, identifier, client_id, client_secret):
    """Esegue l'analisi unificata per Playlist o Artista."""
    
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    all_tracks_data = []
    
    if analysis_type == "Playlist":
        st.info(f"Analisi della Playlist in corso: {identifier}")
        # Pulizia URL per ottenere ID
        playlist_id = identifier.split("/")[-1].split("?")[0]
        results = sp.playlist(playlist_id)
        tracks = results['tracks']['items']
        name = results['name']
        image_url = results['images'][0]['url'] if results['images'] else None
        
        for index, item in enumerate(tracks):
            track = item['track']
            if track:
                all_tracks_data.append({
                    "position": index + 1,
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "score": track['popularity']
                })
                
    elif analysis_type == "Artista":
        # Cerca l'artista per nome per ottenere l'ID
        results = sp.search(q='artist:' + identifier, type='artist')
        items = results['artists']['items']
        if not items:
            return {"error": f"Artista non trovato: {identifier}"}
            
        artist = items[0]
        artist_id = artist['id']
        name = f"Top Tracks di {artist['name']}"
        image_url = artist['images'][0]['url'] if artist['images'] else None
        st.info(f"Analisi delle Top 10 Tracks per: {artist['name']}")
        
        # Ottiene le top track dell'artista
        top_tracks = sp.artist_top_tracks(artist_id)['tracks']
        
        for index, track in enumerate(top_tracks):
            all_tracks_data.append({
                "position": index + 1,
                "name": track['name'],
                "artist": artist['name'],
                "score": track['popularity']
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
    """Helper function per il rendering della barra di progresso personalizzata."""
    score = track['score']
    
    if score >= 60:
        score_class = 'fill-high'
    elif score >= 20:
        score_class = 'fill-medium'
    else:
        score_class = 'fill-low'
        
    name_class = 'low-track-name' if score < 20 else ''

    # Larghezza minima per visualizzare il testo del punteggio
    bar_width = max(score, 3) 
    
    # Struttura HTML con punteggio all'esterno (richiesta utente)
    track_html = f"""
    <div class="track-bar-container">
        <div class="track-info-area">
            <span class="track-index">#{track['position']}</span>
            <div class="track-name-artist">
                <span class="{name_class}">{track['name']}</span> <i style='color:#a0a0b0'>by {track['artist']}</i>
            </div>
        </div>
        <div class="track-score-display-area">
            <span class="track-score-value">{score}</span>
            <div class="track-score-bar-wrapper">
                <div class="track-score-fill {score_class}" style="width: {bar_width}%;">
                </div>
            </div>
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
        placeholder = "✍️ Inserisci il nome completo dell'Artista..."
        
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
            <li>**Tasso di Salto & Completezza:** Quanto spesso gli utenti ascoltano l'intero brano.</li>
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

# 3. Results Display
if 'data' in st.session_state and st.session_state['data']:
    data = st.session_state['data']
    
    st.markdown(f"### 📈 Risultati Analisi per: {data['name']} ({data['total_tracks']} Tracks)")
    
    col_img, col_score = st.columns([1, 2])

    # Visualizzazione Artwork 
    with col_img:
        st.markdown('<div class="css-card" style="padding: 15px; text-align: center;">', unsafe_allow_html=True)
        if data['image_url']:
            # Per rendere l'immagine più moderna, la rendiamo un po' più grande
            st.image(data['image_url'], width=180) 
        else:
            st.markdown("<p style='text-align:center;'>Artwork Non Trovato</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Visualizzazione Score Medio
    with col_score:
        score_display = 'score-badge-good' if data['avg_pop'] >= 50 else 'score-badge-bad'
        st.markdown('<div class="css-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">', unsafe_allow_html=True)
        st.markdown("<h4 style='text-align:center; margin-bottom: 0;'>Punteggio Popolarità Medio</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; margin-top: 5px;' class='{score_display}'>{data['avg_pop']}/100</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


    # 3.2 High-Risk Tracks (< 20 Score)
    low_risk_tracks = [t for t in data['all_tracks_data'] if t['score'] < 20]
    
    st.markdown("### 🚨 High-Risk Tracks (Score < 20)")
    
    if low_risk_tracks:
        st.warning(f"Trovati **{len(low_risk_tracks)}** brani con engagement estremamente basso. **Si suggerisce la Rimozione.**")
        st.markdown('<div class="css-card" style="max-height: 250px; overflow-y: auto;">', unsafe_allow_html=True)
        for track in low_risk_tracks:
            st.markdown(_render_track_with_bar(track), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("Nessun brano ad alto rischio trovato (Score < 20). Ottima salute per la tua analisi!")

    # 3.3 Detailed Track Breakdown (All Tracks)
    st.markdown("### ⬇️ Dettaglio Completo Brani - Positions")
    st.markdown('<div class="css-card" style="max-height: 450px; overflow-y: auto;">', unsafe_allow_html=True)
    for track in data['all_tracks_data']:
        st.markdown(_render_track_with_bar(track), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
