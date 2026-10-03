import pytest
from httpx import AsyncClient, ASGITransport
from agent.main import app
from agent import config


@pytest.mark.asyncio
async def test_get_and_patch_models():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET current models
        res = await client.get("/api/models")
        assert res.status_code == 200
        data = res.json()
        assert "default_video_model_family" in data
        assert "default_veo_model" in data

        orig_family = data["default_video_model_family"]
        orig_veo = data["default_veo_model"]

        try:
            # 2. PATCH to Veo with ultra model
            patch_res = await client.patch("/api/models", json={
                "default_video_model_family": "veo",
                "default_veo_model": "veo_3_1_i2v_s_fast_ultra",
            })
            assert patch_res.status_code == 200
            updated = patch_res.json()["models"]
            assert updated["default_video_model_family"] == "veo"
            assert updated["default_veo_model"] == "veo_3_1_i2v_s_fast_ultra"
            assert config.DEFAULT_VIDEO_MODEL_FAMILY == "veo"
            assert config.DEFAULT_VEO_MODEL == "veo_3_1_i2v_s_fast_ultra"

            # 3. PATCH back to omni_flash default
            patch_res2 = await client.patch("/api/models", json={
                "default_video_model_family": "omni_flash",
                "default_veo_model": "veo_3_1_i2v_lite_low_priority",
                "default_omni_duration": 6,
                "default_omni_resolution": "720p",
            })
            assert patch_res2.status_code == 200
            updated2 = patch_res2.json()["models"]
            assert updated2["default_video_model_family"] == "omni_flash"
            assert updated2["default_veo_model"] == "veo_3_1_i2v_lite_low_priority"
            assert config.DEFAULT_VIDEO_MODEL_FAMILY == "omni_flash"
            assert config.DEFAULT_VEO_MODEL == "veo_3_1_i2v_lite_low_priority"
            assert config.DEFAULT_OMNI_DURATION == 6
            assert config.DEFAULT_OMNI_RESOLUTION == "720p"
        finally:
            # Restore
            await client.patch("/api/models", json={
                "default_video_model_family": orig_family,
                "default_veo_model": orig_veo,
            })


@pytest.mark.asyncio
async def test_patch_models_invalid_duration():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.patch("/api/models", json={"default_omni_duration": "not-a-number"})
        assert res.status_code == 422
        assert "integer" in res.json()["detail"]

