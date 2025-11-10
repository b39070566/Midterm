import pandas as pd

def travel_data_clean(travel_df):
    # 去除空值    
    travel_df = travel_df.dropna()

    # 將花費欄位從str轉換成int
    travel_df['Accommodation cost'] = travel_df['Accommodation cost'].str.replace('$', '')
    travel_df['Accommodation cost'] = travel_df['Accommodation cost'].str.replace(',', '')
    travel_df['Accommodation cost'] = travel_df['Accommodation cost'].str.replace(' USD', '')
    travel_df['Accommodation cost'] = travel_df['Accommodation cost'].astype(float)

    travel_df['Transportation cost'] = travel_df['Transportation cost'].str.replace('$', '')
    travel_df['Transportation cost'] = travel_df['Transportation cost'].str.replace(',', '')
    travel_df['Transportation cost'] = travel_df['Transportation cost'].str.replace(' USD', '')
    travel_df['Transportation cost'] = travel_df['Transportation cost'].astype(float)

    # 將日期欄位從str轉換成datetime
    travel_df['Start date'] = pd.to_datetime(travel_df['Start date'])
    travel_df['End date'] = pd.to_datetime(travel_df['End date'])

    # 新增總花費欄位
    travel_df['Total cost'] = travel_df['Accommodation cost'] + travel_df['Transportation cost']

    # 將年齡劃分成不同區間 - 5歲一組
    # 先取出最大最小值
    min_age = travel_df['Traveler age'].min()
    max_age = travel_df['Traveler age'].max()
    # 以5歲為一組，劃分年齡區間
    bins = list(range(int(min_age), int(max_age), 5))
    # 將年齡區間轉換成str
    labels = [f'{i}-{i+4}' for i in bins[:-1]]
    # 將年齡區間新增到DataFrame中
    travel_df['Age group'] = pd.cut(travel_df['Traveler age'], bins=bins, labels=labels)

    # 依照旅遊開始日期劃分月份
    travel_df['Start month'] = travel_df['Start date'].dt.month
    # 將月份轉換成英文
    travel_df['Start month'] = travel_df['Start month'].map({1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'})

    return travel_df

def countryinfo_data_clean(countryinfo_df):
    # 去除空值
    countryinfo_df = countryinfo_df.dropna()

    return countryinfo_df

def data_merge(df_travel, df_countryinfo):

    df_countryinfo = df_countryinfo.rename(columns={'Country': 'Destination'})

    df = pd.merge(df_travel, df_countryinfo, on='Destination', how='left')

    return df