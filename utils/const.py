import pandas as pd

ALERT_RANK_MAP = {'灰色': 2, '黃色': 3, '橙色': 4}
ALL_COMPARE_METRICS = ['safety', 'cpi', 'pce', 'accommodation', 'transportation', 'travelers']
TAB_STYLE = {
    'idle': {
        'borderRadius': '10px','padding': '0px','marginInline': '5px','display':'flex',
        'alignItems':'center','justifyContent':'center','fontWeight': 'bold',
        'backgroundColor': '#deb522','border':'none'
    },
    'active': {
        'borderRadius': '10px','padding': '0px','marginInline': '5px','display':'flex',
        'alignItems':'center','justifyContent':'center','fontWeight': 'bold','border':'none',
        'textDecoration': 'underline','backgroundColor': '#deb522'
    }
}

def get_constants(travel_df):
    """
    計算旅遊資料的主要統計數據 (Compute key travel statistics).

    包含：
        - 總旅遊國家數 (Number of destination countries)
        - 總旅遊人數 (Number of travelers)
        - 總國籍數 (Number of traveler nationalities)
        - 平均旅遊天數 (Average travel duration, 四捨五入到小數點一位)

    參數 (Args):
        travel_df (pandas.DataFrame): 旅遊資料的 DataFrame。

    回傳 (Returns):
        tuple: (num_of_country, num_of_traveler, num_of_nationality, avg_days)
    """
    # 總旅遊國家數
    num_of_country = travel_df['Destination'].nunique()
    
    # 總旅遊人數
    num_of_traveler = travel_df['Traveler name'].nunique()

    # 總國籍數
    num_of_nationality = travel_df['Traveler nationality'].nunique()

    # 平均旅遊天數
    avg_days = round(float(travel_df['Duration (days)'].mean()), 1)

    return num_of_country, num_of_traveler, num_of_nationality, avg_days