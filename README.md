# Сборка фронта
```
cd orvim-frontend
yarn install && yarn build
mkdir ../nginx/public
mv dist/* chat-widget/ ../nginx/public
```

# Развертывание
```
cp .env.example .env
docker compose up -d --build
```