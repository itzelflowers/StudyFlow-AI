"""
Study plan visualization component.
"""

from __future__ import annotations


RESOURCE_ICONS = {
    "video": "🎬",
    "article": "📄",
    "exercise": "✏️",
    "course": "🎓",
    "book": "📚",
    "tool": "🔧",
}


def format_study_plan(plan_data: dict, task_schedule: list[dict], resources: list[dict]) -> str:
    """Format a study plan as rich HTML."""
    if not plan_data:
        return '<p style="color: #94a3b8;">No study plan generated yet.</p>'

    milestones = plan_data.get("milestones", [])
    level = plan_data.get("assessed_level", "beginner")
    total_weeks = plan_data.get("total_weeks", 4)
    summary = plan_data.get("plan_summary", "")

    # Badge color
    badge_class = f"badge-{level}"

    html = '<div class="animate-in">'

    # Plan overview
    html += f'''
    <div style="background: linear-gradient(145deg, #ede9fe, #e0e7ff); border-radius: 12px; 
                padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #c7d2fe;">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
            <h3 style="margin: 0; color: #3730a3;">📋 Your Study Plan</h3>
            <span class="badge {badge_class}">{level}</span>
            <span style="margin-left: auto; color: #6366f1; font-weight: 600;">
                {total_weeks} weeks
            </span>
        </div>
        <p style="color: #4338ca; margin: 0; line-height: 1.5;">{summary}</p>
    </div>
    '''

    # Resource lookup by milestone
    resource_map = {}
    for mr in resources:
        mid = mr.get("milestone_id", "")
        resource_map[mid] = mr.get("resources", [])

    # Task lookup by milestone
    task_map = {}
    for t in task_schedule:
        mid = t.get("milestone_id", "")
        if mid not in task_map:
            task_map[mid] = []
        task_map[mid].append(t)

    # Milestones
    for i, milestone in enumerate(milestones):
        mid = milestone.get("id", f"m{i+1}")
        title = milestone.get("title", "Untitled")
        desc = milestone.get("description", "")
        week = milestone.get("week", i + 1)
        objectives = milestone.get("learning_objectives", [])

        html += f'''
        <div class="milestone-card">
            <div class="milestone-header">
                <div class="milestone-number">{i + 1}</div>
                <div class="milestone-title">{title}</div>
                <div class="milestone-week">Week {week}</div>
            </div>
            <div class="milestone-description">{desc}</div>
        '''

        # Learning objectives
        if objectives:
            html += '<div style="margin-top: 0.75rem;">'
            html += '<strong style="font-size: 0.85rem; color: #6366f1;">Learning Objectives:</strong>'
            html += '<ul style="margin: 0.25rem 0 0 1rem; color: #475569; font-size: 0.9rem;">'
            for obj in objectives:
                html += f'<li>{obj}</li>'
            html += '</ul></div>'

        # Tasks for this milestone
        milestone_tasks = task_map.get(mid, [])
        if milestone_tasks:
            html += '<div style="margin-top: 0.75rem;">'
            html += '<strong style="font-size: 0.85rem; color: #6366f1;">📋 Tasks:</strong>'
            html += '<div style="margin-top: 0.5rem;">'
            for t in milestone_tasks[:5]:  # Show first 5
                task_type_icon = {"learn": "📖", "practice": "✏️", "review": "🔄", "project": "🚀"}.get(
                    t.get("task_type", "learn"), "📌"
                )
                html += f'''
                <div class="task-item">
                    <span>{task_type_icon}</span>
                    <div>
                        <div class="task-title">{t.get("title", "")}</div>
                        <div class="task-meta">
                            Day {t.get("day", "?")} · {t.get("estimated_minutes", 30)} min
                        </div>
                    </div>
                </div>
                '''
            if len(milestone_tasks) > 5:
                html += f'<p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">+ {len(milestone_tasks) - 5} more tasks</p>'
            html += '</div></div>'

        # Resources for this milestone
        milestone_resources = resource_map.get(mid, [])
        if milestone_resources:
            html += '<div style="margin-top: 0.75rem;">'
            html += '<strong style="font-size: 0.85rem; color: #6366f1;">📚 Resources:</strong>'
            html += '<div style="margin-top: 0.5rem;">'
            for r in milestone_resources[:4]:
                icon = RESOURCE_ICONS.get(r.get("resource_type", ""), "📌")
                html += f'''
                <div class="resource-item">
                    <span class="resource-icon">{icon}</span>
                    <div style="flex: 1;">
                        <a href="{r.get("url", "#")}" target="_blank" class="resource-title" 
                           style="text-decoration: none;">
                            {r.get("title", "Resource")}
                        </a>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                            {r.get("description", "")[:100]}
                        </div>
                    </div>
                    <span class="resource-type">{r.get("resource_type", "")}</span>
                </div>
                '''
            html += '</div></div>'

        html += '</div>'  # close milestone-card

    html += '</div>'  # close animate-in
    return html
