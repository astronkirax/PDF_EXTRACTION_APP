# Dockerfile (use this exact content)
FROM python:3.11-slim

# Install system deps including tesseract and helper packages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    poppler-utils \
    build-essential \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the requirements file you have (req.txt)
COPY req.txt /app/req.txt

# Upgrade pip and install Python deps
RUN pip install --upgrade pip
RUN pip install -r /app/req.txt

# Copy the rest of the app code
COPY . /app

# Expose port for Render
ENV PORT 8080

# Run Streamlit on the provided port
CMD ["bash", "-lc", "streamlit run main.py --server.port $PORT --server.address 0.0.0.0"]
