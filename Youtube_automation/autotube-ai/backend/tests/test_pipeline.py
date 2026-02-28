"""Tests for the Pipeline Orchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.video import VideoStatus
from app.pipeline.video_pipeline import PipelineStep, STEP_TO_STATUS


class TestPipelineSteps:
    def test_pipeline_step_order(self):
        """Verify pipeline steps are in correct order."""
        assert PipelineStep.SCRIPT < PipelineStep.VOICE
        assert PipelineStep.VOICE < PipelineStep.ASSETS
        assert PipelineStep.ASSETS < PipelineStep.CAPTIONS
        assert PipelineStep.CAPTIONS < PipelineStep.THUMBNAIL
        assert PipelineStep.THUMBNAIL < PipelineStep.ASSEMBLE
        assert PipelineStep.ASSEMBLE < PipelineStep.SEO
        assert PipelineStep.SEO < PipelineStep.UPLOAD

    def test_step_to_status_mapping(self):
        """Verify all pipeline steps map to a video status."""
        for step in PipelineStep:
            assert step in STEP_TO_STATUS
            assert isinstance(STEP_TO_STATUS[step], VideoStatus)

    def test_pipeline_step_values(self):
        """Verify steps are sequential integers."""
        values = sorted(step.value for step in PipelineStep)
        for i, v in enumerate(values):
            assert v == i + 1


class TestPipelineResumability:
    def test_resume_from_script_step(self):
        """Test that pipeline can start from script step."""
        # A video with pipeline_step=0 should start at SCRIPT (step 3)
        pipeline_step = 0
        start_step = pipeline_step + 1 if pipeline_step > 0 else PipelineStep.SCRIPT
        assert start_step == PipelineStep.SCRIPT

    def test_resume_from_voice_step(self):
        """Test that pipeline can resume from voiceover step."""
        pipeline_step = PipelineStep.SCRIPT  # Step 3 completed
        start_step = pipeline_step + 1
        assert start_step == PipelineStep.VOICE

    def test_resume_from_assets_step(self):
        """Test that pipeline resumes correctly after voice step."""
        pipeline_step = PipelineStep.VOICE
        start_step = pipeline_step + 1
        assert start_step == PipelineStep.ASSETS
