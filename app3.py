import dash
from dash import dcc, html, Input, Output, State
import requests

# ==========================================
# 1. 設定你的 API Key
# ==========================================
# ⚠️ 請務必將下方的字串換成你申請到的 Google Maps API Key
API_KEY = "AIzaSyBU9HJ0M0EspZNoHf40JprQL8tDPZ_UZbU"

# ==========================================
# 2. 後端邏輯：串接 Places API (New)
# ==========================================
def fetch_exact_price(place_name):
    """
    輸入地點名稱，回傳顯示文字與計算後的平均金額
    """
    if not place_name:
        return "❌ 請輸入地點名稱", None

    # 新版 API 的搜尋端點
    url = "https://places.googleapis.com/v1/places:searchText"
    
    # 設定 Header
    # FieldMask 就像點菜單，我們只點我們需要的欄位，節省資源
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.priceRange"
    }
    
    # 設定搜尋關鍵字
    data = {
        "textQuery": place_name
    }

    try:
        # 發送請求
        response = requests.post(url, json=data, headers=headers)
        result = response.json()

        # 檢查回傳結果
        if "places" not in result or not result["places"]:
            return "⚠️ 找不到該地點，請嘗試輸入更完整的名稱 (例如包含地區)", None

        # 取出第一筆最相關的地點
        place = result["places"][0]
        name = place.get("displayName", {}).get("text", "未知地點")
        address = place.get("formattedAddress", "未知地址")
        price_range = place.get("priceRange")

        # 核心邏輯：如果有價格區間，就計算平均值
        if price_range:
            start_price = int(price_range['startPrice']['units'])
            end_price = int(price_range['endPrice']['units'])
            currency = price_range['startPrice']['currencyCode']
            
            # 計算平均
            average_price = (start_price + end_price) / 2
            
            # 組合顯示文字
            display_text = (
                f"📍 **地點**：{name}\n"
                f"🏠 **地址**：{address}\n"
                f"💰 **價格區間**：{start_price} - {end_price} ({currency})\n"
                f"✅ **預估平均花費：{int(average_price)} {currency}**"
            )
            return display_text, average_price
        else:
            # 雖然找到了地點，但 Google 沒有該地點的價格資料
            return (
                f"📍 **地點**：{name}\n"
                f"🏠 **地址**：{address}\n"
                f"ℹ️ 此地點在 Google 資料庫中沒有具體的「價格數字」資訊。"
            ), None

    except Exception as e:
        return f"❌ 系統發生錯誤: {str(e)}", None


# ==========================================
# 3. 前端介面：Dash 網頁佈局
# ==========================================
app = dash.Dash(__name__)
app.title = "預估花費查詢神器"

app.layout = html.Div([
    html.Div([
        # 標題區
        html.H1("Google Maps 地點花費計算器", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P("使用 Places API (New) 精確抓取價格區間", 
               style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '40px'}),
        
        # 輸入區
        html.Div([
            dcc.Input(
                id='input-place',
                type='text',
                placeholder='請輸入餐廳名稱 (例如：鼎泰豐 101)',
                style={
                    'width': '60%', 
                    'padding': '12px', 
                    'fontSize': '16px', 
                    'borderRadius': '5px',
                    'border': '1px solid #bdc3c7'
                }
            ),
            html.Button(
                '開始搜尋', 
                id='btn-search', 
                n_clicks=0,
                style={
                    'padding': '12px 25px', 
                    'fontSize': '16px', 
                    'backgroundColor': '#3498db', 
                    'color': 'white', 
                    'border': 'none',
                    'borderRadius': '5px',
                    'cursor': 'pointer',
                    'marginLeft': '10px',
                    'fontWeight': 'bold'
                }
            ),
        ], style={'textAlign': 'center', 'marginBottom': '30px'}),

        # 載入動畫與結果區
        dcc.Loading(
            id="loading-spinner",
            type="circle",
            color="#3498db",
            children=html.Div(
                id='result-display', 
                style={
                    'whiteSpace': 'pre-line',  # 讓換行符號生效
                    'backgroundColor': '#ecf0f1',
                    'padding': '30px',
                    'borderRadius': '10px',
                    'maxWidth': '600px',
                    'margin': '0 auto',
                    'fontSize': '18px',
                    'lineHeight': '1.8',
                    'color': '#2c3e50',
                    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                }
            )
        )
    ], style={'fontFamily': 'Microsoft JhengHei, Arial, sans-serif', 'padding': '50px'})
])

# ==========================================
# 4. 互動控制：連接按鈕與函式
# ==========================================
@app.callback(
    Output('result-display', 'children'),
    Input('btn-search', 'n_clicks'),
    State('input-place', 'value'),
    prevent_initial_call=True
)
def update_output(n_clicks, value):
    if not value:
        return "請輸入地點名稱"
    
    # 呼叫後端邏輯
    result_text, _ = fetch_exact_price(value)
    return dcc.Markdown(result_text) # 使用 Markdown 讓粗體顯示更漂亮

# ==========================================
# 5. 啟動伺服器
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=8050)