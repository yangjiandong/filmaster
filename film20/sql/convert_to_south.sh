find -maxdepth 1 -type d|cut -b 3-|xargs --verbose -n 1 ./manage.py convert_to_south
