import json

with open('output/pose_data.json', 'r') as f:
    data = json.load(f)

print(f'总帧数: {len(data)}')
print(f'第1帧 position: {data[0]["persons"][0]["position"]}')
print(f'第50帧 position: {data[49]["persons"][0]["position"]}')
print(f'最后1帧 position: {data[-1]["persons"][0]["position"]}')

# 检查是否所有帧都一样
all_same = all(d["persons"][0]["position"] == data[0]["persons"][0]["position"] for d in data)
print(f'\n所有帧位置相同: {all_same}')

# 找出位置变化的帧
print('\n位置变化的帧:')
prev_pos = data[0]["persons"][0]["position"]
changes = 0
for i, d in enumerate(data[1:], 1):
    curr_pos = d["persons"][0]["position"]
    if curr_pos != prev_pos:
        changes += 1
        if changes <= 5:  # 只打印前5个变化
            print(f'  第{i}帧: {prev_pos} -> {curr_pos}')
    prev_pos = curr_pos
print(f'总共有 {changes} 帧位置发生变化')
