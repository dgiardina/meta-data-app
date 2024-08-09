import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/')

layout = html.Div(
    [   
        dbc.Card([
        dbc.CardBody([
        dcc.Store(id = 'store-inst-mtn-bool'),
            dbc.Row([
                dbc.Col([            
                    dbc.Row(dbc.Button('Add Log', id='button-inst-mtn', color = 'danger'),),
                    html.Div([],id = 'warning-text-inst-mtn'),
                    ]),
                    dbc.Col([html.H4(' ')], width = 1),
                dbc.Col([
                    html.Div([],id = 'submit-text-mtn'),
                ]),  
            ]),
            dbc.Row([html.Div([],id = 'warning-text-inst-mtn'),]),
        ]),
        ]),
        dbc.Row([
        dbc.Col([html.Div([],id = 'div-inst-mtn')], width=12, lg=12),
        ])
    ]
)



