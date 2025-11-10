import pandas as pd
import numpy as np
from .const import ALERT_RANK_MAP
from .data_validation import is_exempt, minmax

def pick_country_level(df_merged, matched_countries):
    """取國家層欄位並做簡單聚合（拿到第一個非空值）"""
    
    # 設定分析所需的關鍵欄位，並確認欄位存在
    cols_needed = ['Destination', 'CPI', 'PCE', 'Safety Index', 'Visa_exempt_entry', 'Travel Alert']
    avail_cols = [c for c in cols_needed if c in df_merged.columns]
    
    # 過濾出「有被篩選到的國家」的資料
    sub = df_merged[df_merged['Destination'].isin(matched_countries)][avail_cols].copy()

    def first_nonnull(series):
        for v in series:
            # ← 去掉空字串與 NaN
            if pd.notna(v) and str(v).strip() != '':
                return v
        return np.nan
    agg_spec = {col: first_nonnull for col in avail_cols if col != 'Destination'}
    
     # groupby 以「Destination」為單位做彙整
    df_country = sub.groupby('Destination', as_index=False).agg(agg_spec)

    # 這些是評分所必需的關鍵欄位；任一缺就先拿掉，避免之後計算有問題
    key_cols = ['CPI', 'PCE', 'Safety Index', 'Travel Alert']
    df_country = df_country.dropna(subset=key_cols, how='any')
    return df_country

def filter_by_alert_and_visa(df_country, alert_max, visa_only):
    """依 Travel Alert 門檻 + 是否只要免簽國過濾"""
    if alert_max is not None:
        max_rank = get_alert_rank(alert_max)
        # ← 將每列的 Travel Alert 轉成 rank 再比大小
        df_country = df_country[df_country['Travel Alert'].apply(get_alert_rank) <= max_rank]

    if 'exempt' in (visa_only or []):
        if 'Visa_exempt_entry' in df_country.columns:
            df_country = df_country[df_country['Visa_exempt_entry'].apply(is_exempt)]
    return df_country

def sanitize_cost_bounds(cost_min, cost_max):
    """防呆：確保 min <= max；若有 None 就原樣回傳"""
    if cost_min is not None and cost_max is not None and cost_min > cost_max:
        return cost_max, cost_min  # ← 對調，避免使用者輸入顛倒
    return cost_min, cost_max

def preprocess_travel_df(df):
    """欄位轉型、去除無效天數、計算每日/整趟住宿費"""
    df = df.copy()
    df['Accommodation cost'] = pd.to_numeric(df['Accommodation cost'], errors='coerce').fillna(0)
    df['Duration (days)']   = pd.to_numeric(df['Duration (days)'], errors='coerce')
    df = df.dropna(subset=['Duration (days)'])
    df = df[df['Duration (days)'] > 0]  # ← 避免除以 0（或負值）造成錯誤
    df['acc_trip_cost']  = df['Accommodation cost']
    df['acc_daily_cost'] = df['acc_trip_cost'] / df['Duration (days)']
    return df

def filter_by_cost_and_types(df, cost_min, cost_max, acc_types):
    """依住宿費區間 + 住宿類型多選過濾"""
    if cost_min is not None:
        df = df[df['Accommodation cost'] >= float(cost_min)]
    if cost_max is not None:
        df = df[df['Accommodation cost'] <= float(cost_max)]
    if acc_types:
        df = df[df['Accommodation type'].isin(acc_types)]
    return df

def get_alert_rank(alert_name, default_rank=3):
    """
    根據 ALERT_RANK_MAP 取得這個警示顏色的等級。
    數字越小代表愈安全。
    如果沒在 map 裡，給它 default_rank = 3。
    """
    return ALERT_RANK_MAP.get(str(alert_name).strip(), default_rank)

def get_dashboard_default_values(df_merged):
    _conts = [c for c in df_merged['Continent'].dropna().unique().tolist() if str(c).strip() != ""]
    _dests = [d for d in df_merged['Destination'].dropna().unique().tolist() if str(d).strip() != ""]
    _first_geo = (_conts[0] if _conts else (_dests[0] if _dests else None))
    defaults = {
        "bar1_geo": _first_geo,
        "pie1_geo": _first_geo,
        "pie2_field": "Traveler nationality",
        "map1_geo": None,                 # None 代表 All
        "map2_metric": "Safety Index",
        "box1_geo": _first_geo,
        "box2_metric": "Accommodation cost",
    }
    return defaults

def adjust_costs_with_cpi(out_df):
    """用 CPI 做相對調整，讓不同國家成本可比"""
    out = out_df.copy()
    cpi_median = out['CPI'].dropna().median() if 'CPI' in out.columns else np.nan

    def adjust_cost(row):
        base = row['median_daily_acc_cost']
        cpi  = row['CPI'] if 'CPI' in row and pd.notna(row['CPI']) else np.nan
        # ← 僅在都有數值且中位數 > 0 才做比例調整
        if pd.notna(base) and pd.notna(cpi) and pd.notna(cpi_median) and cpi_median > 0:
            return base * (cpi / cpi_median)
        return base

    out['adj_daily_acc_cost'] = out.apply(adjust_cost, axis=1)  # ← row-wise 計算
    return out

def normalize_weights(w_safety, w_cost):
    """權重正規化，避免 (0,0) 造成除以 0"""
    ws = (w_safety or 0)
    wc = (w_cost or 0)
    denom = (ws + wc) or 1  # ← 若兩者皆 0，令分母為 1，避免 ZeroDivision
    return ws / denom, wc / denom

def compute_scores(out, w_safety, w_cost):
    """把 Safety 與 Cost（反向）做 0~1 MinMax，依權重算總分"""
    out = out.copy()

    # 數值欄位轉型（以防有字串）
    for col in ['CPI', 'PCE', 'Safety Index']:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors='coerce')

    # 成本 × CPI 調整
    out = adjust_costs_with_cpi(out)

    # 指標正規化：安全越高越好；成本越低越好（所以要 1 - minmax）
    s_safety  = minmax(out['Safety Index']) if 'Safety Index' in out.columns else None
    s_cost_raw = minmax(out['adj_daily_acc_cost'])
    s_cost = 1 - s_cost_raw if s_cost_raw is not None else None  # ← 成本越低分數越高

    ws, wc = normalize_weights(w_safety, w_cost)

    scores = []
    for i in range(len(out)):
        parts, wts = [], []
        if s_safety is not None and pd.notna(s_safety.iloc[i]):
            parts.append(s_safety.iloc[i]); wts.append(ws)
        if s_cost is not None and pd.notna(s_cost.iloc[i]):
            parts.append(s_cost.iloc[i]);   wts.append(wc)

        if len(parts) == 0 or sum(wts) == 0:
            scores.append(np.nan)  # ← 沒有任何有效指標時給 NaN
        else:
            norm = sum(wts)
            wts = [w / norm for w in wts]  # ← 實際參與的權重再正規化一次
            scores.append(100 * sum(p * w for p, w in zip(parts, wts)))  # ← 拉到 0~100 分
    out['Score'] = scores
    return out

def prepare_country_compare_data(countries, metrics, df_merged):
    valid_metrics = metrics or []
    valid_countries = countries or []

    if not valid_countries or not valid_metrics:
        return pd.DataFrame(), []

    # 去除非字串或重複國家，並限制最大數量
    seen = set()
    deduped = []
    for country in valid_countries:
        if not isinstance(country, str):
            continue
        if country in seen:
            continue
        seen.add(country)
        deduped.append(country)

    available_destinations = set(df_merged['Destination'].dropna().unique())
    limited_countries = [c for c in deduped if c in available_destinations][:5]

    if not limited_countries:
        return pd.DataFrame(), []

    df_compare = df_merged[df_merged['Destination'].isin(limited_countries)].copy()
    if df_compare.empty:
        return pd.DataFrame(), []

    comparison_data = []
    for country in limited_countries:
        country_data = df_compare[df_compare['Destination'] == country]
        if country_data.empty:
            continue

        row = {'Country': country}

        if 'safety' in valid_metrics and 'Safety Index' in country_data.columns:
            safety = country_data['Safety Index'].dropna()
            row['Safety Index'] = safety.iloc[0] if not safety.empty else np.nan

        if 'cpi' in valid_metrics and 'CPI' in country_data.columns:
            cpi = country_data['CPI'].dropna()
            row['CPI'] = cpi.iloc[0] if not cpi.empty else np.nan

        if 'pce' in valid_metrics and 'PCE' in country_data.columns:
            pce = country_data['PCE'].dropna()
            row['PCE'] = pce.iloc[0] if not pce.empty else np.nan

        if 'accommodation' in valid_metrics and 'Accommodation cost' in country_data.columns:
            acc_cost = pd.to_numeric(country_data['Accommodation cost'], errors='coerce')
            row['Avg Accommodation Cost'] = acc_cost.mean() if not acc_cost.isna().all() else np.nan

        if 'transportation' in valid_metrics and 'Transportation cost' in country_data.columns:
            trans_cost = pd.to_numeric(country_data['Transportation cost'], errors='coerce')
            row['Avg Transportation Cost'] = trans_cost.mean() if not trans_cost.isna().all() else np.nan

        if 'travelers' in valid_metrics:
            row['Total Travelers'] = len(country_data)

        comparison_data.append(row)

    df_result = pd.DataFrame(comparison_data)
    return df_result, limited_countries
