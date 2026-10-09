#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=== [1/3] Installing Python Dependencies ==="
pip install -r requirements.txt

echo "=== [2/3] Building React Frontend SPA ==="
cd frontend
npm install
npm run build
cd ..

echo "=== [3/3] Verifying ML Models ==="
python -c "
import os
if not os.path.exists('ml_artifacts/champion_model.joblib'):
    print('Training initial champion model...')
    import backend.ml.train
    backend.ml.train.train_and_evaluate_all_models()
else:
    print('ML champion model artifacts verified successfully.')
"

echo "=== Build Completed Successfully! ==="
