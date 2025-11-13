# Stage 1: Build Angular
FROM node:20 AS build

# 🔽 UPDATED: Added libgbm1 and libvulkan1 to the initial install list
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
    # 💥 ADDED MISSING CHROME DEPENDENCIES 💥
    libgbm1 \
    libvulkan1 \
    --no-install-recommends \
    # Download and install Google Chrome
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    # Install the package
    && dpkg -i google-chrome-stable_current_amd64.deb \
    # Fix any remaining broken dependencies (just in case)
    && apt-get -f install --yes \
    # Clean up
    && rm google-chrome-stable_current_amd64.deb

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the frontend source
COPY . .

# 💥 RUN JASMINE/KARMA TESTS (Using our new launcher) 💥
RUN npx ng test --watch=false --browsers=ChromeHeadlessNoSandbox

# Build Angular for production
RUN npx ng build --configuration production

# Stage 2: Serve with Nginx
FROM nginx:alpine


# Copy Angular build output to Nginx html folder
# (Update 'dashboard-admin' if your project name is different in angular.json)
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]