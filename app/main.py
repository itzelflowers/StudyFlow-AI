"""
StudyFlow AI — Main Gradio Application.

This is the entry point for the entire application. It mounts:
- A Gradio Blocks UI with tabs for onboarding, plan view, and task tracking
- The FastAPI backend as a sub-application
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import gradio as gr

from app.theme import get_theme, CUSTOM_CSS
from app.components.onboarding import HEADER_HTML, format_diagnostic_questions
from app.components.plan_view import format_study_plan
from app.components.task_tracker import format_progress_bar, format_task_list, format_coaching_message

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── State Management ────────────────────────────────────────────────────────

class AppState:
    """Application state manager."""

    def __init__(self):
        self.session_id: str | None = None
        self.goal: str = ""
        self.hours_per_week: float = 10.0
        self.deadline_weeks: int | None = None
        self.diagnostic_questions: list[dict] = []
        self.diagnostic_answers: list[dict] = []
        self.study_plan: dict = {}
        self.task_schedule: list[dict] = []
        self.resources: list[dict] = []
        self.task_statuses: dict[str, str] = {}

    def reset(self):
        self.__init__()


# Global app state
state = AppState()


# ─── Initialize Backend Services ─────────────────────────────────────────────

def init_services():
    """Initialize database and Qdrant."""
    try:
        from backend.models.database import init_db
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ DB init failed: {e}")

    try:
        from rag.indexer import seed_from_file
        count = seed_from_file()
        logger.info(f"✅ Seeded {count} resources")
    except Exception as e:
        logger.warning(f"⚠️ Qdrant seed failed: {e}")


# ─── Event Handlers ──────────────────────────────────────────────────────────

def start_session(goal: str, hours: float, weeks: str):
    """Handle the 'Start Learning' button click."""
    if not goal or not goal.strip():
        return (
            gr.update(visible=True),   # onboarding section stays
            gr.update(visible=False),  # diagnostic section hidden
            gr.update(visible=False),  # plan section hidden
            gr.update(visible=False),  # tracker section hidden
            "",                         # diagnostic html
            gr.update(value="⚠️ Please enter a learning goal."),
            gr.update(choices=[], label="Question 1"),
            gr.update(choices=[], label="Question 2"),
            gr.update(choices=[], label="Question 3"),
            gr.update(choices=[], label="Question 4"),
        )

    state.reset()
    state.goal = goal.strip()
    state.hours_per_week = hours
    state.deadline_weeks = int(weeks) if weeks and weeks.strip() else None

    # Generate diagnostic questions via LLM
    try:
        from backend.services.llm_client import generate_json

        messages = [
            {"role": "system", "content": "You are an educational assessment expert. Generate diagnostic questions to assess a learner's current level."},
            {"role": "user", "content": f"""Generate exactly 4 diagnostic questions for this learning goal:

**Goal:** {state.goal}

Return as JSON:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "Question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "category": "knowledge|style|prerequisites|motivation"
        }}
    ]
}}"""},
        ]

        result = generate_json(messages)
        questions = result.get("questions", [])
        state.diagnostic_questions = questions

        # Prepare gr.update() for each radio with both choices and label
        q_updates = []
        for i in range(4):
            if i < len(questions):
                q = questions[i]
                q_updates.append(
                    gr.update(
                        choices=q.get("options", []),
                        label=q.get("question", f"Question {i+1}"),
                        value=None,
                    )
                )
            else:
                q_updates.append(gr.update(choices=[], label=f"Question {i+1}", value=None))

        return (
            gr.update(visible=False),  # hide onboarding
            gr.update(visible=True),   # show diagnostic
            gr.update(visible=False),  # plan hidden
            gr.update(visible=False),  # tracker hidden
            format_diagnostic_questions(questions),  # diagnostic html
            "",                         # clear status
            q_updates[0],
            q_updates[1],
            q_updates[2],
            q_updates[3],
        )

    except Exception as e:
        logger.error(f"Failed to generate diagnostic: {e}")
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            f"❌ Error: {str(e)[:200]}",
            gr.update(choices=[], label="Question 1"),
            gr.update(choices=[], label="Question 2"),
            gr.update(choices=[], label="Question 3"),
            gr.update(choices=[], label="Question 4"),
        )


def generate_plan(a1: str, a2: str, a3: str, a4: str):
    """Handle diagnostic submission and generate the study plan."""
    answers = [
        {"question_id": "q1", "answer": a1 or "Not answered"},
        {"question_id": "q2", "answer": a2 or "Not answered"},
        {"question_id": "q3", "answer": a3 or "Not answered"},
        {"question_id": "q4", "answer": a4 or "Not answered"},
    ]
    state.diagnostic_answers = answers

    try:
        from agents.graph import create_study_plan

        result = create_study_plan(
            goal=state.goal,
            available_hours=state.hours_per_week,
            deadline_weeks=state.deadline_weeks,
            diagnostic_answers=answers,
        )

        state.study_plan = result.get("study_plan", {})
        state.task_schedule = result.get("task_schedule", [])
        state.resources = result.get("resources", [])

        # Initialize task statuses
        state.task_statuses = {
            t.get("id", f"t{i}"): "pending"
            for i, t in enumerate(state.task_schedule)
        }

        plan_html = format_study_plan(state.study_plan, state.task_schedule, state.resources)
        task_html = format_task_list(state.task_schedule, state.task_statuses)
        progress_html = format_progress_bar(0, len(state.task_schedule))

        return (
            gr.update(visible=False),  # hide diagnostic
            gr.update(visible=True),   # show plan
            gr.update(visible=True),   # show tracker
            plan_html,
            progress_html + task_html,
            "✅ Your personalized study plan is ready!",
        )

    except Exception as e:
        logger.error(f"Failed to generate plan: {e}")
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            "",
            f"❌ Error generating plan: {str(e)[:200]}",
        )


def update_task_status(task_dropdown: str, new_status: str, feedback: str):
    """Update a task's status and get coaching feedback."""
    if not task_dropdown:
        return (
            gr.update(),
            gr.update(),
            "⚠️ Please select a task first.",
        )

    # Extract task ID from dropdown (format: "Day X: Task Title (id)")
    task_id = ""
    for t in state.task_schedule:
        label = f"Day {t.get('day', '?')}: {t.get('title', '?')}"
        if task_dropdown.startswith(label[:30]):
            task_id = t.get("id", "")
            break

    if not task_id and state.task_schedule:
        # Try by index
        try:
            choices = get_task_choices()
            idx = choices.index(task_dropdown) if task_dropdown in choices else 0
            task_id = state.task_schedule[idx].get("id", "")
        except (ValueError, IndexError):
            task_id = state.task_schedule[0].get("id", "") if state.task_schedule else ""

    if task_id:
        state.task_statuses[task_id] = new_status

    # Count completed
    completed = sum(1 for s in state.task_statuses.values() if s == "completed")
    total = len(state.task_schedule)

    # Get coaching message
    coaching_msg = ""
    if feedback or new_status == "stuck":
        try:
            from agents.graph import check_progress
            result = check_progress(
                goal=state.goal,
                study_plan=state.study_plan,
                task_schedule=state.task_schedule,
                task_statuses=state.task_statuses,
                user_feedback=feedback or "",
            )
            coaching_msg = result.get("coaching_message", "")
        except Exception as e:
            logger.warning(f"Progress check failed: {e}")
            coaching_msg = "Keep going! Every step counts. 💪"

    progress_html = format_progress_bar(completed, total)
    task_html = format_task_list(state.task_schedule, state.task_statuses)
    coaching_html = format_coaching_message(coaching_msg) if coaching_msg else ""

    return (
        progress_html + coaching_html + task_html,
        gr.update(),
        f"✅ Task updated to '{new_status}'!" + (f" Coach says: {coaching_msg[:100]}" if coaching_msg else ""),
    )


def get_task_choices() -> list[str]:
    """Get task choices for the dropdown."""
    return [
        f"Day {t.get('day', '?')}: {t.get('title', 'Task')}"
        for t in state.task_schedule
    ]


def go_back_to_start():
    """Reset and go back to the start."""
    state.reset()
    return (
        gr.update(visible=True),   # show onboarding
        gr.update(visible=False),  # hide diagnostic
        gr.update(visible=False),  # hide plan
        gr.update(visible=False),  # hide tracker
        "",
    )


# ─── Build the Gradio App ────────────────────────────────────────────────────

def create_app() -> gr.Blocks:
    """Build the Gradio Blocks application."""

    theme = get_theme()

    with gr.Blocks(
        theme=theme,
        css=CUSTOM_CSS,
        title="StudyFlow AI — Personalized Learning Coach",
    ) as app:

        # ─── Header ─────────────────────────────────────────────
        gr.HTML(HEADER_HTML)

        # Status bar
        status_msg = gr.Markdown("", elem_id="status-message")

        # ═══════════════════════════════════════════════════════
        # SECTION 1: ONBOARDING (Goal Input)
        # ═══════════════════════════════════════════════════════
        with gr.Group(visible=True, elem_id="onboarding-section") as onboarding_section:
            gr.Markdown("### 🎯 What do you want to learn?")
            gr.Markdown("Tell us your learning goal and we'll create a personalized study plan powered by AI agents.")

            goal_input = gr.Textbox(
                label="Learning Goal",
                placeholder="e.g., I want to learn calculus from scratch, I need to prepare for my linear algebra exam...",
                lines=2,
                elem_id="goal-input",
            )

            with gr.Row():
                hours_input = gr.Slider(
                    minimum=1, maximum=40, value=10, step=1,
                    label="Hours available per week",
                    elem_id="hours-input",
                )
                weeks_input = gr.Textbox(
                    label="Target weeks (optional)",
                    placeholder="e.g., 8",
                    elem_id="weeks-input",
                )

            start_btn = gr.Button(
                "🚀 Start My Learning Journey",
                variant="primary",
                size="lg",
                elem_id="start-btn",
            )

        # ═══════════════════════════════════════════════════════
        # SECTION 2: DIAGNOSTIC QUIZ
        # ═══════════════════════════════════════════════════════
        with gr.Group(visible=False, elem_id="diagnostic-section") as diagnostic_section:
            diagnostic_html = gr.HTML("")

            with gr.Row():
                with gr.Column():
                    q1_radio = gr.Radio(choices=[], label="Question 1", elem_id="q1-radio")
                    q2_radio = gr.Radio(choices=[], label="Question 2", elem_id="q2-radio")
                with gr.Column():
                    q3_radio = gr.Radio(choices=[], label="Question 3", elem_id="q3-radio")
                    q4_radio = gr.Radio(choices=[], label="Question 4", elem_id="q4-radio")

            with gr.Row():
                back_btn = gr.Button("← Back", variant="secondary", elem_id="back-btn")
                submit_btn = gr.Button(
                    "✨ Generate My Study Plan",
                    variant="primary",
                    size="lg",
                    elem_id="submit-btn",
                )

        # ═══════════════════════════════════════════════════════
        # SECTION 3: STUDY PLAN VIEW
        # ═══════════════════════════════════════════════════════
        with gr.Group(visible=False, elem_id="plan-section") as plan_section:
            gr.Markdown("### 📋 Your Personalized Study Plan")
            plan_html = gr.HTML("")

        # ═══════════════════════════════════════════════════════
        # SECTION 4: TASK TRACKER
        # ═══════════════════════════════════════════════════════
        with gr.Group(visible=False, elem_id="tracker-section") as tracker_section:
            gr.Markdown("### ✅ Task Tracker")

            tracker_html = gr.HTML("")

            with gr.Row():
                task_dropdown = gr.Dropdown(
                    choices=[],
                    label="Select Task",
                    elem_id="task-dropdown",
                    interactive=True,
                )
                status_dropdown = gr.Dropdown(
                    choices=["completed", "in_progress", "stuck", "skipped"],
                    value="completed",
                    label="New Status",
                    elem_id="status-dropdown",
                )

            feedback_input = gr.Textbox(
                label="Feedback (optional)",
                placeholder="e.g., 'This topic is harder than expected', 'I want to go faster'",
                elem_id="feedback-input",
            )

            with gr.Row():
                update_btn = gr.Button(
                    "📊 Update Progress",
                    variant="primary",
                    elem_id="update-btn",
                )
                new_plan_btn = gr.Button(
                    "🔄 Start New Plan",
                    variant="secondary",
                    elem_id="new-plan-btn",
                )

        # ─── Footer ─────────────────────────────────────────────
        gr.HTML("""
        <div style="text-align: center; padding: 2rem 1rem; margin-top: 2rem; 
                    border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 0.85rem;">
            <p>Built with 🧠 <strong>StudyFlow AI</strong> — Powered by Qwen, LangGraph, Qdrant & FastAPI</p>
            <p style="margin-top: 0.25rem;">From the intention to learn to real progress, guided by AI.</p>
        </div>
        """)

        # ═══════════════════════════════════════════════════════
        # EVENT HANDLERS
        # ═══════════════════════════════════════════════════════

        start_btn.click(
            fn=start_session,
            inputs=[goal_input, hours_input, weeks_input],
            outputs=[
                onboarding_section,
                diagnostic_section,
                plan_section,
                tracker_section,
                diagnostic_html,
                status_msg,
                q1_radio, q2_radio, q3_radio, q4_radio,
            ],
        )

        submit_btn.click(
            fn=generate_plan,
            inputs=[q1_radio, q2_radio, q3_radio, q4_radio],
            outputs=[
                diagnostic_section,
                plan_section,
                tracker_section,
                plan_html,
                tracker_html,
                status_msg,
            ],
        )

        # Populate task dropdown when plan is generated
        def refresh_task_dropdown():
            choices = get_task_choices()
            return gr.update(choices=choices, value=choices[0] if choices else None)

        submit_btn.click(
            fn=refresh_task_dropdown,
            inputs=[],
            outputs=[task_dropdown],
        )

        update_btn.click(
            fn=update_task_status,
            inputs=[task_dropdown, status_dropdown, feedback_input],
            outputs=[tracker_html, feedback_input, status_msg],
        )

        back_btn.click(
            fn=go_back_to_start,
            inputs=[],
            outputs=[
                onboarding_section,
                diagnostic_section,
                plan_section,
                tracker_section,
                status_msg,
            ],
        )

        new_plan_btn.click(
            fn=go_back_to_start,
            inputs=[],
            outputs=[
                onboarding_section,
                diagnostic_section,
                plan_section,
                tracker_section,
                status_msg,
            ],
        )

    return app


# ─── Main Entry Point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    # Initialize services
    init_services()

    # Build and launch
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
