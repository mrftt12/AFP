# Development Dockerfile for React frontend
FROM node:16-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source files
COPY . .

# Expose port 3000 for React dev server
EXPOSE 3000

# Start the development server with hot reload
CMD ["npm", "start"]