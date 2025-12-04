import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION AND CUSTOM CSS (Soundvertise Theme) ---
st.set_page_config(page_title="Spotify Popularity Analyzer", layout="centered", page_icon="🎵")

# --- SECURE CREDENTIAL LOADING ---
# On Streamlit Cloud, these variables will be read securely from the secrets.toml file.
try:
    SPOTIFY_CLIENT_ID = st.secrets["spotify"]["client_id"]
    SPOTIFY_CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
    credentials_ok = True
except:
    # Fallback if secrets are not configured (e.g., local test without secrets file)
    SPOTIFY_CLIENT_ID = None
    SPOTIFY_CLIENT_SECRET = None
    credentials_ok = False
    
# Custom CSS for Dark/Neon Theme, optimized for visual interactivity
st.markdown("""
<style>
    /* General Styles and Theme */
    [data-testid="stAppViewContainer"] { background-color: #0b0c15; color: #ffffff; }
    .stTextInput > div > div > input { background-color: #161823; color: white; border: 1px solid #2a2d3e; border-radius: 8px; }
    
    /* Card Styling (Inspired by your example) */
    .css-card { 
        background-color: #161823; 
        border: 1px solid #2a2d3e; 
        border-radius: 12px; 
        padding: 25px;
        margin-bottom: 20px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.5); 
    }
    
    h1 { background: linear-gradient(90deg, #7b2cbf 0%, #9d4edd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-weight: 800; }
    .stButton > button { width: 100%; background: linear-gradient(90deg, #7b2cbf 0%, #9d4edd 100%); color: white; border: none; padding: 15px; font-weight: bold; border-radius: 8px; transition: 0.3s; }
    
    /* Overall Score Display */
    .overall-score-box {
        text-align: center;
        padding: 20px;
        border-radius: 12px;
        background-color: #10121b;
        margin-bottom: 15px;
    }
    .score-badge-good { color: #00e676; font-size: 3.5rem; font-weight: bold; }
    .score-badge-bad { color: #ff4d4d; font-size: 3.5rem; font-weight: bold; }

    /* Interactive Progress Bar Styling */
    .track-bar-container {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        padding: 5px 0;
        border-bottom: 1px solid #2a2d3e;
    }
    .track-info { width: 40%; color: #fff; font-size: 0.95rem; }
    .track-score-bar {
        width: 60%;
        height: 25px;
        background-color: #2a2d3e; 
        border-radius: 12px;
        overflow: hidden;
        margin-left: 10px;
    }
    .track-score-fill {
        height: 100%;
        border-radius: 12px;
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 8px;
        font-size: 1rem;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    /* Bar Colors based on Score */
    .fill-high { background: linear-gradient(90deg, #00b36e, #00e676); color: #161823; }
    .fill-medium { background: linear-gradient(90deg, #e6b800, #ffff00); color: #161823; }
    .fill-low { background: linear-gradient(90deg, #cc0000, #ff4d4d); color: #fff; }
    
    .track-index { color: #7b2cbf; font-weight: bold; margin-right: 10px; min-width: 25px; text-align: right; }
    .low-track-name { color: #ff4d4d; font-weight: bold; }

</style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---

def get_spotify_data(url, client_id, client_secret):
    """Performs Spotify playlist analysis and retrieves all track data."""
    try:
        # Usa le credenziali fornite da st.secrets
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        playlist_id = url.split("/")[-1].split("?")[0]
        results = sp.playlist(playlist_id)
        tracks = results['tracks']['items']
        
        playlist_image_url = results['images'][0]['url'] if results['images'] else None
        
        all_tracks_data = []
        total_pop = 0
        
        for index, item in enumerate(tracks):
            track = item['track']
            if track:
                pop = track['popularity']
                total_pop += pop
                
                all_tracks_data.append({
                    "position": index + 1,
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "score": pop
                })
        
        avg_pop = int(total_pop / len(all_tracks_data)) if all_tracks_data else 0
        
        return {
            "name": results['name'],
            "avg_pop": avg_pop,
            "all_tracks_data": all_tracks_data,
            "total_tracks": len(all_tracks_data),
            "image_url": playlist_image_url
        }
    except Exception as e:
        return {"error": str(e)}

def _render_track_with_bar(track):
    """Helper function to render a track using the custom progress bar UI."""
    score = track['score']
    
    if score >= 60:
        score_class = 'fill-high'
    elif score >= 20:
        score_class = 'fill-medium'
    else:
        score_class = 'fill-low'
        
    name_class = 'low-track-name' if score < 20 else ''

    # Controllo per non avere barre vuote in caso di score 0
    bar_width = max(score, 2) 
    
    track_html = f"""
    <div class="track-bar-container">
        <span class="track-index">#{track['position']}</span>
        <span class="track-info">
            <span class="{name_class}">{track['name']}</span> <i style='color:#a0a0b0'>by {track['artist']}</i>
        </span>
        <div class="track-score-bar">
            <div class="track-score-fill {score_class}" style="width: {bar_width}%;">
                {score}
            </div>
        </div>
    </div>
    """
    return track_html

# --- UI COMPONENTS ---

st.title("Playlist Popularity Analyzer")
st.markdown("<p style='text-align: center;'>Analyze the engagement score of every track in your Spotify playlist.</p>", unsafe_allow_html=True)

# 1. Configuration/Input Section
with st.container():
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Configuration")
    playlist_url = st.text_input("🔗 Spotify Playlist URL")
    
    # Rimosse le caselle di input per Client ID e Secret per sicurezza.
    if not credentials_ok:
        st.error("🔒 **Error:** Spotify credentials not found. Please configure `secrets.toml` on Streamlit Cloud.")


    if 'data' not in st.session_state:
         st.session_state['data'] = None

    analyze_btn = st.button("🚀 Analyze Playlist Popularity")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. Popularity Score Explanation
st.markdown("### 📖 Understanding the Popularity Index")
st.markdown("""
<div class="css-card">
    <p>The **Popularity Index** is a score from **0 to 100** that gauges a track's current relevance and engagement on Spotify. This score is not static; it reflects relative performance based on several factors, including:</p>
    <ul>
        <li>**Stream Frequency:** The total number of recent streams.</li>
        <li>**Save Rate:** How often users add the song to their personal libraries or playlists.</li>
        <li>**Skip Rate & Completeness:** How often users listen to the entire track.</li>
    </ul>
    <p>The index is crucial because **Spotify's algorithm** prioritizes playlists and tracks with high relative popularity, influencing discoverability and performance.</p>
</div>
""", unsafe_allow_html=True)


# --- LOGIC EXECUTION AND RESULTS DISPLAY ---
if analyze_btn:
    if not credentials_ok:
        st.error("Please configure your Spotify Client ID and Secret in Streamlit Secrets.")
    elif not playlist_url:
        st.warning("Please enter a valid Playlist URL.")
    else:
        with st.spinner("Analyzing tracks and calculating scores..."):
            sp_data = get_spotify_data(playlist_url, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
            
            if "error" in sp_data:
                st.error(f"Spotify API Error: {sp_data['error']}")
            else:
                st.session_state['data'] = sp_data
                st.rerun()

# 3. Results Display
if st.session_state['data']:
    data = st.session_state['data']
    
    st.markdown(f"### 📈 Analysis Results for: {data['name']} ({data['total_tracks']} Tracks)")
    
    col_img, col_score = st.columns([1, 2])

    # Visualizzazione Artwork
    with col_img:
        st.markdown('<div class="css-card" style="padding: 15px;">', unsafe_allow_html=True)
        if data['image_url']:
            st.image(data['image_url'], use_column_width=True)
        else:
            st.markdown("<p style='text-align:center;'>Artwork Not Found</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Visualizzazione Score Medio
    with col_score:
        score_display = 'score-badge-good' if data['avg_pop'] >= 50 else 'score-badge-bad'
        st.markdown('<div class="css-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">', unsafe_allow_html=True)
        st.markdown("<h4 style='text-align:center; margin-bottom: 0;'>Overall Playlist Score (Average)</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; margin-top: 5px;' class='{score_display}'>{data['avg_pop']}/100</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


    # 3.2 High-Risk Tracks (< 20 Score)
    low_risk_tracks = [t for t in data['all_tracks_data'] if t['score'] < 20]
    
    st.markdown("### 🚨 High-Risk Tracks (Score < 20)")
    
    if low_risk_tracks:
        st.warning(f"Found **{len(low_risk_tracks)}** tracks with extremely low engagement. **Suggest Removal.**")
        st.markdown('<div class="css-card" style="max-height: 250px; overflow-y: auto;">', unsafe_allow_html=True)
        for track in low_risk_tracks:
            st.markdown(_render_track_with_bar(track), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("No high-risk tracks found (Score < 20). Excellent playlist health!")

    # 3.3 Detailed Track Breakdown (All Tracks)
    st.markdown("### ⬇️ Full Track Breakdown")
    st.markdown('<div class="css-card" style="max-height: 450px; overflow-y: auto;">', unsafe_allow_html=True)
    for track in data['all_tracks_data']:
        st.markdown(_render_track_with_bar(track), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)