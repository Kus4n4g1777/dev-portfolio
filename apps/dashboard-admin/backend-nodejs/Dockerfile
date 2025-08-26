# --- Stage 1: Build Stage ---
#This stage is responsible for installing all dependencies (including dev dependencies)
# and compiling the TypeScript code into JavaScript.
#Use an official Node.js runtime as a parent image
#We'll use a specific version for stability (e.g., Node.js 20 with Alpine Linux for smaller image size)
FROM node:20-alpine as build-stage

# Set the working directory inside this stage-container
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
# This step installs all dependencies, including development ones. If package.json doesn't change, this layer is cached.
COPY package*.json ./

# Install all dependencies (including devDependencies needed for compilation)
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the NestJS aplication
# This compiles the TypeScript source files into JavaScript
# Typically outputting them into a 'dist' directory/
RUN npm run build

# --- Stage 2: Production Stage ---
# This stage creates the final, lean image. It only includes the compiled
# application core and the minimal runtime dependencies.
FROM node:20-alpine as production-stage

# Set the working directory for the production application
WORKDIR /app

# Copy only the production dependencies from package.json
# We do this to ensure only necessary runtime packages are installed
COPY package.json ./

# Install only production dependencies
# The --omit=dev flag ensures devDependencies are skipped.
RUN npm install --omit=dev

# Copy the compiled application code from the 'build-stage'
# The 'dist' folder contains the JavaScript output from 'npm run build'
COPY --from=build-stage /app/dist ./dist

# Copy any other necessary production files (e.g., public assets, config files not built)
# For a NestJS app, often the 'dist' folder is sufficient, but if you have
# static assets or non-TypeScript config files outside 'src' that need to be in 'dist',
# you might need to copy them explicitly or ensure your NestJS build process handles them.
# For now, we'll assume 'dist' contains everything needed.
# Example: COPY --from=build-stage /app/public ./public

# Expose the port the NestJS application will run on
# This should match the port configured in your NestJS app (default 3000, but we'll use 3001 as per docker-compose.yml)
EXPOSE 3001

# Command to run the application
# 'node dist/main' runs the compiled JavaScript application
CMD ["node", "dist/main"]
