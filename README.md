# INE5622 — Introdução a Compiladores (UFSC, 2026.2)

Atividades da disciplina INE5622, turma 06238 (Sistemas de Informação, noturno),
Departamento de Informática e Estatística da UFSC. Docente: Prof. Alvaro Junio Pereira Franco.

**Ementa:** Gramáticas, Autômatos e Linguagens; Análise Léxica; Análise Sintática; Análise
Semântica e Geração de Código.

## Atividades

| Atividade | O que é | Unidade do plano de ensino |
|---|---|---|
| [`atividades/analisador-lexico-diagramas`](atividades/analisador-lexico-diagramas/) | Analisadores léxicos baseados em diagramas de transição: ex. 1 (IDENT, BRANCO, OUTRO) e ex. 2 (+ NI, NPF). Python tipado (`mypy --strict`), leitura caractere a caractere, simulação das tabelas de transição com `lexemeBegin`/`forward` | 4 · Análise Léxica (4.1 AFD, 4.4 ER, 4.6 implementação) |

Para rodar os testes da atividade:

```bash
cd atividades/analisador-lexico-diagramas
bash testar.sh
```

## Avaliação (plano de ensino)

```
MF = (AT1 + 2·AT2 + 3·AT3) / 6
```

| Semana | Avaliação |
|---|---|
| 9ª | AT1 |
| 10ª → 16ª | AT2 (trabalho de 6 semanas) |
| 16ª | AT3 e entrega da AT2 |
| 17ª | Segunda chamada |
| 18ª | Recuperação |

## Materiais

- [`materiais/planoEnsino_INE5622_20262_06238.pdf`](materiais/planoEnsino_INE5622_20262_06238.pdf) — plano de ensino 2026.2
- Bibliografia básica [1]: R. de Santiago, *Anotações para a Disciplina de Introdução a
  Compiladores*, 2020 — www.inf.ufsc.br/~r.santiago/downloads/INE5622.pdf
