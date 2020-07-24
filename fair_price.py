import logging, time, argparse, csv, json
import pandas as pd
import openpyxl as pxl
from datetime import date

from raw import Raw
from intrinsic_value_eps_growth import EPS
from intrinsic_value_div_growth import Div
from intrinsic_value_bfbk import BuffetBookIntrinsicValue
from intrinsic_value_dcf import DCFIntrinsicValue

sector_tickers = {
    "Airline": [{"in": 1, "sym": "DAL"}, {"in": 1, "sym": "UAL"}, {"in": 0, "sym": "JBLU"}, {"in": 0, "sym": "AAL"}, {"in": 1, "sym": "LUV"}],
    "Aircraft": [{"in": 1, "sym": "BA"}, {"in": 0, "sym": "TDG"}, {"in": 0, "sym": "LHX"}, {"in": 1, "sym": "LMT"}, {"in": 1, "sym": "CVU"}],
    "Cruise": [{"in": 0, "sym": "RCL"}, {"in": 1, "sym": "NCLH"}, {"in": 1, "sym": "CCL"}],
    "E&TC": [{"in": 1, "sym": "VZ"}, {"in": 0, "sym": "T"}, {"in": 1, "sym": "DIS"}],
    "Eat": [{"in": 1, "sym": "SBUX"}, {"in": 1, "sym": "PEP"}, {"in": 1, "sym": "MCD"}, {"in": 1, "sym": "KO"},
            {"in": 0, "sym": "CMG"}, {"in": 0, "sym": "DPZ"}, {"in": 1, "sym": "UNFI"}, {"in": 1, "sym": "TSN"}, {"in": 1, "sym": "SFM"}],
    "Energy": [{"in": 1, "sym": "ARE"}, {"in": 1, "sym": "PCG"}],
    "Finance": [{"in": 1, "sym": "V"},{"in": 1, "sym": "IBTX"}, {"in": 0, "sym": "MCO"},{"in": 1, "sym": "MA"},{"in": 1, "sym": "PYPL"},
                {"in": 1, "sym": "SQ"}],
    "Bank": [{"in": 1, "sym": "PNC"}, {"in": 1, "sym": "USB"}, {"in": 1, "sym": "BAC"}, {"in": 1, "sym": "BK"},
             {"in": 1, "sym": "JPM"}, {"in": 1, "sym": "AXP"}, {"in": 1, "sym": "KEY"}],
    "Health": [{"in": 1, "sym": "JNJ"}, {"in": 1, "sym": "UNH"}, {"in": 1, "sym": "ISRG"}, {"in": 1, "sym": "GILD"},
               {"in": 1, "sym": "CVS"}, {"in": 1, "sym": "JNJ"}, {"in": 1, "sym": "PG"}],
    "Bio Tech": [{"in": 1, "sym": "ABMD"},{"in": 1, "sym": "ALXN"}, {"in": 0, "sym": "IONS"}],
    "Vehicle": [{"in": 1, "sym": "GM"}],
    "Real Estate": [{"in": 1, "sym": "RDFN"},{"in": 1, "sym": "ZG"}, {"in": 1, "sym": "MHO"}, {"in": 1, "sym": "LGIH"}],
    "Car Auction": [{"in": 1, "sym": "CPRT"}, {"in": 0, "sym": "IAA"}, {"in": 0, "sym": "KAR"}],
    "Oil": [{"in": 1, "sym": "XOM"}, {"in": 0, "sym": "BP"}, {"in": 0, "sym": "RDS-A"}, {"in": 1, "sym": "OXY"},
            {"in": 1, "sym": "CVX"}, {"in": 1, "sym": "IMO"}, {"in": 1, "sym": "COP"}],
    "Retail": [{"in": 1, "sym": "WMT"}, {"in": 1, "sym": "TGT"}, {"in": 1, "sym": "NKE"}, {"in": 1, "sym": "COST"}],
    "Tech": [{"in": 1, "sym": "INTU"}, {"in": 1, "sym": "GOOG"}, {"in": 1, "sym": "MSFT"},
               {"in": 1, "sym": "AAPL"}, {"in": 1, "sym": "FB"}],
    "Semiconductor": [{"in": 1, "sym": "NVDA"}, {"in": 0, "sym": "TER"}, {"in": 1, "sym": "INTC"}, {"in": 1, "sym": "AMD"}, {"in": 1, "sym": "QCOM"}, 
                      {"in": 0, "sym": "TSM"}],
    "High Growth": [{"in": 1, "sym": "IPHI"}, {"in": 1, "sym": "FSLY"}, {"in": 1, "sym": "CDLX"}, {"in": 1, "sym": "PAYS"},{"in": 1, "sym": "TDG"}, 
                    {"in": 1, "sym": "ZS"}, {"in": 1, "sym": "PAYC"}, {"in": 1, "sym": "TWLO"}, {"in": 1, "sym": "WDAY"},{"in": 1, "sym": "NOW"}, 
                    {"in": 1, "sym": "WORK"}, {"in": 1, "sym": "UBER"}, {"in": 1, "sym": "LYFT"}, {"in": 1, "sym": "SHOP"}, {"in": 1, "sym": "BYND"}, 
                    {"in": 1, "sym": "OKTA"}, {"in": 1, "sym": "ROKU"},{"in": 1, "sym": "TTD"}, {"in": 1, "sym": "AMZN"}, {"in": 1, "sym": "TSLA"}, 
                    {"in": 1, "sym": "NFLX"}, {"in": 1, "sym": "AYX"}]
}


def setup_logger(level):
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S', level=level)
    logger = logging.getLogger('gains')
    return logger


def get_args():
    parser = argparse.ArgumentParser(description='Calculates fair price for a give ticker')
    parser.add_argument('--o', dest='override_in', help='override in flag', default=1)
    parser.add_argument('--w', dest='write_to_excel', help='write to file', default=False)
    parser.add_argument('--l', dest='level', help='log level', default='WARNING')
    parser.add_argument('--t', dest='sector_tickers', help='tickers dict', default='{}')
    args = parser.parse_args()
    return args.override_in, args.write_to_excel, args.level, json.loads(args.sector_tickers)

# workon .
# python fair_price.py --l WARNING --w False --o 1 --t '{"Airline":[{"in":1,"sym":"PAYS"}]}'
def main():
    override_in, write_to_excel, level, in_sector_tickers = get_args()
    sector_tickers_dict = sector_tickers
    if len(in_sector_tickers) > 0:
        sector_tickers_dict = in_sector_tickers
    logger = setup_logger(level)

    data_frame= {}
    data_frame[''] = ['Current Price', 'EPS 15 Rate', 'Div Growth 20 Rate', 'Div Formula 15 Rate', 'By DCF', 'BB TR',
                      'BB 10 Rate', 'Exp PE Price', 'Exp PB Price', '52wk Drop', 'Returns', 'Safety', 'PE', 'Exp PE',
                      'PB', 'Exp PB', 'TR'] + Raw.AVG_KEYS

    for sector, tickers in sector_tickers_dict.items():
        data_frame[sector] = ''
        for tickerDict in tickers:
            ticker = tickerDict.get('sym')
            if override_in == 1 or tickerDict.get('in') == 1:
                time.sleep(2)
                logger.warning("")
                logger.warning(f"************************ {ticker} ************************")
                raw_data = Raw(ticker, logger)

                fair_eps_by_eps_growth = EPS(eps_growth_rate=raw_data.analyst_growth_rate_estimates,
                                             eps_ttm=raw_data.eps_ttm, avg_pe_ratio=raw_data.avg_pe_ratio, logger=logger)
                fair_price_by_eps = fair_eps_by_eps_growth.calculate(no_of_years=10, rate_of_return=15)
                logger.warning(f"fair_price_by_eps= {fair_price_by_eps}")

                fair_price_by_div = Div(div_rate=raw_data.forward_div_rate, div_growth_rate=raw_data.div_avg_growth,
                                        current_price=raw_data.current_price, logger=logger)
                fair_price_by_div_growth = fair_price_by_div.calculate(no_of_years=10, rate_of_return=20)
                logger.warning(f"fair_price_by_div_growth= {fair_price_by_div_growth}")
                fair_price_by_div_formula = fair_price_by_div.calculate_by_formula(rate_of_return=15)
                logger.warning(f"fair_price_by_div_formula= {fair_price_by_div_formula}")

                buffet_book_intrinsic_value = BuffetBookIntrinsicValue(raw_data.forward_div_rate, raw_data.book_value, raw_data.avg_book_value, raw_data.avg_forward_eps, 10, logger)
                bb_intrinsic_value_by_treasury_rate = buffet_book_intrinsic_value.calculate_intrinsic_value(raw_data.latest_treasury_rate)
                logger.warning(f"bb_intrinsic_value_by_treasury_rate= {bb_intrinsic_value_by_treasury_rate}")
                bb_intrinsic_value_by_exp_rate = buffet_book_intrinsic_value.calculate_intrinsic_value(10)
                logger.warning(f"bb_intrinsic_value_by_exp_rate= {bb_intrinsic_value_by_exp_rate}")
                dcf = DCFIntrinsicValue(raw_data.avg_fcf_of_last_10_years, raw_data.avg_op_income, raw_data.shares_outstanding, logger)
                intrinsic_value_by_dcf = dcf.calculate_intrinsic_value(10)
                logger.warning(f"intrinsic_value_by_dcf= {intrinsic_value_by_dcf}")
                
                data_frame[ticker] = [raw_data.current_price, fair_price_by_eps, fair_price_by_div_growth,
                                     fair_price_by_div_formula, intrinsic_value_by_dcf, bb_intrinsic_value_by_treasury_rate, bb_intrinsic_value_by_exp_rate, 
                                     round(15 * raw_data.current_price/raw_data.pe, 2), round(1.5 * raw_data.current_price/raw_data.pb, 2), round(raw_data.h52wk_drop, 2),
                                     raw_data.ret, raw_data.margin, raw_data.pe, 15, raw_data.pb, 1.5, raw_data.latest_treasury_rate] + list(raw_data.growth.values())
    if write_to_excel:
        today = date.today()
        sheet = today.strftime("%B_%d_%Y")
        path = './xlsx/fair_prices.xlsx'

        workbook = pxl.load_workbook(path)
        writer = pd.ExcelWriter(path, engine='openpyxl')
        writer.book = workbook
        df = pd.DataFrame(data_frame)
        df.to_excel(writer, sheet_name=sheet, index=False)
        writer.sheets[sheet]
        s = workbook[sheet]
        s.column_dimensions['A'].width = 20
        writer.save()

if __name__ == "__main__":
    main()
