#!/bin/bash
set -euo pipefail

# Change to the directory where the script is located
cd "$(dirname "$0")"

python3 sort.py
python3 convert.py

if [ -f roots-glossary.tex ] || [ -f general-glossary.tex ]; then
    distrobox enter tex -- bash -c 'cd "$1" && xelatex -interaction=nonstopmode roots-glossary.tex && xelatex -interaction=nonstopmode general-glossary.tex' _ "$(pwd)"
    rm -f roots-glossary.aux roots-glossary.log roots-glossary.tex general-glossary.aux general-glossary.log general-glossary.tex
fi

echo "Done! roots-glossary.pdf and general-glossary.pdf have been generated."
