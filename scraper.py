import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
from functools import reduce

# FUNCIONS
# 1) GET ALL THE ITEMS IN A SPECIFIC CATEGORY (ex watches)
def get_lots(n_pages,category):
    lots_df = pd.DataFrame()

    for p in range(1,n_pages):
        try:
            # Make the request
            r = requests.get('https://www.catawiki.it/buyer/api/v1/categories/' + str(
                category) + '/lots?locale=it&per_page=100&page=' + str(p) + '&q=')
            # Extract content
            c = r.content
            # We convert json to dictionary
            result = json.loads(c)
            # we extract the lot
            lots = result["lots"]

            for i in range(len(lots) - 1):
                single_lot_id = pd.DataFrame.from_dict(lots[i], orient='index').T
                lots_df = pd.concat([lots_df, single_lot_id], ignore_index=True)
        except:
            pass

    return lots_df

# 2) EXTRACT IDS
def extract_ids(lots_df):
    lots_list = lots_df['id'].tolist()
    return  lots_list

# 3) EXTRACT FOR A GIVEN ITEM AUCTION DETAILS
def get_item_auction_details(id_list):
    items_df = pd.DataFrame()
    for id in id_list:
        try:
            r = requests.get('https://www.catawiki.it/buyer/api/v1/lots/live?ids=' + str(id))
            c = r.content
            # We convert json to dictionary
            result = json.loads(c)
            # we extract the lot
            lots = pd.DataFrame.from_dict(result["lots"][0], orient='index').T
            items_df = pd.concat([items_df, lots], ignore_index=True)
            print(id)
        except:
            pass
    return items_df

# 4) EXTRACT FOR A GIVEN BIDDING AUCTION DETAILS
def get_bidding_details(id_list):
    items_df = pd.DataFrame()
    for id in id_list:
        try:
            r = requests.get(
                'https://www.catawiki.com/buyer/api/v3/lots/' + str(id) + '/bidding_block?currency_code=EUR')
            c = r.content
            # We convert json to dictionary
            result = json.loads(c)
            # we extract the lot
            lots = pd.DataFrame.from_dict(result["bidding_block"]['lot'], orient='index').T
            items_df = pd.concat([items_df, lots], ignore_index=True)
            print(id)
        except:
            pass
    return items_df

def get_expert_estimates(list_of_ids):
    min_max = {}
    for id in list_of_ids:
        try:
            # Make the request
            r = requests.get('https://www.catawiki.com/it/l/' + str(id))
            # Extract content
            c = r.content
            soup = BeautifulSoup(c)
            min_expert_estimate_dict = \
                json.loads(soup.findAll("div", {"class": "lot-details-page-wrapper"})[0].attrs['data-props'])[
                    'expertsEstimate'][
                    'min']
            max_expert_estimate_dict = \
                json.loads(soup.findAll("div", {"class": "lot-details-page-wrapper"})[0].attrs['data-props'])[
                    'expertsEstimate'][
                    'max']
            max_expert_estimate = pd.DataFrame.from_dict(max_expert_estimate_dict, orient='index').T['EUR'][0]
            min_expert_estimate = pd.DataFrame.from_dict(min_expert_estimate_dict, orient='index').T['EUR'][0]
            min_max[id] = [min_expert_estimate, max_expert_estimate]
        except:
            pass
        expert_df = pd.DataFrame.from_dict(min_max, orient='index').reset_index()
        expert_df.columns = ['id', 'min_estimate', 'max_estimate']
        print(id)
    return expert_df


def get_shipping_costs(list_of_ids):
    shipping_cost_dict = {}
    for ids in list_of_ids:
        try:
            r = requests.get(
                'https://www.catawiki.com/buyer/api/v2/lots/%s/shipping?locale=it&currency_code=EUR' % str(ids))
            c = r.content
            # We convert json to dictionary
            result = json.loads(c)
            shipping_costs = pd.DataFrame(result["shipping"]["rates"])
            shipping_cost_dict[ids] = shipping_costs[shipping_costs['region_code'] == 'it']['price'].div(100).iloc[0]
        except:
            pass
        print(ids)
    shipping_df = pd.DataFrame.from_dict(shipping_cost_dict, orient='index').reset_index()
    shipping_df.columns = ['id', 'shipping_cost']
    return  shipping_df

# MAIN CODE
# Setting some parameters
n_pages = 2
category = 333


# Getting Lots info
lots = get_lots(n_pages, category)
# Extract list of ids
list_of_ids = extract_ids(lots)
# Get Auction Details
auction_details = get_item_auction_details(list_of_ids)
# Get bidding Details
bidding_details = get_bidding_details(list_of_ids)

# We now add the expert's estimate to the df
expert_df = get_expert_estimates(list_of_ids)

# We get shipping information
shipping_df = get_shipping_costs(list_of_ids)


# enrich info (i.e., merging all
dfs = [lots, auction_details, bidding_details,expert_df,shipping_df]
df_final = reduce(lambda left,right: pd.merge(left,right,on='id'), dfs)

# Now we have to filter out auctions that are either closed or item is sold
df_final = df_final[(df_final['is_closed']==False) & (df_final['is_sold']==False)]



print('ciao')