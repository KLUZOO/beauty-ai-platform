FROM node:20-alpine AS builder
WORKDIR /app

ENV CYPRESS_INSTALL_BINARY=0

COPY package*.json ./

RUN npm ci --ignore-scripts


COPY . .

EXPOSE 5173



CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]