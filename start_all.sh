#!/usr/bin/env bash

# ==============================================================================
# FlowSentinel - 1-Click Master Launch Script
# AI-Powered Intelligent Chute Blockage Detection System
# ==============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "===================================================================="
echo "   🛡️   FLOWSENTINEL: AI CHUTE BLOCKAGE DETECTION SYSTEM"
echo "        Real-Time Industrial SCADA & Predictive AI Pipeline"
echo "===================================================================="
echo -e "${NC}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# 1. Check Python / Virtual Environment
echo -e "${YELLOW}[1/4] Checking Python Environment...${NC}"
if [ -d "$ROOT_DIR/.venv" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
    PIP_BIN="$ROOT_DIR/.venv/bin/pip"
    echo -e "${GREEN}✓ Using virtual environment at ./.venv${NC}"
elif [ -d "$ROOT_DIR/venv" ]; then
    PYTHON_BIN="$ROOT_DIR/venv/bin/python"
    PIP_BIN="$ROOT_DIR/venv/bin/pip"
    echo -e "${GREEN}✓ Using virtual environment at ./venv${NC}"
else
    PYTHON_BIN="python3"
    PIP_BIN="pip3"
fi

if ! command -v "$PYTHON_BIN" &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed. Aborting.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python runtime: $($PYTHON_BIN --version)${NC}"

# 2. Check and Install Dependencies
echo -e "\n${YELLOW}[2/4] Verifying Python Dependencies...${NC}"
$PYTHON_BIN -c "import fastapi, uvicorn, sklearn, joblib, pandas, numpy" &> /dev/null || {
    echo -e "${YELLOW}Installing required dependencies from requirements.txt...${NC}"
    $PIP_BIN install -r "$ROOT_DIR/requirements.txt"
}
echo -e "${GREEN}✓ All dependencies satisfied.${NC}"

# 3. Train / Verify ML Models
echo -e "\n${YELLOW}[3/4] Verifying Machine Learning Model Artifacts...${NC}"
MODEL_DIR="$ROOT_DIR/team3-ml-simulation/models"
if [ ! -f "$MODEL_DIR/chute_random_forest.joblib" ] || [ ! -f "$MODEL_DIR/chute_isolation_forest.joblib" ] || [ ! -f "$MODEL_DIR/scaler.joblib" ]; then
    echo -e "${YELLOW}🧠 Pre-trained models not detected. Training Isolation Forest & Random Forest now...${NC}"
    $PYTHON_BIN "$ROOT_DIR/team3-ml-simulation/train_models.py"
else
    echo -e "${GREEN}✓ Model artifacts detected at team3-ml-simulation/models/${NC}"
fi

# 4. Launch FastAPI Backend Server
echo -e "\n${YELLOW}[4/4] Starting FastAPI Server & WebSocket Telemetry Hub...${NC}"
echo -e "${CYAN}====================================================================${NC}"
echo -e "${GREEN}🚀 FlowSentinel Dashboard: http://localhost:8000${NC}"
echo -e "${GREEN}📡 REST API & Swagger UI:  http://localhost:8000/docs${NC}"
echo -e "${GREEN}🔌 WebSocket Endpoint:     ws://localhost:8000/ws/telemetry${NC}"
echo -e "${CYAN}====================================================================${NC}"
echo -e "Press Ctrl+C to terminate the system.\n"

export PYTHONPATH="$ROOT_DIR/team2-backend:$ROOT_DIR/team3-ml-simulation:$PYTHONPATH"
cd "$ROOT_DIR/team2-backend"
$PYTHON_BIN -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

