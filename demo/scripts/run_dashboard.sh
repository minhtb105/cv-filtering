#!/bin/bash
# Run Streamlit Dashboard for CV Intelligence Platform

# Set working directory
cd /root/myproject/cv-filtering/demo

# Activate virtual environment
source /root/myproject/cv-filtering/.venv/bin/activate

# Run Streamlit app
echo "🚀 Starting CV Intelligence Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run src/dashboard/app.py --logger.level=info
