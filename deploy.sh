#!/bin/bash
# Copy package.json to root
cp package.json /
cd /

# Install dependencies
npm install

# Build the application
npm run build

# Start the application
npm start
