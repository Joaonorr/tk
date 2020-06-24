- Instalação
    - Linux
        - Instalação local na pasta ~/bin pelo script do github
    - Windows
        - Instalação manual
- O que é um teste?
    - Um teste define qual o comportamento esperado de um programa determinístico. Para uma determinada entrada, o programa deve gerar **sempre** a mesma saída.
    - A entrada, a saída e o comportamento esperado devem ser bem definidos, por exemplo:
        - Dados dois números inteiros de entrada, um por linha, mostre o resultado da divisão. Se o resultado for inteiro, mostre o valor inteiro, se for flutuante, mostre com duas casas decimais.
    - Formatos de teste:
        - Um arquivo de texto com vários testes:
            - modelo TIO(test input output).
            - modelo VPL que é utilizado no plugin do moodle.
        - Uma pasta com um dois arquivos para cada teste, um arquivo com a entrada e outro com a saída.
            - modelo maratona:
                - Arquivos .in e .out
                - Arquivos .in e .sol

---
### Sintaxe TIO
```
>>>>>>>>
entrada
...
========
saída
...
<<<<<<<<

>>>>>>>>
entrada
...
========
saída
...
<<<<<<<<
```

---
### Escrevendo alguns testes

Vamos escrever alguns testes para o problema proposto. Crie um arquivo chamado `testes.tio` e vamos inserir algumas entradas para o problema proposto.

```
>>>>>>>>
4
2
========
2
<<<<<<<<

>>>>>>>>
3
2
========
1.50
<<<<<<<<

>>>>>>>>
5
4
========
1.25
<<<<<<<<

>>>>>>>>
1
3
========
0.33
<<<<<<<<
```

---

### Listando os testes
- Salve o arquivo.
- Abra o terminal na pasta onde colocou o arquivo.
- Para simplificar, certifique-se que só existe esse arquivo na pasta.
- Abra o terminal na pasta onde você criou o arquivo `testes.tio`.
- O comando `tk` funciona com subcomandos. 
- O subcomando `tk list` mostra os testes.
    - Mostrando as opções: `tk list -h`
    - Procurando todos os arquivos de teste na pasta: `tk list`
    - Passando explicitamento o arquivo de testes: `tk list testes.tio`
    - Opções:
        - `-d ou --display`: mostra entradas e saídas
        - `-i ou --index`: um índice específico
        - `-r ou --raw`: não renderiza os whitespaces
    - Vamos testar as opções.

---
## Testando seu código
- Crie algum código que resolve o problema.

```python
# solver.py
a = int(input())
b = int(input())
print(a/b)
```

```c
// solver.c
#include <stdio.h>
int main(){
    int a = 0, b = 0;
    scanf("%d %d", &a, &b);
    printf("%d\n", (a/b));
}
```
- Rodando o código
    - Rodando diretamente passando o código fonte
        - `tk run solver.c test.tio`: compila e testa seu código.
        - `tk run solver.py test.tio`: chama o interpretador e testa o código.
        - `tk.run`: Ele procura os arquivos tipo solver* e os arquivo *.tio na pasta.
    - Se você passar o fonte, ele vai compilar utilizando várias critérios.
        - Você pode **APENAS** compilar seu código usando `tk compile arquivo`.
        - Erros de variáveis não declaradas, não utilizadas e muitos outros vão ser "pegues".
            - `gcc -Wall -fsanitize=address -Wuninitialized -Wparentheses -Wreturn-type -Werror -fno-diagnostics-color`
        - `tk` também funciona se você quiser compilar manualmente o código fonte e passar o executável para o script e 
        isso funciona para qualquer linguagem de programação: `tk run executavel testes.tio`
    - Opções extras:
        - As mesmas do list:
            - `-i ou --index`: roda um índice específico
            - `-r ou --raw`: não renderiza os whitespaces
        - `-a ou --all`: mostra todos os testes que falharam e não apenas o primeiro.
- Vamos consertar nosso código
```c
// solver.c
#include <stdio.h>
int main(){
    int a = 0, b = 0;
    scanf("%d %d", &a, &b);
    if(a % b == 0)
        printf("%d\n", (a/b));
    else
        printf("%.2f\n", (float)a/b);
}
```
- Rode agora e ele deve mostrar que todos os testes foram sucesso.
___
### Convertendo entre formatos
- Gerando um `.vpl`
    - `tk build t.vpl testes.tio`
- Gerando ou lendo o modelo de maratona
    - Vamos definir que o padrão de entrada e saída são arquivos `.in` e `.sol`.
        - `tk build "obi @.in @.sol" testes.tio`
    - Se quisesse os testes no formato 00.in out.00, 01.in out.01, ...
        - `tk build "obi @.in out.@" testes.tio`
    - O @ funciona como um wildcard