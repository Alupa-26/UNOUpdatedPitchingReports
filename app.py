import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="Gasoline Alley Reporting", layout="wide")

# High-Contrast Colors
OMAHA_RED = "#D71920"
BLACK = "#000000"
WHITE = "#FFFFFF"
LIGHT_GRAY = "#F0F0F0"

# Pitch Mapping & Colors: (Abbreviation, Background, Text)
PITCH_DICT = {
    "Fastball": ("FB", OMAHA_RED, WHITE),
    "FourSeamFastball": ("FB", OMAHA_RED, WHITE),
    "OneSeamFastball": ("FB", OMAHA_RED, WHITE),
    "Sinker": ("SI", WHITE, BLACK),
    "TwoSeamFastball": ("SI", WHITE, BLACK),
    "Slider": ("SL", "#FFD700", BLACK), # Yellow
    "ChangeUp": ("CH", "#0047AB", WHITE), # Cobalt Blue
    "Splitter": ("SPL", "#0047AB", WHITE),
    "Curveball": ("CB", BLACK, WHITE),
    "Knuckleball": ("KB", "#FFC0CB", BLACK), # Pink
    "Cutter": ("CT", "#696969", WHITE), # Dim Gray
    "Sweeper": ("SW", "#228B22", WHITE) # Forest Green
}

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- CUSTOM CSS FOR PROFESSIONAL MINIMALIST STYLING ---
st.markdown(f"""
    <style>
        .report-header {{
            text-align: center;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: {BLACK};
            margin-top: 20px;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}
        .styled-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 16px;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            background-color: {WHITE};
            color: {BLACK};
        }}
        .styled-table thead tr {{
            background-color: {BLACK};
            border-bottom: 3px solid {OMAHA_RED};
            text-align: center;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        .styled-table th {{
            padding: 14px 18px;
            border: 1px solid #333;
            text-align: center;
        }}
        .styled-table td {{
            padding: 14px 18px;
            border: 1px solid #ddd;
            text-align: center;
        }}
        .header-red {{ color: {OMAHA_RED}; }}
        .header-white {{ color: {WHITE}; }}
        
        .splits-table tbody tr:nth-of-type(even) {{
            background-color: {LIGHT_GRAY};
        }}
        .splits-table tbody tr:last-of-type {{
            border-bottom: 3px solid {OMAHA_RED};
        }}
        .download-btn {{
            display: inline-block;
            background-color: {OMAHA_RED};
            color: {WHITE};
            padding: 12px 24px;
            font-size: 16px;
            font-weight: bold;
            text-decoration: none;
            border-radius: 4px;
            text-align: center;
            margin-top: 20px;
            transition: 0.3s;
        }}
        .download-btn:hover {{
            background-color: {BLACK};
            color: {WHITE};
        }}
    </style>
""", unsafe_allow_html=True)

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

def generate_html_report(date_str, pitcher, splits_html, arsenal_html):
    logo_b64 = get_base64_image("Logo.png")
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height: 60px;">' if logo_b64 else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: {BLACK}; }}
            .header-container {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid {OMAHA_RED}; padding-bottom: 15px; margin-bottom: 30px; }}
            h2 {{ text-align: center; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 1px; }}
            h3 {{ text-transform: uppercase; font-size: 18px; margin-top: 30px; border-left: 5px solid {OMAHA_RED}; padding-left: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; text-align: center; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            th, td {{ border: 1px solid #ddd; padding: 12px; }}
            th {{ background-color: {BLACK}; border-bottom: 3px solid {OMAHA_RED}; }}
            .header-red {{ color: {OMAHA_RED}; }}
            .header-white {{ color: {WHITE}; }}
            .splits-table tr:nth-child(even) {{ background-color: {LIGHT_GRAY}; }}
        </style>
    </head>
    <body>
        <div class="header-container">
            <div>{img_tag}</div>
            <h2>{date_str} {pitcher} Post Outing Report</h2>
            <div>{img_tag}</div>
        </div>
        
        <h3>Splits Performance</h3>
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
        st.image("Logo.png", width=150)
with col2:
    st.markdown(f"<h1 style='text-align: center; color: {OMAHA_RED}; font-weight: 800; letter-spacing: 2px; margin-top: 10px;'>GASOLINE ALLEY REPORTING</h1>", unsafe_allow_html=True)
with col3:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)

st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

# --- TABS ---
tab_dash, tab_upload = st.tabs(["Dashboard", "Manage/Upload CSV's"])

# --- TAB 2: UPLOAD & MANAGE ---
with tab_upload:
    st.markdown("### Upload Trackman CSV")
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
        
    st.markdown("---")
    st.markdown("### Manage Uploads")
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv')]
    
    if not files:
        st.info("No CSV files uploaded yet.")
    else:
        for f in files:
            c1, c2 = st.columns([4, 1])
            c1.write(f"📄 {f}")
            if c2.button("Delete", key=f):
                os.remove(os.path.join(UPLOAD_DIR, f))
                st.rerun()

# --- TAB 1: DASHBOARD ---
with tab_dash:
    df_all = load_all_data()
    
    if df_all.empty:
        st.info("No data available. Please upload a CSV in the Manage/Upload tab.")
    else:
        if 'Date' not in df_all.columns:
            df_all['Date'] = datetime.today().strftime('%Y-%m-%d')
            
        pitchers = sorted(df_all['Pitcher'].dropna().unique())
        
        st.markdown("<br>", unsafe_allow_html=True)
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
            
            st.markdown(f"<h2 class='report-header'>{title_str}</h2>", unsafe_allow_html=True)
            
            # --- SPLITS TABLE CALCS ---
            def calc_splits(data, name):
                if data.empty:
                    # Formatted as a single string line without indents to prevent markdown code-block rendering
                    return f"<tr><td><b>{name}</b></td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0%</td><td>0%</td></tr>"
                
                data['PA_ID'] = data['Inning'].astype(str) + "_" + data['PAofInning'].astype(str)
                batters_faced = data['PA_ID'].nunique()
                
                pitches = len(data)
                k = len(data[data['KorBB'] == 'Strikeout'])
                free = len(data[(data['PitchCall'] == 'HitByPitch') | (data['KorBB'] == 'Walk')])
                hits = len(data[data['PlayResult'].isin(['Single', 'Double', 'Triple', 'HomeRun'])])
                
                fps_pitches = data[(data['Balls'] == 0) & (data['Strikes'] == 0)]
                fps_strikes = fps_pitches[fps_pitches['PitchCall'].isin(['StrikeCalled', 'StrikeSwinging', 'FoulBallFieldable', 'FoulBallNotFieldable', 'InPlay'])]
                fps_pct = f"{(len(fps_strikes) / batters_faced * 100):.1f}%" if batters_faced > 0 else "0%"
                
                s22_pa_count = 0
                for pa_id, group in data.groupby('PA_ID'):
                    if len(group[((group['Balls'] == 0) & (group['Strikes'] == 2)) | ((group['Balls'] == 1) & (group['Strikes'] == 2))]) > 0:
                        s22_pa_count += 1
                s22_pct = f"{(s22_pa_count / batters_faced * 100):.1f}%" if batters_faced > 0 else "0%"
                
                return f"<tr><td><b>{name}</b></td><td>{batters_faced}</td><td>{pitches}</td><td>{k}</td><td>{free}</td><td>{hits}</td><td>{fps_pct}</td><td>{s22_pct}</td></tr>"

            splits_rows = [
                calc_splits(df, "Totals"),
                calc_splits(df[df['BatterSide'] == 'Right'], "Vs. RHH"),
                calc_splits(df[df['BatterSide'] == 'Left'], "Vs. LHH")
            ]
            splits_html_body = "".join(splits_rows)
            
            # Flush left HTML to avoid markdown formatting interference
            splits_html_full = f"""
<div style="overflow-x: auto;">
<table class="styled-table splits-table">
<thead>
<tr>
<th><span class="header-red">SPLIT</span></th>
<th><span class="header-white">BATTERS FACED</span></th>
<th><span class="header-white">PITCHES</span></th>
<th><span class="header-white">K</span></th>
<th><span class="header-white">FREE</span></th>
<th><span class="header-white">H</span></th>
<th><span class="header-white">FPS %</span></th>
<th><span class="header-white">S22 %</span></th>
</tr>
</thead>
<tbody>
{splits_html_body}
</tbody>
</table>
</div>
"""
            st.markdown(splits_html_full, unsafe_allow_html=True)
            
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
                    
                    usage = f"{(count / total_pitches * 100):.1f}%"
                    
                    if 'PlateLocSide' in pt_df.columns and 'PlateLocHeight' in pt_df.columns:
                        in_zone = pt_df[(pt_df['PlateLocSide'] >= -0.8) & (pt_df['PlateLocSide'] <= 0.8) & 
                                        (pt_df['PlateLocHeight'] >= 1.575) & (pt_df['PlateLocHeight'] <= 3.575)]
                        zone_pct = f"{(len(in_zone) / count * 100):.1f}%"
                    else:
                        zone_pct = "-"
                    
                    swings = pt_df[pt_df['PitchCall'].isin(['StrikeSwinging', 'FoulBallFieldable', 'FoulBallNotFieldable', 'InPlay'])]
                    whiffs = pt_df[pt_df['PitchCall'] == 'StrikeSwinging']
                    whiff_pct = f"{(len(whiffs) / len(swings) * 100):.1f}%" if len(swings) > 0 else "0%"
                    
                    speeds = pt_df['RelSpeed'].dropna()
                    velo_str = f"{int(speeds.min())}-{int(speeds.mean())}, T{int(speeds.max())}" if not speeds.empty else "-"
                        
                    spins = pt_df['SpinRate'].dropna()
                    spin_str = f"{int(spins.min())}-{int(spins.mean())}, T{int(spins.max())}" if not spins.empty else "-"
                        
                    hb = f"{pt_df['HorzBreak'].mean():.1f}" if 'HorzBreak' in pt_df.columns else "-"
                    ivb = f"{pt_df['InducedVertBreak'].mean():.1f}" if 'InducedVertBreak' in pt_df.columns else "-"
                    vaa = f"{pt_df['VertApprAngle'].mean():.1f}" if 'VertApprAngle' in pt_df.columns else "-"
                    
                    # Single line HTML to prevent markdown parser bugs
                    row_html = f'<tr style="background-color: {bg_color}; color: {text_color}; border-bottom: 2px solid #FFFFFF;"><td><b>{abbr}</b></td><td>{usage}</td><td>{zone_pct}</td><td>{whiff_pct}</td><td>{velo_str}</td><td>{spin_str}</td><td>{hb}</td><td>{ivb}</td><td>{vaa}</td></tr>'
                    arsenal_rows.append(row_html)
            
            arsenal_html_body = "".join(arsenal_rows) if arsenal_rows else "<tr><td colspan='9'>No Pitch Data Available</td></tr>"
            
            arsenal_html_full = f"""
<div style="overflow-x: auto;">
<table class="styled-table arsenal-table">
<thead>
<tr>
<th><span class="header-red">PITCH TYPE</span></th>
<th><span class="header-white">USAGE %</span></th>
<th><span class="header-white">ZONE %</span></th>
<th><span class="header-white">WHIFF %</span></th>
<th><span class="header-white">VELO</span></th>
<th><span class="header-white">SPIN RATE</span></th>
<th><span class="header-white">HB</span></th>
<th><span class="header-white">IVB</span></th>
<th><span class="header-white">VAA</span></th>
</tr>
</thead>
<tbody>
{arsenal_html_body}
</tbody>
</table>
</div>
"""
            st.markdown(arsenal_html_full, unsafe_allow_html=True)
            
            # --- PDF / PRINT EXPORT ---
            st.markdown("<br>", unsafe_allow_html=True)
            
            report_html = generate_html_report(date_str, selected_pitcher, splits_html_full, arsenal_html_full)
            b64_html = base64.b64encode(report_html.encode('utf-8')).decode()
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                href = f'<a href="data:text/html;base64,{b64_html}" download="{title_str}.html" class="download-btn" style="width: 100%;">📥 Download Report (Open & Print as PDF)</a>'
                st.markdown(href, unsafe_allow_html=True)
