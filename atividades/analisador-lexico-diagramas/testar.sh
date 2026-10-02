#!/usr/bin/env bash
# Roda os dois analisadores com a entrada do enunciado e compara com a saída esperada.
# Se o mypy estiver instalado, confere também a tipagem.
cd "$(dirname "$0")"
status=0
for ex in ex1_ident_branco_outro ex2_ident_branco_ni_npf_outro; do
  if diff <(python3 "$ex/lexico.py" "$ex/entrada.txt") "$ex/saida_esperada.txt" > /dev/null; then
    echo "OK    $ex"
  else
    echo "FALHA $ex"
    diff <(python3 "$ex/lexico.py" "$ex/entrada.txt") "$ex/saida_esperada.txt"
    status=1
  fi
done
if python3 -m mypy --version > /dev/null 2>&1; then
  for ex in ex1_ident_branco_outro ex2_ident_branco_ni_npf_outro; do
    python3 -m mypy --strict "$ex/lexico.py" > /dev/null && echo "OK    mypy --strict $ex" || { echo "FALHA mypy --strict $ex"; status=1; }
  done
else
  echo "(mypy não instalado: tipagem não conferida)"
fi
exit $status
