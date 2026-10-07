"""
KRISHIRAKSHA AI - Model Registry & Metadata Loader
Student Roll Number: 231FA04291
"""

import os
import json
import logging
import joblib
from typing import Optional, Dict, Any
from backend.app.config import settings

logger = logging.getLogger("krishiraksha.model_registry")

class ModelRegistry:
    def __init__(self, artifacts_dir: str = "ml_artifacts"):
        self.artifacts_dir = artifacts_dir
        self.model_path = os.path.join(artifacts_dir, "champion_model.joblib")
        self.metadata_path = os.path.join(artifacts_dir, "model_metadata.json")
        self._cached_model = None
        self._cached_metadata = None

    def is_model_ready(self) -> bool:
        return os.path.exists(self.model_path) and os.path.exists(self.metadata_path)

    def load_champion_model(self):
        if not self.is_model_ready():
            return None
        if self._cached_model is None:
            logger.info(f"Loading champion model artifact from {self.model_path}")
            self._cached_model = joblib.load(self.model_path)
        return self._cached_model

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.metadata_path):
            return None
        if self._cached_metadata is None:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self._cached_metadata = json.load(f)
        return self._cached_metadata

    def reload(self):
        self._cached_model = None
        self._cached_metadata = None
        return self.load_champion_model()

model_registry = ModelRegistry()
