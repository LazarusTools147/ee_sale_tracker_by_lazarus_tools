import streamlit as st

def inject_global_css():
    """Injects a premium, modern fintech dark/neutral theme with responsive adjustments."""
    st.markdown("""
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, sans-serif;
        }
        [data-testid="stSidebar"] {
            background-color: #111625 !important;
            padding-top: 10px;
        }
        .kpi-card {
            background: #1e2433;
            border: 1px solid #2e374d;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
        }
        .kpi-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #8a99ad;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #ffffff;
            margin: 4px 0;
        }
        .kpi-progress {
            font-size: 0.9rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 8px;
        }
        .progress-green { background-color: rgba(16, 185, 129, 0.2); color: #10b981; }
        .progress-yellow { background-color: rgba(245, 158, 11, 0.2); color: #f59e0b; }
        .progress-red { background-color: rgba(239, 68, 68, 0.2); color: #ef4444; }
        .kpi-meta {
            font-size: 0.85rem;
            color: #a0aec0;
            line-height: 1.5;
        }
        .kpi-pace {
            font-weight: 600;
            color: #6366f1;
        }
        </style>
    """, unsafe_allow_html=True)

def render_logo(location: str = "sidebar"):
    """Renders the official Lazarus Tools 'Upward Maverick' geometric logo asset via inline SVG."""
    logo_svg = """
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
        <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M25 20V75H70" stroke="#00d2ff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M45 40H80M62.5 40V65" stroke="#0072ff" stroke-width="8" stroke-linecap="round"/>
            <path d="M40 75L78 37" stroke="#00d2ff" stroke-width="10" stroke-linecap="round"/>
            <path d="M60 35H80V55" stroke="#00d2ff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div>
            <span style="font-family: 'Inter', sans-serif; font-weight: 800; font-size: 1.3rem; color: #ffffff; letter-spacing: 1px;">LAZARUS</span>
            <span style="font-family: 'Inter', sans-serif; font-weight: 300; font-size: 1.3rem; color: #00d2ff; letter-spacing: 1px;">TOOLS</span>
        </div>
    </div>
    """
    if location == "login":
        st.markdown(f"<div style='display: flex; justify-content: center; width: 100%; margin-bottom: 10px;'>{logo_svg}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(logo_svg, unsafe_allow_html=True)

def render_kpi_block(label: str, actual: int, target: int, shifts_left: int):
    """Generates a premium HTML/CSS dashboard card with dynamic target-to-pace math and custom color-coding."""
    target_val = float(target)
    actual_val = int(actual)
    remaining = max(0, int(target_val - actual_val))
    percentage = (actual_val / target_val * 100) if target_val > 0 else (100.0 if actual_val > 0 else 0.0)
    pace = remaining / max(1, shifts_left)
    if percentage >= 100:
        color_class = "progress-green"
        status_text = "🎯 Target Smashed"
    elif percentage >= 75:
        color_class = "progress-yellow"
        status_text = "⚡ On Track"
    else:
        color_class = "progress-red"
        status_text = "🚩 Pacing Behind"
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{label}</div>
        <div class="kpi-value">{actual_val} <span style="font-size: 1rem; color: #718096; font-weight: 400;">/ {int(target_val)}</span></div>
        <div class="kpi-progress {color_class}">{percentage:.1f}% • {status_text}</div>
        <div class="kpi-meta">
            📉 <b>Remaining:</b> {remaining} Left<br>
            🚀 <b>Required Pace:</b> <span class="kpi-pace">{pace:.1f}</span> / shift
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)