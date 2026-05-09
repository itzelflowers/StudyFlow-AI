"""
Task tracker component — Progress tracking and task management.
"""

from __future__ import annotations


def format_progress_bar(completed: int, total: int) -> str:
    """Generate a progress bar HTML."""
    pct = round((completed / total) * 100, 1) if total > 0 else 0

    return f'''
    <div class="progress-container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; color: #1e293b;">📊 Your Progress</h3>
            <span style="font-size: 1.5rem; font-weight: 800; color: #4f46e5;">{pct}%</span>
        </div>
        <div class="progress-bar-wrapper">
            <div class="progress-bar-fill" style="width: {pct}%;"></div>
        </div>
        <div class="progress-stats">
            <span>✅ {completed} completed</span>
            <span>📋 {total} total tasks</span>
            <span>📅 {total - completed} remaining</span>
        </div>
    </div>
    '''


def format_task_list(tasks: list[dict], task_statuses: dict[str, str] | None = None) -> str:
    """Format the task list with status checkboxes."""
    if not tasks:
        return '<p style="color: #94a3b8;">No tasks yet. Generate a study plan first!</p>'

    task_statuses = task_statuses or {}
    html = '<div class="animate-in">'

    # Group tasks by day
    days: dict[int, list[dict]] = {}
    for t in tasks:
        day = t.get("day", 1)
        if day not in days:
            days[day] = []
        days[day].append(t)

    for day in sorted(days.keys()):
        day_tasks = days[day]
        html += f'''
        <div style="margin-bottom: 1rem;">
            <h4 style="color: #6366f1; font-size: 0.9rem; margin-bottom: 0.5rem; 
                        font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">
                Day {day}
            </h4>
        '''

        for t in day_tasks:
            tid = t.get("id", "")
            status = task_statuses.get(tid, "pending")
            completed_class = " task-completed" if status == "completed" else ""
            check_icon = "✅" if status == "completed" else ("🔄" if status == "in_progress" else ("❌" if status == "stuck" else "⬜"))

            task_type_icon = {
                "learn": "📖", "practice": "✏️", "review": "🔄", "project": "🚀"
            }.get(t.get("task_type", "learn"), "📌")

            html += f'''
            <div class="task-item{completed_class}">
                <span class="task-checkbox" style="font-size: 1.2rem;">{check_icon}</span>
                <div style="flex: 1;">
                    <div class="task-title">{task_type_icon} {t.get("title", "")}</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 4px;">
                        {t.get("description", "")[:150]}
                    </div>
                    <div class="task-meta">
                        ⏱ {t.get("estimated_minutes", 30)} min · 
                        Milestone: {t.get("milestone_id", "?")}
                    </div>
                </div>
            </div>
            '''

        html += '</div>'

    html += '</div>'
    return html


def format_coaching_message(message: str) -> str:
    """Format a coaching/encouragement message."""
    if not message:
        return ""

    return f'<div class="coaching-message">{message}</div>'
