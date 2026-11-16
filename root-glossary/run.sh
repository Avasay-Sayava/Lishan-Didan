#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

echo "Running conversion script inside distrobox 'lex-builder'..."
distrobox enter lex-builder -- bash -c "python3 -c 'import regex' 2>/dev/null || (sudo apt-get update -qq && sudo apt-get install -y python3-regex) || (curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --break-system-packages && python3 -m pip install regex --break-system-packages); python3 sort.py && python3 convert.py"
rm -f glossary.aux glossary.log glossary.tex

echo "Done! The file glossary.pdf has been generated."
