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
    #"REITS": [{"in": 1, "sym": "SPG"}, {"in": 1, "sym": "DLR"}, {"in": 1, "sym": "ESS"}, {"in": 1, "sym": "PLD"}, {"in": 1, "sym": "O"}], # removed cci
    #"Health": [{"in": 1, "sym": "UNH"}, {"in": 1, "sym": "ABMD"}], # removed pg & jnj, alxn
    #"Genomics": [{"in": 1, "sym": "BNGO"}, {"in": 1, "sym": "EDIT"}, {"in": 1, "sym": "CRSP"}, {"in": 1, "sym": "TXG"}, {"in": 1, "sym": "ILMN"}],
    # "Airline": [{"in": 1, "sym": "UAL"}, {"in": 1, "sym": "LUV"}, {"in": 1, "sym": "DAL"}],
    # "Cruise": [{"in": 1, "sym": "NCLH"}, {"in": 1, "sym": "CCL"}],
    # "Finance": [{"in": 1, "sym": "V"},{"in": 1, "sym": "IBTX"}], #removed MA
    
    "Dividend": [{"in": 1, "sym": "LMT"}, {"in": 1, "sym": "LOW"}, {"in": 1, "sym": "HD"}, {"in": 1, "sym": "TSN"}, {"in": 1, "sym": "CVS"}], # removed pg, jnj and clx
    "Aircraft": [{"in": 1, "sym": "BA"}, {"in": 0, "sym": "LHX"}, {"in": 1, "sym": "LMT"}, {"in": 0, "sym": "TDG"}, {"in": 0, "sym": "CVU"}],
    # "Real Estate": [{"in": 0, "sym": "LGIH"}],
    "Oil": [{"in": 0, "sym": "CVX"}, {"in": 1, "sym": "IMO"}, {"in": 0, "sym": "COP"}],
    "Eat": [{"in": 1, "sym": "SBUX"}, {"in": 1, "sym": "TTCF"}, {"in": 0, "sym": "MCD"}, {"in": 0, "sym": "PEP"}], # removed cmg, tsn
    "Bank": [{"in": 1, "sym": "PNC"}, {"in": 0, "sym": "USB"}, {"in": 0, "sym": "JPM"}, {"in": 1, "sym": "DFS"}],
    "Tech": [{"in": 1, "sym": "GOOG"}, {"in": 1, "sym": "MSFT"}, {"in": 1, "sym": "AAPL"}],
    "Retail": [{"in": 1, "sym": "NKE"}], # removed TGT, NKE
    "Solar": [{"in": 0, "sym": "FSLR"}, {"in": 0, "sym": "BE"}, {"in": 1, "sym": "ENPH"}, {"in": 1, "sym": "PLUG"}],
    "Semiconductor": [{"in": 1, "sym": "QCOM"}, {"in": 1, "sym": "nvda"}], # removed nvdia
    "Med Growth": [{"in": 1, "sym": "TSLA"}, {"in": 1, "sym": "AMZN"}, {"in": 1, "sym": "AYX"}, 
                   {"in": 1, "sym": "SPLK"}, 
                   {"in": 0, "sym": "NOW"}, {"in": 0, "sym": "PAYC"},  # removed wday
                   {"in": 1, "sym": "FB"}, {"in": 1, "sym": "CRM"}, {"in": 1, "sym": "PYPL"}],                     
    "High Growth": [{"in": 1, "sym": "SQ"}, {"in": 1, "sym": "UBER"}, {"in": 0, "sym": "SHOP"}, # more stable
                    {"in": 1, "sym": "OKTA"}, # established growth
                    {"in": 1, "sym": "CRWD"}, {"in": 1, "sym": "ABNB"}, {"in": 1, "sym": "SNOW"}, 
                    {"in": 1, "sym": "PINS"}, {"in": 1, "sym": "SNAP"}, 
                    {"in": 1, "sym": "TTD"}, {"in": 1, "sym": "FSLY"}, {"in": 1, "sym": "NET"}], #CSLX, ETSY, FSLY, NET Organic growth
    "Bet": [{"in": 1, "sym": "BB"}, {"in": 1, "sym": "NOK"}, {"in": 1, "sym": "KBNT"}, {"in": 1, "sym": "QS"}, {"in": 1, "sym": "PLUG"},  # comm/adv
            {"in": 1, "sym": "BNGO"}, {"in": 0, "sym": "TXG"}, {"in": 1, "sym": "VXRT"}, #genomics
            {"in": 0, "sym": "VRM"}, {"in": 0, "sym": "SFT"} #vehicle not interested
            ],
} 


def setup_logger(level):
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S', level=level)
    logger = logging.getLogger('gains')
    return logger


def get_args():
    parser = argparse.ArgumentParser(description='Calculates fair price for a give ticker')
    parser.add_argument('--w', dest='write_to_excel', help='write to file', default=False)
    parser.add_argument('--t', dest='sector_tickers', help='tickers dict', default='{}')
    parser.add_argument('--o', dest='override_in', help='override in flag', default='No')
    parser.add_argument('--l', dest='level', help='log level', default='WARNING')
    args = parser.parse_args()
    return args.override_in, args.write_to_excel, args.level, json.loads(args.sector_tickers)

# workon .
# do not write: 
#   python fair_price.py --t '{"Airline":[{"in":1,"sym":"MSFT"}]}' 
#   python fair_price.py  --l WARNING --w False --o No --t '{"Airline":[{"in":1,"sym":"MSFT"}]}'
# write with given tickers
#   python fair_price.py --w True --t '{"Food":[{"in": 1, "sym": "SBUX"}, {"in": 1, "sym": "TTCF"}, {"in": 1, "sym": "UNFI"}, {"in": 1, "sym": "BYND"}]}'
# write only in=1: 
#   python fair_price.py --w True
# write All: 
#   python fair_price.py --w True --o Yes
def main():
    override_in, write_to_excel, level, in_sector_tickers = get_args()
    sector_tickers_dict = sector_tickers
    if len(in_sector_tickers) > 0:
        sector_tickers_dict = in_sector_tickers
    logger = setup_logger(level)

    data_frame= {}
    data_frame['labels'] = []

    for sector, tickers in sector_tickers_dict.items():
        data_frame[sector] = ''
        for tickerDict in tickers:
            ticker = tickerDict.get('sym')
            if override_in == 'Yes' or tickerDict.get('in') == 1:
                time.sleep(1)
                logger.warning("")
                logger.warning(f"************************ {ticker} ************************")
                rd = Raw(ticker, logger)

                fair_eps_by_eps_growth = EPS(eps_growth_rate=rd.growth_next_5_yrs,
                                             eps_ttm=rd.eps_ttm, avg_pe_ratio=rd.avg_pe_ratio, logger=logger)
                fair_price_by_eps = fair_eps_by_eps_growth.calculate(no_of_years=10, rate_of_return=15)
                logger.warning(f"fair_price_by_eps= {fair_price_by_eps}")

                fair_price_by_div = Div(div_rate=rd.forward_div_rate, div_growth_rate=rd.div_avg_growth,
                                        current_price=rd.current_price, logger=logger)
                fair_price_by_div_growth = fair_price_by_div.calculate(no_of_years=10, rate_of_return=20)
                logger.warning(f"fair_price_by_div_growth= {fair_price_by_div_growth}")
                fair_price_by_div_formula = fair_price_by_div.calculate_by_formula(rate_of_return=15)
                logger.warning(f"fair_price_by_div_formula= {fair_price_by_div_formula}")

                buffet_book_intrinsic_value = BuffetBookIntrinsicValue(rd.forward_div_rate, rd.book_value, rd.avg_book_value, rd.avg_forward_eps, 10, logger)
                bb_intrinsic_value_by_treasury_rate = buffet_book_intrinsic_value.calculate_intrinsic_value(rd.latest_treasury_rate)
                logger.warning(f"bb_intrinsic_value_by_treasury_rate= {bb_intrinsic_value_by_treasury_rate}")
                bb_intrinsic_value_by_exp_rate = buffet_book_intrinsic_value.calculate_intrinsic_value(10)
                logger.warning(f"bb_intrinsic_value_by_exp_rate= {bb_intrinsic_value_by_exp_rate}")
                dcf = DCFIntrinsicValue(rd.avg_fcf_of_last_10_years, rd.avg_op_income, rd.shares_outstanding, logger)
                intrinsic_value_by_dcf = dcf.calculate_intrinsic_value(10)
                logger.warning(f"intrinsic_value_by_dcf= {intrinsic_value_by_dcf}")

                data_frame['labels'] = ['EPS 15% Rate', 'Div Growth 20% Rate', 'Div Formula 15% Rate', 'By DCF', 'BB TR Current Rate',
                                        'BB 10% Rate', '15 PE', '1.5 PB', 'TR', 'Mkt Cap', 
                                        'EV', 'Current Price', 'SMA 50D', 'SMA 200D', 'Below 52wk H', 
                                        'Above 52wk L', 'Growth Nxt 5 Yr', 'Growth Past 5 Yr', 'Growth Nxt Yr', 'Growth Cur Yr', 
                                        'Growth Nxt Q', 'Growth Cur Q', 'Sales Growth Nxt Yr', 'Sales Growth Cur Yr', 'Sales Growth Nxt Q', 
                                        'Sales Growth Cur Q', 'Rev Growth Past 3 Yr', 'PS', 'EVS', 'EV_TO_EBITDA',
                                        'PE TTM', 'PE FWD', 'PB','PEG', 'P-OP-Cash', 
                                        'ROE', 'Op Margin', 'Current Ratio', 'Dbt-to-Eqty', 'div rate',
                                        'div yield', 'div payout ratio', '#Emp', 'Inst Own', 'Insdier Own', 
                                        'Short Days'
                            ]
                
                data_frame[ticker] = [  fair_price_by_eps, fair_price_by_div_growth, fair_price_by_div_formula, intrinsic_value_by_dcf, bb_intrinsic_value_by_treasury_rate, 
                                        bb_intrinsic_value_by_exp_rate, round(15 * rd.current_price/rd.pe, 2), round(1.5 * rd.current_price/rd.pb, 2), rd.latest_treasury_rate, rd.mkt_cap,
                                        rd.ev, rd.current_price, rd.sma_50d, rd.sma_200d, rd.h52wk_drop, 
                                        rd.l52wk_up, rd.growth_next_5_yrs, rd.growth_p_5y, rd.growth_n_y, rd.growth_c_y, 
                                        rd.growth_n_q, rd.growth_c_q, rd.sales_growth_n_y, rd.sales_growth_c_y, rd.sales_growth_n_q, 
                                        rd.sales_growth_c_q, rd.rev_growth_3yr, rd.ps, rd.ev_to_sales, rd.ev_to_ebitda,
                                        rd.pe, rd.fwd_pe, rd.pb, rd.peg, rd.price_to_op_cash_flow, 
                                        rd.roe, rd.op_margin, rd.cur_ratio, rd.dbt_to_equity, rd.forward_div_rate,
                                        rd.div_yield, rd.div_payout_ratio, rd.emp, rd.institutaion_ownership, rd.insider_ownership, 
                                        rd.short_days_to_cover
                                    ]
                labels = data_frame['labels']
                ticker_values = data_frame[ticker]
                for i in range(len(labels)):
                    logger.warning(f'{labels[i]} : {ticker_values[i]}')
        
    if write_to_excel == 'True':
        path = './xlsx/fair_prices.xlsx'
        workbook = pxl.load_workbook(path)
        writer = pd.ExcelWriter(path, engine='openpyxl')
        writer.book = workbook
        df = pd.DataFrame(data_frame)

        # apply colors
        df.reset_index()
        df = df.style.apply(color, axis=None)
        # write dataframe onto sheet
        today = date.today()
        sheet_name = today.strftime("%m_%d")
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.sheets[sheet_name]
        # set column width
        sheet = workbook[sheet_name]
        sheet.column_dimensions['A'].width = 40
        sheet.freeze_panes = 'A2'
        # save excel file
        writer.save()

def color(x):
    #color by row lables
    fair_price = x['labels'].isin(['EPS 15% Rate', 'Div Growth 20% Rate', 'Div Formula 15% Rate', 'By DCF', 'BB TR Current Rate', 'BB 10% Rate', '15 PE', '1.5 PB',])
    price = x['labels'].isin(['Mkt Cap', 'EV', 'Current Price', 'SMA 50D', 'SMA 200D', 'Below 52wk H', 'Above 52wk L',])
    price_ratios = x['labels'].isin(['PE TTM', 'PE FWD', 'PB', 'PEG', 'P-OP-Cash', 'PS', 'EVS', 'EV_TO_EBITDA'])
    eps_growth = x['labels'].isin(['Growth Past 5 Yr', 'Growth Nxt 5 Yr', 'Growth Cur Q', 'Growth Nxt Q', 'Growth Cur Yr', 'Growth Nxt Yr',])
    sales_growth = x['labels'].isin(['Rev Growth Past 3 Yr', 'Sales Growth Cur Q', 'Sales Growth Nxt Q', 'Sales Growth Cur Yr', 'Sales Growth Nxt Yr',])
    debt_margin = x['labels'].isin(['Op Margin', 'ROE', 'Current Ratio', 'Dbt-to-Eqty'])
    inside_view = x['labels'].isin(['#Emp', 'Inst Own', 'Insdier Own', 'Short Days'])
    
    df =  pd.DataFrame('', index=x.index, columns=x.columns)
    df.loc[fair_price, :] = 'background-color: #f5f58d'
    df.loc[price, :] = 'background-color: #d9d2e9'
    df.loc[price_ratios, :] = 'background-color: #93c47d'
    df.loc[eps_growth, :] = 'background-color: #6699ff'
    df.loc[sales_growth, :] = 'background-color: #ffb366'
    df.loc[debt_margin, :] = 'background-color: #ea9999'
    df.loc[inside_view, :] = 'background-color: #d0e0e3'
    
    return df

if __name__ == "__main__":
    main()
