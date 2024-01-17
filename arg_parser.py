import argparse, json

import constants

def get_args():
    parser = argparse.ArgumentParser(description='Calculates fair price for a give ticker')
    parser.add_argument('--w', dest='write_to_excel', help='write to file', default=False)
    parser.add_argument('--t', dest='sector_tickers', help='tickers dict', default='{}')
    parser.add_argument('--overwrite', dest='override_in', help='override in flag', default='No')
    parser.add_argument('--level', dest='level', help='log level', default='WARNING')
    parser.add_argument('--small', dest='small', help='small', default=False)
    args = parser.parse_args()

    tickers = json.loads(args.sector_tickers)
    if len(tickers) == 0:
        tickers = constants.sector_tickers

    return args.override_in, args.write_to_excel, args.level, tickers, args.small