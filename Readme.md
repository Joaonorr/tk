# tk Test Helper

<!--TOC_BEGIN-->
- [Instalação](#instalação)
- [Exemplos rápidos](#exemplos-rápidos)
- [Subcomandos](#subcomandos)
    - [List](#list)
    - [Run](#run)
    - [Compile](#compile)
    - [Build](#build)
    - [Update](#update)
- [Formatos de testes suportados](#formatos-de-testes-suportados)
    - [VPL](#vpl)
    - [OBI](#obi)
    - [TIO](#tio)
- [Rodando](#rodando)
- [Exemplo de problema](#exemplo-de-problema)

<!--TOC_END-->

## Instalação

**Linux**
Para baixar ou atualizar execute esse comando
```
sh -c "$(wget -O- https://raw.gitkubusercontent.com/senapk/tk/master/tools/install_linux.sh)"
```

**Windows**

- Baixe o arquivo tk.py para algum diretório que esteja no path.

## Exemplos rápidos
```bash
# mostra os testes
tk list t.tio

# roda o executável solver.c e usa o arquivo t.tio como pacote de testes
tk run solver.c t.tio

# se seus testes estiverem em arquivos com a extensão .tio ou .vpl ou .md
# para listar basta digitar
tk list

# se os códigos de resposta iniciarem com a palavra solver, basta digitar
tk run

# roda apenas o teste número 3
tk run solver.py t.tio -t 3

# se os testes estiverem no formato da OBI, .in .sol, na pasta testes basta utilizar assim:
tk list "testes @.in @.sol"
# ou então rodar usando
tk run solver.cpp "testes @.in @.sol"

# para converter os vários testes de uma pasta em um único arquivo no formato .tio
tk build t.tio pasta1 pasta2 pasta3
```

## Subcomandos

```
usage: tk [-h] {list,run,build,update} ...

Roda, Converte e Contrói testes de entrada e saída.
Use "./tk comando -h" para obter informações do comando específico.

Exemplos:
    ./tk list t.vpl                        # lista os testes
    ./tk list t.vpl -d                     # mostra os testes
    ./tk list t.vpl -d -i 5                # mostra apenas o teste índice 5
    ./tk compile main.c                    # apenas compila o arquivo main.c para main.c.out
    ./tk run solver.c t.tio                # roda o comando e verifica utilizando o arquivo t.tio
    ./tk run solver.exe t.vpl              # roda o comando e verifica utilizando o arquivo t.vpl

optional arguments:
  -h, --help            show tk help message and exit

subcommands:
  {list,run,build,update,compile}
                        help for subcommand
    list                show case packs or folders.
    run                 run you solver
    build               build a test target
    update              update a test target
    compile             compile you solver.

```

### List
```
usage: tk list [-h] [--brief] [--raw] [--index I] [--display] [T [T ...]]

positional arguments:
  T                targets

optional arguments:
  -h, --help       show this help message and exit
  --brief, -b      show less information
  --raw, -r        raw mode, disable whitespaces rendering
  --index I, -i I  run a specific index
  --display, -d    display full test description

```

### Run
```bash
usage: tk run [-h] [--brief] [--raw] [--index I] [--all] [--none] [T [T ...]]

positional arguments:
  T                solvers, test cases or folders

optional arguments:
  -h, --help       show this help message and exit
  --brief, -b      show less information
  --raw, -r        raw mode, disable whitespaces rendering
  --index I, -i I  run a specific index
  --all, -a        show all failures
  --none, -n       show none failures

```

### Compile
```bash
usage: tk compile [-h] [--keep] cmd

positional arguments:
  cmd         solver cmd to compile

optional arguments:
  -h, --help  show this help message and exit
  --keep, -k  keep all compilation files
```


### Build
```bash
usage: tk build [-h] [--unlabel] [--number] [--sort] [--force] T_OUT T [T ...]

positional arguments:
  T_OUT          target to be build.
  T              input test targets.

optional arguments:
  -h, --help     show this help message and exit
  --unlabel, -u  remove all labels
  --number, -n   number labels
  --sort, -s     sort test cases by input size
  --force, -f    enable overwrite

```

### Update
```bash
usage: tk update [-h] [--unlabel] [--number] [--sort] [--cmd CMD] T [T ...]

positional arguments:
  T                  input test targets.

optional arguments:
  -h, --help         show this help message and exit
  --unlabel, -u      remove all labels
  --number, -n       number labels
  --sort, -s         sort test cases by input size
  --cmd CMD, -c CMD  solver file or command to update outputs

```

## Formatos de testes suportados
O script suporta os seguintes formatos de testes:

- LEITURA
  - obi: uma pasta com arquivos diferentes para entrada e saída.
  - .vpl: formato utilizado pelo vpl no moodle
  - .tio: formato equivalente ao vpl, mais otimizado para visualização.
  - .md: contendo testes em diversos formatos.
- UPDATE
  - vpl, tio, md
- BUILD
  - obi, vpl, tio
  
O script pode ser utilizado para rodar seu código contra os testes ou converter entre os formatos.


### VPL

O formato VPL é utilizado no moodle e tem toda definição dos testes a serem executados em um único arquivo. Seja o problema que envolve ler dois números, um por linha e exibir a soma e a subtração em linhas separadas. Um típico teste VPL seria assim. Você pode encontrar esse exemplo na pasta *exemplo_readme/VPL*.

```
case=
input=5
4
output="9
1
"
grade reduction=100%

case=invertido
input=3
-7
output="-4
10
"

case=numeros_grandes
input=1000000
1000000
output="2000000
0
"
grade reduction=50%
```

Regras
- Todos os testes devem ter obrigatoriamente as tags case, input e output.
- Eviter colocar espaços antes e depois do igual quando definir as tags:
- O output
    - Deve terminar com uma linha vazia
    - Deve ter aspas no inicio e fim

**Errado**
```
case = nome
case= nome
case =nome
output=5 9
output="5 9"
grade reduction = 100%
```
**Certo**
```
case=nome
input=value
output="value
"
grade reduction=40%
```
- O conteúdo do case é opcional.
- Se não houver o valor da tag grade reduction, a redução da nota será proporcional à quantidade de testes.
    - Se existem 5 testes. Cada teste vale 20% da notas.
    - Se em um caso for aplicado um grade reduction de 50%, ao errar o teste o aluno perde 50% da nota.

### OBI

A OBI mudou o formato de teste com o passar dos anos. Vamos utilizar o modelo de 2017 como referência. Nele, cada caso de teste é formado por dois arquivos, um arquivo .in que contém a entrada e um arquivo .sol que contém a solução esperada. Seja o problema que consiste em ler dois números, um por linha e escrever na primeira linha a soma e na segunda a subtração.
Para ler ou executar uma pasta com os testes nesse formato, o parâmetro a ser passado seria

    tk list "pasta @.in @.sol"

```
==> 1.in <==
5
4

==> 1.sol <==
9
1

==> 2.in <==
3
-7

==> 2.sol <==
-4
10

==> 3.in <==
1000000
1000000

==> 3.sol <==
2000000
0

```

### TIO

O formato é o seguinte

```
>>>>>>>> nome_do_caso_opcional grade_reduction_opcional%
input
...
input
========
output
...
output
<<<<<<<<

```
- Se não for informado o grade reduction, será de 100%
- Se o grade informador for !%, será porporcional ao número de questões.
- O nome do caso é opcional.

## Rodando

    tk run solver_cmd [list of input]

Se o comando for .py, .js, .h, .c, .cpp ele compila ou prepara e roda contra os testes.

    tk run main.c t.tio
    tk run main.js Readme.md

Você também pode passar o executável que compilou
    
    tk run main.exe t.vpl
    
Se você não digitar nenhum parâmtro após o run, ele vai procurar na pasta atual
por todos os arquivos que começam com a palavra `solver` e também por todos os arquivos
que terminam com as extensões `.md`, `.vpl` e `.tio`.

## Exemplo de problema
O problema a seguir é: leia 3 números, um por linha e informe quantos são iguais.

```
>>>>>>>>
1
1
1
========
3 iguais
<<<<<<<<

>>>>>>>> dois primeiros 10%
1
1
2
========
2 iguais
<<<<<<<<

>>>>>>>> ultimos
1
2
2
========
2 iguais
<<<<<<<<

>>>>>>>> pontas
3
2
3
========
2 iguais
<<<<<<<<

>>>>>>>> todos diferentes 100%
3
2
2
========
diferentes
<<<<<<<<
```
