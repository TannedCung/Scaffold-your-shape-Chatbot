#!/bin/bash

# Build script for Pili Chatbot with automatic date tagging
# Usage: ./build.sh [command]
# Commands: build, up, down, push

set -e

# Get today's date in YYYYMMDD format
export BUILD_DATE=$(date +%Y%m%d)
export IMAGE_TAG="tannedcung/scaffold-your-shape:pili-${BUILD_DATE}"

echo "🏗️  Building Pili Chatbot with tag: ${IMAGE_TAG}"

# Default command is build
COMMAND=${1:-build}

case $COMMAND in
    "build")
        echo "📦 Building Docker image..."
        docker compose build pili-api
        echo "✅ Build completed: ${IMAGE_TAG}"
        ;;
    "up")
        echo "🚀 Starting services..."
        docker compose up -d
        echo "✅ Services started"
        ;;
    "down")
        echo "🛑 Stopping services..."
        docker compose down
        echo "✅ Services stopped"
        ;;
    "push")
        echo "📤 Pushing image to registry..."
        docker tag pili-chatbot ${IMAGE_TAG}
        docker push ${IMAGE_TAG}
        echo "✅ Image pushed: ${IMAGE_TAG}"
        ;;
    "build-and-up")
        echo "📦 Building and starting services..."
        docker compose up -d --build
        echo "✅ Services built and started"
        ;;
    "logs")
        echo "📋 Showing logs..."
        docker compose logs -f pili-api
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "Available commands: build, up, down, push, build-and-up, logs"
        exit 1
        ;;
esac

echo "🏷️  Current image tag: ${IMAGE_TAG}" 