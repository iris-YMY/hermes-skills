#!/usr/bin/env python3
"""列出用户自建 Skill（不在 bundled manifest 中的）

用途：在发布前快速了解哪些 Skill 是用户自己创建/定制的
输出：按分类列出 skill 名称、描述、路径
"""

import os
import re
from pathlib import Path

def main():
    skills_dir = Path.home() / '.hermes' / 'skills'
    manifest_path = skills_dir / '.bundled_manifest'
    
    # 读取 bundled skills
    bundled = set()
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            for line in f:
                if ':' in line:
                    skill_name = line.split(':')[0].strip()
                    bundled.add(skill_name)
    
    # 查找所有 SKILL.md
    user_skills = []
    for root, dirs, files in os.walk(skills_dir):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file == 'SKILL.md':
                skill_path = Path(root) / file
                skill_dir = skill_path.parent
                skill_name = skill_dir.name
                parent_dir = skill_dir.parent.name
                
                # 如果不在 bundled 中，就是用户自建的
                if skill_name not in bundled:
                    # 读取描述
                    description = "无描述"
                    try:
                        with open(skill_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            match = re.search(r'description:\s*(.+?)[\n\r]', content, re.IGNORECASE)
                            if match:
                                description = match.group(1).strip().strip('"\'')
                    except:
                        pass
                    
                    category = parent_dir if parent_dir != 'skills' else '独立'
                    user_skills.append({
                        'name': skill_name,
                        'category': category,
                        'description': description,
                        'path': str(skill_dir).replace(str(Path.home()), '~')
                    })
    
    # 按分类排序
    user_skills.sort(key=lambda x: (x['category'], x['name']))
    
    # 输出
    print("=" * 80)
    print(f"🔨 用户自建 Skill 清单（共 {len(user_skills)} 个）")
    print("=" * 80)
    
    current_category = None
    for skill in user_skills:
        if skill['category'] != current_category:
            current_category = skill['category']
            print(f"\n📁 {current_category}")
            print("-" * 80)
        
        desc = skill['description']
        if len(desc) > 60:
            desc = desc[:57] + "..."
        
        print(f"  • {skill['name']}")
        print(f"    {desc}")
        print(f"    路径: {skill['path']}")
    
    print("\n" + "=" * 80)
    print(f"总计: {len(user_skills)} 个用户自建 Skill")
    print("=" * 80)

if __name__ == '__main__':
    main()
