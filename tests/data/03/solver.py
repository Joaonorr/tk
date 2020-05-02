lista = list(map(int, input().split(" ")))
impares = [x for x in lista if x % 2 == 1]
pares = [x for x in lista if x % 2 == 0]
impares.sort()
pares.sort()
print(impares, end='')
print(pares)
