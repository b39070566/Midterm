import dash
from dash import dcc, html, Output, Input, State
import requests
import json

app = dash.Dash(__name__)

API_KEY = '' 
 # 換你的 Google Maps API Key

app.layout = html.Div([
    dcc.Input(id='address', type='text', placeholder='輸入地址...', style={'fontSize': 20}),
    dcc.Input(id='budget', type='number', placeholder='預算上限', style={'fontSize': 20}),
    html.Button('查詢', id='search-btn', style={'fontSize': 20}),
    html.Div(id='result', style={'fontSize': 20}),
    dcc.Checklist(id='place-selector', options=[], value=[]),
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

def search_places(lat, lng, apikey, radius=1000, types='restaurant'):
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
        place_details_dict[p['place_id']] = p
        pl = p.get('price_level')
        print(f"店名: {p.get('name','未知')}, price_level={pl} ({type(pl)}), 預算等級={max_price_level}")
        try:
            pl_int = int(pl) if pl is not None else None
        except Exception as e:
            print(f"型別轉換失敗: {e}")
            pl_int = None

        if pl_int is not None and pl_int <= max_price_level:
            ann = f"{p.get('name','未知')} - 地址：{p.get('vicinity','無')} - 價位等級 {pl_int} - 評分 {p.get('rating','無')}"
            results.append({'label': ann, 'value': p['place_id']})
        elif 'price_range' in p and within_budget(p['price_range'], budget):
            ann = f"{p.get('name','未知')} - 地址：{p.get('vicinity','無')} - 價格區間 {p['price_range']} - 評分 {p.get('rating','無')}"
            results.append({'label': ann, 'value': p['place_id']})

    if not results:
        return '附近有店家，但 "價位等級" 欄位出現型別錯誤或缺值，請檢查API回傳。', {}

    return dcc.Checklist(
        options=results,
        value=[],
        id='place-selector'
    ), place_details_dict

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
            try:
                pl_int = int(pl) if pl is not None else None
            except:
                pl_int = None
            if pl_int:
                level_price_map = {1: 100, 2: 300, 3: 600, 4: 1000}
                cost = level_price_map.get(pl_int, 0)
        total_cost += cost

    if total_cost > budget:
        return f'⚠️ 超出預算 {total_cost}，請調整選擇或提高預算！'
    return ''

if __name__ == '__main__':
    app.run(debug=True)

