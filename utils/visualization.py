import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dash import html, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.colors as colors
from .data_validation import fmt

def build_compare_figure(df_result, chart_type, title):
    metric_columns = [col for col in df_result.columns if col != 'Country']
    fig = go.Figure()

    if not metric_columns:
        fig.update_layout(
            template='plotly_dark', font=dict(color='#deb522'), title=title,
            annotations=[dict(text='沒有可比較的指標', x=0.5, y=0.5, showarrow=False, font=dict(color='#deb522'))]
        )
        return fig

    df_numeric = df_result.copy()
    for col in metric_columns:
        df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce')

    if chart_type == 'radar':
        df_normalized = df_numeric.copy()
        for col in metric_columns:
            series = df_numeric[col]
            if series.dropna().empty:
                df_normalized[col] = np.nan
                continue
            min_val, max_val = series.min(), series.max()
            if max_val > min_val:
                df_normalized[col] = 100 * (series - min_val) / (max_val - min_val)
            else:
                df_normalized[col] = 50

        for _, row in df_normalized.iterrows():
            values = [row[col] if pd.notna(row[col]) else 0 for col in metric_columns]
            if values:
                values.append(values[0])
            theta = metric_columns + [metric_columns[0]] if metric_columns else metric_columns
            fig.add_trace(go.Scatterpolar(r=values, theta=theta, fill='toself', name=row['Country']))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            template='plotly_dark', font=dict(color='#deb522'), title=title, height=600
        )

    elif chart_type == 'bar':
        for col in metric_columns:
            fig.add_trace(go.Bar(
                name=col, x=df_result['Country'], y=df_numeric[col],
                text=df_numeric[col].round(2), textposition='auto'
            ))
        fig.update_layout(
            barmode='group', template='plotly_dark', font=dict(color='#deb522'), title=title,
            xaxis_title='Country', yaxis_title='Value', height=600
        )

    else:  # line
        for col in metric_columns:
            fig.add_trace(go.Scatter(
                x=df_result['Country'], y=df_numeric[col], mode='lines+markers+text',
                name=col, text=df_numeric[col].round(2), textposition='top center'
            ))
        fig.update_layout(
            template='plotly_dark', font=dict(color='#deb522'), title=title,
            xaxis_title='Country', yaxis_title='Value', height=600
        )

    return fig

def generate_stats_card(title, value, image_path):
    return html.Div(
        dbc.Card([
            dbc.CardImg(src=image_path, top=True, style={'width': '50px', 'height': '50px','alignSelf': 'center'}),
            dbc.CardBody([
                html.P(value, className="card-value",
                       style={'margin': '0px','fontSize': '22px','fontWeight': 'bold'}),
                html.H4(title, className="card-title",
                        style={'margin': '0px','fontSize': '18px','fontWeight': 'bold'})
            ], style={'textAlign': 'center'}),
        ], style={'paddingBlock':'10px',"backgroundColor":'#deb522','border':'none','borderRadius':'10px'})
    )

def build_table_component(out):
    """整理欄位格式與樣式，輸出 Dash DataTable 元件"""
    shown_cols = [
        'Country', 'Score', 'Safety Index', 'Travel Alert', 'CPI', 'PCE', 'Visa_exempt_entry',
        'trips', 'median_daily_acc_cost', 'adj_daily_acc_cost', 'median_trip_acc_cost'
    ]
    available_cols = [c for c in shown_cols if c in out.columns]
    out_display = out[available_cols].copy()

    # 格式化分數與金額
    if 'Score' in out_display:
        out_display['Score'] = out_display['Score'].apply(lambda v: fmt(v, 0))
    for c in ['median_daily_acc_cost', 'adj_daily_acc_cost', 'median_trip_acc_cost']:
        if c in out_display:
            out_display[c] = out_display[c].apply(lambda v: fmt(v, 0))

    table = dash_table.DataTable(
        data=out_display.to_dict('records'),
        page_size=10,
        export_format='csv',
        sort_action='native',
        filter_action='native',
        style_data={'backgroundColor': '#deb522', 'color': 'black'},
        style_header={'backgroundColor': 'black', 'color': '#deb522', 'fontWeight': 'bold'},
        style_table={'overflowX': 'auto'},
        columns=[{'name': col, 'id': col} for col in available_cols]
    )
    return table    


# 長條圖
def generate_bar(df, dropdown_value):
    if dropdown_value is None:
        # 回傳一個空的圖表，或在這裡設置一個預設訊息
        fig_bar = px.bar(title="請選擇有效的選項")
        fig_bar.update_layout(template='plotly_dark', font=dict(color='#deb522'))
    
        return fig_bar

    # 長條圖的x軸要依照月份順序排列
    # 定義月份的順序
    month_order = ['January', 'February', 'March', 'April', 'May', 
                'June', 'July', 'August', 'September', 'October', 
                'November', 'December']

    # 過濾資料
    df_group = df[(df['Continent'] == dropdown_value) | (df['Destination'] == dropdown_value)]

    # 計算 'Start month' 的數量
    month_counts = df_group['Start month'].value_counts().reindex(month_order, fill_value=0).reset_index()
    month_counts.columns = ['Start month', 'count']  # 設定新列名

    # 計算百分比
    month_counts['percentage'] = (month_counts['count'] / month_counts['count'].sum()) * 100

    # 將 'Start month' 列轉換為類別型資料並設置順序
    month_counts['Start month'] = pd.Categorical(month_counts['Start month'], categories=month_order, ordered=True)
        
    # 依照月份順序排序
    month_counts = month_counts.sort_values(by='Start month')

    fig_bar = px.bar(month_counts, x='Start month', y='count',
                    color='count', text='percentage',
                    title=f'{dropdown_value} - Traveler number each month',
                    labels={'count': 'Count', 'index': 'Start month', 'percentage': 'Percentage'},
                    color_continuous_scale='Viridis')
    
    fig_bar.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_bar.update_layout(yaxis=dict(categoryorder='total ascending'))
    fig_bar.update_layout(template='plotly_dark', font=dict(color='#deb522'))

    return fig_bar

def generate_pie(df, dropdown_value_1, dropdown_value_2):

    if dropdown_value_1 is None or dropdown_value_2 is None:
        # 回傳一個空的圖表，或在這裡設置一個預設訊息
        fig_pie = px.pie(title="請選擇有效的選項")
        fig_pie.update_layout(template='plotly_dark', font=dict(color='#deb522'))
    
        return fig_pie
 
    # 過濾出符合 `dropdown_value_1` 的資料
    df_group = df[(df['Continent'] == dropdown_value_1) | (df['Destination'] == dropdown_value_1)]
    
    # 使用 `value_counts()` 計算 `dropdown_value_2` 欄位的次數，並重置索引以創建新的資料框
    df_counts = df_group[dropdown_value_2].value_counts().reset_index(name = 'count')
    
    # 建立圓餅圖，使用 `dropdown_value_2` 作為標籤，`count` 作為數值
    fig_pie = px.pie(
        df_counts, 
        names=dropdown_value_2,  # 圓餅圖的標籤欄位
        values='count',  # 圓餅圖的數值欄位
        title=f'{dropdown_value_1} - {dropdown_value_2}',
        color_discrete_sequence=colors.sequential.Viridis  # 圖表標題
    )
        
    # 更新圖表樣式
    fig_pie.update_layout(template='plotly_dark', font=dict(color='#deb522'))

    return fig_pie

def generate_map(df, dropdown_value_1, dropdown_value_2):

    if dropdown_value_1 is None and dropdown_value_2 is None:
        # 回傳一個空的圖表，或在這裡設置一個預設訊息
        fig_choropleth = px.choropleth(title="請選擇有效的選項")
        fig_choropleth.update_layout(template='plotly_dark', font=dict(color='#deb522'))
    
        return fig_choropleth

    country_mapping = {
        'USA': 'USA',
        'UK': 'GB-ENG',
        'France': 'FRA',
        'Canada': 'CAN',
        'Germany': 'DEU',
        'Japan': 'JPN',
        'Australia': 'AUS',
        'Italy': 'ITA',
        'Spain': 'ESP',
        'Mexico': 'MEX',
        'New Zealand': 'NZL',
        'South Korea': 'KOR',
        'United Arab Emirates': 'ARE',
        'Netherlands': 'NLD',
        'South Africa': 'ZAF',
        'Thailand': 'THA',
        'Egypt': 'EGY',
        'Brazil': 'BRA',
        'Morocco': 'MAR',
        'Indonesia': 'IDN',
        'Scotland': 'GB-SCT',
        'Greek': 'GRC',
        'Cambodia': 'KHM',  
    }

    if dropdown_value_1 != None:
        df_group = df[df['Continent'] == dropdown_value_1]  
    else:
        df_group = df.copy()

    df_group['Destination'] = df_group['Destination'].map(country_mapping)

    fig_choropleth = px.choropleth(df_group, 
                                    locations="Destination",
                                    color=dropdown_value_2,
                                    hover_name="Destination",
                                    title=f"{dropdown_value_1} - {dropdown_value_2}",
                                    projection="natural earth",
                                    color_continuous_scale='Viridis')
    
    fig_choropleth.update_layout(template='plotly_dark', font=dict(color='#deb522'))
    
    return fig_choropleth

def generate_box(df, dropdown_value_1, dropdown_value_2):

    if dropdown_value_1 is None or dropdown_value_2 is None:
        # 回傳一個空的圖表，或在這裡設置一個預設訊息
        fig_boxplot = px.box(title="請選擇有效的選項")
        fig_boxplot.update_layout(template='plotly_dark', font=dict(color='#deb522'))
    
        return fig_boxplot

    df_group = df[(df['Continent'] == dropdown_value_1) | (df['Destination'] == dropdown_value_1)]
    
    fig_boxplot = px.box(df_group, x=dropdown_value_2, title=f'{dropdown_value_1} - {dropdown_value_2}')
    fig_boxplot.update_traces(marker=dict(color='#deb522'))
    fig_boxplot.update_layout(template='plotly_dark', font=dict(color='#deb522'))

    return fig_boxplot