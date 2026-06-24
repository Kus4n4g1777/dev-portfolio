# We use the official lean Node image
FROM node:20-alpine AS base
WORKDIR /app

# We copy the dependency definitions first to leverage Docker layer caching
COPY package.json package-lock.json* ./

# We cleanly install the dependencies
RUN npm install

# We copy the rest of our Next.js application code
COPY . .

# We build the Next.js App Router for production
RUN npm run build

# We expose the port Next.js uses inside the container
EXPOSE 3000
ENV PORT=3000

# We start the production server
CMD ["npm", "start"]
