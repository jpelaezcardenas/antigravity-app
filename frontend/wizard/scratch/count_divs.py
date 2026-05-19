
with open(r'C:\Users\jpela\Projects\Contexia\contexia-wizard\components\wizard\steps\Step8Diagnostico.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

open_divs = 0
for i, line in enumerate(lines):
    open_count = line.count('<div')
    close_count = line.count('</div>')
    open_divs += open_count - close_count
    if open_count > 0 or close_count > 0:
        print(f"L{i+1:3} | Open: {open_count} | Close: {close_count} | Net: {open_divs:2} | {line.strip()[:60]}")

print(f"\nFinal net open divs: {open_divs}")
