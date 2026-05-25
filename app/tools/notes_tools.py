# app/tools/notes_tools.py
#
# User notes tools — api_doc/notes_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("notes-tools")


# =========================================================
# LIST NOTES
# GET /api/v1/user/notes
# =========================================================
async def list_notes():
    logger.info("Listing notes")
    return await backend_client.get(endpoint="/api/v1/user/notes")


# =========================================================
# CREATE NOTE
# POST /api/v1/user/notes
# =========================================================
async def create_note(payload: dict):
    logger.info("Creating note", title=payload.get("title"))
    return await backend_client.post(endpoint="/api/v1/user/notes", data=payload)


# =========================================================
# UPDATE NOTE
# PUT /api/v1/user/notes/{note_id}
# =========================================================
async def update_note(note_id: str, payload: dict):
    logger.info("Updating note", note_id=note_id)
    return await backend_client.put(
        endpoint=f"/api/v1/user/notes/{note_id}", data=payload
    )


# =========================================================
# DELETE NOTE
# DELETE /api/v1/user/notes/{note_id}
# =========================================================
async def delete_note(note_id: str):
    logger.info("Deleting note", note_id=note_id)
    return await backend_client.delete(endpoint=f"/api/v1/user/notes/{note_id}")
