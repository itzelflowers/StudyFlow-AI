"""
Custom Gradio theme for StudyFlow AI.
Premium dark theme with vibrant accent colors.
"""

import gradio as gr


def get_theme() -> gr.Theme:
    """Create the StudyFlow AI custom theme."""
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.indigo,
        secondary_hue=gr.themes.colors.purple,
        neutral_hue=gr.themes.colors.slate,
        font=[
            gr.themes.GoogleFont("Inter"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif",
        ],
        font_mono=[
            gr.themes.GoogleFont("JetBrains Mono"),
            "ui-monospace",
            "monospace",
        ],
    )

    return theme


CUSTOM_CSS = """
/* ─── Global Overrides ──────────────────────────────────────────── */

.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto;
}

/* ─── Header ────────────────────────────────────────────────────── */

.app-header {
    text-align: center;
    padding: 2rem 1rem;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
    position: relative;
    overflow: hidden;
}

.app-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
    animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
}

.app-header h1 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    position: relative;
    z-index: 1;
    letter-spacing: -0.02em;
}

.app-header p {
    font-size: 1.1rem;
    opacity: 0.9;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

/* ─── Cards ─────────────────────────────────────────────────────── */

.milestone-card {
    background: linear-gradient(145deg, #f8fafc, #f1f5f9);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.milestone-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(79, 70, 229, 0.12);
    border-color: #a5b4fc;
}

.milestone-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}

.milestone-number {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
    flex-shrink: 0;
}

.milestone-title {
    font-weight: 700;
    font-size: 1.1rem;
    color: #1e293b;
}

.milestone-week {
    font-size: 0.8rem;
    color: #64748b;
    background: #e2e8f0;
    padding: 2px 10px;
    border-radius: 99px;
    margin-left: auto;
}

.milestone-description {
    color: #475569;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* ─── Tasks ─────────────────────────────────────────────────────── */

.task-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
    border-radius: 8px;
    background: white;
    border: 1px solid #e2e8f0;
    margin-bottom: 0.5rem;
    transition: all 0.2s ease;
}

.task-item:hover {
    background: #f8fafc;
    border-color: #c7d2fe;
}

.task-checkbox {
    margin-top: 2px;
}

.task-title {
    font-weight: 600;
    color: #1e293b;
}

.task-meta {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 2px;
}

.task-completed .task-title {
    text-decoration: line-through;
    color: #94a3b8;
}

/* ─── Resource Cards ────────────────────────────────────────────── */

.resource-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    background: white;
    border: 1px solid #e2e8f0;
    margin-bottom: 0.5rem;
    transition: all 0.2s ease;
}

.resource-item:hover {
    background: #faf5ff;
    border-color: #c4b5fd;
}

.resource-icon {
    font-size: 1.5rem;
}

.resource-title {
    font-weight: 600;
    color: #4f46e5;
}

.resource-type {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #7c3aed;
    background: #ede9fe;
    padding: 2px 8px;
    border-radius: 4px;
}

/* ─── Progress Bar ──────────────────────────────────────────────── */

.progress-container {
    background: #f1f5f9;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.progress-bar-wrapper {
    background: #e2e8f0;
    border-radius: 99px;
    height: 12px;
    overflow: hidden;
    margin: 0.75rem 0;
}

.progress-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #4f46e5, #7c3aed, #a855f7);
    transition: width 0.5s ease;
}

.progress-stats {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #64748b;
}

/* ─── Coaching Message ──────────────────────────────────────────── */

.coaching-message {
    background: linear-gradient(145deg, #ede9fe, #e0e7ff);
    border: 1px solid #c7d2fe;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 1rem 0;
    font-size: 0.95rem;
    color: #3730a3;
    line-height: 1.6;
}

.coaching-message::before {
    content: '🧠 ';
    font-size: 1.2rem;
}

/* ─── Tabs Enhancement ──────────────────────────────────────────── */

.tab-nav button {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1.5rem !important;
}

/* ─── Status Badges ─────────────────────────────────────────────── */

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-beginner { background: #dcfce7; color: #166534; }
.badge-intermediate { background: #fef3c7; color: #92400e; }
.badge-advanced { background: #fce7f3; color: #9d174d; }

/* ─── Animations ────────────────────────────────────────────────── */

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-in {
    animation: fadeInUp 0.5s ease forwards;
}

/* ─── Loading State ─────────────────────────────────────────────── */

.generating-message {
    text-align: center;
    padding: 2rem;
    color: #7c3aed;
    font-size: 1.1rem;
}

.generating-message .spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #e2e8f0;
    border-top-color: #7c3aed;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 0.5rem;
    vertical-align: middle;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
"""
