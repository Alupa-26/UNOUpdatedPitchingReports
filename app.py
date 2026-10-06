import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from datetime import datetime

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="Gasoline Alley Reporting", layout="wide")

# Colors
OMAHA_RED = "#D71920"
BLACK = "#000000"
WHITE = "#FFFFFF"

# Pitch Mapping & Colors: (Abbreviation, Background, Text)
PITCH_DICT = {
    "Fastball": ("FB", OMAHA_RED, WHITE),
    "FourSeamFastball": ("FB", OMAHA_RED, WHITE),
    "OneSeamFastball": ("FB", OMAHA_RED, WHITE),
    "Sinker": ("SI", WHITE, BLACK),
    "TwoSeamFastball": ("SI", WHITE, BLACK),
    "Slider": ("SL", "#FFD700", BLACK), # Yellow
    "ChangeUp": ("CH", "blue", WHITE),
    "Splitter": ("SPL", "blue", WHITE),
    "Curveball": ("CB", BLACK, WHITE),
    "Knuckleball": ("KB", "#FFC0CB", BLACK), # Pink
    "Cutter": ("CT", "gray", WHITE),
    "Sweeper": ("SW", "green", WHITE)
}

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- HELPER FUNCTIONS ---
def load_all_data():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv')]
    df_list = []
    for file in files:
        tmp = pd.read_csv(os.path.join(UPLOAD_DIR, file))
        tmp['SourceFile'] = file
        df_list.append(tmp)
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return pd.DataFrame()

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def generate_html_report(df, pitcher, date_str, splits_html, arsenal_html):
    # This generates a printable HTML that can be saved as PDF natively via the browser
    logo_b64 = get_base64_image("Logo.png")
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" width="80">' if logo_b64 else ''
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid {OMAHA_RED}; padding-bottom: 10px; margin-bottom: 20px; }}
            h2 {{ text-align: center; margin: 0; color: {BLACK}; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; text-align: center; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: {OMAHA_RED}; color: white; }}
        </style>
    </head>
    <body>
        <div class="header">
            {img_tag}
            <h2>{date_str} {pitcher} Post Outing Report</h2>
            {img_tag}
        </div>
        <h3>Splits</h3>
        {splits_html}
        <h3>Arsenal Performance</h3>
        {arsenal_html}
    </body>
    </html>
    """
    return html

# --- UI HEADER ---
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)
with col2:
    st.markdown(f"<h1 style='text-align: center; color: {OMAHA_RED};'>GASOLINE ALLEY REPORTING</h1>", unsafe_allow_html=True)
with col3:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)

st.markdown("---")

# --- TABS ---
tab_dash, tab_upload = st.tabs(["Dashboard", "Manage/Upload CSV's"])

# --- TAB 2: UPLOAD & MANAGE ---
with tab_upload:
    st.subheader("Upload Trackman CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    col_type, col_title = st.columns(2)
    with col_type:
        session_type = st.selectbox("Session Type", ["Game", "Bullpen"])
    with col_title:
        session_title = st.text_input("Opponent / Session Title")
        
    if st.button("Upload & Save") and uploaded_file is not None:
        filename = f"{session_type}_{session_title.replace(' ', '_')}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Saved: {filename}")
        
    st.markdown("### Manage Uploads")
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv')]
    for f in files:
        c1, c2 = st.columns([4, 1])
        c1.write(f)
        if c2.button("Delete", key=f):
            os.remove(os.path.join(UPLOAD_DIR, f))
            st.rerun()

# --- TAB 1: DASHBOARD ---
with tab_dash:
    df_all = load_all_data()
    
    if df_all.empty:
        st.info("No data available. Please upload a CSV in the Manage/Upload tab.")
    else:
        # Check required columns exist to avoid errors
        if 'Date' not in df_all.columns:
            df_all['Date'] = datetime.today().strftime('%Y-%m-%d')
            
        pitchers = sorted(df_all['Pitcher'].dropna().unique())
        
        col_p, col_d = st.columns(2)
        with col_p:
            selected_pitcher = st.selectbox("Select Pitcher", pitchers)
        
        pitcher_df = df_all[df_all['Pitcher'] == selected_pitcher]
        dates = sorted(pitcher_df['Date'].dropna().unique())
        
        with col_d:
            selected_dates = st.multiselect("Select Date(s)", dates, default=dates)
            
        if selected_pitcher and selected_dates:
            df = pitcher_df[pitcher_df['Date'].isin(selected_dates)].copy()
            
            date_str = ", ".join(selected_dates) if len(selected_dates) <= 2 else f"{selected_dates[0]} to {selected_dates[-1]}"
            title_str = f"{date_str} {selected_pitcher} Post Outing Report"
            
            st.markdown(f"<h3 style='text-align: center;'>{title_str}</h3>", unsafe_allow_html=True)
            
            # --- SPLITS TABLE CALCS ---
            def calc_splits(data, name):
                if data.empty:
                    return {"Split": name, "Batters Faced": 0, "Pitches": 0, "K": 0, "Free": 0, "H": 0, "FPS %": "0%", "S22%": "0%"}
                
                # Batters faced approximated by unique Inning + PAofInning
                data['PA_ID'] = data['Inning'].astype(str) + "_" + data['PAofInning'].astype(str)
                batters_faced = data['PA_ID'].nunique()
                
                pitches = len(data)
                k = len(data[data['KorBB'] == 'Strikeout'])
                free = len(data[(data['PitchCall'] == 'HitByPitch') | (data['KorBB'] == 'Walk')])
                hits = len(data[data['PlayResult'].isin(['Single', 'Double', 'Triple', 'HomeRun'])])
                
                # FPS %
                fps_pitches = data[(data['Balls'] == 0) & (data['Strikes'] == 0)]
                fps_strikes = fps_pitches[fps_pitches['PitchCall'].isin(['StrikeCalled', 'StrikeSwinging', 'FoulBallFieldable', 'FoulBallNotFieldable', 'InPlay'])]
                fps_pct = f"{(len(fps_strikes) / batters_faced * 100):.1f}%" if batters_faced > 0 else "0%"
                
                # S22% (Reached 0-2 or 1-2)
                s22_pa_count = 0
                for pa_id, group in data.groupby('PA_ID'):
                    if len(group[((group['Balls'] == 0) & (group['Strikes'] == 2)) | ((group['Balls'] == 1) & (group['Strikes'] == 2))]) > 0:
                        s22_pa_count += 1
                s22_pct = f"{(s22_pa_count / batters_faced * 100):.1f}%" if batters_faced > 0 else "0%"
                
                return {
                    "Split": name, "Batters Faced": batters_faced, "Pitches": pitches,
                    "K": k, "Free": free, "H": hits, "FPS %": fps_pct, "S22%": s22_pct
                }

            splits_data = [
                calc_splits(df, "Totals"),
                calc_splits(df[df['BatterSide'] == 'Right'], "Vs. RHH"),
                calc_splits(df[df['BatterSide'] == 'Left'], "Vs. LHH")
            ]
            splits_df = pd.DataFrame(splits_data)
            
            # Convert splits DF to HTML for styling & PDF
            splits_html = splits_df.to_html(index=False, classes="table table-bordered")
            st.markdown(splits_html, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- ARSENAL PERFORMANCE TABLE CALCS ---
            arsenal_rows = []
            if 'TaggedPitchType' in df.columns:
                pitch_types = df['TaggedPitchType'].dropna().unique()
                total_pitches = len(df)
                
                for pt in pitch_types:
                    pt_df = df[df['TaggedPitchType'] == pt]
                    if pt_df.empty: continue
                    
                    abbr, bg_color, text_color = PITCH_DICT.get(pt, (pt, WHITE, BLACK))
                    count = len(pt_df)
                    
                    # Usage %
                    usage = f"{(count / total_pitches * 100):.1f}%"
                    
                    # Zone % (-0.8 to 0.8 Horz, 1.575 to 3.575 Vert)
                    in_zone = pt_df[(pt_df['PitchLocSide'] >= -0.8) & (pt_df['PitchLocSide'] <= 0.8) & 
                                    (pt_df['PitchLocHeight'] >= 1.575) & (pt_df['PitchLocHeight'] <= 3.575)]
                    zone_pct = f"{(len(in_zone) / count * 100):.1f}%"
                    
                    # Whiff %
                    swings = pt_df[pt_df['PitchCall'].isin(['StrikeSwinging', 'FoulBallFieldable', 'FoulBallNotFieldable', 'InPlay'])]
                    whiffs = pt_df[pt_df['PitchCall'] == 'StrikeSwinging']
                    whiff_pct = f"{(len(whiffs) / len(swings) * 100):.1f}%" if len(swings) > 0 else "0%"
                    
                    # Velo
                    speeds = pt_df['RelSpeed'].dropna()
                    if len(speeds) > 0:
                        velo_str = f"{int(speeds.min())}-{int(speeds.mean())}, T{int(speeds.max())}"
                    else:
                        velo_str = "-"
                        
                    # Spin Rate
                    spins = pt_df['SpinRate'].dropna()
                    if len(spins) > 0:
                        spin_str = f"{int(spins.min())}-{int(spins.mean())}, T{int(spins.max())}"
                    else:
                        spin_str = "-"
                        
                    # Movement
                    hb = f"{pt_df['HorzBreak'].mean():.1f}" if 'HorzBreak' in pt_df.columns else "-"
                    ivb = f"{pt_df['InducedVertBreak'].mean():.1f}" if 'InducedVertBreak' in pt_df.columns else "-"
                    vaa = f"{pt_df['VertApprAngle'].mean():.1f}" if 'VertApprAngle' in pt_df.columns else "-"
                    
                    row_html = f"""
                    <tr style="background-color: {bg_color}; color: {text_color};">
                        <td><b>{abbr}</b></td>
                        <td>{usage}</td>
                        <td>{zone_pct}</td>
                        <td>{whiff_pct}</td>
                        <td>{velo_str}</td>
                        <td>{spin_str}</td>
                        <td>{hb}</td>
                        <td>{ivb}</td>
                        <td>{vaa}</td>
                    </tr>
                    """
                    arsenal_rows.append(row_html)
            
            arsenal_html = f"""
            <table class="table table-bordered">
                <thead>
                    <tr style="background-color: {OMAHA_RED}; color: {WHITE};">
                        <th>Pitch Type</th>
                        <th>Usage %</th>
                        <th>Zone %</th>
                        <th>Whiff %</th>
                        <th>Velo</th>
                        <th>Spin Rate</th>
                        <th>HB</th>
                        <th>IVB</th>
                        <th>VAA</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(arsenal_rows)}
                </tbody>
            </table>
            """
            st.markdown(arsenal_html, unsafe_allow_html=True)
            
            # --- PDF / PRINT EXPORT ---
            st.markdown("---")
            report_html = generate_html_report(df, selected_pitcher, date_str, splits_html, arsenal_html)
            
            b64_html = base64.b64encode(report_html.encode('utf-8')).decode()
            href = f'<a href="data:text/html;base64,{b64_html}" download="{title_str}.html" style="background-color:{OMAHA_RED}; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Download Report (Open & Print as PDF)</a>'
            st.markdown(href, unsafe_allow_html=True)
