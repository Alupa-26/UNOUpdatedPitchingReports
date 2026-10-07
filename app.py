import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from datetime import datetime
import plotly.graph_objects as go

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
    "Slider": ("SL", "#FFD700", BLACK), 
    "ChangeUp": ("CH", "#0047AB", WHITE), 
    "Splitter": ("SPL", "#0047AB", WHITE),
    "Curveball": ("CB", BLACK, WHITE),
    "Knuckleball": ("KB", "#FFC0CB", BLACK), 
    "Cutter": ("CT", "#696969", WHITE), 
    "Sweeper": ("SW", "#228B22", WHITE) 
}

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- CUSTOM CSS FOR DASHBOARD ---
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
        .section-title {{
            text-align: center;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: {BLACK};
            margin-top: 30px;
            margin-bottom: 10px;
            font-size: 20px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .styled-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0 25px 0;
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
        .pitcher-view-text {{
            text-align: center;
            color: #A9A9A9;
            font-size: 14px;
            font-style: italic;
            margin-top: 5px;
            margin-bottom: 25px;
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

def format_val(val, decimals=1):
    try:
        if pd.isna(val): return "-"
        return f"{float(val):.{decimals}f}"
    except:
        return "-"

def generate_html_report(date_str, pitcher, splits_html, arsenal_html, movement_plot_html, 
                         plot_pre2k, plot_2k, plot_whiff, plot_damage):
    logo_b64 = get_base64_image("Logo.png")
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height: 50px;">' if logo_b64 else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 20px; padding: 0; color: {BLACK}; background-color: {WHITE}; }}
            .page-border {{ border: 4px solid {BLACK}; padding: 25px; box-sizing: border-box; }}
            .header-container {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid {OMAHA_RED}; padding-bottom: 10px; margin-bottom: 15px; }}
            h2 {{ text-align: center; margin: 0; font-size: 20px; text-transform: uppercase; letter-spacing: 1px; }}
            .section-title {{ text-align: center; text-transform: uppercase; font-size: 16px; margin-top: 15px; margin-bottom: 5px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; text-align: center; font-size: 12px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: {BLACK}; border-bottom: 3px solid {OMAHA_RED}; }}
            .header-red {{ color: {OMAHA_RED}; }}
            .header-white {{ color: {WHITE}; }}
            .splits-table tr:nth-child(even) {{ background-color: {LIGHT_GRAY}; }}
            .plot-container {{ display: flex; justify-content: center; margin-top: 10px; }}
            .grid-table {{ border: none; box-shadow: none; width: 100%; margin-bottom: 5px; table-layout: fixed; }}
            .grid-table td {{ border: none; padding: 2px; text-align: center; vertical-align: middle; }}
            .pitcher-view-text {{ text-align: center; color: #A9A9A9; font-size: 11px; font-style: italic; margin-top: 0px; }}
            @media print {{
                @page {{ margin: 10mm; }}
            }}
        </style>
    </head>
    <body>
        <div class="page-border">
            <div class="header-container">
                <div>{img_tag}</div>
                <h2>{date_str} {pitcher} Post Outing Report</h2>
                <div>{img_tag}</div>
            </div>
            
            <div class="section-title">SPLITS PERFORMANCE</div>
            {splits_html}
            
            <div class="section-title">ARSENAL PERFORMANCE</div>
            {arsenal_html}
            
            <div class="section-title">PITCH MOVEMENT PLOT</div>
            <div class="plot-container">
                {movement_plot_html}
            </div>
            
            <div class="section-title">PITCH LOCATION PLOTS</div>
            <table class="grid-table">
                <tr>
                    <td>{plot_pre2k}</td>
                    <td>{plot_2k}</td>
                    <td>{plot_whiff}</td>
                    <td>{plot_damage}</td>
                </tr>
            </table>
            <div class="pitcher-view-text">*All location plots are displayed from a pitcher's view.</div>
        </div>
    </body>
    </html>
    """
    return html

def create_location_plot(plot_df, title):
    fig = go.Figure()
    
    # Strike Zone Shape
    fig.add_shape(type="rect",
        x0=-0.8, y0=1.575, x1=0.8, y1=3.575,
        line=dict(color=BLACK, width=2),
        fillcolor="gray", opacity=0.3,
        layer="below"
    )
    
    # Home Plate Shape (Pitcher's View)
    fig.add_shape(type="path",
        path="M -0.71 0.25 L 0.71 0.25 L 0.71 0.1 L 0 0 L -0.71 0.1 Z",
        fillcolor=WHITE, line=dict(color=BLACK, width=2),
        layer="below"
    )
    
    if 'TaggedPitchType' in plot_df.columns and 'PlateLocSide' in plot_df.columns and 'PlateLocHeight' in plot_df.columns:
        for pt in plot_df['TaggedPitchType'].dropna().unique():
            pt_df = plot_df[plot_df['TaggedPitchType'] == pt].copy()
            if pt_df.empty: continue
            
            abbr, bg_color, text_color = PITCH_DICT.get(pt, (pt, WHITE, BLACK))
            
            hover_text = pt_df.apply(lambda row: 
                f"<b>{abbr}</b><br>"
                f"Velo: {format_val(row.get('RelSpeed'))} mph<br>"
                f"IVB: {format_val(row.get('InducedVertBreak'))} in<br>"
                f"HB: {format_val(row.get('HorzBreak'))} in<br>"
                f"VAA: {format_val(row.get('VertApprAngle'))}°<br>"
                f"Call: {row.get('PitchCall', '-')}<br>"
                f"Exit Speed: {format_val(row.get('ExitSpeed'))} mph", axis=1)
            
            fig.add_trace(go.Scatter(
                x=pt_df['PlateLocSide'],
                y=pt_df['PlateLocHeight'],
                mode='markers',
                name=abbr,
                marker=dict(
                    size=8,
                    color=bg_color,
                    line=dict(width=1, color=BLACK)
                ),
                text=hover_text,
                hoverinfo='text'
            ))

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14, color=BLACK, family="Helvetica Neue, Arial, sans-serif")),
        xaxis=dict(title="", range=[2.5, -2.5], zeroline=False, showticklabels=False),
        yaxis=dict(title="", range=[-0.2, 5.0], zeroline=False, showticklabels=False),
        width=160, height=280,  # Taller, narrower aspect ratio
        plot_bgcolor=WHITE,
        showlegend=False,
        margin=dict(l=5, r=5, t=30, b=5), # Very little gaps
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Adds the plot border
    fig.update_xaxes(showline=True, linewidth=2, linecolor=BLACK, mirror=True)
    fig.update_yaxes(showline=True, linewidth=2, linecolor=BLACK, mirror=True)
    
    return fig

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
            st.markdown("<div class='section-title'>SPLITS PERFORMANCE</div>", unsafe_allow_html=True)
            
            def calc_splits(data, name):
                if data.empty:
                    return f"<tr><td><b>{name}</b></td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0%</td><td>0%</td></tr>"
                
                data['PA_ID'] = data['Inning'].astype(str) + "_" + data['PAofInning'].astype(str)
                batters_faced = data['PA_ID'].nunique()
                
                pitches = len(data)
                k = len(data[data['KorBB'] == 'Strikeout'])
                free = len(data[(data['PitchCall'] == 'HitByPitch') | (data['KorBB'] == 'Walk')])
                hits = len(data[data['PlayResult'].isin(['Single', 'Double', 'Triple', 'HomeRun'])])
                
                # New FPS% Logic: 0 Balls and 1 Strikes pitches divided by batters faced
                fps_count = len(data[(data['Balls'] == 0) & (data['Strikes'] == 1)])
                fps_pct = f"{(fps_count / batters_faced * 100):.1f}%" if batters_faced > 0 else "0%"
                
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
            st.markdown("<div class='section-title'>ARSENAL PERFORMANCE</div>", unsafe_allow_html=True)
            
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
                    
                    row_html = f'<tr style="background-color: {bg_color}; color: {text_color}; border-bottom: 2px solid #FFFFFF;"><td><b>{abbr}</b></td><td>{usage}</td><td>{zone_pct}</td><td>{whiff_pct}</td><td>{velo_str}</td><td>{spin_str}</td><td>{ivb}</td><td>{hb}</td><td>{vaa}</td></tr>'
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
<th><span class="header-white">IVB</span></th>
<th><span class="header-white">HB</span></th>
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
            
            # --- MOVEMENT PLOT (PLOTLY) ---
            st.markdown("<div class='section-title'>PITCH MOVEMENT PLOT</div>", unsafe_allow_html=True)
            
            fig_mov = go.Figure()
            fig_mov.add_hline(y=0, line_dash="dash", line_color=BLACK, opacity=0.4)
            fig_mov.add_vline(x=0, line_dash="dash", line_color=BLACK, opacity=0.4)

            if 'TaggedPitchType' in df.columns and 'HorzBreak' in df.columns and 'InducedVertBreak' in df.columns:
                for pt in df['TaggedPitchType'].dropna().unique():
                    pt_df = df[df['TaggedPitchType'] == pt].copy()
                    if pt_df.empty: continue
                    
                    abbr, bg_color, text_color = PITCH_DICT.get(pt, (pt, WHITE, BLACK))
                    
                    hover_text = pt_df.apply(lambda row: 
                        f"<b>{abbr}</b><br>"
                        f"Velo: {format_val(row.get('RelSpeed'))} mph<br>"
                        f"IVB: {format_val(row.get('InducedVertBreak'))} in<br>"
                        f"HB: {format_val(row.get('HorzBreak'))} in<br>"
                        f"VAA: {format_val(row.get('VertApprAngle'))}°<br>"
                        f"Call: {row.get('PitchCall', '-')}", axis=1)
                    
                    fig_mov.add_trace(go.Scatter(
                        x=pt_df['HorzBreak'],
                        y=pt_df['InducedVertBreak'],
                        mode='markers',
                        name=abbr,
                        marker=dict(size=10, color=bg_color, line=dict(width=1, color=BLACK)),
                        text=hover_text,
                        hoverinfo='text'
                    ))

            fig_mov.update_layout(
                xaxis=dict(title="Horizontal Break (in)", range=[-30, 30], zeroline=False),
                yaxis=dict(title="Induced Vertical Break (in)", range=[-30, 30], zeroline=False),
                width=400, height=400,
                plot_bgcolor=WHITE,
                legend_title_text='Pitch Type',
                margin=dict(l=40, r=40, t=20, b=40),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Adds the plot border
            fig_mov.update_xaxes(showline=True, linewidth=2, linecolor=BLACK, mirror=True)
            fig_mov.update_yaxes(showline=True, linewidth=2, linecolor=BLACK, mirror=True)

            col_plot1, col_plot2, col_plot3 = st.columns([1, 2, 1])
            with col_plot2:
                st.plotly_chart(fig_mov, use_container_width=True)

            plotly_html_mov = fig_mov.to_html(full_html=False, include_plotlyjs='cdn')
            
            st.markdown("---")
            
            # --- LOCATION PLOTS ---
            st.markdown("<div class='section-title'>PITCH LOCATION PLOTS</div>", unsafe_allow_html=True)
            
            # Data subsets
            df_pre2k = df[df['Strikes'].fillna(0) < 2]
            df_2k = df[df['Strikes'] == 2]
            df_whiff = df[df['PitchCall'] == 'StrikeSwinging']
            
            damage_results = ['Single', 'Double', 'Triple', 'HomeRun']
            df_damage = df[
                (df['PlayResult'].isin(damage_results)) & 
                (df['ExitSpeed'].fillna(0) > 96) & 
                (df['Angle'].fillna(0) >= 15) & 
                (df['Angle'].fillna(0) <= 25)
            ]
            
            fig_pre2k = create_location_plot(df_pre2k, "Pre 2K")
            fig_2k = create_location_plot(df_2k, "2K")
            fig_whiff = create_location_plot(df_whiff, "Whiff")
            fig_damage = create_location_plot(df_damage, "Damage")
            
            # Tightly spaced 4 columns for Dashboard
            col_loc1, col_loc2, col_loc3, col_loc4 = st.columns(4, gap="small")
            with col_loc1: st.plotly_chart(fig_pre2k, use_container_width=True)
            with col_loc2: st.plotly_chart(fig_2k, use_container_width=True)
            with col_loc3: st.plotly_chart(fig_whiff, use_container_width=True)
            with col_loc4: st.plotly_chart(fig_damage, use_container_width=True)
                
            st.markdown("<div class='pitcher-view-text'>*All location plots are displayed from a pitcher's view.</div>", unsafe_allow_html=True)
            
            plotly_html_pre2k = fig_pre2k.to_html(full_html=False, include_plotlyjs=False)
            plotly_html_2k = fig_2k.to_html(full_html=False, include_plotlyjs=False)
            plotly_html_whiff = fig_whiff.to_html(full_html=False, include_plotlyjs=False)
            plotly_html_damage = fig_damage.to_html(full_html=False, include_plotlyjs=False)
            
            # --- PDF / PRINT EXPORT ---
            st.markdown("<br>", unsafe_allow_html=True)
            
            report_html = generate_html_report(
                date_str, selected_pitcher, splits_html_full, arsenal_html_full, 
                plotly_html_mov, plotly_html_pre2k, plotly_html_2k, plotly_html_whiff, plotly_html_damage
            )
            b64_html = base64.b64encode(report_html.encode('utf-8')).decode()
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                href = f'<a href="data:text/html;base64,{b64_html}" download="{title_str}.html" class="download-btn" style="width: 100%;">📥 Download Report (Open & Print as PDF)</a>'
                st.markdown(href, unsafe_allow_html=True)
