# Use an official Python base
FROM python:3.11-slim

# Install system deps including tesseract and fonts
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    poppler-utils \
    build-essential \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create app dir
WORKDIR /app

# Copy requirements and install Python deps
COPY req.txt requirements.txt /app/
# make sure your requirements are in either req.txt or requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/req.txt || pip install -r /app/requirements.txt

# Copy app code
COPY . /app

# Expose the port that Render assigns
ENV PORT 8080

# Run streamlit with the port Render provides
CMD ["bash", "-lc", "streamlit run main.py --server.port $PORT --server.address 0.0.0.0"]
