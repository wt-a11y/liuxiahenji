import json

with open('output/pose_data.json', 'r') as f:
    data = json.load(f)

print(f'总帧数: {len(data)}')

if data:
    first_person = data[0]['persons'][0] if data[0]['persons'] else None
    last_person = data[-1]['persons'][0] if data[-1]['persons'] else None
    
    if first_person and last_person:
        first_pos = first_person['position']
        last_pos = last_person['position']
        
        print(f'第1帧 position: {first_pos}')
        print(f'最后1帧 position: {last_pos}')
        
        dx = last_pos[0] - first_pos[0]
        dy = last_pos[1] - first_pos[1]
        distance = (dx**2 + dy**2)**0.5
        
        print(f'位置变化: x={dx:.1f}, y={dy:.1f}')
        print(f'总移动距离: {distance:.1f} 像素')
        
        # 检查是否所有帧都一样
        all_positions = [d['persons'][0]['position'] if d['persons'] else None for d in data]
        unique_positions = set(tuple(p) if p else None for p in all_positions)
        
        print(f'\n唯一位置数: {len(unique_positions)}')
        if len(unique_positions) == 1:
            print("⚠️  所有帧位置都相同！")
        else:
            print(f"✓ 检测到 {len(unique_positions)} 种不同位置")
