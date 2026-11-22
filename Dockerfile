FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 app

COPY --chown=app:app src ./src
COPY --chown=app:app SetupWhatsApp.py GetQRCode.py ./

USER app
EXPOSE 8000

CMD ["python", "-m", "src.Main.Main"]
