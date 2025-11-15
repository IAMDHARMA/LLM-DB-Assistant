FROM python:3.11-slim
WORKDIR /app
COPY backend/ /app/
RUN pip install --no-cache-dir -r requirements.txt

ENV GOOGLE_API_KEY=""
ENV FERNET_KEY=""


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
