#!/usr/bin/env python3
"""
Script to patch the frontend build to work with local development.
This replaces the hardcoded API URLs with local ones.
"""

import os
import shutil
import re

def patch_frontend():
    """Patch the frontend to use local API endpoints"""
    
    # Backup original files
    dist_dir = "social_story_frontend/dist"
    assets_dir = f"{dist_dir}/assets"
    
    if not os.path.exists(assets_dir):
        print("❌ Frontend dist directory not found!")
        return False
    
    # Find the main JS file
    js_files = [f for f in os.listdir(assets_dir) if f.startswith('index-') and f.endswith('.js')]
    
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
    
    # Read the JS file
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 Original file size: {len(content)} characters")
    
    # Patterns to replace
    replacements = [
        # Replace hardcoded API URLs to point to local proxy (port 3001)
        (r'https://api\.example\.com', 'http://localhost:3001'),
        (r'https://api\.example\.dev', 'http://localhost:3001'),
        (r'api\.example\.com', 'localhost:3001'),
        (r'api\.example\.dev', 'localhost:3001'),
        # Replace accidental references to localhost:3002
        (r'http://localhost:3002', 'http://localhost:3001'),
        (r'https://localhost:3002', 'http://localhost:3001'),
        (r'//localhost:3002', '//localhost:3001'),
        # Add more patterns as needed
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
        print("⚠️  No API URLs found to replace. Let me try a different approach...")
        
        # Try to find any URL patterns that might be API calls
        url_patterns = re.findall(r'https?://[a-zA-Z0-9.-]+[a-zA-Z0-9.-/]*', content)
        if url_patterns:
            print("🔍 Found these URLs in the code:")
            for url in set(url_patterns[:10]):  # Show first 10 unique URLs
                print(f"   - {url}")
        
        # Look for fetch calls or axios calls
        fetch_patterns = re.findall(r'fetch\s*\(\s*["\']([^"\']+)["\']', content)
        if fetch_patterns:
            print("🔍 Found these fetch URLs:")
            for url in set(fetch_patterns[:10]):
                print(f"   - {url}")
    
    # Write the modified content back
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Modified file size: {len(content)} characters")
    print(f"🎯 Made {changes_made} changes to API URLs")
    
    return changes_made > 0

def restore_frontend():
    """Restore the original frontend from backup"""
    
    dist_dir = "social_story_frontend/dist"
    assets_dir = f"{dist_dir}/assets"
    
    js_files = [f for f in os.listdir(assets_dir) if f.startswith('index-') and f.endswith('.js')]
    
    if not js_files:
        print("❌ No main JS file found!")
        return False
    
    js_file = os.path.join(assets_dir, js_files[0])
    backup_file = f"{js_file}.backup"
    
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, js_file)
        print(f"🔄 Restored original file from backup")
        return True
    else:
        print("❌ No backup file found!")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        print("🔄 Restoring original frontend...")
        restore_frontend()
    else:
        print("🔧 Patching frontend for local development...")
        success = patch_frontend()
        
        if success:
            print("\n✅ Frontend patched successfully!")
            print("🌐 Try the frontend again at http://localhost:3001")
        else:
            print("\n⚠️  Patching had limited success. Let me create an alternative solution...")
            
            # Create a JavaScript injection approach
            print("🚀 Creating a runtime API interceptor...")
            
            # This will be handled by the enhanced proxy server
