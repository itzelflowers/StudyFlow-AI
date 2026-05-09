"""
Onboarding component — Goal input and diagnostic quiz.
"""

from __future__ import annotations

HEADER_HTML = """
<div class="app-header">
    <h1>🧠 StudyFlow AI</h1>
    <p>From the intention to learn to real progress, guided by AI</p>
</div>
"""


def format_diagnostic_questions(questions: list[dict]) -> str:
    """Format diagnostic questions as HTML for display."""
    if not questions:
        return "<p>No diagnostic questions available.</p>"

    html = '<div class="animate-in">'
    html += '<h3 style="margin-bottom: 1rem; color: #4f46e5;">📝 Quick Assessment</h3>'
    html += '<p style="color: #64748b; margin-bottom: 1.5rem;">Help us understand your current level so we can create the perfect plan for you.</p>'

    for i, q in enumerate(questions):
        html += f'''
        <div class="milestone-card" style="margin-bottom: 1rem;">
            <div class="milestone-header">
                <div class="milestone-number">{i + 1}</div>
                <div class="milestone-title">{q.get("question", "")}</div>
            </div>
        </div>
        '''

    html += '</div>'
    return html
