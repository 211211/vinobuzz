"""Tests for the sommelier API endpoint and models."""

from app.core.models import SommelierInput
from app.core.streaming import EventType, format_sse


class TestSommelierInput:
    def test_default_session_id(self):
        input_data = SommelierInput(
            message_history=[{"role": "user", "content": "Hello"}]
        )
        assert input_data.session_id is not None
        assert len(input_data.session_id) > 0

    def test_custom_session_id(self):
        input_data = SommelierInput(
            session_id="test-123",
            message_history=[{"role": "user", "content": "Hello"}],
        )
        assert input_data.session_id == "test-123"

    def test_history_limited_to_20(self):
        messages = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
        input_data = SommelierInput(message_history=messages)
        assert len(input_data.message_history) == 20
        assert input_data.message_history[0]["content"] == "msg 10"

    def test_empty_history_allowed(self):
        input_data = SommelierInput(message_history=[])
        assert input_data.message_history == []


class TestSSEFormatting:
    def test_format_metadata_event(self):
        event = format_sse(EventType.METADATA, {"session_id": "abc", "trace_id": "xyz"})
        assert "event: metadata" in event
        assert '"session_id": "abc"' in event

    def test_format_data_event(self):
        event = format_sse(EventType.DATA, {"content": "Hello world"})
        assert "event: data" in event
        assert '"content": "Hello world"' in event

    def test_format_done_event(self):
        event = format_sse(EventType.DONE, {"message": "Stream completed"})
        assert "event: done" in event

    def test_format_agent_updated_event(self):
        event = format_sse(
            EventType.AGENT_UPDATED,
            {"agent": "coordinator", "content_type": "thoughts"},
        )
        assert "event: agent_updated" in event
        assert '"agent": "coordinator"' in event

    def test_format_error_event(self):
        event = format_sse(EventType.ERROR, {"message": "Something went wrong"})
        assert "event: error" in event
