#!/usr/bin/env python3
"""
Create Windows .ico and macOS .icns files from a PNG source image.

This script:
1. Converts assets/logo_conto.png to assets/logo_conto.ico (Windows)
2. Creates assets/logo_conto.iconset with PNG files at required macOS sizes
   (which can be converted to .icns using: iconutil -c icns assets/logo_conto.iconset)

Usage:
    python scripts/create_icons.py

Requirements:
    - PIL/Pillow (already in requirements.txt)
    - Source image: assets/logo_conto.png (1024x1024 recommended)
"""

import os
import sys
from pathlib import Path
from PIL import Image

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
SOURCE_PNG = ASSETS_DIR / "logo_conto.png"
OUTPUT_ICO = ASSETS_DIR / "logo_conto.ico"
OUTPUT_ICONSET = ASSETS_DIR / "logo_conto.iconset"


def validate_source():
    """Validate that source PNG exists and is readable."""
    if not SOURCE_PNG.exists():
        print(f"❌ Error: Source image not found: {SOURCE_PNG}")
        sys.exit(1)
    
    try:
        img = Image.open(SOURCE_PNG)
        width, height = img.size
        print(f"✅ Source image: {SOURCE_PNG}")
        print(f"   Dimensions: {width}×{height}")
        print(f"   Mode: {img.mode}")
        
        if width < 256 or height < 256:
            print(f"⚠️  Warning: Small source image ({width}×{height}). Recommend 512×512 or larger.")
        
        return img
    except Exception as e:
        print(f"❌ Error reading source image: {e}")
        sys.exit(1)


def create_ico(source_img):
    """Create Windows .ico file from source PNG."""
    print(f"\n📦 Creating Windows .ico file...")
    
    try:
        # Ensure RGBA mode for ICO format
        if source_img.mode != 'RGBA':
            img_rgba = source_img.convert('RGBA')
        else:
            img_rgba = source_img.copy()
        
        # Create .ico with standard Windows icon sizes
        # ICO files can contain multiple sizes for different contexts
        sizes = [
            (16, 16),    # Small icon (taskbar)
            (32, 32),    # Standard icon
            (48, 48),    # Large icon
            (64, 64),    # Extra large
            (128, 128),  # Very large
            (256, 256),  # Largest standard
        ]
        
        # Resize source to 256x256 as base, generate smaller sizes from it
        base = img_rgba.resize((256, 256), Image.Resampling.LANCZOS)
        
        # Create images dict for ICO
        icon_images = []
        for size in sizes:
            if size[0] <= 256:  # Don't upscale
                resized = base.resize(size, Image.Resampling.LANCZOS)
                icon_images.append(resized)
        
        # Save as ICO
        base.save(
            OUTPUT_ICO,
            format='ICO',
            sizes=[(img.size[0], img.size[1]) for img in icon_images]
        )
        
        print(f"✅ Created: {OUTPUT_ICO}")
        print(f"   Size: {OUTPUT_ICO.stat().st_size / 1024:.1f} KB")
        print(f"   Icon contains sizes: {[img.size for img in icon_images]}")
        
    except Exception as e:
        print(f"❌ Error creating .ico file: {e}")
        sys.exit(1)


def create_iconset(source_img):
    """Create macOS .iconset folder with PNG files at required sizes."""
    print(f"\n📦 Creating macOS .iconset folder...")
    
    try:
        # Ensure RGBA mode
        if source_img.mode != 'RGBA':
            img_rgba = source_img.convert('RGBA')
        else:
            img_rgba = source_img.copy()
        
        # Create iconset directory
        OUTPUT_ICONSET.mkdir(exist_ok=True)
        print(f"   Created: {OUTPUT_ICONSET}")
        
        # macOS icon sizes (name convention: icon_<size>x<size>.png)
        # Also include @2x (Retina) versions
        sizes = [
            (16, "icon_16x16"),
            (32, "icon_32x32"),
            (64, "icon_32x32@2x"),
            (128, "icon_128x128"),
            (256, "icon_128x128@2x"),
            (256, "icon_256x256"),
            (512, "icon_256x256@2x"),
            (512, "icon_512x512"),
            (1024, "icon_512x512@2x"),
        ]
        
        # Resize source as base (use 512x512 to avoid upscaling)
        base_size = min(512, source_img.size[0])
        base = img_rgba.resize((base_size, base_size), Image.Resampling.LANCZOS)
        
        created_files = []
        for pixel_size, name in sizes:
            # Don't upscale beyond source
            actual_size = min(pixel_size, source_img.size[0])
            
            if actual_size != 512:
                resized = base.resize((actual_size, actual_size), Image.Resampling.LANCZOS)
            else:
                resized = base.copy()
            
            output_path = OUTPUT_ICONSET / f"{name}.png"
            resized.save(output_path, format='PNG')
            created_files.append((name, actual_size))
        
        print(f"✅ Created {len(created_files)} PNG files in .iconset:")
        for name, size in created_files:
            file_path = OUTPUT_ICONSET / f"{name}.png"
            file_size = file_path.stat().st_size / 1024
            print(f"   {name}.png ({size}×{size}) — {file_size:.1f} KB")
        
        print(f"\n⏭️  Next step (run in terminal):")
        print(f"   iconutil -c icns {OUTPUT_ICONSET}")
        
    except Exception as e:
        print(f"❌ Error creating .iconset folder: {e}")
        sys.exit(1)


def main():
    print("=" * 70)
    print("Icon Generator: PNG → Windows .ico + macOS .iconset")
    print("=" * 70)
    
    # Step 1: Validate source
    source_img = validate_source()
    
    # Step 2: Create .ico for Windows
    create_ico(source_img)
    
    # Step 3: Create .iconset for macOS (to be converted to .icns)
    create_iconset(source_img)
    
    print("\n" + "=" * 70)
    print("✅ Icon generation complete!")
    print("=" * 70)
    print(f"\n📝 Summary:")
    print(f"   ✅ {OUTPUT_ICO} — Ready for Windows builds")
    print(f"   ⏳ {OUTPUT_ICONSET}/ — Ready to convert to .icns")
    print(f"\n🎬 Next steps:")
    print(f"   1. Run: iconutil -c icns {OUTPUT_ICONSET}")
    print(f"   2. This creates: {ASSETS_DIR}/logo_conto.icns")
    print(f"   3. Verify files exist and test locally with PyInstaller")
    print(f"   4. Then commit all files: .ico, .icns, and .iconset/")


if __name__ == '__main__':
    main()
