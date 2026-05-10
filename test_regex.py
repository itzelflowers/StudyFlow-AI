import json
import re

raw = '''
Here is the JSON you requested:
{
    "assessed_level": "beginner",
    "total_weeks": 8,
    "milestones": [
        {
            "id": "m1",
            "title": "Calculus Basics",
            "description": "Learn functions and limits",
            "order": 1,
            "week": 1,
            "topics": ["functions", "limits"],
            "learning_objectives": ["Understand functions"],
            "estimated_hours": 10
        }
    ],
    "plan_summary": "A beginner plan for calculus."
}
I hope this helps! Let me know if you need any adjustments.
'''

print("Raw length:", len(raw))

# Method 1
json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
if json_match:
    print('Matched code block')
else:
    print('No code block')

# Method 2
json_match = re.search(r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", raw, re.DOTALL)
if json_match:
    try:
        data = json.loads(json_match.group(1))
        print('Matched nested dict:', type(data))
    except json.JSONDecodeError:
        print('Failed to load nested dict')
else:
    print('No nested dict match')

# Method 3
json_match = re.search(r"(\{.*\})", raw, re.DOTALL)
if json_match:
    try:
        data = json.loads(json_match.group(1))
        print('Matched greedy dict:', type(data))
    except json.JSONDecodeError as e:
        print(f'Greedy failed: {e}')
else:
    print('No greedy dict match')

# A better method: find first { and last }
try:
    start_idx = raw.find('{')
    end_idx = raw.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = raw[start_idx:end_idx+1]
        data = json.loads(json_str)
        print('Matched manual { } bounds:', type(data))
except Exception as e:
    print('Manual bounds failed:', e)

