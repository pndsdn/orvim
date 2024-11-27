# Сборка фронта
```
cd frontend
yarn install && yarn build
mv ./dist/ ../nginx/
```

# Развертывание
```
docker compose up -d --build
```