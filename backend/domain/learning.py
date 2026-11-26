from math import cos, pi, sin, sqrt

MINUTES_PER_DAY = 1440

def phase_point(minute):
    angle = 2 * pi * minute / MINUTES_PER_DAY
    return (cos(angle), sin(angle))

def phase_distance(a, b):
    first, second = phase_point(a), phase_point(b)
    return sqrt(sum((x-y)**2 for x,y in zip(first,second,strict=True)))

def circular_minutes(a, b):
    gap = abs(a-b)
    return min(gap, MINUTES_PER_DAY-gap)

def calculate(data):
    target = data['target']
    neighbors = []
    for item in data['history']:
        phase = phase_distance(target['opening_minute'], item['opening_minute'])
        spread = abs(item['minutes'] - target['minutes'])
        neighbors.append({'窗口': item['code'], '开始': item['opens'], '结束': item['closes'],
            '绕午夜相差分钟': circular_minutes(target['opening_minute'], item['opening_minute']),
            '时长差分钟': spread, '距离': round(phase + spread / 180, 6)})
    neighbors.sort(key=lambda row: (row['距离'], row['窗口']))
    return {'目标':target['code'], '邻窗':neighbors[:5], '样本量':len(neighbors)}
