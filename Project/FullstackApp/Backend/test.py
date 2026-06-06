def solve(boxes_a, boxes_b, boxes_c):
    stacks = {'A': list(boxes_a), 'B': list(boxes_b), 'C': list(boxes_c)}
    commands = []
    
    def move(src, dst):
        stacks[dst].append(stacks[src].pop())
        commands.append(f"{src} {dst}")

    # These lines must be outside the 'move' function!
    target_order = sorted(stacks['A'] + stacks['B'] + stacks['C'], reverse=True)
    
    sorted_count = 0
    for current, target in zip(stacks['A'], target_order):
        if current == target:
            sorted_count += 1
        else:
            break
            
    while len(stacks['A']) > sorted_count:
        move('A', 'B')
        
    for target in target_order[sorted_count:]:
        src = 'B' if target in stacks['B'] else 'C'
        aux = 'C' if src == 'B' else 'B'
        
        while stacks[src][-1] != target:
            move(src, aux)
            
        move(src, 'A')
        
    return commands