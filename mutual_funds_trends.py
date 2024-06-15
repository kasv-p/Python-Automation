mf_prefix = "baroda bnp"
import requests
from collections import defaultdict
import datetime
import time
import bisect
import json

current_date, one_day_before, start_of_week, start_of_month = None, None, None, None

def get_data_from_url(url, params={}):
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data for search query: {response.status_code},{url}")
        return None
    
def set_start_periods():
    global current_date, one_day_before, start_of_week, start_of_month

    current_date = datetime.datetime.now().date()
    one_day_before = current_date - datetime.timedelta(days=1)
    start_of_week = current_date - datetime.timedelta(days=current_date.weekday())
    
    
    periods = [
        datetime.datetime.combine(current_date, datetime.time.min),
        datetime.datetime.combine(one_day_before, datetime.time.min),
        datetime.datetime.combine(start_of_week, datetime.time.min),
        datetime.datetime(current_date.year, current_date.month, 1)
    ]
    
    current_date, one_day_before, start_of_week, start_of_month  = [int(time.mktime(epoch.timetuple()))*1000 for epoch in periods]

def get_time_framed_data(scheme_code):
    url = f"https://groww.in/v1/api/data/mf/web/v1/scheme/{scheme_code}/graph"
    params = {
        "benchmark": False,
        "months": 1
    }
    data = get_data_from_url(url, params)
    if data is None:
        return
    data = data['folio']['data']
    data_dict = defaultdict(lambda:-1)
    for i,j in data:
        data_dict[i]=j
    return data_dict

def binary_search_dict(key, d, bisect_right = True):
    sorted_keys = list(d.keys())
    if key in d:
        return d[key]
    if bisect_right:
        index = bisect.bisect_right(sorted_keys, key)
        if index < len(sorted_keys):
            return d[sorted_keys[index]]
        else:
            return -1
    else:
        index = bisect.bisect_left(sorted_keys, key)
        if index < len(sorted_keys):
            return d[sorted_keys[index]]
        else:
            return -1

    
schemes_data = defaultdict(dict)
def analyze_scheme(scheme_data):
    # need help for this 
    # regex and sort based on some heuristic , need to figure out some heuristic
    # "exit_load": "For units more than 10% of the investments, an exit load of 1% if redeemed within 12 months.",
    if scheme_data is None:return
    name = scheme_data['scheme_name']
    schemes_data[name]['exit_load'] = scheme_data['exit_load']
    schemes_data[name]['scheme_code'] = scheme_data['scheme_code']
    return_stats = scheme_data['return_stats']
    return_stats = return_stats[0]
    for key in return_stats.keys():
        if key.startswith("return"):
            schemes_data[name][key] = return_stats[key]
    # url to get data of a month and analyze on that data 
    # why bisect market will not be there on holidays bruhhh !!!
    time_framed_data = get_time_framed_data(scheme_data['scheme_code'])
    schemes_data[name]['today'] = binary_search_dict(current_date, time_framed_data, True)
    schemes_data[name]['one_day_before'] = binary_search_dict(one_day_before, time_framed_data, False)
    schemes_data[name]['from_start_of_the_month'] = binary_search_dict(start_of_month, time_framed_data, True)
    schemes_data[name]['from_start_of_the_week'] = binary_search_dict(start_of_week, time_framed_data, True)

    x = schemes_data[name]['from_start_of_the_month']
    y = schemes_data[name]['one_day_before']
    schemes_data[name]['percent_change_from_month_start_to_day_before'] = (y - x)*100/x


def search_scheme(mfs_data):
    global schemes_data
    n=len(mfs_data)
    for i in range(n):
        search_id = mfs_data[i]['search_id']
        # url to search for sub scheme
        url = f"https://groww.in/v1/api/data/mf/web/v3/scheme/search/{search_id}"
        analyze_scheme(get_data_from_url(url))
    # print(schemes_data)
    schemes_data = dict(sorted(schemes_data.items(), key=lambda x: x[1]['percent_change_from_month_start_to_day_before']))
    print(json.dumps(schemes_data))


set_start_periods()
    
# this is api for global search
url = "https://groww.in/v1/api/search/v3/query/global/st_p_query"
params = {
    "entity_type": "scheme",
    "page": 0,
    "query": mf_prefix,
    "size": 500,
    "web": "true"
}

search_scheme(get_data_from_url(url,params)['data']['content'])

