#!/bin/bash

# Create directories for optimized images
mkdir -p public/images/hero/desktop
mkdir -p public/images/hero/mobile

# Array of image URLs
urls=(
  "https://i.pinimg.com/736x/ff/96/71/ff96715736a5f2daa19cb1a558b27f69.jpg"
  "https://i.pinimg.com/736x/05/41/04/0541041435ed5f74de007961837bb31d.jpg"
  "https://i.pinimg.com/736x/01/c1/e8/01c1e82212d2bd1d7886a60bf2a1c797.jpg"
  "https://i.pinimg.com/736x/de/fc/39/defc39531043ba2c6b363dd2a15541d8.jpg"
  "https://i.pinimg.com/736x/e5/e8/dc/e5e8dcd67419294bc3b110f753dee787.jpg"
  "https://i.pinimg.com/736x/11/cb/74/11cb74427fdc40ddc3db046aeaf53fa0.jpg"
  "https://i.pinimg.com/736x/94/02/58/9402583515e12f806e5130fe7d44a777.jpg"
  "https://i.pinimg.com/736x/96/84/2a/96842a8a7c85158ab4cc5a8bff58fc80.jpg"
)

echo "Downloading and optimizing images..."

# Download and optimize each image
for i in "${!urls[@]}"; do
  num=$((i + 2))  # Start from 2 since image 1 is the original
  url="${urls[$i]}"
  
  echo "Processing image $num..."
  
  # Download original
  wget -q "$url" -O "/tmp/hero-$num-original.jpg"
  
  # Create desktop version (1920px, quality 75)
  convert "/tmp/hero-$num-original.jpg" \
    -resize 1920x \
    -quality 75 \
    "public/images/hero/desktop/hero-$num.jpg"
  
  # Create mobile version (1080px, quality 70)
  convert "/tmp/hero-$num-original.jpg" \
    -resize 1080x \
    -quality 70 \
    "public/images/hero/mobile/hero-$num.jpg"
  
  # Clean up temp file
  rm "/tmp/hero-$num-original.jpg"
  
  echo "✓ Image $num optimized"
done

# Also optimize the existing hero image
if [ -f "src/assets/hero-image.jpg" ]; then
  echo "Optimizing original hero image..."
  
  # Desktop version
  convert "src/assets/hero-image.jpg" \
    -resize 1920x \
    -quality 75 \
    "public/images/hero/desktop/hero-1.jpg"
  
  # Mobile version
  convert "src/assets/hero-image.jpg" \
    -resize 1080x \
    -quality 70 \
    "public/images/hero/mobile/hero-1.jpg"
  
  echo "✓ Original hero image optimized"
fi

echo ""
echo "✅ All images optimized!"
echo "Desktop images: public/images/hero/desktop/"
echo "Mobile images: public/images/hero/mobile/"
