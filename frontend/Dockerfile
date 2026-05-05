FROM --platform=$BUILDPLATFORM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

COPY index.html vite.config.ts tsconfig*.json ./
COPY src ./src
COPY public ./public

RUN npm run build


FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# nginx entrypoint processes *.template files with envsubst on container start
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Default backend URL — override at runtime with -e BACKEND_URL=http://...
ENV BACKEND_URL=http://backend:8000

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
