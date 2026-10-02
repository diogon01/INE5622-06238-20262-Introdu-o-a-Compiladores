#!/usr/bin/env python3
"""
INE5622 - Introdução a Compiladores (2026.2)
Exercício 2: analisador léxico baseado em diagramas de transição.
Tokens: IDENT, BRANCO, NI (número inteiro), NPF (número de ponto flutuante)
e OUTRO.

Roteiro do plano de ensino, unidade 4 (Análise Léxica):
  4.4  cada token é especificado por uma expressão regular;
  4.1  cada expressão vira um autômato finito determinístico M = (Q, Σ, δ, q0, F),
       desenhado como diagrama de transição (diagramas/ex2.png);
  4.6  o analisador simula os diagramas sobre a entrada, lida caractere por
       caractere, com os apontadores lexemeBegin e forward (bibliografia
       básica [1], seção 2.2: tabela de transição + simulador).

Especificação (4.4):
  delim  = ' ' | '\\t' | '\\n' | '\\r' | '\\f' | '\\v'
  letra  = A | ... | Z | a | ... | z
  dígito = 0 | ... | 9
  BRANCO = delim delim*
  IDENT  = letra (letra | dígito)*
  NPF    = dígito dígito* . dígito dígito*
  NI     = dígito dígito*
  OUTRO  = qualquer caractere que não inicie nenhum dos tokens acima

Diagramas (estados numerados como no desenho; * = retrai forward 1 posição;
caractere sem aresta = falha, tenta o próximo diagrama):
  BRANCO:  0 -delim-> 1,   1 -delim-> 1,   1 -outro-> 2*
  IDENT:   3 -letra-> 4,   4 -letra|dígito-> 4,   4 -outro-> 5*
  NPF:     6 -dígito-> 7,  7 -dígito-> 7,  7 -.-> 8,
           8 -dígito-> 9,  9 -dígito-> 9,  9 -outro-> 10*
  NI:     11 -dígito-> 12, 12 -dígito-> 12, 12 -outro-> 13*
  OUTRO:  14 -qualquer-> 15

Os diagramas são tentados nessa ordem. NPF vem antes de NI para que "3.9" seja
reconhecido como um NPF, e não como NI, OUTRO, NI.

Uso:
  python3 lexico.py entrada.txt
  python3 lexico.py < entrada.txt
  python3 lexico.py entrada.txt --lexemas     (mostra o par <nome, lexema>)

Requer Python 3.8 ou mais novo. Tipagem conferida com: mypy --strict lexico.py
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Final, Iterator, List, Mapping, Optional, Sequence, TextIO, Tuple

EOF: Final = ""  # read(1) devolve a string vazia no fim da entrada


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

class NomeToken(Enum):
    IDENT = "IDENT"
    BRANCO = "BRANCO"
    NI = "NI"
    NPF = "NPF"
    OUTRO = "OUTRO"


@dataclass(frozen=True)
class Token:
    """Token = par <nome, atributo>. O atributo guardado é o lexema."""

    nome: NomeToken
    lexema: str
    linha: int


class ErroLexico(Exception):
    pass


# ---------------------------------------------------------------------------
# Alfabeto: classes de caracteres usadas como rótulos das arestas
# ---------------------------------------------------------------------------

class Classe(Enum):
    DELIM = "delim"
    LETRA = "letra"
    DIGITO = "dígito"
    PONTO = "."
    DEMAIS = "demais"  # qualquer outro caractere
    FIM = "fim"        # fim da entrada


DELIMITADORES: Final = frozenset(" \t\n\r\f\v")


def classificar(c: str) -> Classe:
    if c == EOF:
        return Classe.FIM
    if c in DELIMITADORES:
        return Classe.DELIM
    if "a" <= c <= "z" or "A" <= c <= "Z":
        return Classe.LETRA
    if "0" <= c <= "9":
        return Classe.DIGITO
    if c == ".":
        return Classe.PONTO
    return Classe.DEMAIS


# ---------------------------------------------------------------------------
# Diagramas de transição
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EstadoFinal:
    token: NomeToken
    retrair: bool  # True nos estados marcados com * no diagrama


@dataclass(frozen=True)
class DiagramaTransicao:
    """Diagrama de transição de um token: AFD M = (Q, Σ, δ, q0, F).

    delta[q][classe] são as arestas rotuladas que saem de q.
    outro[q] é a aresta "outro" de q: vale para qualquer classe sem aresta
    rotulada. Se nenhuma aresta se aplica, o diagrama falha.
    """

    nome: str
    inicial: int
    delta: Mapping[int, Mapping[Classe, int]]
    outro: Mapping[int, int]
    finais: Mapping[int, EstadoFinal]

    def transicao(self, estado: int, classe: Classe) -> Optional[int]:
        rotuladas = self.delta.get(estado, {})
        if classe in rotuladas:
            return rotuladas[classe]
        return self.outro.get(estado)


DIAGRAMA_BRANCO: Final = DiagramaTransicao(
    nome="BRANCO",
    inicial=0,
    delta={0: {Classe.DELIM: 1},
           1: {Classe.DELIM: 1}},
    outro={1: 2},
    finais={2: EstadoFinal(NomeToken.BRANCO, retrair=True)},
)

DIAGRAMA_IDENT: Final = DiagramaTransicao(
    nome="IDENT",
    inicial=3,
    delta={3: {Classe.LETRA: 4},
           4: {Classe.LETRA: 4, Classe.DIGITO: 4}},
    outro={4: 5},
    finais={5: EstadoFinal(NomeToken.IDENT, retrair=True)},
)

DIAGRAMA_NPF: Final = DiagramaTransicao(
    nome="NPF",
    inicial=6,
    delta={6: {Classe.DIGITO: 7},
           7: {Classe.DIGITO: 7, Classe.PONTO: 8},
           8: {Classe.DIGITO: 9},
           9: {Classe.DIGITO: 9}},
    outro={9: 10},  # 7 e 8 não têm aresta "outro": sem ponto ou sem dígito após o ponto, falha
    finais={10: EstadoFinal(NomeToken.NPF, retrair=True)},
)

DIAGRAMA_NI: Final = DiagramaTransicao(
    nome="NI",
    inicial=11,
    delta={11: {Classe.DIGITO: 12},
           12: {Classe.DIGITO: 12}},
    outro={12: 13},
    finais={13: EstadoFinal(NomeToken.NI, retrair=True)},
)

DIAGRAMA_OUTRO: Final = DiagramaTransicao(
    nome="OUTRO",
    inicial=14,
    delta={},
    outro={14: 15},  # qualquer caractere (o fim da entrada é tratado antes)
    finais={15: EstadoFinal(NomeToken.OUTRO, retrair=False)},
)

# Ordem em que os diagramas são tentados.
DIAGRAMAS: Final[Tuple[DiagramaTransicao, ...]] = (
    DIAGRAMA_BRANCO,
    DIAGRAMA_IDENT,
    DIAGRAMA_NPF,
    DIAGRAMA_NI,
    DIAGRAMA_OUTRO,
)


# ---------------------------------------------------------------------------
# Leitura da entrada
# ---------------------------------------------------------------------------

class BufferEntrada:
    """Lê a entrada um caractere por vez, com os apontadores
    lexemeBegin (início do lexema atual) e forward (próximo caractere)."""

    def __init__(self, fluxo: TextIO) -> None:
        self._fluxo = fluxo
        self._lidos: List[str] = []  # caracteres lidos a partir de lexemeBegin
        self.lexeme_begin = 0
        self.forward = 0
        self.linha = 1  # linha do caractere em lexemeBegin

    def proximo_caractere(self) -> str:
        if self.forward == len(self._lidos):
            c = self._fluxo.read(1)  # lê exatamente um caractere da entrada
            if c != EOF:
                self._lidos.append(c)
        c = self._lidos[self.forward] if self.forward < len(self._lidos) else EOF
        self.forward += 1
        return c

    def retrair(self) -> None:
        """Estado com *: o último caractere lido não pertence ao lexema."""
        self.forward -= 1

    def falhar(self) -> None:
        """Diagrama falhou: forward volta para lexemeBegin."""
        self.forward = self.lexeme_begin

    def fim_da_entrada(self) -> bool:
        c = self.proximo_caractere()
        self.retrair()
        return c == EOF

    def aceitar(self) -> Tuple[str, int]:
        """Fecha o lexema entre lexemeBegin e forward; lexemeBegin = forward."""
        lexema = "".join(self._lidos[self.lexeme_begin:self.forward])
        linha = self.linha
        self.linha += lexema.count("\n")
        del self._lidos[:self.forward]  # descarta o que já foi reconhecido
        self.lexeme_begin = self.forward = 0
        return lexema, linha


# ---------------------------------------------------------------------------
# Analisador léxico
# ---------------------------------------------------------------------------

class AnalisadorLexico:
    def __init__(self, fluxo: TextIO,
                 diagramas: Sequence[DiagramaTransicao] = DIAGRAMAS) -> None:
        self._entrada = BufferEntrada(fluxo)
        self._diagramas = diagramas

    def proximo_token(self) -> Optional[Token]:
        """Devolve o próximo token da entrada, ou None no fim."""
        if self._entrada.fim_da_entrada():
            return None
        for diagrama in self._diagramas:
            token = self._simular(diagrama)
            if token is not None:
                return token
            self._entrada.falhar()
        raise ErroLexico("nenhum diagrama reconhece o caractere na linha %d"
                         % self._entrada.linha)

    def _simular(self, diagrama: DiagramaTransicao) -> Optional[Token]:
        """Percorre um diagrama a partir de lexemeBegin; None se falhar."""
        estado = diagrama.inicial
        while estado not in diagrama.finais:
            c = self._entrada.proximo_caractere()
            destino = diagrama.transicao(estado, classificar(c))
            if destino is None:
                return None
            estado = destino
        final = diagrama.finais[estado]
        if final.retrair:
            self._entrada.retrair()
        lexema, linha = self._entrada.aceitar()
        return Token(final.token, lexema, linha)

    def tokens(self) -> Iterator[Token]:
        token = self.proximo_token()
        while token is not None:
            yield token
            token = self.proximo_token()


def analisar(fluxo: TextIO) -> List[Token]:
    """Lista de tokens do código-fonte, sem os tokens BRANCO."""
    return [t for t in AnalisadorLexico(fluxo).tokens()
            if t.nome is not NomeToken.BRANCO]


def imprimir(tokens: Sequence[Token], mostrar_lexemas: bool = False) -> None:
    """Escreve os tokens na tela, quebrando a linha como no código-fonte."""
    linha_atual: Optional[int] = None
    partes: List[str] = []
    for t in tokens:
        if t.linha != linha_atual and partes:
            print(" ".join(partes))
            partes = []
        linha_atual = t.linha
        partes.append("<%s, %s>" % (t.nome.value, t.lexema) if mostrar_lexemas
                      else t.nome.value)
    if partes:
        print(" ".join(partes))


def main() -> None:
    p = argparse.ArgumentParser(
        description="Analisador léxico: IDENT, BRANCO, NI, NPF e OUTRO.")
    p.add_argument("arquivo", nargs="?",
                   help="código-fonte (sem arquivo, lê da entrada padrão)")
    p.add_argument("-l", "--lexemas", action="store_true",
                   help="mostra o par <nome, lexema> de cada token")
    args = p.parse_args()

    arquivo: Optional[str] = args.arquivo
    mostrar_lexemas: bool = args.lexemas
    if arquivo is not None:
        with open(arquivo, encoding="utf-8") as f:
            tokens = analisar(f)
    else:
        tokens = analisar(sys.stdin)

    imprimir(tokens, mostrar_lexemas)


if __name__ == "__main__":
    main()
