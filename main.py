from time import sleep
from selenium.common.exceptions import NoSuchElementException

from raw import Raw
from raw_small import RawSmall
from arg_parser import *
from logger import *
from excel_utils import *

# workon .
# do not write: 
#   python main.py --t '{"Airline":[{"in":1,"sym":"MSFT"}]}' 
#   python main.py  --l WARNING --w False --o No --t '{"Airline":[{"in":1,"sym":"MSFT"}]}'
# write with given tickers
#   python main.py --w True --t '{"Food":[{"in": 1, "sym": "SBUX"}, {"in": 1, "sym": "TTCF"}, {"in": 1, "sym": "UNFI"}, {"in": 1, "sym": "BYND"}]}'
# write only in=1: 
#   python main.py --w True
# write All: 
#   python main.py --w True --o Yes
def main():
    override_in, write_to_excel, level, sector_tickers_dict, small = get_args()
    logger = setup_logger(level)

    data_frame= {}
    data_frame['labels'] = []

    for sector, tickers in sector_tickers_dict.items():
        data_frame[sector] = ''
        for tickerDict in tickers:
            ticker = tickerDict.get('sym')
            try:
                if override_in == 'Yes' or tickerDict.get('in') == 1:
                    sleep(4)
                    logger.warning("")
                    logger.warning(f"************************ {ticker} ************************")
                    rd = None
                    retryAttempt = 0
                    while not rd and retryAttempt < 3:
                        try:
                            rd = RawSmall(ticker, logger) if small == 'True' else Raw(ticker, logger)    
                            retryAttempt = retryAttempt + 1
                        except Exception as e:
                            logger.exception("::::::::::::::::::::::::::::")    
                    build_small_dataframe_for_a_ticker(data_frame, ticker, rd, logger) if small == 'True' else build_dataframe_for_a_ticker(data_frame, ticker, rd, logger)

            except NoSuchElementException as driverError:
                logger.warning("error :::::::::", driverError)

    if write_to_excel == 'True':
       write(data_frame)

if __name__ == "__main__":
    main()
