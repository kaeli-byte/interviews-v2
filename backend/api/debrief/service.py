"""Debrief service - post-interview analysis."""
import uuid
from datetime import datetime
from typing import List, Optional

# In-memory storage
debriefs_db: dict = {}


async def generate_debrief(
    session_id: str,
    user_id: str,
    transcript: List[dict],
    rubric: List[dict]
) -> dict:
    """Generate debrief from transcript and rubric using AI."""
    from backend.config import settings
    from google import genai
    from google.genai import types

    # Build rubric text
    rubric_text = ""
    for item in rubric:
        rubric_text += f"- {item.get('criteria', '')}: {item.get('description', '')}\n"

    # Build transcript text
    transcript_text = ""
    for entry in transcript:
        speaker = entry.get("speaker", "unknown")
        text = entry.get("text", "")
        transcript_text += f"{speaker}: {text}\n"

    prompt = f"""Analyze this interview transcript and provide a debrief.

Rubric:
{rubric_text}

Transcript:
{transcript_text}

Return JSON with:
- overall_score: number 0-100
- strengths: array of strings
- areas_for_improvement: array of strings
- detailed_feedback: object with scores for each rubric item
- suggested_focus: array of strings for areas to practice
"""

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        if response.text:
            import json
            debrief_data = json.loads(response.text)
        else:
            debrief_data = {}
    except Exception as e:
        debrief_data = {"error": str(e)}

    # Store debrief
    debrief_id = uuid.uuid4().hex
    debrief = {
        "debrief_id": debrief_id,
        "session_id": session_id,
        "user_id": user_id,
        "overall_score": debrief_data.get("overall_score", 0),
        "strengths": debrief_data.get("strengths", []),
        "areas_for_improvement": debrief_data.get("areas_for_improvement", []),
        "detailed_feedback": debrief_data.get("detailed_feedback", {}),
        "suggested_focus": debrief_data.get("suggested_focus", []),
        "created_at": datetime.utcnow().isoformat()
    }
    debriefs_db[session_id] = debrief
    return debrief


def get_debrief(session_id: str) -> Optional[dict]:
    """Get debrief for a session."""
    return debriefs_db.get(session_id)


def get_debriefs_by_user(user_id: str) -> list:
    """Get all debriefs for a user."""
    return [d for d in debriefs_db.values() if d.get("user_id") == user_id]


def delete_debrief(session_id: str) -> bool:
    """Delete a debrief."""
    if session_id in debriefs_db:
        del debriefs_db[session_id]
        return True
    return False