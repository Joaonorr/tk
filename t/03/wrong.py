lista = list(map(int, input().split(" ")))
impares = [x for x in lista if x % 2 == 1]
pares = [x for x in lista if x % 2 == 0]
print(impares, end='')
print(pares)
