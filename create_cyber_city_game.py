#!/usr/bin/env python3
"""
Generate Cyber City Protection Squad Game using DecipherWorld Framework
Demonstrates rapid game development with scaffolding tools
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decipherworld.settings.base')
django.setup()

from games.utils.builders import GameScaffold


def main():
    """Generate the Cyber City Protection Squad game"""
    
    print("🏙️ Generating Cyber City Protection Squad Game")
    print("=" * 60)
    
    # Create the game scaffold
    scaffold = GameScaffold(
        game_name="Cyber City Protection Squad",
        game_type="cyber_security",
        app_name="cyber_city"
    )
    
    print("🔧 Creating game structure...")
    structure = scaffold.create_game_structure()
    
    # Create the directory structure
    game_dir = "cyber_city"
    os.makedirs(game_dir, exist_ok=True)
    os.makedirs(f"{game_dir}/templates/cyber_security", exist_ok=True)
    os.makedirs(f"{game_dir}/static/cyber_security", exist_ok=True)
    
    # Write the generated files
    files_created = []
    
    # Models
    with open(f"{game_dir}/models.py", "w") as f:
        f.write(structure['models'])
    files_created.append("models.py")
    
    # Views
    with open(f"{game_dir}/views.py", "w") as f:
        f.write(structure['views'])
    files_created.append("views.py")
    
    # Plugin
    with open(f"{game_dir}/plugin.py", "w") as f:
        f.write(structure['plugin'])
    files_created.append("plugin.py")
    
    # URLs
    with open(f"{game_dir}/urls.py", "w") as f:
        f.write(structure['urls'])
    files_created.append("urls.py")
    
    # Admin
    with open(f"{game_dir}/admin.py", "w") as f:
        f.write(structure['admin'])
    files_created.append("admin.py")
    
    # Templates
    for template_name, template_content in structure['templates'].items():
        template_path = f"{game_dir}/templates/cyber_security/{template_name}"
        with open(template_path, "w") as f:
            f.write(template_content)
        files_created.append(f"templates/cyber_security/{template_name}")
    
    # Create __init__.py
    with open(f"{game_dir}/__init__.py", "w") as f:
        f.write("# Cyber City Protection Squad Game")
    files_created.append("__init__.py")
    
    print("✅ Game scaffold generated successfully!")
    print(f"📁 Created directory: {game_dir}/")
    print("📄 Generated files:")
    for file in files_created:
        print(f"   • {file}")
    
    print("\n🎮 Next Steps:")
    print("1. Customize models for cybersecurity game")
    print("2. Enhance views with avatar system")
    print("3. Create cyberpunk-themed templates")
    print("4. Add 5 security challenges")
    print("5. Integrate AI Captain Tessa")
    
    return structure


if __name__ == '__main__':
    structure = main()