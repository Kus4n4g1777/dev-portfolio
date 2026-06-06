# Stage 1: Build Angular
FROM node:20 AS build

RUN apt-get update && apt-get install -yq \
    gconf-service \
    libasound2 \
    libatk-bridge2.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    libappindicator1 \
    libnss3 \
    lsb-release \
    xdg-utils \
    wget \
    libgbm1 \
    libvulkan1 \
    --no-install-recommends \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb \
    && apt-get -f install --yes \
    && rm google-chrome-stable_current_amd64.deb

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

RUN npx ng test --watch=false --browsers=ChromeHeadlessNoSandbox

RUN npx ng build --configuration production

# Stage 2: Serve with Nginx
FROM nginx:alpine

COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# ── SPA routing fix ──────────────────────────────────────────────────────────
# Angular uses client-side routing — NGINX must serve index.html for all routes
# and let Angular's router handle navigation. Without this, refreshing on any
# route other than / returns 404 because NGINX looks for a physical directory.
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
