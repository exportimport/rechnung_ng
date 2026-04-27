"""Build info shown in page footer."""
import pytest


@pytest.mark.asyncio
async def test_build_info_shown_in_footer(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "Build #" in r.text
