#!/usr/bin/env python3
"""
Script to patch the frontend build to use production backend API.
This replaces the local API URLs with the production Vercel backend URL.
"""

import os
import shutil
import re

def patch_frontend_for_production():
    """Patch the frontend to use production API endpoints"""
    
    # Production backend URL
    PRODUCTION_API_URL = "https://social-story-backend-kgt8yz10s-alexs-projects-43af42f1.vercel.app"
    
    # Backup original files
    dist_dir = "dist"
    assets_dir = f"{dist_dir}/assets"
    
    if not os.path.exists(assets_dir):
        print("❌ Frontend dist directory not found!")
        return False
    
    # Find the main JS file
    js_files = [f for f in os.listdir(assets_dir) if f.startswith('index-') and f.endswith('.js') and not f.endswith('.backup')]
    
    if not js_files:
        print("❌ No main JS file found!")
        return False
    
    js_file = os.path.join(assets_dir, js_files[0])
    backup_file = f"{js_file}.backup"
    
    print(f"📁 Found JS file: {js_file}")
    
    # Create backup if it doesn't exist
    if not os.path.exists(backup_file):
        shutil.copy2(js_file, backup_file)
        print(f"💾 Created backup: {backup_file}")
    else:
        print(f"📄 Using existing backup: {backup_file}")
        # Restore from backup first
        shutil.copy2(backup_file, js_file)
        print("🔄 Restored from backup to start fresh")
    
    # Read the JS file
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 Original file size: {len(content)} characters")
    
    # Patterns to replace for production
    replacements = [
        # Replace localhost development URLs with production
        (r'http://localhost:3001', PRODUCTION_API_URL),
        (r'http://localhost:8000', PRODUCTION_API_URL),
        (r'http://127\.0\.0\.1:3001', PRODUCTION_API_URL),
        (r'http://127\.0\.0\.1:8000', PRODUCTION_API_URL),
        (r'localhost:3001', PRODUCTION_API_URL.replace('https://', '')),
        (r'localhost:8000', PRODUCTION_API_URL.replace('https://', '')),
        (r'127\.0\.0\.1:3001', PRODUCTION_API_URL.replace('https://', '')),
        (r'127\.0\.0\.1:8000', PRODUCTION_API_URL.replace('https://', '')),
        # Replace any example API URLs
        (r'https://api\.example\.com', PRODUCTION_API_URL),
        (r'https://api\.example\.dev', PRODUCTION_API_URL),
        (r'api\.example\.com', PRODUCTION_API_URL.replace('https://', '')),
        (r'api\.example\.dev', PRODUCTION_API_URL.replace('https://', '')),
    ]
    
    changes_made = 0
    for pattern, replacement in replacements:
        original_content = content
        content = re.sub(pattern, replacement, content)
        matches = len(re.findall(pattern, original_content))
        if matches > 0:
            print(f"🔄 Replaced {matches} instances of '{pattern}' with '{replacement}'")
            changes_made += matches
    
    if changes_made == 0:
        print("⚠️  No local API URLs found to replace.")
        
        # Try to find any URL patterns that might be API calls
        url_patterns = re.findall(r'https?://[a-zA-Z0-9.-]+[a-zA-Z0-9.-/]*', content)
        if url_patterns:
            print("🔍 Found these URLs in the code:")
            for url in set(url_patterns[:10]):  # Show first 10 unique URLs
                print(f"   - {url}")
        
        print(f"ℹ️  Frontend might already be configured correctly or using relative URLs.")
    
    # Write the patched content back
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Patched frontend for production!")
    print(f"📄 New file size: {len(content)} characters")
    print(f"🔗 Frontend will now connect to: {PRODUCTION_API_URL}")
    
    return True

if __name__ == "__main__":
    print("🚀 Patching frontend for production deployment...")
    success = patch_frontend_for_production()
    if success:
        print("✅ Frontend successfully patched for production!")
    else:
        print("❌ Failed to patch frontend!")
