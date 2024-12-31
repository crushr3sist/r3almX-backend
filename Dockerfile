FROM python:3.14.0a3-slim	

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "r3almX_backend:r3almX", "--host", "0.0.0.0", "--port", "8000"]
