from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.biz.agent.sommelier.mode import SommelierMode
from app.core.models import SommelierInput

router = APIRouter(prefix="/sommelier", tags=["sommelier"])


@router.post("/chat")
async def chat(input_data: SommelierInput):
    """Conversational wine recommendation endpoint. Returns SSE stream."""
    mode = SommelierMode()

    async def event_generator():
        async for event in mode.run(
            session_id=input_data.session_id,
            message_history=input_data.message_history,
        ):
            yield event

    return EventSourceResponse(event_generator(), media_type="text/event-stream")
