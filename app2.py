from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import os


# =======================================
# 讀取四個 CSV 並統一欄位
# 我是嘉宏
# =======================================
def load_data() -> pd.DataFrame:
    base_dir = os.path.dirname(__file__)

    def prepare(df: pd.DataFrame, mappings: dict, category: str) -> pd.DataFrame:
        df = df.copy()
        df.columns = df.columns.map(str)
        df = df.rename(columns=mappings)
        df["Category"] = category
        # 活動沒有具體地址 → 用縣市代替
        if category == "活動" and "City" in df.columns:
            df["Add"] = df["City"]
        for col in ["Name", "Add", "Tel", "City"]:
            if col not in df.columns:
                df[col] = ""
        return df[["Name", "Add", "Tel", "City", "Category"]]

    mappings_views = {"名稱": "Name", "地址": "Add", "電話": "Tel", "縣市": "City"}
    mappings_food = {"名稱": "Name", "地址": "Add", "電話": "Tel", "縣市": "City"}
    mappings_acco = {"名稱": "Name", "地址": "Add", "電話": "Tel", "縣市": "City"}
    mappings_act = {"名稱": "Name", "縣市": "City", "電話": "Tel"}

    views = pd.read_csv(os.path.join(base_dir, "data", "views.csv"))
    food = pd.read_csv(os.path.join(base_dir, "data", "food.csv"))
    accom = pd.read_csv(os.path.join(base_dir, "data", "accomadation.csv"))
    act = pd.read_csv(os.path.join(base_dir, "data", "activity.csv"))

    views_prepared = prepare(views, mappings_views, "景點")
    food_prepared = prepare(food, mappings_food, "食物")
    accom_prepared = prepare(accom, mappings_acco, "住宿")
    act_prepared = prepare(act, mappings_act, "活動")

    combined = pd.concat(
        [views_prepared, food_prepared, accom_prepared, act_prepared],
        ignore_index=True,
    ).reset_index(drop=True)

    return combined.fillna("")


# =======================================
# 建立 Dash App
# =======================================
def create_app() -> Dash:
    travel_df = load_data()
    category_options = [
        {"label": c, "value": c} for c in sorted(travel_df["Category"].unique())
    ]
    city_options = [
        {"label": c, "value": c} for c in sorted(travel_df["City"].unique()) if c
    ]

    app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
    server = app.server

    app.layout = html.Div(
        style={"backgroundColor": "#FFFFFF", "minHeight": "100vh", "padding": "40px"},
        children=[
            dbc.Container(
                [
                    html.H2(
                        "🏖️ 旅遊資料查詢",
                        className="text-center mb-4",
                        style={"color": "#0d6efd"},
                    ),
                    # 篩選
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label("類別", style={"fontWeight": "bold"}),
                                                    dcc.Dropdown(
                                                        id="category-dropdown",
                                                        options=[{"label": "全部", "value": "全部"}] + category_options,
                                                        value="全部",
                                                        clearable=False,
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label("縣市", style={"fontWeight": "bold"}),
                                                    dcc.Dropdown(
                                                        id="city-dropdown",
                                                        options=[{"label": "全部", "value": "全部"}] + city_options,
                                                        value="全部",
                                                        clearable=False,
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        className="shadow-sm mb-4",
                        style={"borderRadius": "12px"},
                    ),
                    # 旅遊清單
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5("📋 旅遊清單", style={"color": "#0d6efd"}),
                                    dash_table.DataTable(
                                        id="travel-table",
                                        columns=[
                                            {"name": "名稱", "id": "Name"},
                                            {"name": "地址", "id": "Add"},
                                            {"name": "電話", "id": "Tel"},
                                            {"name": "類別", "id": "Category", "hidden": True},
                                        ],
                                        data=travel_df.to_dict("records"),
                                        row_selectable="multi",
                                        page_size=10,
                                        style_table={"borderRadius": "10px", "overflow": "hidden"},
                                        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                                        style_cell={"backgroundColor": "#fff", "color": "#000", "textAlign": "left", "padding": "8px"},
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Button(
                                                    "加入願望清單",
                                                    id="add-to-wishlist",
                                                    n_clicks=0,
                                                    className="btn btn-primary mt-3 w-100",
                                                ),
                                                width=6,
                                            ),
                                            dbc.Col(
                                                html.Button(
                                                    "🆕新增空白列",
                                                    id="add-empty-row",
                                                    n_clicks=0,
                                                    className="btn btn-outline-secondary mt-3 w-100",
                                                ),
                                                width=6,
                                            ),
                                        ],
                                        className="mt-2",
                                    ),
                                ]
                            )
                        ],
                        className="shadow-sm mb-4",
                        style={"borderRadius": "12px"},
                    ),
                    # 願望清單
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5("📝 願望清單", style={"color": "#0d6efd"}),
                                    dash_table.DataTable(
                                        id="wishlist-table",
                                        columns=[
                                            {"name": "名稱", "id": "name", "editable": True},
                                            {"name": "類型", "id": "type", "editable": True},
                                            {"name": "價格", "id": "price", "type": "numeric", "editable": True},
                                        ],
                                        data=[],
                                        row_deletable=True,
                                        editable=True,
                                        style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                                        style_cell={"backgroundColor": "#fff", "color": "#000", "padding": "8px"},
                                    ),
                                ]
                            )
                        ],
                        className="shadow-sm mb-4",
                        style={"borderRadius": "12px"},
                    ),
                    # 預算設定
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5("💰 預算設定", style={"color": "#0d6efd"}),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("食預算"), dbc.Input(id="budget-food", type="number", value=0, min=0)]), width=3),
                                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("活預算"), dbc.Input(id="budget-clothing", type="number", value=0, min=0)]), width=3),
                                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("住預算"), dbc.Input(id="budget-housing", type="number", value=0, min=0)]), width=3),
                                            dbc.Col(dbc.InputGroup([dbc.InputGroupText("景預算"), dbc.Input(id="budget-transport", type="number", value=0, min=0)]), width=3),
                                        ]
                                    ),
                                    dcc.Graph(id="budget-pie"),
                                    html.Div(id="remaining-budget", style={"fontWeight": "bold", "fontSize": "18px", "marginTop": "10px"}),
                                ]
                            )
                        ],
                        className="shadow-sm",
                        style={"borderRadius": "12px"},
                    ),
                ]
            )
        ],
    )

    # ===== Callbacks =====
    @app.callback(
        Output("travel-table", "data"),
        [Input("category-dropdown", "value"), Input("city-dropdown", "value")],
    )
    def filter_travel_table(category, city):
        df = travel_df.copy()
        if category != "全部":
            df = df[df["Category"] == category]
        if city != "全部":
            df = df[df["City"] == city]
        return df[["Name", "Add", "Tel", "Category"]].to_dict("records")

    # 合併「加入願望清單」與「新增空白列」
    @app.callback(
        [Output("wishlist-table", "data"), Output("travel-table", "selected_rows")],
        [Input("add-to-wishlist", "n_clicks"), Input("add-empty-row", "n_clicks")],
        [State("travel-table", "selected_rows"), State("travel-table", "data"), State("wishlist-table", "data")],
    )
    def update_wishlist(add_clicks, empty_clicks, selected_rows, travel_data, wishlist_data):
        wishlist_data = wishlist_data or []
        triggered = ctx.triggered_id

        type_map = {"食物": "食", "住宿": "住", "景點": "景", "活動": "活"}

        # 新增空白列
        if triggered == "add-empty-row":
            wishlist_data.append({"name": "", "type": "", "price": 0})
            return wishlist_data, []

        #  加入願望清單
        if triggered == "add-to-wishlist" and selected_rows:
            names_in_wishlist = {item["name"] for item in wishlist_data}
            for idx in selected_rows:
                row = travel_data[idx]
                name = row["Name"]
                if name not in names_in_wishlist:
                    src_cat = row.get("Category", "")
                    wish_type = type_map.get(src_cat, "活")
                    wishlist_data.append({"name": name, "type": wish_type, "price": 0})
        return wishlist_data, []

    @app.callback(
        Output("budget-pie", "figure"),
        [Input("budget-food", "value"), Input("budget-clothing", "value"), Input("budget-housing", "value"), Input("budget-transport", "value")],
    )
    def update_pie(food, clothing, housing, transport):
        values = [food or 0, clothing or 0, housing or 0, transport or 0]
        labels = ["食", "活", "住", "景"]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
        fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#FFF", width=2)))
        fig.update_layout(title="各類型支出佔比", paper_bgcolor="#fff", plot_bgcolor="#fff", font_color="#000")
        return fig


    # 顯示「食 50000 - 32000 = 18000 元」，空白類型也列入總支出
    @app.callback(
        Output("remaining-budget", "children"),
        [
            Input("budget-food", "value"),
            Input("budget-clothing", "value"),
            Input("budget-housing", "value"),
            Input("budget-transport", "value"),
            Input("wishlist-table", "data"),
        ],
    )
    def update_remaining(food, clothing, housing, transport, wishlist_data):
        budget = {"食": food or 0, "活": clothing or 0, "住": housing or 0, "景": transport or 0}
        spent = {"食": 0, "活": 0, "住": 0, "景": 0}
        untyped_spent = 0  # 用來記錄空白類型的支出

        # 累加各類型支出，空白類型另記
        for item in wishlist_data or []:
            t = item.get("type", "")
            price = float(item.get("price", 0) or 0)
            if t in spent:
                spent[t] += price
            else:
                untyped_spent += price  # 沒分類的也要計入總支出

        # 計算剩餘金額
        remain = {k: budget[k] - spent[k] for k in budget}

        # 顏色提示
        def colorize(v): return "red" if v < 0 else "black"

        # 顯示每一類預算狀況
        rows = []
        for k in ["食", "活", "住", "景"]:
            rows.append(
                html.Div(
                    f"{k} {budget[k]:,.0f} - {spent[k]:,.0f} = {remain[k]:,.0f} 元",
                    style={"color": colorize(remain[k]), "marginBottom": "3px"},
                )
            )

        # 計算總體
        total_budget = sum(budget.values())
        total_spent = sum(spent.values()) + untyped_spent
        total_remaining = total_budget - total_spent

        rows.append(
            html.Div(
                f"💰 總剩餘預算：{total_budget:,.0f} - {total_spent:,.0f} = {total_remaining:,.0f} 元",
                style={"color": colorize(total_remaining), "fontWeight": "bold", "marginTop": "5px"},
            )
        )

        # 若有未分類支出，額外提示
        if untyped_spent > 0:
            rows.append(
                html.Div(
                    f"⚠️ 含未分類支出：{untyped_spent:,.0f} 元（無類型項目）",
                    style={"color": "#888", "fontSize": "14px", "marginTop": "2px"},
                )
            )

        return rows

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=80)
