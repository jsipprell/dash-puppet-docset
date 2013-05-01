#!/bin/bash
# Utility script to regenerate sql for the docset.  The contents of the searchIndex table
# *must* be deleted before this is run.

function output_type() {
  local type="$1"
  local input="$2"
  local file=$(basename "$input")

  perl -ne $'print "$2 $1\n" if m@<h\d id=["\']([\w_,.+/\\@-]+)["\']>([^<]+)</h\d>@;' "$input" | \
    while read line; do
      #echo "line = $line"
      set -- $line
      [ $# -ne 2 ] && continue
      [[ $1 = Features ]] && continue
      [[ $1 = Parameters ]] && continue
      [[ $2 = parameters-* ]] && continue
      [[ $2 = Feature ]] && continue
      echo "INSERT OR IGNORE INTO searchIndex(name,type,path) VALUES ('$type','$1','${file}#$2');"
    done
}

if [ $# -eq 0 ]; then
  [[ $docdir ]] || docdir=puppet.docset/Contents/Resources/Documents
  output_type Directive $docdir/configuration.html
  output_type Function $docdir/function.html
  output_type Interface $docdir/indirection.html
  output_type Parameter $docdir/metaparameter.html
  output_type Record $docdir/report.html
  output_type Type $docdir/type.html
else
  while [ $# -gt 0 ]; do
    output_type "$1" "$2"; shift; shift
  done
fi