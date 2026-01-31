# frontend/Dockerfile

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Копируем package files
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем исходники
COPY . .

# Build аргументы
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Собираем
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Копируем конфиг nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем собранное приложение
COPY --from=builder /app/dist /usr/share/nginx/html

# Порт
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]