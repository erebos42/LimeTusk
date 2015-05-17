#!/bin/bash

# TODO:
# - DEBUG Flag einbauen

GEN_BIN=./bin/tabbook_gen.py
OUT_PATH=output/
IN_PATH=input/
BOOK=example

trap "exit" INT

echo "Parsing book and converting songs..."
$GEN_BIN --in $IN_PATH --out $OUT_PATH --book $BOOK

echo "Generating book..."
lilypond-book --pdf --loglevel=WARN --lily-loglevel=WARN --format=latex --out=$OUT_PATH ${OUT_PATH}/${BOOK}.lytex

echo "Compiling book..."
export TEXINPUTS=$OUT_PATH:$TEXINPUTS
echo "Run 1..."
pdflatex -draftmode -output-directory $OUT_PATH -interaction=batchmode $BOOK.tex
echo "Run 2..."
pdflatex -draftmode -output-directory $OUT_PATH -interaction=batchmode $BOOK.tex
echo "Run 3..."
pdflatex -output-directory $OUT_PATH -interaction=batchmode $BOOK.tex

#cp ${OUT_PATH}/${BOOK}.pdf .

echo "Done..."
