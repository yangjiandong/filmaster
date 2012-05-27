import os, getopt, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from film20.shop.shop_helper import *
import logging

logger = logging.getLogger("simple_example")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def main():
    """
        -i fetch posters by imdb_code
        -t fetch posters by title
    """
    options, args = getopt.getopt(sys.argv[1:],'f:')
    opts = dict(options)

    if len(opts) == 0:
        print "-f XML file with Amazonka films"
        sys.exit()
    
    file_name = opts.get('-f','').replace('"',"") 

    shop_helper = ShopHelper()
    shop_helper.import_items(file_name)

if __name__ == '__main__':
    main()
