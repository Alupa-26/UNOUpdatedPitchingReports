import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from datetime import datetime
import plotly.graph_objects as go
import json

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
                         plot_pre2k, plot_2k, plot_whiff, plot_damage, json_data):
    logo_b64 = get_base64_image("Logo.png")
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height: 50px;">' if logo_b64 else ''
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gasoline Alley Team Report</title>
        <!-- Tailwind CSS -->
        <script src="https://cdn.tailwindcss.com"></script>
        <!-- Google Fonts -->
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Teko:wght@500;700&display=swap" rel="stylesheet">
        
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        fontFamily: {{
                            sans: ['Inter', 'sans-serif'],
                            display: ['Teko', 'sans-serif'],
                        }},
                        colors: {{
                            brand: {{
                                dark: '#0B0F19',
                                panel: 'rgba(30, 41, 59, 0.6)',
                                border: 'rgba(255, 255, 255, 0.1)',
                                accent: '#E53E3E',
                            }}
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            /* --- PAGE 1 STYLES --- */
            body {{ margin: 0; padding: 0; background-color: #FFFFFF; }}
            .page-1-wrapper {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 20px; background-color: #FFFFFF; color: #000000; min-height: 100vh; }}
            .page-border {{ border: 4px solid #000000; padding: 25px; box-sizing: border-box; }}
            .header-container {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #D71920; padding-bottom: 10px; margin-bottom: 15px; }}
            h2.p1-title {{ text-align: center; margin: 0; font-size: 20px; text-transform: uppercase; letter-spacing: 1px; }}
            .section-title {{ text-align: center; text-transform: uppercase; font-size: 16px; margin-top: 15px; margin-bottom: 5px; font-weight: bold; }}
            table.p1-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; text-align: center; font-size: 12px; }}
            table.p1-table th, table.p1-table td {{ border: 1px solid #ddd; padding: 8px; }}
            table.p1-table th {{ background-color: #000000; border-bottom: 3px solid #D71920; }}
            .header-red {{ color: #D71920; }}
            .header-white {{ color: #FFFFFF; }}
            table.p1-table tr:nth-child(even) {{ background-color: #F0F0F0; }}
            .plot-container {{ display: flex; justify-content: center; margin-top: 10px; }}
            .grid-table {{ border: none; box-shadow: none; width: 90%; margin: 0 auto 5px auto; table-layout: fixed; border-collapse: separate; border-spacing: 10px 0; }}
            .grid-table td {{ border: none; padding: 0; text-align: center; vertical-align: middle; }}
            .pitcher-view-text {{ text-align: center; color: #A9A9A9; font-size: 11px; font-style: italic; margin-top: 10px; }}

            /* --- PAGE 2 STYLES --- */
            .page-2-wrapper {{ background-color: #0B0F19; color: #ffffff; min-height: 100vh; padding: 24px; font-family: 'Inter', sans-serif; }}
            .glass-panel {{ background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }}
            .metric-box {{ display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 1rem; text-align: center; transition: all 0.3s ease; }}
            .goal-pass {{ border-left: 4px solid #22c55e; box-shadow: inset 2px 0 10px rgba(34, 197, 94, 0.1); }}
            .goal-fail {{ border-left: 4px solid #ef4444; box-shadow: inset 2px 0 10px rgba(239, 68, 68, 0.1); }}
            .text-pass {{ color: #4ade80; }}
            .text-fail {{ color: #f87171; }}
            .progress-ring__circle {{ transform: rotate(-90deg); transform-origin: 50% 50%; }}
            table.p2-table {{ border-collapse: separate; border-spacing: 0; width: 100%; }}
            table.p2-table th, table.p2-table td {{ padding: 0.75rem 1rem; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); }}
            table.p2-table th {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: 600; }}
            table.p2-table tr:last-child td {{ border-bottom: none; }}

            /* --- Strict Print CSS --- */
            @media print {{
                * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }}
                @page {{ margin: 10mm; }}
                .no-print {{ display: none !important; }}
                .page-2-wrapper {{ background-color: #0B0F19 !important; }}
                .glass-panel {{ background-color: #1e293b !important; border: 1px solid #334155 !important; box-shadow: none !important; }}
                .metric-box {{ background-color: #1e293b !important; }}
                .goal-pass {{ border-left: 4px solid #22c55e !important; }}
                .goal-fail {{ border-left: 4px solid #ef4444 !important; }}
                .text-pass {{ color: #4ade80 !important; }}
                .text-fail {{ color: #f87171 !important; }}
                .grid {{ display: grid !important; }}
                .break-inside-avoid {{ break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        
        <!-- ==================== PAGE 1: DASHBOARD REPORT ==================== -->
        <div class="page-1-wrapper">
            <div class="page-border">
                <div class="header-container">
                    <div>{img_tag}</div>
                    <h2 class="p1-title">{date_str} {pitcher} Post Outing Report</h2>
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
        </div>

        <!-- ==================== PAGE BREAK ==================== -->
        <div style="page-break-before: always;"></div>

        <!-- ==================== PAGE 2: GASOLINE ALLEY REPORT CARD ==================== -->
        <div class="page-2-wrapper font-sans">
            <div id="reportContainer" class="max-w-7xl mx-auto">
                <!-- Header Section -->
                <div class="relative flex justify-center items-center mb-10 mt-4">
                    <div class="absolute left-0 top-0 glass-panel px-4 py-2 text-sm text-gray-300">
                        <p>Date: <span id="lblDate" class="font-bold text-white"></span></p>
                        <p>Pitcher: <span id="lblOpponent" class="font-bold text-white"></span></p>
                    </div>
                    
                    <div class="text-center">
                        <h1 class="font-display text-5xl md:text-7xl font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-gray-100 to-gray-500 uppercase leading-none">Gasoline Alley</h1>
                        <h2 class="font-display text-2xl md:text-3xl tracking-[0.2em] text-red-500 mt-1 uppercase">Team Report</h2>
                    </div>
                </div>

                <!-- Top Metrics & Grade Circle -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10 items-center break-inside-avoid">
                    
                    <!-- Left Column Metrics -->
                    <div class="space-y-4">
                        <div class="glass-panel metric-box" id="boxStrikePct">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">Strike %</span>
                            <div class="text-3xl font-bold" id="valStrikePct">--%</div>
                            <span class="text-xs mt-1 font-semibold" id="goalStrikePct">Goal: &ge; 60%</span>
                        </div>
                        <div class="glass-panel metric-box" id="boxFpsPct">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">FPS %</span>
                            <div class="text-3xl font-bold" id="valFpsPct">--%</div>
                            <span class="text-xs mt-1 font-semibold" id="goalFpsPct">Goal: &ge; 60%</span>
                        </div>
                        <div class="glass-panel metric-box" id="boxKZonePct">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">KZone %</span>
                            <div class="text-3xl font-bold" id="valKZonePct">--%</div>
                            <span class="text-xs mt-1 font-semibold" id="goalKZonePct">Goal: &ge; 50%</span>
                        </div>
                        <div class="glass-panel metric-box" id="boxS22Pct">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">S22 %</span>
                            <div class="text-3xl font-bold" id="valS22Pct">--%</div>
                            <span class="text-xs mt-1 font-semibold" id="goalS22Pct">Goal: &ge; 60%</span>
                        </div>
                    </div>

                    <!-- Center Grade Circle -->
                    <div class="flex justify-center items-center relative">
                        <svg class="w-64 h-64" viewBox="0 0 120 120">
                            <!-- Background circle -->
                            <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="8"></circle>
                            <!-- Progress circle -->
                            <circle id="gradeCirclePath" class="progress-ring__circle" cx="60" cy="60" r="54" fill="none" stroke="#22c55e" stroke-width="8" stroke-dasharray="339.292" stroke-dashoffset="339.292" stroke-linecap="round"></circle>
                        </svg>
                        <div class="absolute inset-0 flex flex-col justify-center items-center text-center">
                            <div id="lblLetterGrade" class="font-display text-7xl font-bold text-white leading-none mb-1">--</div>
                            <div id="lblGoalsHit" class="text-sm font-semibold text-gray-400 tracking-wide">(-/7 Goals Hit)</div>
                        </div>
                    </div>

                    <!-- Right Column Metrics -->
                    <div class="space-y-4">
                        <div class="glass-panel metric-box" id="boxWhiffPct">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">WHIFF %</span>
                            <div class="text-3xl font-bold" id="valWhiffPct">--%</div>
                            <span class="text-xs mt-1 font-semibold" id="goalWhiffPct">Goal: &ge; 25%</span>
                        </div>
                        <div class="glass-panel metric-box" id="boxChasePct">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">Chase %</span>
                            <div class="text-3xl font-bold" id="valChasePct">--%</div>
                            <span class="text-xs mt-1 font-semibold" id="goalChasePct">Goal: &ge; 25%</span>
                        </div>
                        <div class="glass-panel metric-box" id="boxFreebies">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">Freebies</span>
                            <div class="text-3xl font-bold" id="valFreebies">--</div>
                            <span class="text-xs mt-1 font-semibold" id="goalFreebies">Goal: &le; 5</span>
                        </div>
                        <div class="glass-panel metric-box">
                            <span class="text-xs text-gray-400 uppercase tracking-wider mb-1">Ks</span>
                            <div class="text-3xl font-bold" id="valKs">--</div>
                            <span class="text-xs mt-1 font-semibold text-gray-500">Total</span>
                        </div>
                    </div>
                </div>

                <!-- Batted Ball Table -->
                <div class="mb-10 break-inside-avoid">
                    <h3 class="text-sm font-bold uppercase tracking-widest text-gray-400 mb-3 ml-1">Batted Ball Table</h3>
                    <div class="glass-panel overflow-hidden">
                        <div class="grid grid-cols-2 md:grid-cols-6 divide-x divide-y md:divide-y-0 divide-white/10 text-center">
                            <div class="p-4">
                                <div class="text-xs text-gray-400 uppercase mb-1">Hits</div>
                                <div class="text-2xl font-bold" id="bbHits">--</div>
                            </div>
                            <div class="p-4">
                                <div class="text-xs text-gray-400 uppercase mb-1">XBH</div>
                                <div class="text-2xl font-bold" id="bbXBH">--</div>
                            </div>
                            <div class="p-4">
                                <div class="text-xs text-gray-400 uppercase mb-1">HR</div>
                                <div class="text-2xl font-bold" id="bbHR">--</div>
                            </div>
                            <div class="p-4">
                                <div class="text-xs text-gray-400 uppercase mb-1">Damage (>96)</div>
                                <div class="text-2xl font-bold" id="bbDamage">--</div>
                            </div>
                            <div class="p-4">
                                <div class="text-xs text-gray-400 uppercase mb-1">Weak (<80)</div>
                                <div class="text-2xl font-bold" id="bbWeak">--</div>
                            </div>
                            <div class="p-4">
                                <div class="text-xs text-gray-400 uppercase mb-1">AVG EV</div>
                                <div class="text-2xl font-bold" id="bbAvgEv">--</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- B-E-A Table -->
                <div class="mb-10 break-inside-avoid">
                    <h3 class="text-sm font-bold uppercase tracking-widest text-gray-400 mb-3 ml-1">B-E-A Table</h3>
                    <div class="glass-panel overflow-x-auto">
                        <table class="p2-table min-w-full">
                            <thead>
                                <tr>
                                    <th class="text-left">State</th>
                                    <th>% of PAs</th>
                                    <th>BB</th>
                                    <th>K</th>
                                    <th>H</th>
                                    <th>EV</th>
                                    <th>OPS</th>
                                </tr>
                            </thead>
                            <tbody id="beaTableBody">
                                <!-- Populated by JS -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Bottom Right AVG Velo -->
                <div class="flex justify-end break-inside-avoid pb-10">
                    <div class="glass-panel p-4 flex items-center space-x-4 border-l-4 border-l-blue-500">
                        <div class="text-right">
                            <div class="text-xs text-gray-400 uppercase tracking-wider">AVG Velo</div>
                            <div class="text-[0.65rem] text-gray-500">(FB & SI)</div>
                        </div>
                        <div class="text-4xl font-display font-bold text-white" id="valAvgVelo">--</div>
                    </div>
                </div>

            </div>
        </div>

        <script>
            function isMLBStrikeZone(h, s) {{
                h = parseFloat(h);
                s = parseFloat(s);
                if (isNaN(h) || isNaN(s)) return false;
                return (h >= 1.5 && h <= 3.5 && s >= -0.83 && s <= 0.83);
            }}

            function setGoalStyling(boxId, valId, goalId, isPass) {{
                const box = document.getElementById(boxId);
                const val = document.getElementById(valId);
                const goal = document.getElementById(goalId);
                
                box.classList.remove('goal-pass', 'goal-fail');
                val.classList.remove('text-pass', 'text-fail');
                goal.classList.remove('text-pass', 'text-fail');

                if (isPass) {{
                    box.classList.add('goal-pass');
                    val.classList.add('text-pass');
                    goal.classList.add('text-pass');
                }} else {{
                    box.classList.add('goal-fail');
                    val.classList.add('text-fail');
                    goal.classList.add('text-fail');
                }}
            }}

            function processData(unoPitches) {{
                if (unoPitches.length === 0) return;

                document.getElementById('lblDate').innerText = '{date_str}';
                document.getElementById('lblOpponent').innerText = '{pitcher}';

                let goalsHit = 0;
                const totalGoals = 7;

                const totalPitches = unoPitches.length;
                const strikeOutcomes = ['StrikeCalled', 'StrikeSwinging', 'FoulBallFieldable', 'FoulBallNotFieldable', 'InPlay'];
                const swings = ['StrikeSwinging', 'FoulBallFieldable', 'FoulBallNotFieldable', 'InPlay'];
                const hitOutcomes = ['Single', 'Double', 'Triple', 'HomeRun'];
                const xbhOutcomes = ['Double', 'Triple', 'HomeRun'];

                // --- Group into Plate Appearances ---
                let pas = [];
                let currentPA = {{ pitches: [], batter: null, inning: null }};

                unoPitches.forEach(row => {{
                    if (row.Batter !== currentPA.batter || row.Inning !== currentPA.inning) {{
                        if (currentPA.pitches.length > 0) pas.push(currentPA);
                        currentPA = {{ pitches: [], batter: row.Batter, inning: row.Inning, playResult: '', korBB: '' }};
                    }}
                    currentPA.pitches.push(row);
                    if (row.PlayResult) currentPA.playResult = row.PlayResult;
                    if (row.KorBB) currentPA.korBB = row.KorBB;
                }});
                if (currentPA.pitches.length > 0) pas.push(currentPA);

                const totalBattersFaced = pas.length;

                // 1. Strike % (*60%)
                let strikePitches = unoPitches.filter(p => strikeOutcomes.includes(p.PitchCall)).length;
                let strikePct = totalPitches > 0 ? (strikePitches / totalPitches) * 100 : 0;
                document.getElementById('valStrikePct').innerText = strikePct.toFixed(1) + '%';
                let passStrike = strikePct >= 60;
                if (passStrike) goalsHit++;
                setGoalStyling('boxStrikePct', 'valStrikePct', 'goalStrikePct', passStrike);

                // 2. FPS % (*60%) - Explicit logic using PitchofPA == 1 and dividing by totalBattersFaced
                let fpsStrikes = unoPitches.filter(p => p.PitchofPA == 1 && strikeOutcomes.includes(p.PitchCall)).length;
                let fpsPct = totalBattersFaced > 0 ? (fpsStrikes / totalBattersFaced) * 100 : 0;
                document.getElementById('valFpsPct').innerText = fpsPct.toFixed(0) + '%';
                let passFps = fpsPct >= 60;
                if (passFps) goalsHit++;
                setGoalStyling('boxFpsPct', 'valFpsPct', 'goalFpsPct', passFps);

                // 3. KZone % (*50%)
                let inZoneCount = unoPitches.filter(p => isMLBStrikeZone(p.PlateLocHeight, p.PlateLocSide)).length;
                let kZonePct = totalPitches > 0 ? (inZoneCount / totalPitches) * 100 : 0;
                document.getElementById('valKZonePct').innerText = kZonePct.toFixed(1) + '%';
                let passKZone = kZonePct >= 50;
                if (passKZone) goalsHit++;
                setGoalStyling('boxKZonePct', 'valKZonePct', 'goalKZonePct', passKZone);

                // 4. WHIFF % (*25%)
                let whiffNum = unoPitches.filter(p => p.PitchCall === 'StrikeSwinging').length;
                let whiffDenom = unoPitches.filter(p => swings.includes(p.PitchCall)).length;
                let whiffPct = whiffDenom > 0 ? (whiffNum / whiffDenom) * 100 : 0;
                document.getElementById('valWhiffPct').innerText = whiffPct.toFixed(1) + '%';
                let passWhiff = whiffPct >= 25;
                if (passWhiff) goalsHit++;
                setGoalStyling('boxWhiffPct', 'valWhiffPct', 'goalWhiffPct', passWhiff);

                // 5. Chase % (*25%)
                let oZonPitches = unoPitches.filter(p => !isMLBStrikeZone(p.PlateLocHeight, p.PlateLocSide));
                let oZoneSwings = oZonPitches.filter(p => swings.includes(p.PitchCall)).length;
                let chasePct = oZonPitches.length > 0 ? (oZoneSwings / oZonPitches.length) * 100 : 0;
                document.getElementById('valChasePct').innerText = chasePct.toFixed(1) + '%';
                let passChase = chasePct >= 25;
                if (passChase) goalsHit++;
                setGoalStyling('boxChasePct', 'valChasePct', 'goalChasePct', passChase);

                // 6. Freebies (*<=5)
                let freebies = unoPitches.filter(p => p.KorBB === 'Walk' || p.PitchCall === 'HitByPitch').length;
                document.getElementById('valFreebies').innerText = freebies;
                let passFreebies = freebies <= 5;
                if (passFreebies) goalsHit++;
                setGoalStyling('boxFreebies', 'valFreebies', 'goalFreebies', passFreebies);

                // Ks (Total)
                let totalKs = unoPitches.filter(p => p.KorBB === 'Strikeout').length;
                document.getElementById('valKs').innerText = totalKs;

                // 7. S22 % (*60%)
                let s22Count = pas.filter(pa => {{
                    return pa.pitches.some(p => (p.Balls == 0 && p.Strikes == 2) || (p.Balls == 1 && p.Strikes == 2));
                }}).length;
                let s22Pct = totalBattersFaced > 0 ? (s22Count / totalBattersFaced) * 100 : 0;
                document.getElementById('valS22Pct').innerText = s22Pct.toFixed(1) + '%';
                let passS22 = s22Pct >= 60;
                if (passS22) goalsHit++;
                setGoalStyling('boxS22Pct', 'valS22Pct', 'goalS22Pct', passS22);

                // --- Batted Ball Table ---
                let hits = unoPitches.filter(p => hitOutcomes.includes(p.PlayResult)).length;
                let xbh = unoPitches.filter(p => xbhOutcomes.includes(p.PlayResult)).length;
                let hr = unoPitches.filter(p => p.PlayResult === 'HomeRun').length;
                let damage = unoPitches.filter(p => hitOutcomes.includes(p.PlayResult) && parseFloat(p.ExitSpeed) > 96).length;
                let weak = unoPitches.filter(p => p.PitchCall === 'InPlay' && parseFloat(p.ExitSpeed) < 80).length;
                
                let inPlayEVs = unoPitches.filter(p => p.PitchCall === 'InPlay' && !isNaN(parseFloat(p.ExitSpeed))).map(p => parseFloat(p.ExitSpeed));
                let avgEv = inPlayEVs.length > 0 ? (inPlayEVs.reduce((a,b)=>a+b,0) / inPlayEVs.length).toFixed(1) : 0;

                document.getElementById('bbHits').innerText = hits;
                document.getElementById('bbXBH').innerText = xbh;
                document.getElementById('bbHR').innerText = hr;
                document.getElementById('bbDamage').innerText = damage;
                document.getElementById('bbWeak').innerText = weak;
                document.getElementById('bbAvgEv').innerText = avgEv;

                // --- B-E-A Logic ---
                let early = {{ label: 'Early', pa: 0, bb: 0, k: 0, h: 0, ev_sum: 0, ev_count: 0, ab: 0, tb: 0, obp_num: 0 }};
                let ahead = {{ label: 'Ahead', pa: 0, bb: 0, k: 0, h: 0, ev_sum: 0, ev_count: 0, ab: 0, tb: 0, obp_num: 0 }};
                let behind = {{ label: 'Behind', pa: 0, bb: 0, k: 0, h: 0, ev_sum: 0, ev_count: 0, ab: 0, tb: 0, obp_num: 0 }};

                pas.forEach(pa => {{
                    let stateObj = null;
                    let inPlayIdx = pa.pitches.findIndex(p => p.PitchCall === 'InPlay');
                    
                    if (inPlayIdx >= 0 && inPlayIdx <= 2) {{
                        stateObj = early;
                    }} else if (pa.pitches.length > 3) {{
                        let p4 = pa.pitches[3];
                        let b = parseInt(p4.Balls);
                        let s = parseInt(p4.Strikes);
                        if ((b === 2 && s === 1) || (b === 3 && s === 0)) stateObj = behind;
                        else if ((b === 1 && s === 2) || (b === 0 && s === 2)) stateObj = ahead;
                    }} else if (pa.pitches.length === 3 && pa.korBB === 'Strikeout') {{
                        stateObj = ahead;
                    }}

                    if (stateObj) {{
                        stateObj.pa++;
                        if (pa.korBB === 'Walk' || pa.korBB === 'HitByPitch') {{ stateObj.bb++; stateObj.obp_num++; }}
                        if (pa.korBB === 'Strikeout') stateObj.k++;

                        let isHit = hitOutcomes.includes(pa.playResult);
                        if (isHit) {{
                            stateObj.h++;
                            stateObj.obp_num++;
                            if (pa.playResult === 'Single') stateObj.tb += 1;
                            if (pa.playResult === 'Double') stateObj.tb += 2;
                            if (pa.playResult === 'Triple') stateObj.tb += 3;
                            if (pa.playResult === 'HomeRun') stateObj.tb += 4;
                        }}

                        let isOut = ['Out', 'FieldersChoice', 'Error'].includes(pa.playResult) || pa.korBB === 'Strikeout';
                        if (isHit || isOut) stateObj.ab++;

                        let lastP = pa.pitches[pa.pitches.length - 1];
                        if (lastP.PitchCall === 'InPlay' && !isNaN(parseFloat(lastP.ExitSpeed))) {{
                            stateObj.ev_sum += parseFloat(lastP.ExitSpeed);
                            stateObj.ev_count++;
                        }}
                    }}
                }});

                const renderBeaRow = (obj) => {{
                    let pctPA = totalBattersFaced > 0 ? ((obj.pa / totalBattersFaced) * 100).toFixed(1) + '%' : '0%';
                    let avgEV = obj.ev_count > 0 ? (obj.ev_sum / obj.ev_count).toFixed(1) : '0';
                    let obp = obj.pa > 0 ? (obj.obp_num / obj.pa) : 0;
                    let slg = obj.ab > 0 ? (obj.tb / obj.ab) : 0;
                    let ops = (obp + slg).toFixed(3).replace(/^0+/, '');
                    
                    return `
                        <tr class="hover:bg-white/5 transition-colors">
                            <td class="text-left font-semibold text-gray-300 uppercase">${{obj.label}}</td>
                            <td class="font-mono text-gray-400">${{pctPA}}</td>
                            <td class="font-mono text-white">${{obj.bb}}</td>
                            <td class="font-mono text-white">${{obj.k}}</td>
                            <td class="font-mono text-white">${{obj.h}}</td>
                            <td class="font-mono text-white">${{avgEV}}</td>
                            <td class="font-mono text-white">${{ops}}</td>
                        </tr>
                    `;
                }};

                document.getElementById('beaTableBody').innerHTML = renderBeaRow(behind) + renderBeaRow(early) + renderBeaRow(ahead);

                // --- AVG Velo (Fastball & Sinker) ---
                let fbSi = unoPitches.filter(p => p.TaggedPitchType === 'Fastball' || p.TaggedPitchType === 'Sinker' || p.AutoPitchType === 'Fastball' || p.AutoPitchType === 'Sinker');
                let velos = fbSi.map(p => parseFloat(p.RelSpeed)).filter(v => !isNaN(v));
                let avgVelo = velos.length > 0 ? (velos.reduce((a,b)=>a+b,0)/velos.length).toFixed(1) : '--';
                document.getElementById('valAvgVelo').innerText = avgVelo;

                // --- Update Grade Circle ---
                document.getElementById('lblGoalsHit').innerText = `(${{goalsHit}}/${{totalGoals}} Goals Hit)`;
                
                let grade = 'F';
                let circleColor = '#ef4444'; // Red
                if (goalsHit >= 7) {{ grade = 'A+'; circleColor = '#22c55e'; }} // Green
                else if (goalsHit === 6) {{ grade = 'A'; circleColor = '#22c55e'; }}
                else if (goalsHit === 5) {{ grade = 'B'; circleColor = '#eab308'; }} // Yellow
                else if (goalsHit === 4) {{ grade = 'C'; circleColor = '#f97316'; }} // Orange
                else if (goalsHit === 3) {{ grade = 'D'; circleColor = '#f97316'; }}
                
                document.getElementById('lblLetterGrade').innerText = grade;
                
                const circle = document.getElementById('gradeCirclePath');
                const radius = circle.r.baseVal.value;
                const circumference = radius * 2 * Math.PI;
                circle.style.strokeDasharray = `${{circumference}} ${{circumference}}`;
                const offset = circumference - ((goalsHit / totalGoals) * circumference);
                
                circle.style.stroke = circleColor;
                circle.style.strokeDashoffset = offset; // Instant execution to ensure PDF renders correctly without animation wait
            }}

            // Inject Python JSON Data into script exactly as expected
            const reportData = {json_data};
            processData(reportData);
        </script>
    </body>
    </html>
    """
    return html

# --- DASHBOARD STYLING ---
st.markdown(f"""
    <style>
        .report-header {{ text-align: center; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: {BLACK}; margin-top: 20px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1.5px; }}
        .section-title {{ text-align: center; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: {BLACK}; margin-top: 30px; margin-bottom: 10px; font-size: 20px; font-weight: bold; text-transform: uppercase; }}
        .styled-table {{ width: 100%; border-collapse: collapse; margin: 10px 0 25px 0; font-size: 16px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); background-color: {WHITE}; color: {BLACK}; }}
        .styled-table thead tr {{ background-color: {BLACK}; border-bottom: 3px solid {OMAHA_RED}; text-align: center; font-weight: bold; letter-spacing: 1px; }}
        .styled-table th {{ padding: 14px 18px; border: 1px solid #333; text-align: center; }}
        .styled-table td {{ padding: 14px 18px; border: 1px solid #ddd; text-align: center; }}
        .header-red {{ color: {OMAHA_RED}; }}
        .header-white {{ color: {WHITE}; }}
        .splits-table tbody tr:nth-of-type(even) {{ background-color: {LIGHT_GRAY}; }}
        .splits-table tbody tr:last-of-type {{ border-bottom: 3px solid {OMAHA_RED}; }}
        .download-btn {{ display: inline-block; background-color: {OMAHA_RED}; color: {WHITE}; padding: 12px 24px; font-size: 16px; font-weight: bold; text-decoration: none; border-radius: 4px; text-align: center; margin-top: 20px; transition: 0.3s; }}
        .download-btn:hover {{ background-color: {BLACK}; color: {WHITE}; }}
        .pitcher-view-text {{ text-align: center; color: #A9A9A9; font-size: 14px; font-style: italic; margin-top: 15px; margin-bottom: 25px; }}
    </style>
""", unsafe_allow_html=True)


# --- DASHBOARD PLOT HELPER ---
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
        path="M -0.71 0 L 0.71 0 L 0.71 0.15 L 0 0.25 L -0.71 0.15 Z",
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
        xaxis=dict(title="", range=[-2.5, 2.5], zeroline=False, showticklabels=False),
        yaxis=dict(title="", range=[-0.2, 5.0], zeroline=False, showticklabels=False),
        width=200, height=320,  
        plot_bgcolor=WHITE,
        showlegend=False,
        margin=dict(l=5, r=5, t=30, b=5), 
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
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
                    return f"<tr><td><b>{name}</b></td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0% (0/0)</td><td>0%</td></tr>"
                
                data['PA_ID'] = data['Inning'].astype(str) + "_" + data['PAofInning'].astype(str)
                batters_faced = data['PA_ID'].nunique()
                
                pitches = len(data)
                k = len(data[data['KorBB'] == 'Strikeout'])
                free = len(data[(data['PitchCall'] == 'HitByPitch') | (data['KorBB'] == 'Walk')])
                hits = len(data[data['PlayResult'].isin(['Single', 'Double', 'Triple', 'HomeRun'])])
                
                fps_count = len(data[(data['PitchofPA'] == 1) & (data['PitchCall'].isin(['StrikeCalled', 'StrikeSwinging', 'InPlay', 'FoulBallFieldable', 'FoulBallNotFieldable']))])
                fps_pct = f"{(fps_count / batters_faced * 100):.0f}% ({fps_count}/{batters_faced})" if batters_faced > 0 else "0% (0/0)"
                
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
<table class="styled-table splits-table p1-table">
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
<table class="styled-table arsenal-table p1-table">
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
                width=350, height=350,
                plot_bgcolor=WHITE,
                legend_title_text='Pitch Type',
                margin=dict(l=40, r=40, t=20, b=40),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            fig_mov.update_xaxes(showline=True, linewidth=2, linecolor=BLACK, mirror=True)
            fig_mov.update_yaxes(showline=True, linewidth=2, linecolor=BLACK, mirror=True)

            col_plot1, col_plot2, col_plot3 = st.columns([1, 2, 1])
            with col_plot2:
                st.plotly_chart(fig_mov, use_container_width=True)

            plotly_html_mov = fig_mov.to_html(full_html=False, include_plotlyjs='cdn')
            
            st.markdown("---")
            
            # --- LOCATION PLOTS ---
            st.markdown("<div class='section-title'>PITCH LOCATION PLOTS</div>", unsafe_allow_html=True)
            
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
            
            col_spacer1, col_loc1, col_loc2, col_loc3, col_loc4, col_spacer2 = st.columns([1, 3, 3, 3, 3, 1])
            with col_loc1: st.plotly_chart(fig_pre2k, use_container_width=True)
            with col_loc2: st.plotly_chart(fig_2k, use_container_width=True)
            with col_loc3: st.plotly_chart(fig_whiff, use_container_width=True)
            with col_loc4: st.plotly_chart(fig_damage, use_container_width=True)
                
            st.markdown("<div class='pitcher-view-text'>*All location plots are displayed from a pitcher's view.</div>", unsafe_allow_html=True)
            
            plotly_html_pre2k = fig_pre2k.to_html(full_html=False, include_plotlyjs=False)
            plotly_html_2k = fig_2k.to_html(full_html=False, include_plotlyjs=False)
            plotly_html_whiff = fig_whiff.to_html(full_html=False, include_plotlyjs=False)
            plotly_html_damage = fig_damage.to_html(full_html=False, include_plotlyjs=False)
            
            # --- PDF / PRINT EXPORT (Pages 1 & 2) ---
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Serialize DataFrame to JSON for Page 2 Script
            json_data = df.fillna("").to_json(orient="records")
            
            report_html = generate_html_report(
                date_str, selected_pitcher, splits_html_full, arsenal_html_full, 
                plotly_html_mov, plotly_html_pre2k, plotly_html_2k, plotly_html_whiff, plotly_html_damage, json_data
            )
            
            b64_html = base64.b64encode(report_html.encode('utf-8')).decode()
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                href = f'<a href="data:text/html;base64,{b64_html}" download="{title_str}.html" class="download-btn" style="width: 100%;">📥 Download Full 2-Page Report (Open & Print as PDF)</a>'
                st.markdown(href, unsafe_allow_html=True)
