# Use Node.js 20
FROM node:20

# Create app directory
WORKDIR /app

# Copy package.json and package-lock.json first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

# Expose dev port
EXPOSE 3000

# Start dev server
CMD ["npm", "run", "dev"]