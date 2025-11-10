from dash import Dash, html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go

# ===== 資料讀取 =====
views_df = pd.read_csv('data/views.csv'); views_df['Category'] = '景點'
food_df = pd.read_csv('data/food.csv'); food_df['Category'] = '食物'
acc_df = pd.read_csv('data/accomadation.csv'); acc_df['Category'] = '住宿'
act_df = pd.read_csv('data/activity.csv'); act_df['Category'] = '活動'

travel_df = pd.concat([views_df, food_df, acc_df, act_df], ignore_index=True)
display_columns = ['Name', 'Add', 'Tel', 'Category', 'City']
travel_df = travel_df[display_columns]

category_options = [{'label': c, 'value': c} for c in travel_df['Category'].unique()]
city_options = [{'label': city, 'value': city} for city in travel_df['City'].dropna().unique()]

# ===== App =====
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

# 關閉暗色模式並強制白底
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta name="color-scheme" content="light only">
        {%metas%}
        <title>旅遊資料查詢</title>
        {%favicon%}
        {%css%}
    </head>
    <body style="background-color:white;color:black;">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ===== Layout =====
app.layout = html.Div(
    style={'backgroundColor': '#FFFFFF', 'minHeight': '100vh', 'padding': '40px'},
    children=[
        dbc.Container([
            html.H2('🏖️ 旅遊資料查詢', className='text-center mb-4', style={'color': '#0d6efd'}),

            # 篩選區塊
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label('類別', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='category-dropdown',
                                options=[{'label': '全部', 'value': '全部'}] + category_options,
                                value='全部', clearable=False
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label('縣市', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='city-dropdown',
                                options=[{'label': '全部', 'value': '全部'}] + city_options,
                                value='全部', clearable=False
                            )
                        ], width=6),
                    ])
                ])
            ], className='shadow-sm mb-4', style={'borderRadius': '12px', 'backgroundColor': 'white'}),

            # 旅遊清單
            dbc.Card([
                dbc.CardBody([
                    html.H5('📋 旅遊清單', style={'color': '#0d6efd'}),
                    dash_table.DataTable(
                        id='travel-table',
                        columns=[{'name': col, 'id': col} for col in ['Name', 'Add', 'Tel']],
                        data=travel_df.to_dict('records'),
                        row_selectable='multi',
                        page_size=10,
                        style_table={'borderRadius': '10px', 'overflow': 'hidden'},
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold',
                            'color': '#000'
                        },
                        style_cell={
                            'backgroundColor': '#fff',
                            'color': '#000',
                            'textAlign': 'left',
                            'padding': '8px'
                        },
                    ),
                    html.Div(
                        html.Button('➕ 加入願望清單', id='add-to-wishlist', n_clicks=0,
                                    className='btn btn-primary mt-3'),
                        className='text-end'
                    )
                ])
            ], className='shadow-sm mb-4', style={'borderRadius': '12px', 'backgroundColor': 'white'}),

            # 願望清單
            dbc.Card([
                dbc.CardBody([
                    html.H5('📝 願望清單', style={'color': '#0d6efd'}),
                    dash_table.DataTable(
                        id='wishlist-table',
                        columns=[
                            {'name': '名稱', 'id': 'name', 'editable': False},
                            {'name': '類型', 'id': 'type', 'presentation': 'dropdown'},
                            {'name': '價格', 'id': 'price', 'type': 'numeric', 'editable': True},
                        ],
                        data=[],
                        row_deletable=True,
                        editable=True,
                        dropdown={
                            'type': {'options': [{'label': i, 'value': i} for i in ['食', '衣', '住', '行']]}
                        },
                        style_table={'marginTop': '10px', 'borderRadius': '10px'},
                        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold', 'color': '#000'},
                        style_cell={'backgroundColor': '#FFFFFF', 'color': '#000', 'textAlign': 'left', 'padding': '8px'},
                    )
                ])
            ], className='shadow-sm mb-4', style={'borderRadius': '12px', 'backgroundColor': 'white'}),

            # 預算設定
            dbc.Card([
                dbc.CardBody([
                    html.H5('💰 預算設定', style={'color': '#0d6efd'}),
                    dbc.Row([
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText('食預算'), dbc.Input(id='budget-food', type='number', value=0, min=0)]), width=3),
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText('衣預算'), dbc.Input(id='budget-clothing', type='number', value=0, min=0)]), width=3),
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText('住預算'), dbc.Input(id='budget-housing', type='number', value=0, min=0)]), width=3),
                        dbc.Col(dbc.InputGroup([dbc.InputGroupText('行預算'), dbc.Input(id='budget-transport', type='number', value=0, min=0)]), width=3),
                    ], className='mb-3'),

                    dcc.Graph(id='budget-pie'),
                    html.Div(id='remaining-budget', style={'fontWeight': 'bold', 'fontSize': '18px'})
                ])
            ], className='shadow-sm', style={'borderRadius': '12px', 'backgroundColor': 'white'})
        ])
    ]
)

# ===== Callbacks =====
@app.callback(
    Output('travel-table', 'data'),
    [Input('category-dropdown', 'value'), Input('city-dropdown', 'value')]
)
def update_travel_table(selected_category, selected_city):
    df = travel_df.copy()
    if selected_category != '全部':
        df = df[df['Category'] == selected_category]
    if selected_city != '全部':
        df = df[df['City'] == selected_city]
    return df[['Name', 'Add', 'Tel']].to_dict('records')


@app.callback(
    [Output('wishlist-table', 'data'), Output('travel-table', 'selected_rows')],
    Input('add-to-wishlist', 'n_clicks'),
    [State('travel-table', 'selected_rows'), State('travel-table', 'data'), State('wishlist-table', 'data')]
)
def add_to_wishlist(n_clicks, selected_rows, travel_data, wishlist_data):
    if not n_clicks:
        return wishlist_data, []
    if not selected_rows:
        return wishlist_data, []
    if wishlist_data is None:
        wishlist_data = []
    names_in_wishlist = {item['name'] for item in wishlist_data}
    for idx in selected_rows:
        if idx < 0 or idx >= len(travel_data):
            continue
        name = travel_data[idx]['Name']
        if name not in names_in_wishlist:
            wishlist_data.append({'name': name, 'type': '', 'price': 0})
            names_in_wishlist.add(name)
    return wishlist_data, []


@app.callback(
    Output('budget-pie', 'figure'),
    [Input('budget-food', 'value'), Input('budget-clothing', 'value'),
     Input('budget-housing', 'value'), Input('budget-transport', 'value')]
)
def update_pie(food, clothing, housing, transport):
    values = [food or 0, clothing or 0, housing or 0, transport or 0]
    labels = ['食', '衣', '住', '行']
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
    fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFF', width=2)))
    fig.update_layout(title='各類型支出佔比', paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', font_color='#000000')
    return fig


@app.callback(
    Output('remaining-budget', 'children'),
    [Input('budget-food', 'value'), Input('budget-clothing', 'value'),
     Input('budget-housing', 'value'), Input('budget-transport', 'value'),
     Input('wishlist-table', 'data')]
)
def update_remaining(food, clothing, housing, transport, wishlist_data):
    total_budget = (food or 0) + (clothing or 0) + (housing or 0) + (transport or 0)
    total_spent = sum(float(item.get('price', 0) or 0) for item in wishlist_data or [])
    remaining = total_budget - total_spent
    color = 'red' if remaining < 0 else 'black'
    return html.Span(f'剩餘預算：{remaining:.0f} 元', style={'color': color})


if __name__ == '__main__':
    app.run(debug=True)
