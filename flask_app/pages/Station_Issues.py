import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/station-issue')


layout = html.Div(
    [   
        dbc.Card([
        dbc.CardBody([
        dcc.Dropdown(id="dropdown-sta-iss", multi = True),
        html.Br(),
        dcc.Store(id = 'store-sta-iss-bool'),
            dbc.Row([
                dbc.Col([            
                    dbc.Row(dbc.Button('Add Log', id='button-sta-iss', color = 'danger'),),
                    ]),
                    dbc.Col([html.H4(' ')], width = 1),
                dbc.Col([
                    html.Div([],id = 'submit-text-sta-iss'),
                ]),  
            ]),
            dbc.Row([html.Div([],id = 'warning-text-sta-iss'),]),
        ]),
        ]),
        dbc.Row([
        dbc.Col([html.Div([],id = 'div-sta-iss')], width=12, lg=12),
        ])
    ]
)



