import pandas as pd
import openpyxl as pxl
from datetime import date

def build_dataframe_for_a_ticker(data_frame, ticker, rd, logger):
    # 'EPS 15% Rate', 'Div Growth 20% Rate', 'Div Formula 15% Rate', 'By DCF', 'BB TR Current Rate', 'BB 10% Rate', '15 PE', '1.5 PB',
    data_frame['labels'] = [ 
                            'Mkt Cap',
                            'EPS Growth Nxt 5 Yr', 'EPS Growth Nxt Yr', 'EPS Growth Cur Yr', 
                            'Sales Growth Nxt Yr', 'Sales Growth Cur Yr',
                            'PS', 'PE TTM', 'PE FWD', 'PB', 'P-FCF', 
                            'Gross Margin', 'Op Margin', 'Profit Margin', 
                            'ROE',
                            'Current Ratio', 'Dbt-to-Eqty', 
                            '#Emp',
                            'Short Days', 'RSI',
                            'div rate', 'div yield', 'div payout ratio',
                            'Inst Own', 'Inst Trans', 'Insdier Own', 'Insdier Trans', 
                            'Current Price',
                ]

    # fair_price_by_eps, fair_price_by_div_growth, fair_price_by_div_formula, intrinsic_value_by_dcf, bb_intrinsic_value_by_treasury_rate, bb_intrinsic_value_by_exp_rate, round(15 * rd.current_price/rd.pe, 2), round(1.5 * rd.current_price/rd.pb, 2), 
    data_frame[ticker] = [  
                            rd.mkt_cap,
                            rd.growth_next_5_yrs, rd.growth_n_y, rd.growth_c_y, 
                            rd.sales_growth_n_y, rd.sales_growth_c_y, 
                            rd.ps, rd.pe, rd.fwd_pe, rd.pb, rd.price_to_free_cash_flow, 
                            rd.gross_margin, rd.op_margin, rd.profit_margin, 
                            rd.roe, 
                            rd.cur_ratio, rd.dbt_to_equity, 
                            rd.emp,
                            rd.short_days_to_cover, rd.rsi,
                            rd.forward_div_rate, rd.div_yield, rd.div_payout_ratio, 
                            rd.institutaion_ownership, rd.institutaion_trans, rd.insider_ownership, rd.insider_trans,
                            rd.current_price,
                        ]
    labels = data_frame['labels']
    ticker_values = data_frame[ticker]
    for i in range(len(labels)):
        logger.warning(f'{labels[i]} : {ticker_values[i]}')

def build_small_dataframe_for_a_ticker(data_frame, ticker, rd, logger):
    # 'EPS 15% Rate', 'Div Growth 20% Rate', 'Div Formula 15% Rate', 'By DCF', 'BB TR Current Rate', 'BB 10% Rate', '15 PE', '1.5 PB',
    data_frame['labels'] = [ 'Current Price']

    # fair_price_by_eps, fair_price_by_div_growth, fair_price_by_div_formula, intrinsic_value_by_dcf, bb_intrinsic_value_by_treasury_rate, bb_intrinsic_value_by_exp_rate, round(15 * rd.current_price/rd.pe, 2), round(1.5 * rd.current_price/rd.pb, 2), 
    data_frame[ticker] = [rd.current_price]
    labels = data_frame['labels']
    ticker_values = data_frame[ticker]
    for i in range(len(labels)):
        logger.warning(f'{labels[i]} : {ticker_values[i]}')        

def write(data_frame):
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
    sheet.column_dimensions['A'].width = 25
    sheet.freeze_panes = 'A2'
    # save excel file
    writer.save()  

def color(x):
    #color by row lables
    fair_price = x['labels'].isin(['EPS 15% Rate', 'Div Growth 20% Rate', 'Div Formula 15% Rate', 'By DCF', 'BB TR Current Rate', 'BB 10% Rate', '15 PE', '1.5 PB',])
    mkt_cap = x['labels'].isin(['Mkt Cap'])
    eps_growth = x['labels'].isin(['EPS Growth Nxt 5 Yr', 'EPS Growth Past 5 Yr', 'EPS Growth Nxt Yr', 'EPS Growth Cur Yr', 'EPS Growth Nxt Q', 'EPS Growth Cur Q',])
    sales_growth = x['labels'].isin(['Sales Growth Past 3 Yr', 'Sales Growth Nxt Yr', 'Sales Growth Cur Yr', 'Sales Growth Nxt Q', 'Sales Growth Cur Q',])
    price_comparision = x['labels'].isin(['PS', 'EVS', 'EV_TO_EBITDA', 'PE TTM', 'PE FWD', 'PB','PEG', 'P-FCF',])
    financials_comparision_1 = x['labels'].isin(['Income', 'Gross Margin', 'Op Margin', 'Profit Margin', 'Current Ratio', 'Dbt-to-Eqty',])
    financials_comparision_2 = x['labels'].isin(['Income', 'ROE',])
    debt_comparision = x['labels'].isin(['Current Ratio', 'Dbt-to-Eqty',])
    misc_comparision = x['labels'].isin(['#Emp', 'Inst Own', 'Inst Trans', 'Insdier Own', 'Insdier Trans',])
    ta_comparision = x['labels'].isin(['Short Days', 'RSI', 'Perf Ytd', 'Perf Yr', '52wk Range', 'Below 52wk H', 'Above 52wk L', 'Current Price'])
    dividend = x['labels'].isin(['div rate', 'div yield', 'div payout ratio',])
    price = x['labels'].isin(['Current Price',])
    
    df =  pd.DataFrame('', index=x.index, columns=x.columns)
    df.loc[fair_price, :] = 'background-color: #f5f58d'
    df.loc[mkt_cap, :] = 'background-color: #d9d2e9'
    df.loc[eps_growth, :] = 'background-color: #6699ff'
    df.loc[sales_growth, :] = 'background-color: #ffb366'
    df.loc[price_comparision, :] = 'background-color: #93c47d'
    df.loc[financials_comparision_1, :] = 'background-color: #ea9999'
    df.loc[financials_comparision_2, :] = 'background-color: #93c47d'
    df.loc[debt_comparision, :] = 'background-color: #f1c232'
    df.loc[misc_comparision, :] = 'background-color: #d0e0e3'
    df.loc[ta_comparision, :] = 'background-color: #dedae7'
    df.loc[dividend, :] = 'background-color: #b6d7a8'
    df.loc[price, :] = 'background-color: #00ffff'
    
    return df
      