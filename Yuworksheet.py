import dash
from dash import dcc, html, Output, Input, State
import requests
import json

app = dash.Dash(__name__)

API_KEY = 'AIzaSyAazjhcq0nW4Qzi7D0I3fMM0kQCz-NUVCU'  # 請替換成你的Google Maps API Key

app.layout = html.Div([
    dcc.Input(id='address', type='text', placeholder='輸入地址...', style={'fontSize': 20}),
    dcc.Input(id='budget', type='number', placeholder='預算上限', style={'fontSize': 20}),
    html.Button('查詢', id='search-btn', style={'fontSize': 20}),
    html.Div(id='result', style={'fontSize': 20}),
    dcc.Checklist(id='place-selector', options=[], value=[]),  # 這行一定要加在 layout 中
    dcc.Store(id='all-place-details', data={}),
    html.Div(id='budget-warning', style={'color': 'red', 'marginTop': '20px', 'fontSize': 20}),
], style={'fontSize': 60})

def get_latlng(address, apikey):
    resp = requests.get(
        'https://maps.googleapis.com/maps/api/geocode/json',
        params={'address': address, 'key': apikey}
    ).json()
    loc = resp['results'][0]['geometry']['location']
    return loc['lat'], loc['lng']

def search_places(lat, lng, apikey, radius=300, types='restaurant'):
    resp = requests.get(
        'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
        params = {
            'location': f'{lat},{lng}',
            'radius': radius,
            'type': types,
            'key': apikey
        }
    ).json()
    print('Nearby API response:', resp)  
    return resp.get('results', [])

def get_place_detail(place_id, apikey):
    resp = requests.get(
        'https://maps.googleapis.com/maps/api/place/details/json',
        params = {
            'place_id': place_id,
            'fields': 'place_id,name,price_level,price_range,rating,formatted_address,type',
            'key': apikey
        }
    ).json()
    return resp.get('result', {})

def price_level_by_budget(budget):
    if budget is None:
        return 4
    if budget <= 100:
        return 1
    elif budget <= 300:
        return 2
    elif budget <= 600:
        return 3
    else:
        return 4

def within_budget(price_range, budget):
    if not price_range or budget is None:
        return False
    try:
        price_range = price_range.replace('$', '')
        start_str, end_str = price_range.split('-')
        start, end = float(start_str.strip()), float(end_str.strip())
        return start <= budget
    except Exception:
        return False

# 搜尋並回傳結果＋存細節
@app.callback(
    Output('result', 'children'),
    Output('all-place-details', 'data'),
    Input('search-btn', 'n_clicks'),
    State('address', 'value'),
    State('budget', 'value'),
)
def suggest(n, address, budget):
    if not address or not budget:
        return '請輸入地址與預算', {}

    try:
        lat, lng = get_latlng(address, API_KEY)
    except Exception as e:
        return f'地址轉經緯度錯誤: {e}', {}

    nearby = search_places(lat, lng, API_KEY)
    if not nearby:
        return '附近找不到相關店家', {}

    max_price_level = price_level_by_budget(budget)
    results = []
    place_details_dict = {}

    for p in nearby:
        detail = get_place_detail(p['place_id'], API_KEY)
        if not detail:
            continue

        place_details_dict[detail['place_id']] = detail

        if 'price_level' in detail and detail['price_level'] <= max_price_level:
            ann = f"{detail.get('name','未知')} - 地址：{detail.get('formatted_address','無')} - 價位等級 {detail.get('price_level')} - 評分 {detail.get('rating','無')}"
            results.append({'label': ann, 'value': detail['place_id']})
        elif 'price_range' in detail and within_budget(detail['price_range'], budget):
            ann = f"{detail.get('name','未知')} - 地址：{detail.get('formatted_address','無')} - 價格區間 {detail.get('price_range')} - 評分 {detail.get('rating','無')}"
            results.append({'label': ann, 'value': detail['place_id']})

    if not results:
        return '沒有符合預算的行程建議', {}

    return dcc.Checklist(
        options=results,
        value=[],
        id='place-selector'
    ), place_details_dict

# 監聽所選景點總價是否超預算
@app.callback(
    Output('budget-warning', 'children'),
    Input('place-selector', 'value'),
    State('budget', 'value'),
    State('all-place-details', 'data')
)
def check_budget(selected_places, budget, all_details):
    if not selected_places or not budget:
        return ''

    total_cost = 0
    for place_id in selected_places:
        detail = all_details.get(place_id, {})
        cost = 0
        # 以 price_range 假設計算平均數，無則用 price_level 換算
        pr = detail.get('price_range')
        if pr and '-' in pr:
            try:
                pr_clean = pr.replace('$', '')
                start, end = pr_clean.split('-')
                cost = (float(start.strip()) + float(end.strip())) / 2
            except:
                cost = 0
        else:
            pl = detail.get('price_level')
            if pl:
                # 簡單換算
                level_price_map = {1: 100, 2: 300, 3: 600, 4: 1000}
                cost = level_price_map.get(pl, 0)

        total_cost += cost

    if total_cost > budget:
        return f'⚠️ 超出預算 {total_cost}，請調整選擇或提高預算！'
    return ''

if __name__ == '__main__':
    app.run(debug=True)
