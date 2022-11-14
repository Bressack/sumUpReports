import argparse
# import numpy as np
import pandas as pd
from IPython.display import display as dd
import sys
import time
from datetime import datetime

parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument('--csv', type=str, dest='csv', help='path of the SumUp csv file')
parser.add_argument('--nb-client', type=int, dest='nb_client', action='store', default=150, help='number of client on the event')
parser.add_argument('--title', dest='title', action='store', default='Sumup_report'+str(datetime.fromtimestamp(time.time())).replace(' ', '-') , help='title of the report')

args = parser.parse_args()

sumup_csv_file_path = args.csv

REPORTS_OUTPUT_PATH = './reports/'
DATAS_PATH = './csv/'
CSS_PATH = './css/'
sumup_tax = 0.0175
nb_client: float = float(args.nb_client)
FMT_FLOAT = '{:,.2f}'


def process():
    #
    # Getting Datas
    #

    try:
        rawds = pd.read_csv(sumup_csv_file_path)
    except:
        try:
            rawds = pd.read_csv(DATAS_PATH + sumup_csv_file_path)
        except:
            print('\033[31;01m' + sys.argv[0] + ' error:\033[0m ' + sumup_csv_file_path + ': \033[38;01mNo such file or directory\033[0m')
            quit()

    rawds.columns = [ 'Account', 'Date', 'Time', 'Type', 'TransactionID', 'Receipt Number', 'PaymentMethod', 'Quantity', 'Description', 'Currency', 'PriceBrut', 'PriceNet', 'Tax', 'Tax rate', 'Transaction refunded' ]
    rawds = rawds[[ 'Account', 'Date', 'Time', 'TransactionID', 'PaymentMethod', 'Quantity', 'Description', 'Currency', 'PriceBrut', 'PriceNet', 'Tax' ]]



    rawds['Description'] = rawds['Description'].apply(lambda x: x.strip())
    card = rawds.query("PaymentMethod=='Card'").copy()
    cash = rawds.query("PaymentMethod=='Cash'").copy()

    card['Tax'] = sumup_tax

    card['PriceNet'] *= 1-card['Tax']
    card['PriceNet'] = card['PriceNet'].round(2)

    rawds = pd.concat([cash, card])
    rawds.sort_index(inplace=True)

    del card
    del cash

    #
    # Getting Stats
    #

    def query_str_equal(field, value):
        v = value.translate(str.maketrans({"'":  r"\'"}))
        return field + "=='" + v + "'"


    ds = rawds[[ 'Quantity', 'TransactionID', 'Description', 'PriceBrut', 'PriceNet', 'PaymentMethod', 'Tax' ]].copy()

    # change all description of beers to Pinte ('1. Blonde', 'Pinte Blonde' -> 'Pinte')
    ds['Description'] = ds['Description'].apply(lambda x: 'Pinte' if x in [ '1. Blonde', 'Pinte Blonde', '1. Blonde Pinte' ] else x )
    ds['Description'] = ds['Description'].apply(lambda x: 'Cocktail' if x in [ 'Cocktail', 'Tequila Sunrise', '1. Cocktail' ] else x )
    ds['Description'] = ds['Description'].apply(lambda x: 'Pichet' if x in [ 'Pichet', '1. Blonde Pichet' ] else x )
    ds['Description'] = ds['Description'].apply(lambda x: 'Demi' if x in [ 'Demi', 'Demi bière' ] else x )

    res = {}
    items = ds['Description'].value_counts().index.to_list()
    for item in items:
        a = ds.query(query_str_equal('Description', item))
        res[item] = {}
        cash = a.query(query_str_equal('PaymentMethod', 'Cash'))
        card = a.query(query_str_equal('PaymentMethod', 'Card'))

        res[item]['Quantity']     = a['Quantity'].sum()
        res[item]['UnitPrice']    = a.iloc[0]['PriceBrut'] / a.iloc[0]['Quantity']
        res[item]['CashQuantity'] = cash['Quantity'].sum()
        res[item]['CashSum']      = cash['PriceNet'].sum()
        res[item]['CardQuantity'] = card['Quantity'].sum()
        res[item]['CardSumBrut']  = card['PriceBrut'].sum()
        res[item]['CardSumNet']   = card['PriceNet'].sum()
        res[item]['PriceSumBrut'] = a['PriceBrut'].sum()
        res[item]['PriceSumNet']  = a['PriceNet'].sum()
        res[item]['fees']  = (a['PriceBrut'] - a['PriceNet']).sum()

    res = pd.DataFrame(res).T.sort_values('PriceSumNet', ascending=False)

    _TOTAL = {}
    _TOTAL['Quantity']     = res['Quantity'].sum()
    _TOTAL['CashQuantity'] = res['CashQuantity'].sum()
    _TOTAL['CashSum']      = res['CashSum'].sum()
    _TOTAL['CardQuantity'] = res['CardQuantity'].sum()
    _TOTAL['CardSumBrut']  = res['CardSumBrut'].sum()
    _TOTAL['CardSumNet']   = res['CardSumNet'].sum()
    _TOTAL['UnitPrice']    = res['UnitPrice'].mean()
    _TOTAL['PriceSumBrut'] = res['PriceSumBrut'].sum()
    _TOTAL['PriceSumNet']  = res['PriceSumNet'].sum()
    _TOTAL['fees']  = res['fees'].sum()

    TOTAL = pd.DataFrame(columns=res.columns)
    TOTAL.loc['TOTAL'] = _TOTAL

    del _TOTAL

    ## index de la ligne median rapport prix total net //////////////////// #
    median = 0
    eighty = 0
    max = float(TOTAL['PriceSumNet'].iloc[0])
    style_stats = 0
    vals = res['PriceSumNet'].values

    for val in vals:
        style_stats += val
        if float(max / 2.0) - style_stats > 0:
            median += 1
        if float(max * 0.8) - style_stats > 0:
            eighty += 1

    style_stats = {}
    style_stats['median'] = median
    style_stats['eighty'] = eighty

    # ///////////////////////////////////////////////////////////////////// #

    TOTAL_PRINTED = TOTAL.copy()
    res_printed = res.copy()

    res_printed['Quantity']     = res_printed['Quantity'].astype(dtype=int)
    res_printed['CashQuantity'] = res_printed['CashQuantity'].astype(dtype=int)
    res_printed['CashSum']      = res_printed['CashSum'].map(FMT_FLOAT.format)
    res_printed['CardQuantity'] = res_printed['CardQuantity'].astype(dtype=int)
    res_printed['CardSumBrut']  = res_printed['CardSumBrut'].map(FMT_FLOAT.format)
    res_printed['CardSumNet']   = res_printed['CardSumNet'].map(FMT_FLOAT.format)
    res_printed['UnitPrice']    = res_printed['UnitPrice'].map(FMT_FLOAT.format)
    res_printed['PriceSumBrut'] = res_printed['PriceSumBrut'].map(FMT_FLOAT.format)
    res_printed['PriceSumNet']  = res_printed['PriceSumNet'].map(FMT_FLOAT.format)
    res_printed['fees']  = res_printed['fees'].map(FMT_FLOAT.format)

    TOTAL_PRINTED['Quantity']     = TOTAL_PRINTED['Quantity'].astype(dtype=int)
    TOTAL_PRINTED['CashQuantity'] = TOTAL_PRINTED['CashQuantity'].astype(dtype=int)
    TOTAL_PRINTED['CashSum']      = TOTAL_PRINTED['CashSum'].map(FMT_FLOAT.format)
    TOTAL_PRINTED['CardQuantity'] = TOTAL_PRINTED['CardQuantity'].astype(dtype=int)
    TOTAL_PRINTED['CardSumBrut']  = TOTAL_PRINTED['CardSumBrut'].map(FMT_FLOAT.format)
    TOTAL_PRINTED['CardSumNet']   = TOTAL_PRINTED['CardSumNet'].map(FMT_FLOAT.format)
    TOTAL_PRINTED['UnitPrice']    = TOTAL_PRINTED['UnitPrice'].map(FMT_FLOAT.format)
    TOTAL_PRINTED['PriceSumBrut'] = TOTAL_PRINTED['PriceSumBrut'].map(FMT_FLOAT.format)
    TOTAL_PRINTED['PriceSumNet']  = TOTAL_PRINTED['PriceSumNet'].map(FMT_FLOAT.format)
    TOTAL_PRINTED['fees']  = TOTAL_PRINTED['fees'].map(FMT_FLOAT.format)

    TOTAL_PRINTED.columns = [[ 'Quantity', 'Prix à l\'Unité', '# vendus en CASH', 'Cash (€)', '# vendus en Card', 'Card Brut (€)', 'Card Net (€)', 'Total Brut (€)', 'Total Net (€)', 'Total Tax SumUp (€)' ]]
    res_printed.columns = [[ 'Quantity', 'Prix à l\'Unité', '# vendus en CASH', 'Cash (€)', '# vendus en Card', 'Card Brut (€)', 'Card Net (€)', 'Total Brut (€)', 'Total Net (€)', 'Total Tax SumUp (€)' ]]

    # dd(TOTAL_PRINTED)
    # dd(res_printed)


    # del TOTAL_PRINTED
    # del res_printed

    #
    # Total stat report
    #

    panierds = rawds[['TransactionID', 'PriceBrut', 'PriceNet']]
    # dd(panierds)
    info = panierds.groupby('TransactionID').mean()

    # dd(info.sort_values('PriceNet'))
    # dd(info.sort_values('PriceNet').mean().loc['PriceBrut'])
    # dd(info.sort_values('PriceNet').mean().loc['PriceNet'])

    panierInfo = {}
    panierInfo['Brut'] = info.sort_values('PriceNet').mean().loc['PriceBrut']
    panierInfo['Net'] = info.sort_values('PriceNet').mean().loc['PriceNet']

    quantities = {}
    gains = {}
    stats = {}

    # total_global = {}
    quantities['ClientCount'] = nb_client
    quantities['UnitCount']  = TOTAL['Quantity']
    quantities['StaffCount'] = rawds['Account'].value_counts().count()

    gains['TotalBrut']   = TOTAL['CardSumBrut'] + TOTAL['CashSum']
    gains['TotalNet']    = TOTAL['CardSumNet'] + TOTAL['CashSum']
    gains['CardBrut']   = TOTAL['CardSumBrut']
    gains['CardNet']    = TOTAL['CardSumNet']
    gains['Cash']       = TOTAL['CashSum']
    gains['SumUpFees']  = TOTAL['CardSumBrut'] - TOTAL['CardSumNet']

    stats['UnitAvg']    = TOTAL['UnitPrice']
    stats['AvgPanierBrut']  = panierInfo['Brut']
    stats['AvgPanierNet']   = panierInfo['Net']
    stats['UnitPerClient']  = TOTAL['Quantity'] / float(nb_client)
    stats['PricePerClientBrut']  = TOTAL['Quantity'] / nb_client * panierInfo['Brut']
    stats['PricePerClientNet']  = TOTAL['Quantity'] / nb_client * panierInfo['Net']


    quantities = pd.DataFrame(quantities); quantities = quantities.apply(lambda x: x.map('{:,.0f}'.format)) ; quantities_printed = quantities.copy().T
    gains      = pd.DataFrame(gains)     ; gains      = gains     .apply(lambda x: x.map(FMT_FLOAT.format)) ; gains_printed      = gains.copy().T
    stats      = pd.DataFrame(stats)     ; stats      = stats     .apply(lambda x: x.map(FMT_FLOAT.format)) ; stats_printed      = stats.copy().T

    quantities.columns = [[
        'Clients',
        'Articles vendus',
        'Staffs',
    ]]
    gains.columns = [[
        'Total Brut',
        'Total Net',
        'Card Brut',
        'Card Net',
        'Cash',
        'SumUp Fees',
    ]]
    stats.columns = [[
        'Prix moyen d\'une conso (€)',
        'Panier moyen Brut (€)',
        'Panier moyen Net (€)',
        'Conso par client',
        'Gain moyen par Client Brut (€)',
        'Gain moyen par Client Net (€)',
    ]]
    quantities = quantities.T
    gains = gains.T
    stats = stats.T

    quantities.columns = [[ 'Quantities' ]]
    gains.columns = [[ 'Gains (€)' ]]
    stats.columns = [[ 'Stats' ]]

    return (
        TOTAL_PRINTED,
        res_printed,
        quantities,
        gains,
        stats,
        style_stats
    )


pd.set_option('colheader_justify', 'center') # FOR TABLE <th>

html_string = '''
<html>
  <head><title>HTML Pandas Dataframe with CSS</title></head>
  <body>
    <div class="title">
        {title}
    </div>
    <div class="legend">
        <div class="onelegend">
            <div class="box box-median"></div>
            <div class="legend_desc">Ligne gain net median</div>
        </div>
        <div><div class="onelegend">
            <div class="box box-eighty"></div>
            <div class="legend_desc">80% des gains net de la ligne 0 a celle ci</div>
        </div></div>
    </div>
    <div class="blockmain">
        <div class="block1">
            {table_0}
            {table_1}
        </div>
        <div class="block2">
            {table_2}
            {table_3}
            {table_4}
        </div>
    </div>
  </body>
</html>
'''

css_string = '''
<style>{style}\n{stats_style_string}</style>
'''

tables = process()

median_line = tables[5]['median'] + 1
eighty_line = tables[5]['eighty'] + 1
# print(median_line)
# print(type(median_line))
stats_style_string = '''
.stats tbody tr:nth-child('''+str(median_line)+''') {
    background: #9d0202;
}
.stats tbody tr:nth-child('''+str(eighty_line)+''') {
    background: #376a21;
}
'''
# quit()
with open(REPORTS_OUTPUT_PATH + args.title.replace(' ', '_').replace('/', '-') + '.html', 'w') as f:
    with open(CSS_PATH + 'pandas_style.css', 'r') as fs:
        f.write(html_string.format(
            title=args.title,
            table_0=tables[0].to_html(classes='mystyle total'),
            table_1=tables[1].to_html(classes='mystyle stats'),
            table_2=tables[2].to_html(classes='mystyle'),
            table_3=tables[3].to_html(classes='mystyle'),
            table_4=tables[4].to_html(classes='mystyle'),
        ))
        css = fs.read()
        f.write(css_string.format(style=css, stats_style_string=stats_style_string))
