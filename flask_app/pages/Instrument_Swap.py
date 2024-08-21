import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/instrument-swap')


layout = html.Div(
    [   
        dbc.Card([
        dbc.CardBody([
        dcc.Dropdown(id="dropdown-inst-swap", multi = True),
        html.Br(),
        dcc.Store(id = 'store-inst-swap-bool'),
        dbc.Row([
            dbc.Col([html.Div([],id = 'div-inst-swap')], width=12, lg=12),
        ]),
        dbc.Row([
            dbc.Col([            
                dbc.Row(dbc.Button('Add Log', id='button-inst-swap', color = 'danger'),),
                ]),
                dbc.Col([html.H4(' ')], width = 1),
            dbc.Col([
                html.Div([],id = 'submit-text-swap'),
            ]),  
        ]),
        dbc.Row([html.Div([],id = 'warning-text-inst-swap'),]),
        ]),
        ]),

    ]
)



