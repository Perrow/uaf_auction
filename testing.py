# coding=utf-8


my_list = [1, 2, 3, 4, 6, 8, 10, 11, 12, 13, 15, 16, 20, 21, 22]
goal =    [1, "-", 4, 6, 8, 10, "-", 13, 15, "-", 16, 20,"-", 22]
start = my_list[0]

result = []
count = 0
end = None
for current in my_list:
    print("start {} current {} count {}".format(start, current, count))
    if start == current:
        print("start == current")
        result.append(start)
    elif start + count == current:
        print("start + count ", current)
        end = current
    else:
        if end:
            result.append("-")
            result.append(end)
            end = None
        result.append(current)
        start = current
        count = 0
    count += 1

if end:
    result.append("-")
    result.append(end)
print(result)
print(goal)
print(result == goal)

old = None
in_dash = False
new_result = []
for index, current in enumerate(result):
    if current == "-":
        in_dash = True

    if current != "-" and not in_dash:
        if old:
            new_result.append("{}".format(old))
        old = current

    if current != "-" and in_dash:
        new_result.append("{}-{}".format(old, current))
        in_dash = False
        old = None




print(new_result)
print(", ".join(new_result))