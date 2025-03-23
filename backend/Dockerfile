ARG PYTHON_VERSION=3.13.2

# ---- Base Image ----
FROM python:${PYTHON_VERSION}-slim as base
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Builder Stage (install dependencies) ----
FROM base as builder

# Copy requirements first, to cache dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install pipenv --user

# ---- Final Stage ----
FROM base as final
WORKDIR /app

# Install same system dependencies in final stage if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (best practice for security)
RUN adduser --disabled-password --gecos '' djangouser
USER djangouser

# Copy system-wide packages from builder
COPY --from=builder /usr/local /usr/local

# Make sure scripts in .local are recognized
ENV PATH=/home/djangouser/.local/bin:$PATH

# Copy project files
COPY . .

# Expose port 8000 for Django development server
EXPOSE 8000

CMD ["pipenv", "run", "start", "0.0.0.0:8000"]
