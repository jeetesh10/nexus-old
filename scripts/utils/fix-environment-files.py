#!/usr/bin/env python3
"""
Fix Environment Files for Postman API
Converts environment files to proper Postman API format
"""

import json
import os

def fix_environment_file(input_file, output_file):
    """Fix environment file format for Postman API"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            env_data = json.load(f)
        
        # Wrap in environment object
        fixed_env = {
            "environment": env_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_env, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Fixed environment file: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error fixing environment file {input_file}: {e}")
        return False

def main():
    """Main function"""
    env_files = [
        "nexus_platform_development_environment.json",
        "nexus_platform_staging_environment.json",
        "nexus_platform_production_environment.json"
    ]
    
    for env_file in env_files:
        input_path = f"postman-collections/{env_file}"
        output_path = f"postman-collections/fixed_{env_file}"
        
        if os.path.exists(input_path):
            fix_environment_file(input_path, output_path)
        else:
            print(f"⚠️  Environment file not found: {input_path}")

if __name__ == "__main__":
    main()
