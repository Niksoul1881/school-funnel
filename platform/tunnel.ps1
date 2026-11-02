# Публичный туннель к локальному MVP (без аккаунта).
# Запускать при работающем uvicorn на 127.0.0.1:8000.
# В консоли появится https://<id>.lhr.life — это и есть публичная ссылка.
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:127.0.0.1:8000 nokey@localhost.run
