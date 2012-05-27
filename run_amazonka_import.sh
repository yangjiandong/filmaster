#!/bin/bash
wget http://www.amazonka.pl/exportxml/filmaster/ekxmmnfpcu/out.films.xml.gz
gunzip out.films.xml.gz
python run_amazonka_import.py -f out.films.xml
rm out.films.xml
