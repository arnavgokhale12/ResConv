FROM python:3.11-slim

# Install system deps (LibreOffice for DOCX -> PDF)
RUN apt-get update && \
    apt-get install -y libreoffice && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Workdir inside container
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Cloud Run will set PORT env var, but Streamlit defaults to 8501.
# We read PORT and pass it to Streamlit.
ENV PORT=8080

CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]
