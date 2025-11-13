# Stage 1: Build & Test React
FROM node:20-alpine AS build
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the app
COPY . .

# 💥 RUN JEST TESTS 💥
# Assumes 'npm test' is configured in your package.json
RUN npm test

# Build static files for production
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy React build output to Nginx html folder
# (Vite/CRA default is 'dist' or 'build'. Adjust if yours is different.)
COPY --from=build /app/dist /usr/share/nginx/html
# If using Create React App, it might be:
# COPY --from=build /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]