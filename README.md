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
docker network create orvim
docker compose up -d --build
```

## Модели
Для развертывания моделей:
```
cd orvim-models
```
### CPU версия
```
docker compose -f docker-compose.cpu.yaml up -d --build
```
### GPU версия
```
docker compose -f docker-compose.gpu.yaml up -d --build
```