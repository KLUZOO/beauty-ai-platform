FROM node:20-alpine AS builder
WORKDIR /app

ENV CYPRESS_INSTALL_BINARY=0

COPY package*.json ./

RUN npm ci --ignore-scripts


COPY . .


RUN npx vite build


FROM nginxinc/nginx-unprivileged:stable-alpine

COPY --chown=nginx:nginx --from=builder /app/dist /usr/share/nginx/html/beauty.ai

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
