tk --single solver.c Readme.md

compilar
executar
comparar os que tiverem sido executados corretamente
mostrar

## Carregar os arquivos .tio, .vpl e Readme.md não ocultos como testes e rodar os arquivos que começam com solver
tk
## Single Solver
### Apenas compilar
tk -s solver.c
### Compilar e testar
tk -s solver.c t.tio Readme.tio
### Compilar e testar apenas alguns testes
tk -s solver.c t.tio -n 5
tk -s solver.c t.tio -n 5-9


## operação de teste e operação de build no mesmo comando
-s solver.c solver.cpp -t t.tio Readme.md --vpl t.vpl --tio t.tio --dir dir

## operação de build only
-t t.tio Readme.md --vpl t.vpl --tio t.tio --dir dir --sort --filter

sort e filter funcionam também no run e no update

tk base/* --vpl .vpl --sort --filter




## Apenas compilar um arquivo .c ou .cpp
tk -c/--compile [par ...]
tk -c solver.c
tk -c solver.c lib.c
tk -c solver.c -o solver ???
tk -c solver.c -lm  ???
## show testes ?? High priority, disable other functions
tk -l/--list
## definir o(s) arquivos de entrada de testes
tk -i/--input Readme.md t.tio
## definir o(s) arquivos de solução
tk -s/--solver solver.c solver.cpp
## modo vertical sem renderizar whitespace
tk -r/--raw
## specify a especific case to be used
tk -n/--number
## generate vpl from testes
tk -v/--vpl t.vpl
## generate tio from testes
tk -t/--tio t.tio
## generate dir from testes
tk -d/--dir directory


## actions
e - execute - [Solver Target ...] [dsf nr]
c - compile - Solver
l - list - [target ...] [dsf nr]
b - build [output_target input_target ...] [dsf n]
u - update [solver target ..]

d, --display - display full case
s, --sort - sort by input size
f, --filter - filter duplicated

n - number
r - raw

- fazer o update e o build
- adicionar suporte ao read from dir
- adicionar suporte ao build do dir
- adicionar o update
- no update, iniciar a numeracao do 00 ao invés do 01
- fazer o htest chamar o tk e rodar o tk em cada pasta
- colocar o -n pra receber um só parâmetro
- fazer o comando check para checar a pasta
- se não passar nenhum parametro ele faz o check .

- deixar filter and sort apenas no update e build

- [x] side by side mostrar as linhas que contem diferenças com o símbolo dotted
- [ ] Colocar um try catch pegando tudo e retornando 0 de não disparou erro.
- [ ] Update
    - [ ] Colocar update para vpl e .tio
    - [ ] Colocar update para .md
    - [ ] Colocar update para .dir
- [ ] CIO
    - [ ] Colocar pra carregar o cio apenas se não achar dio no md
    - [ ] Fazer testes no modelo cio pra quando as coisas estão coladas
    - [ ] Fazer cio com expressões regulares
 

