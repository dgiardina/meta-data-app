import gspread
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_auth

import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np
from datetime import datetime, timedelta, date
import datetime as dt
import json
from io import StringIO
import re
from flask import Flask
import os
from dotenv import load_dotenv
import ast

load_dotenv()
GC_JSON = os.getenv('GC_JSON')
USER_PWD = os.getenv('USER_PWD')
gc = gspread.service_account_from_dict(ast.literal_eval(GC_JSON))

def sheet_to_df(sheet):
    try:
        sh = gc.open(sheet)
        worksheet = sh.get_worksheet(0)
        df = pd.DataFrame(worksheet.get_all_records())
        return df
    except:
        return None
    
def meta_sheet_to_df():
    try:
        sh = gc.open('metadata-defs')
        worksheet = sh.get_worksheet(0)
        df = pd.DataFrame(worksheet.get_all_records())
        df.to_csv('defs/log-defs.csv', index=False)
        # print('a')
        
        worksheet = sh.get_worksheet(1)
        df = pd.DataFrame(worksheet.get_all_records())
        df.to_csv('defs/instrument-defs.csv', index=False)
        # print('b')

        worksheet = sh.get_worksheet(2)
        df = pd.DataFrame(worksheet.get_all_records())
        df.to_csv('defs/project-techs.csv', index=False)
        # print('c')
        worksheet = sh.get_worksheet(4)
        df = pd.DataFrame(worksheet.get_all_records())
        df.to_csv('defs/station-list.csv', index=False)
        # print('d')
    except:
        print('newp')


def gen_inst_df(df):
    # generate df and df_old
    # df: will provide list of all instruments for app
    # df_old: keeps record for future concat
    # df_map: detailed instrumnet names and regex verification for instrument metadata format
    df_map = pd.read_csv('defs/instrument-defs.csv')
    
    if df_map is None:
        # create empty df with standard formatting
        df = pd.DataFrame(columns = [
            'report_at', 'report', 'tech', 'site_name', 'site_id', 'inst_id',
            'inst_mdl', 'inst_sn', 'inst_coef', 'inst_ht', 'inst_pos', 'log',
            'log_desc', 'log_start', 'log_end', 'log_description', 'inst_name'
        ],index = [0])
        df_old = df.copy()
        return [df, df_old]    
    elif df is None:
        # create empty df with standard formatting
        df = pd.DataFrame(columns = [
            'report_at', 'report', 'tech', 'site_name', 'site_id', 'inst_id',
            'inst_mdl', 'inst_sn', 'inst_coef', 'inst_ht', 'inst_pos', 'log',
            'log_desc', 'log_start', 'log_end', 'log_description', 'inst_name'
        ],index = [0])
        df_old = df.copy()
        return [df, df_old]
    elif df.empty:
        df = pd.DataFrame(columns = [
            'report_at', 'report', 'tech', 'site_name', 'site_id', 'inst_id',
            'inst_mdl', 'inst_sn', 'inst_coef', 'inst_ht', 'inst_pos', 'log',
            'log_desc', 'log_start', 'log_end', 'log_description', 'inst_name'
        ],index = [0])
        df_old = df.copy()
        return [df, df_old]
    else:
        # get the latest meta data from the station
        # strip instrument number to avoid hardcoding df_map
        # get instrument number and apply number to labels
        df_old = df.copy()
        latest_report = df['report'].max() # get latest report
        df = df[df['log'] == 'metadata'].drop_duplicates(subset='inst_id', keep='last') # only keep last instance of metadata for each instrument
        df['report'] = latest_report + 1# populate report      
        
        df.index = range(len(df.index))
        # print(df)
        df_map_todict = df_map.set_index('inst_id') 
        # print(df_map_todict)
        map_dict = df_map_todict.to_dict('index')
        # print(map_dict)
        for i in range(len(df)):
            try:
                inst = df['inst_id'][i].rstrip('_1234567890')      
                inst_num = df['inst_id'][i]
                if inst in inst_num:
                    inst_num = inst_num.replace(inst,'')
                    inst_num = ' ' + inst_num.lstrip('_')
                    inst_num = inst_num.rstrip(' ')
                df.loc[df.index[i], 'inst_name'] = map_dict[inst]['inst_name'] + inst_num
            except: 
                df.loc[df.index[i], 'inst_name'] = df['inst_id'][i]

        df.replace('',None,inplace = True)
        return [df, df_old]

class instrument_mtn: 
# Build class for instrument mtn page
# Input metadata for each instrument 

    def __init__(self,report,inst_id,inst_mdl,inst_sn,inst_coef,inst_ht,inst_pos,inst_name):
        # Define metadata associated with each instrument
        self.report = str(report)
        self.inst   = str(inst_id)
        self.mdl    = str(inst_mdl)
        self.sn     = str(inst_sn)
        self.coef   = str(inst_coef)
        self.ht     = str(inst_ht)
        self.pos    = str(inst_pos)
        self.name   = str(inst_name)
        self.id = self.mdl+self.sn+'mtn' # id unique to each instrument

# Store formatting
# dash component function: <dcc_obi>_<log>_<desc>
# component id function: <dcc_obi>_<log>_<desc>id
# component id: <dcc_obi>-<log>-<desc>
  

    def store_inst_mtn_all_id(self):
        # store for all instruments
        id = 'store-inst-mtn-all'
        return id
    
    def store_inst_mtn_id(self):
        # store for single instrument
        id = {'type': 'store-inst-mtn', 'index': self.id}
        return id

    def checklist_inst_mtn_1_id(self):
        id = {'type': 'checklist-inst-mtn-1', 'index': self.id}
        return id
    
    def checklist_inst_mtn_2_id(self):
        id = {'type': 'checklist-inst-mtn-2', 'index': self.id}
        return id
    
    def checklist_inst_mtn_1(self):
        # generate checklist for instrument mtn for log defs table
        # checklist split between two functions for formatting
        try:
            
            df = pd.read_csv('defs/log-defs.csv')
            # df = log_defs()
            df = df[df['log'].str.contains('maintenance') == True] # get logs associate with mtn
            df= df[df['log_tags'].str.contains(self.inst.rstrip('_1234567890')) == True] 
            df = df.iloc[:len(df)//2]
            # checklist uses log_desc_name for label, log_desc for value
            checklist_inst_mtn = dcc.Checklist(options=[{'label' : html.Div(i, style={'font-size': 16, 'paddingLeft': "1rem"}), 'value' : j } for i,j in zip(df['log_desc_name'],df['log_desc'])],
                inline = False, labelStyle = {'display': 'flex'}, id= self.checklist_inst_mtn_1_id())
            return checklist_inst_mtn
        except:
            checklist_inst_mtn = html.Div(id= self.checklist_inst_mtn_1_id())
            return checklist_inst_mtn
    
    def checklist_inst_mtn_2(self):
        try:
            df = pd.read_csv('defs/log-defs.csv')
            # df = log_defs()
            df = df[df['log'].str.contains('maintenance') == True]
            df= df[df['log_tags'].str.contains(self.inst.rstrip('_1234567890')) == True]
            df = df.iloc[len(df)//2:]
            checklist_inst_mtn = dcc.Checklist(options=[{'label' : html.Div(i, style={'font-size': 16, 'paddingLeft': "1rem"}), 'value' : j } for i,j in zip(df['log_desc_name'],df['log_desc'])],
                inline = False, labelStyle = {'display': 'flex'}, id= self.checklist_inst_mtn_2_id())
            return checklist_inst_mtn
        except:
            checklist_inst_mtn = html.Div(id= self.checklist_inst_mtn_2_id())
            return checklist_inst_mtn
        
    def dt_inst_mtn_id(self):
        id = {'type': 'dt-start-sta-iss', 'index': self.id}
        return id
    
    def yn_inst_mtn_id(self):
        id = {'type': 'yn-inst-mtn', 'index': self.id}
        return id
    
    def hh_start_inst_mtn_id(self):
        id = {'type': 'hh-start-inst-mtn', 'index': self.id}
        return id
    
    def hh_end_inst_mtn_id(self):
        id = {'type': 'hh-end-inst-mtn', 'index': self.id}
        return id
    
    def mm_start_inst_mtn_id(self):
        id = {'type': 'mm-start-inst-mtn', 'index': self.id}
        return id
    
    def mm_end_inst_mtn_id(self):
        id = {'type': 'mm-end-inst-mtn', 'index': self.id}
        return id
    
    def sh_inst_mtn_data_id(self):
        id = {'type': 'sh-sta-inst-mtn', 'index': self.id}
        return id

    def input_inst_mtn_id(self):
        id = {'type': 'input-inst-mtn', 'index': self.id}
        return id

    def inst_mtn_card(self):
        card = dbc.Card([
            dcc.Store(data = json.dumps(self.report),   id = {'type':'store-report-mtn' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.inst)  ,   id = {'type':'store-inst_id-mtn' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.mdl)   ,   id = {'type':'store-mdl-mtn'  , 'index': self.id}),
            dcc.Store(data = json.dumps(self.sn)    ,   id = {'type':'store-sn-mtn'   , 'index': self.id}),
            dcc.Store(data = json.dumps(self.coef)  ,   id = {'type':'store-coef-mtn' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.ht)    ,   id = {'type':'store-ht-mtn'   , 'index': self.id}),
            dcc.Store(data = json.dumps(self.pos)   ,   id = {'type':'store-pos-mtn'  , 'index': self.id}),
            dcc.Store(data = json.dumps(self.name)  ,   id = {'type':'store-name-mtn' , 'index': self.id}),
            dcc.Store(id = self.store_inst_mtn_all_id()),
            dcc.Store(id = self.store_inst_mtn_id()),
            dbc.CardBody([

                dbc.Row([                 
                    html.Div([html.H6(self.name)]),
                ]),

                dbc.Row([
                    dbc.Col([
                        html.Div([html.Small('Model: ' + self.mdl.replace(',', ' / '))], 
                            id = {'type':'div-mdl-mtn' , 'index': self.id}),
                    ]),
                    dbc.Col([
                        html.Div([html.Small('SN: '    + self.sn.replace(',' , ' / '))], 
                            id = {'type':'div-sn-mtn' , 'index': self.id}),
                    ]),
                ]),
                dbc.Row((html.Hr(style={'borderWidth': ".2vh", "width": "100%", "borderColor": "#6666ff","borderStyle":"solid"})),),
                dbc.Row([
                    dbc.Col([self.checklist_inst_mtn_1()]),
                    dbc.Col([self.checklist_inst_mtn_2()]),
                ]),
                dbc.Row([dcc.RadioItems(['No Impact on Data','Data Affected'],'No Impact on Data',inline=True, labelStyle= {"width":"13rem"}, id = self.yn_inst_mtn_id())]),
                html.Div([
                dbc.Row([
                    dbc.Col([html.Label('Affected Date')],width = 5),
                    dbc.Col([html.Label('Affected Start Time')])
                ]),
                
                dbc.Row([
                    dbc.Col([
                    dcc.DatePickerSingle(
                        id=self.dt_inst_mtn_id(),
                        min_date_allowed=date(1950, 1, 1),
                        max_date_allowed= dt.date.today()+ timedelta(days=1),
                        initial_visible_month=dt.date.today(),
                        date=dt.date.today())
                    ],width = 5),
                    dbc.Col([dbc.Input(id=self.hh_start_inst_mtn_id(), type='number', min=0, max=23, step=1, value = datetime.today().hour, size="md",valid = False)],width = 3),
                    dbc.Col([html.H4(':')],width = 1),
                    dbc.Col([dbc.Input(id=self.mm_start_inst_mtn_id(), type='number', min=0, max=59, step=1, value = datetime.today().minute, size="md",valid = False)],width = 3),
                ]),
                dbc.Row([
                    dbc.Col([],width = 5),
                    dbc.Col([html.Label('Affected End Time')])
                ]),
                dbc.Row([
                    dbc.Col([],width = 5),
                    dbc.Col([dbc.Input(id=self.hh_end_inst_mtn_id(), type='number', min=0, max=23, step=1, value = datetime.today().hour, size="md",valid = False)],width = 3),
                    dbc.Col([html.H4(':')],width = 1),
                    dbc.Col([dbc.Input(id=self.mm_end_inst_mtn_id(), type='number', min=0, max=59, step=1, value = datetime.today().minute, size="md",valid = False)],width = 3),
                ]),
                ], id = self.sh_inst_mtn_data_id()),
                dbc.Row([html.Label('Notes:')]),
                dbc.Row([
                    dcc.Input(id=self.input_inst_mtn_id(), placeholder=""),
                ])
            ]),
        ])

        return card

class instrument_swap: 
# Build class for instrument swap page
# Input metadata for each instrument 

    def __init__(self,report,inst_id,inst_mdl,inst_sn,inst_coef,inst_ht,inst_pos,inst_name):
        self.report = str(report)
        self.inst   = str(inst_id)
        self.mdl    = str(inst_mdl)
        self.sn     = str(inst_sn)
        self.coef   = str(inst_coef)
        self.ht     = str(inst_ht)
        self.pos    = str(inst_pos)
        self.name   = str(inst_name)
        self.id = self.mdl+self.sn+'swap'

# Store formatting
# dash component function: <dcc_obi>_<log>_<desc>
# component id function: <dcc_obi>_<log>_<desc>id
# component id: <dcc_obi>-<log>-<desc>
  
    def store_inst_swap_all_id(self):
        # store for all instruments
        id = 'store-inst-swap-all'
        return id
    
    def store_inst_swap_id(self):
        # store for single instruments
        id = {'type': 'store-inst-swap', 'index': self.id}
        return id

    def dropdown_inst_swap_mdl(self):
        try:
            df = pd.read_csv('defs/instrument-defs.csv')
            df = df[df['inst_id'].str.contains('Station') == False]
            df = df[df['inst_id'].str.contains(self.inst.rstrip('_1234567890')) == True]
            dropdown = dcc.Dropdown(options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : i } for i in df['inst_mdl'].item().split(',')], 
                                    value = self.mdl, id=self.dropdown_inst_swap_mdl_id(), multi = False, optionHeight=50)
            return dropdown
        except:
            return dcc.Dropdown(value=None, id=self.dropdown_inst_swap_mdl_id(), multi = True, optionHeight=50)
    
    def dropdown_inst_swap_mdl_id(self):
        id = {'type': 'dropdown-inst-swap-mdl', 'index': self.id}
        return id
    
    def input_inst_swap_mdl_id(self):
        id = {'type': 'input-inst-swap-mdl', 'index': self.id}
        return id

    def input_inst_swap_sn_id(self):
        id = {'type': 'input-inst-swap-sn', 'index': self.id}
        return id
    
    def input_inst_swap_coef_sh_id(self):
        id = {'type': 'input-inst-swap-coef-sh', 'index': self.id}
        return id
    
    def input_inst_swap_coef_id(self):
        id = {'type': 'input-inst-swap-coef', 'index': self.id}
        return id
    
    def input_inst_swap_desc_id(self):
        id = {'type': 'input-inst-swap-desc', 'index': self.id}
        return id
    def inst_swap_card(self):
        card = dbc.Card([
        # card = html.Div([
            dcc.Store(data = json.dumps(self.report), id = {'type':'store-report-swap' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.inst), id = {'type':'store-inst_id-swap' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.mdl) , id = {'type':'store-mdl-swap'  , 'index': self.id}),
            dcc.Store(data = json.dumps(self.sn)  , id = {'type':'store-sn-swap'   , 'index': self.id}),
            dcc.Store(data = json.dumps(self.coef), id = {'type':'store-coef-swap' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.ht)  , id = {'type':'store-ht-swap'   , 'index': self.id}),
            dcc.Store(data = json.dumps(self.pos) , id = {'type':'store-pos-swap'  , 'index': self.id}),
            dcc.Store(data = json.dumps(self.name), id = {'type':'store-name-swap' , 'index': self.id}),

            dcc.Store(id = self.store_inst_swap_all_id()),
            dcc.Store(id = self.store_inst_swap_id()),

            dbc.CardBody([
                dbc.Row([                 
                    html.Div([html.H6(self.name)]),
                    ]),
                dbc.Row([
                    dbc.Col([
                    html.Div([html.Small('Model: ' + self.mdl.replace(',', ' / '))], 
                             id = {'type':'div-mdl-mtn' , 'index': self.id}),
                    ]),
                    dbc.Col([
                        html.Div([html.Small('SN: '    + self.sn.replace(',' , ' / '))], 
                                 id = {'type':'div-sn-mtn' , 'index': self.id}),
                    ]),
                ]),
                dbc.Row((html.Hr(style={'borderWidth': ".2vh", "width": "100%", "borderColor": "#6666ff","borderStyle":"solid"})),),
                dbc.Row([
                    dbc.Col([dbc.Label('New Model:')]),
                    dbc.Col([self.dropdown_inst_swap_mdl()]),
                    ]),
                
                dbc.Row([
                    dbc.Col([dbc.Label('New SN:')]),
                    dbc.Col([dcc.Input(id=self.input_inst_swap_sn_id(),value=self.sn)]),
                    ]),
                
                html.Div([
                    dbc.Row([
                    dbc.Col([dbc.Label('New Coef:'),]),
                    dbc.Col([dcc.Input(id=self.input_inst_swap_coef_id(),value=self.coef)]),
                    ]),  
                ], id = self.input_inst_swap_coef_sh_id()),
                dbc.Row([dbc.Label('Notes:')]),
                dbc.Row([dcc.Input(id = self.input_inst_swap_desc_id())])
            ]),
        ])
        return card

class station_issue: 
# Build class for instrument swap page
# Input metadata for each instrument 

    def __init__(self,report,inst_id,inst_mdl,inst_sn,inst_coef,inst_ht,inst_pos,inst_name):
        self.report = str(report)
        self.inst   = str(inst_id)
        self.mdl    = str(inst_mdl)
        self.sn     = str(inst_sn)
        self.coef   = str(inst_coef)
        self.ht     = str(inst_ht)
        self.pos    = str(inst_pos)
        self.name   = str(inst_name)
        self.id = self.mdl+self.sn+'iss'

# Store formatting
# dash component function: <dcc_obi>_<log>_<desc>
# component id function: <dcc_obi>_<log>_<desc>id
# component id: <dcc_obi>-<log>-<desc>
  
    def store_sta_iss_all_id(self):
        # store for all instruments
        id = 'store-sta-iss-all'
        return id
    
    def store_sta_iss_id(self):
        # store for single instruments
        id = {'type': 'store-sta-iss', 'index': self.id}
        return id
    
    def log_sta_iss_id(self):
        id = {'type': 'log-sta-iss', 'index': self.id}
        return id
    
    def yn_sta_iss_id(self):
        id = {'type': 'yn-sta-iss', 'index': self.id}
        return id

    def dropdown_sta_iss_log_id(self):
        id = {'type': 'dropdown-sta-iss-log', 'index': self.id}
        return id
    
    def dt_start_sta_iss_id(self):
        id = {'type': 'dt-start-sta-iss', 'index': self.id}
        return id
    
    def dt_end_sta_iss_id(self):
        id = {'type': 'dt-end-sta-iss', 'index': self.id}
        return id
    
    def hh_start_sta_iss_id(self):
        id = {'type': 'hh-start-sta-iss', 'index': self.id}
        return id
    
    def hh_end_sta_iss_id(self):
        id = {'type': 'hh-end-sta-iss', 'index': self.id}
        return id
    
    def mm_start_sta_iss_id(self):
        id = {'type': 'mm-start-sta-iss', 'index': self.id}
        return id
    
    def mm_end_sta_iss_id(self):
        id = {'type': 'mm-end-sta-iss', 'index': self.id}
        return id
    
    def sh_sta_iss_res_id(self):
        id = {'type': 'sh-sta-iss-res', 'index': self.id}
        return id
    
    def input_sta_iss_desc_id(self):
        id = {'type': 'input-sta-iss-desc', 'index': self.id}
        return id
    
    def sta_iss_card(self):
        card = dbc.Card([
        # card = html.Div([
            dcc.Store(data = json.dumps(self.report), id = {'type':'store-report-sta-iss' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.inst), id = {'type':'store-inst_id-sta-iss' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.mdl) , id = {'type':'store-mdl-sta-iss'  , 'index': self.id}),
            dcc.Store(data = json.dumps(self.sn)  , id = {'type':'store-sn-sta-iss'   , 'index': self.id}),
            dcc.Store(data = json.dumps(self.coef), id = {'type':'store-coef-sta-iss' , 'index': self.id}),
            dcc.Store(data = json.dumps(self.ht)  , id = {'type':'store-ht-sta-iss'   , 'index': self.id}),
            dcc.Store(data = json.dumps(self.pos) , id = {'type':'store-pos-sta-iss'  , 'index': self.id}),
            dcc.Store(data = json.dumps(self.name), id = {'type':'store-name-sta-iss' , 'index': self.id}),

            dcc.Store(id = self.store_sta_iss_all_id()),
            dcc.Store(id = self.store_sta_iss_id()),

            dbc.CardBody([
                dbc.Row([                 
                    html.Div([html.H6(self.name)]),
                    ]),
                dbc.Row([
                    dbc.Col([
                    html.Div([html.Small('Model: ' + self.mdl.replace(',', ' / '))], 
                             id = {'type':'div-mdl-mtn' , 'index': self.id}),
                    ]),
                    dbc.Col([
                        html.Div([html.Small('SN: '    + self.sn.replace(',' , ' / '))], 
                                 id = {'type':'div-sn-mtn' , 'index': self.id}),
                    ]),
                ]),
                dbc.Row((html.Hr(style={'borderWidth': ".2vh", "width": "100%", "borderColor": "#6666ff","borderStyle":"solid"})),),
                dbc.Row([dbc.Col([dbc.Label('Issue Type:')]),dbc.Col([dbc.Label('Issue Status:')])]),
                dbc.Row([
                    dbc.Col([dcc.RadioItems(options = [
                        {'label': 'Site Issue', 'value': 'site_iss'},
                        {'label': 'Instrument Issue', 'value': 'inst_iss'}], 
                        value = 'site_iss', inline=False,labelStyle={'display': 'block',},
                        id = self.log_sta_iss_id())]),
                    dbc.Col([dcc.RadioItems(options = [
                        {'label':'Issue Ongoing', 'value':'cont'},
                        {'label' : 'Issue Resolved', 'value': 'res'}], 
                        value = 'cont', inline=False,labelStyle={'display': 'block',},
                        id = self.yn_sta_iss_id())]),
                    ]),
                    html.Br(),
                dbc.Row([dbc.Label('Station Issue(s):')]),
                dbc.Row([dcc.Dropdown(id = self.dropdown_sta_iss_log_id(), multi = True)]),
                dbc.Row([
                    dbc.Col([html.Label('Issue Start Date')],width = 5),
                    dbc.Col([html.Label('Issue Start Time')])
                ]),
                dbc.Row([
                    dbc.Col([
                    dcc.DatePickerSingle(
                        id=self.dt_start_sta_iss_id(),
                        min_date_allowed=date(1950, 1, 1),
                        max_date_allowed= dt.date.today()+ timedelta(days=1),
                        initial_visible_month=dt.date.today(),
                        placeholder="Known",)
                    ],width = 5),
                    dbc.Col([dbc.Input(id=self.hh_start_sta_iss_id(), type='number', min=0, max=23, step=1, size="md",valid = False)],width = 3),
                    dbc.Col([html.H4(':')],width = 1),
                    dbc.Col([dbc.Input(id=self.mm_start_sta_iss_id(), type='number', min=0, max=59, step=1, size="md",valid = False)],width = 3),
                ]),
                html.Div([
                dbc.Row([
                    dbc.Col([html.Label('Issue Res. Date')],width = 5),
                    dbc.Col([html.Label('Issue Res. Time')])
                ]),
                dbc.Row([
                    dbc.Col([
                    dcc.DatePickerSingle(
                        id=self.dt_end_sta_iss_id(),
                        min_date_allowed=date(1950, 1, 1),
                        max_date_allowed= dt.date.today()+ timedelta(days=1),
                        initial_visible_month=dt.date.today(),
                        date=dt.date.today())
                    ],width = 5),
                    dbc.Col([dbc.Input(id=self.hh_end_sta_iss_id(), type='number', min=0, max=23, step=1, value = datetime.today().hour, size="md",valid = False)],width = 3),
                    dbc.Col([html.H4(':')],width = 1),
                    dbc.Col([dbc.Input(id=self.mm_end_sta_iss_id(), type='number', min=0, max=59, step=1, value = datetime.today().minute, size="md",valid = False)],width = 3),
                ]),
                ], id = self.sh_sta_iss_res_id()),
                dbc.Row([dbc.Label('Notes:')]),
                dbc.Row([dcc.Input(id = self.input_sta_iss_desc_id())])
            ]),
        ])
        return card

# Fetch stations on app startup to populate the dropdown
def dropdown_tech():
    try:
        df = pd.read_csv('defs/project-techs.csv')
        dropdown = dcc.Dropdown(id='dropdown-tech', 
            options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : j } for i,j in zip(df['tech'],df['tech'])],value = df['tech'][0],
        clearable=False,
        optionHeight=50)
        # dropdown = dcc.Dropdown(['NYC', 'MTL', 'SF'],id='dropdown-tech')
        return dropdown
    except:
        return dcc.Dropdown(value=None,id='dropdown-tech')

def dropdown_station():
    try:

        # stations = get_stations()
        
        # station_options = [{'label': station['site_id']+ ' ' + station['site_name'], 'value': station['site_id']+ '_' + station['site_name']} for station in stations]
        # df = pd.DataFrame(station_options)
        # df.sort_values(by='value',inplace=True)
        

        # dropdown = dcc.Dropdown(id='dropdown-stations', 
        #     options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : j } for i,j in zip(df['label'],df['value'])],value = df['value'].iloc[0],
        # clearable=False,
        # optionHeight=50)

        df = pd.read_csv('defs/station-list.csv')
        dropdown = dcc.Dropdown(id='dropdown-stations', 
            options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : j } for i,j in zip(df['label'],df['value'])],value = df['value'].iloc[0],
        clearable=False,
        optionHeight=50)
        
        return dropdown
    except: 
        
        return dcc.Dropdown(value=None,id='dropdown-stations')



# Intitialze empty classes for pattern matching callbacks
[df_init, df_init_old] = gen_inst_df(None)
a = (df_init.iloc[0].tolist())
inst_mtn = instrument_mtn(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16])   
inst_swap = instrument_swap(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16])  
sta_iss = station_issue(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16])  

header = dbc.Card([
    html.Div([
            dbc.Label("Tech:"),
            dropdown_tech(),
    ]),
    html.Div(
            [
            dbc.Label("Station:"),
            dcc.Store(id = 'store-all-log'),
            dropdown_station(),
            dcc.Store(id = 'init-store'),
            dcc.Store(id = 'init-store-df'),
            dcc.Store(id = 'init-store-df-old'),
                
            ]
        ),
    html.Div(
            [
            dbc.Row([
                dbc.Col([html.Label('Log Date')],width = 5),
                dbc.Col([html.Label('Log Time')])
            ]),
            dbc.Row([
                dbc.Col([
                dcc.DatePickerSingle(
                    id='dt-single-log',
                    min_date_allowed=date(1950, 1, 1),
                    max_date_allowed= dt.date.today()+ timedelta(days=1),
                    initial_visible_month=dt.date.today(),
                    date=dt.date.today())
                    
                ],width = 5),
                dbc.Col([dbc.Input(id='input-time-hh-log', type='number', min=0, max=23, step=1, value = datetime.today().hour, size="md",valid = False)],width = 3),
                dbc.Col([html.H4(':')],width = 1),
                dbc.Col([dbc.Input(id='input-time-mm-log', type='number', min=0, max=59, step=1, value = datetime.today().minute, size="md",valid = False)],width = 3),
                        
            ]),
            ]
        ),

    ],body=True,color="dark", outline=True)

server = Flask(__name__)
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP],suppress_callback_exceptions=True, use_pages=True,server=server)

auth = dash_auth.BasicAuth(
    app, ast.literal_eval(USER_PWD)
)

app.layout = dbc.Container([
    dbc.Stack([
        
        dbc.Col([header], width=12, lg=12),
            html.Div([
                dcc.Link(page['name']+"  |  ", href=page['path'])
                for page in dash.page_registry.values()
            ]),
        html.Hr(),
        dash.page_container
        ]),
    ])


#%% Preload callback
@app.callback(
    Output('init-store','data'),
    [Input('dropdown-stations', 'value')])

def gen_inst_mtn_cards(station): 
    meta_sheet_to_df()
    return station

@app.callback(
    Output('init-store-df','data'),
    [Input('dropdown-stations', 'value')])

def gen_inst_mtn_cards(station): 
    print(station)
    [df, df_old] = gen_inst_df(sheet_to_df(station))
    print(df)
    return df.to_json()


#%% Mtn Callbacks

@app.callback(
    Output('div-inst-mtn','children'),
    [Input('init-store-df', 'data')]
    )

def gen_inst_mtn_cards(station_data): 
    # Generate instrument mtn cards for instruments that require regular mtn tasks
    df = pd.read_json(StringIO(station_data))
    df_logs = pd.read_csv('defs/log-defs.csv')
    df_logs = df_logs[df_logs['log'].str.contains('maintenance') == True]
    list = df_logs['log_tags'].values.tolist()
    list = [x for xs in list for x in xs.split(',')]

    
    instrument_list = []
    for i in range(len(df)):
    # for index, row in df.iterrows():
        a = (df.iloc[i].tolist())
        if pd.isna(a[5]) is False: 
            if a[5].rstrip('_1234567890') in list:
                instrument_list.append(instrument_mtn(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16]))
            else:
                instrument_list = instrument_list
        else:
            instrument_list.append(inst_mtn)
        
        
    div = html.Div([
        dbc.Stack([
            dbc.Row([
                *[dbc.Col([instrument_list[i].inst_mtn_card()], width=12, lg=12)
                    for i in range(len(instrument_list))],
            ])
        ])
    ]),

    return div

@app.callback(
    Output({'type': 'div-mdl-mtn', 'index': MATCH}, 'style'),
    [Input(component_id = {'type': 'store-mdl-mtn', 'index': MATCH}, component_property = 'data')])

def show_hide_element(data):
    if any(x in data for x in ['None' , 'nan']):
        return {'display': 'none'}
    else:
        return {'display': 'block'}

@app.callback(
    Output({'type': 'div-sn-mtn', 'index': MATCH}, 'style'),
    [Input(component_id = {'type': 'store-sn-mtn', 'index': MATCH}, component_property = 'data')])

def show_hide_element(data):
    if any(x in data for x in ['None' , 'nan']):
        return {'display': 'none'}
    else:
        return {'display': 'block'}

@app.callback(
    Output(component_id={'type': inst_mtn.sh_inst_mtn_data_id()['type']   , 'index': MATCH}, component_property='style'),
    [Input(component_id={'type': inst_mtn.yn_inst_mtn_id()['type']   , 'index': MATCH}, component_property = 'value')])

def show_hide_element(value):
    if any(x in value for x in ['Data Affected']):
        return {'display': 'block'}
    elif value == None:
        return {'display': 'none'}
    else:
        return {'display': 'none'}


@app.callback(
    Output(component_id={'type': inst_mtn.store_inst_mtn_id()['type']    , 'index': MATCH}, component_property='data'),
    [Input(component_id={'type': inst_mtn.checklist_inst_mtn_1_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': inst_mtn.checklist_inst_mtn_2_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': inst_mtn.input_inst_mtn_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': 'store-report-mtn', 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-inst_id-mtn', 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-mdl-mtn' , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-sn-mtn'  , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-coef-mtn'  , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-ht-mtn'  , 'index': MATCH}, component_property='data')],
    [Input(component_id={'type': 'store-pos-mtn'  , 'index': MATCH}, component_property='data')],
    [Input(component_id={'type': inst_mtn.yn_inst_mtn_id()['type']   , 'index': MATCH}, component_property = 'value')],
    [Input(component_id={'type': inst_mtn.dt_inst_mtn_id()['type'], 'index': MATCH}, component_property='date')],
    [Input(component_id={'type': inst_mtn.hh_start_inst_mtn_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': inst_mtn.hh_end_inst_mtn_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': inst_mtn.mm_start_inst_mtn_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': inst_mtn.mm_end_inst_mtn_id()['type'], 'index': MATCH}, component_property='value')],
    )

def show_hide_element(log_desc_1, log_desc_2,log_description,report,inst,mdl,sn,coef,ht,pos,yn_data,log_dt,log_start_hh,log_end_hh,log_start_mm,log_end_mm):
    
    if log_desc_1 == None and log_desc_2 == None:
        d = {'report': [None], 'inst_id': [None],'inst_mdl': [None],'inst_sn': [None],'inst_coef': [None],'inst_ht': [None],'inst_pos': [None],'log':[None],'log_desc': [None],'log_start' : [None], 'log_end' : [None], 'log_description': [None]}
        df = pd.DataFrame(d, index=[0])
    else:
        
        if log_desc_1 is None:
            log_desc = ','.join(log_desc_2)
        elif log_desc_2 is None:
            log_desc = ','.join(log_desc_1)
        else:
            log_desc_1 = ','.join(log_desc_1)
            log_desc_2 = ','.join(log_desc_2)
            log_desc = log_desc_1 +','+log_desc_2


        if yn_data == 'Data Affected':
            if log_dt is None:
                log_start = None
            elif log_start_hh is None:
                log_start = None
            elif log_start_mm is None:
                log_start = None
            else:
                time_str = str(log_start_hh).zfill(2) +':' + str(log_start_mm).zfill(2) + ':00'
                log_start = log_dt+ ' ' + time_str
            

            if log_dt is None:
                log_end = None
            elif log_end_hh is None:
                log_end = None
            elif log_end_mm is None:
                log_end = None
            else:
                time_str = str(log_end_hh).zfill(2) +':' + str(log_end_mm).zfill(2) + ':00'
                log_end = log_dt+ ' ' + time_str
        else:
            log_start = None
            log_end = None


        # report = int(report.strip('""'))+1
        report = str(report)
        d = {'report': report, 'inst_id': inst,'inst_mdl': mdl,'inst_sn': sn, 'inst_coef': coef, 'inst_ht': ht,'inst_pos': pos, 'log': 'gen_mtn','log_desc': log_desc,'log_start' : log_start, 'log_end' : log_end, 'log_description': log_description}
        df = pd.DataFrame(data = d, index=[0])
        
        
    return df.to_json()

@app.callback(
    Output(component_id=inst_mtn.store_inst_mtn_all_id(), component_property='data'),
    [Input(component_id={'type': inst_mtn.store_inst_mtn_id()['type'], 'index': ALL}, component_property='data')],
    [Input(component_id='dt-single-log', component_property='date')],
    [Input(component_id='input-time-hh-log', component_property='value')],
    [Input(component_id='input-time-mm-log', component_property='value')],
    [Input(component_id='dropdown-stations', component_property='value')],
    [Input(component_id='dropdown-tech', component_property='value')],    
    )

def show_hide_element(log_desc,dt_single_log,hh_log,mm_log,sta,tech):
    if log_desc is None:
        raise PreventUpdate
    elif dt_single_log is None:
        raise PreventUpdate
    elif hh_log is None:
        raise PreventUpdate
    elif mm_log is None:
        raise PreventUpdate
    elif sta is None:
        raise PreventUpdate
    elif tech is None:
        raise PreventUpdate
    else:
        dt_time = str(hh_log).zfill(2) +':' + str(mm_log).zfill(2) + ':00'
        dt_single_log = dt_single_log + ' ' + dt_time
        df = pd.concat([pd.read_json(StringIO(row)) for row in log_desc],axis=0)
        
        df.replace('\"','', regex=True, inplace=True) 
        df = df.replace({np.nan: None})
        df = df.dropna(subset = ['inst_id'])
        df.index = range(len(df.index))
        
        if df.empty:
            return None
        else:
            df.insert(1,'site_id',sta[0:4])
            df.insert(1,'site_name',sta)
            df.insert(1,'tech',tech)
            df.insert(0,'report_at',dt_single_log)
            
            return df.to_json()

@app.callback(
    Output(component_id='store-inst-mtn-bool', component_property='data'),
    [Input(component_id=inst_mtn.store_inst_mtn_all_id(), component_property='data')],
    [Input(component_id='dt-single-log', component_property='date')],
    [Input(component_id='input-time-hh-log', component_property='value')],
    [Input(component_id='input-time-mm-log', component_property='value')],
    [Input(component_id='dropdown-tech', component_property='value')],    
    prevent_initial_call=True)

def show_hide_element(log_desc,dt_single_log,hh_log,mm_log,tech):
    d = {'bool': [0,0,0,0], 'Text': ['Log Empty','Log Date Empty', 'Log Time Empty','No Tech Selected']}
    df_bool = pd.DataFrame(data=d)
    if log_desc is None: 
        return dash.no_update
    else:
        df = pd.read_json(StringIO(log_desc))
        df = df.replace({np.nan: None})
        df.replace('\"','', regex=True, inplace=True) 
        if dt_single_log is None:
            df_bool['bool'][1] = 1
        if hh_log is None:
            df_bool['bool'][2] = 1
        if mm_log is None:
            df_bool['bool'][2] = 1

        if tech is None:
            df_bool['bool'][3] = 1

        return df_bool.to_json()



@app.callback(
    Output(component_id='button-inst-mtn', component_property='color'),
    [Input(component_id='store-inst-mtn-bool', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(data):
    df = pd.read_json(StringIO(data))
    if 1 in df['bool'].values:
        return 'danger'
    else: 
        return 'primary'

@app.callback(
    Output(component_id='warning-text-inst-mtn', component_property='children'),
    [Input(component_id='store-inst-mtn-bool', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(data):
    df = pd.read_json(StringIO(data))
    if 1 in df['bool'].values:
        text = df.loc[df['bool'] == 1, 'Text']
        a = ', '.join(text.to_list())
        return 'Errors: ' + a
    else: 
        return 'Log ready to submit!'


@app.callback(
    Output(component_id='submit-text-mtn', component_property='children'),
    [Input(component_id='button-inst-mtn', component_property='n_clicks')],
    [State(component_id=inst_mtn.store_inst_mtn_all_id(), component_property='data')],
    [State(component_id='dropdown-stations', component_property='value')],
    # [State(component_id='init-store-df-old', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(n_clicks, data_log, sta):
    df1 = pd.read_json(StringIO(data_log))
    
    [df, df2] = gen_inst_df(sheet_to_df(sta))
    
    df = pd.concat([df2,df1], axis = 0)
    df.replace('',None,inplace = True)
    df = df.replace({np.nan: None})
    df.fillna("",inplace=True)
    df['report_at'] = df['report_at'].astype(str)
    try:
        sh = gc.open(sta)
        worksheet = sh.get_worksheet(0)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return 'Submission Successful!'
    except:
        return 'Nope :('


#%% Swap Callbacks

@app.callback(
    Output('dropdown-inst-swap','options'),
    [Input('init-store-df', 'data')])

def show_hide_element(sta_data): 
    df = pd.read_json(StringIO(sta_data))
    df = df.iloc[1:]
    options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : j } for i,j in zip(df['inst_name'],df['inst_id'])]
    return options

@app.callback(
    Output('dropdown-inst-swap','value'),
    [Input('init-store-df', 'data')])

def show_hide_element(sta_data): 
    try:
        df = pd.read_json(StringIO(sta_data))
        
        df = df.iloc[1:]
        value = df['inst_id'].iloc[0]

        return value
    except:
        return None

@app.callback(
    Output('div-inst-swap','children'),
    [Input('init-store-df', 'data')],
    [Input('dropdown-inst-swap', 'value')],
    )

def show_hide_element(sta_data, inst_id): 
    df = pd.read_json(StringIO(sta_data))
    # print(df)
    # print(inst_id)
    try:
        if isinstance(inst_id, str):
            inst_id =[inst_id]
        if isinstance(inst_id, list):
            inst_id = inst_id
        instrument_list = []
        for i in range(len(inst_id)):
            
            df2 = df[df['inst_id'] == inst_id[i]].copy()
            a = df2.iloc[0].to_list()  

            instrument_list.append(instrument_swap(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16]))

        div = html.Div([
        dbc.Stack([
            dbc.Row([
                *[dbc.Col([instrument_list[i].inst_swap_card()], width=12, lg=12)
                    for i in range(len(instrument_list))],
                ])
            ])
        ]),   
        return div
    except:

        [df_init, asd] = gen_inst_df(None)
        a = (df_init.iloc[0].tolist())
        inst_swap = instrument_swap(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16])   

        div = inst_swap.inst_swap_card()
        return div
    
@app.callback(
    Output(component_id={'type': inst_swap.input_inst_swap_coef_sh_id()['type']   , 'index': MATCH}, component_property='style'),
    [Input(component_id={'type': 'store-coef-swap'  , 'index': MATCH}, component_property = 'data')])

def show_hide_element(value):
    if any(x in value for x in ['None' , 'nan']):
        return {'display': 'none'}
    elif value == None:
        return {'display': 'none'}
    elif 'None' in value:
        return {'display': 'none'}
    else:
        return {'display': 'block'}
    
@app.callback(
    Output(component_id={'type': inst_swap.store_inst_swap_id()['type']    , 'index': MATCH}, component_property='data'),
    [Input(component_id={'type': inst_swap.dropdown_inst_swap_mdl_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': inst_swap.input_inst_swap_sn_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': inst_swap.input_inst_swap_coef_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': 'store-report-swap', 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-inst_id-swap', 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-mdl-swap' , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-sn-swap'  , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-coef-swap'  , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-ht-swap'  , 'index': MATCH}, component_property='data')],
    [Input(component_id={'type': 'store-pos-swap'  , 'index': MATCH}, component_property='data')],
    [Input(component_id={'type':  inst_swap.input_inst_swap_desc_id()['type'] , 'index': MATCH}, component_property='data')],
    )

def show_hide_element(mdl_swap,sn_swap,coef_swap,report,inst,mdl,sn,coef,ht,pos,log_description):

    if mdl_swap == None:
        d = {'report': [None], 'inst_id': [None],'inst_mdl': [None],'inst_sn': [None],'inst_coef': [None],'inst_ht': [None],'inst_pos': [None],'log':[None],'log_desc': [None],'log_start' : [None], 'log_end' : [None], 'log_description': [None]}
        df = pd.DataFrame(d, index=[0])
    else:
        if 'None' in coef_swap:
            log_desc = mdl_swap + '/' + sn_swap 
        else:
            log_desc = mdl_swap + '/' + sn_swap +'/'+coef_swap
        # report = int(report.strip('""'))+1
        report = str(report)
        d = {'report': report, 'inst_id': inst,'inst_mdl': mdl,'inst_sn': sn, 'inst_coef': coef, 'inst_ht': ht,'inst_pos': pos, 'log': 'inst_swap','log_desc': log_desc,'log_start' : [None], 'log_end' : [None], 'log_description': log_description}
        df = pd.DataFrame(data = d, index=[0])

    return df.to_json()


@app.callback(
    Output(component_id=inst_swap.store_inst_swap_all_id(), component_property='data'),
    [Input(component_id={'type': inst_swap.store_inst_swap_id()['type'], 'index': ALL}, component_property='data')],
    [Input(component_id='dt-single-log', component_property='date')],
    [Input(component_id='input-time-hh-log', component_property='value')],
    [Input(component_id='input-time-mm-log', component_property='value')],
    [Input(component_id='dropdown-stations', component_property='value')],
    [Input(component_id='dropdown-tech', component_property='value')],    
    )

def show_hide_element(inst_swap,dt_single_log,hh_log,mm_log,sta,tech):
    
    if inst_swap is None:
        raise PreventUpdate
    elif dt_single_log is None:
        raise PreventUpdate
    elif hh_log is None:
        raise PreventUpdate
    elif mm_log is None:
        raise PreventUpdate
    elif sta is None:
        raise PreventUpdate
    elif tech is None:
        raise PreventUpdate
    else:
        
        dt_time = str(hh_log).zfill(2) +':' + str(mm_log).zfill(2) + ':00'
        dt_single_log = dt_single_log + ' ' + dt_time
        df = pd.concat([pd.read_json(StringIO(row)) for row in inst_swap],axis=0)
        df.replace('\"','', regex=True, inplace=True) 
        df = df.replace({np.nan: None})
        df = df.dropna(subset = ['inst_id'])
        df.index = range(len(df.index))
        
        if df.empty:
            return None
        else:
            df.insert(1,'site_id',sta[0:4])
            df.insert(1,'site_name',sta)
            df.insert(1,'tech',tech)
            
            df.insert(0,'report_at',dt_single_log)
            
            return df.to_json()

@app.callback(
    Output(component_id='store-inst-swap-bool', component_property='data'),
    [Input(component_id=inst_swap.store_inst_swap_all_id(), component_property='data')],
    [Input(component_id='dt-single-log', component_property='date')],
    [Input(component_id='input-time-hh-log', component_property='value')],
    [Input(component_id='input-time-mm-log', component_property='value')],
    [Input(component_id='dropdown-tech', component_property='value')],    
    prevent_initial_call=True)

def show_hide_element(inst_log,dt_single_log,hh_log,mm_log,tech):
    
    d = {'bool': [0,0,0,0,0,0], 'Text': ['Log Empty','Log Date Empty', 'Log Time Empty','No Tech Selected','Incorrect SN/Coef','Same SN as Outgoing Sensor']}
    df_bool = pd.DataFrame(data=d)

    if inst_log is None: 
        return dash.no_update
    else:
        df = pd.read_json(StringIO(inst_log))
        
        df = df.replace({np.nan: None})
        df.replace('\"','', regex=True, inplace=True) 
        if dt_single_log is None:
            df_bool['bool'][1] = 1
        if hh_log is None:
            df_bool['bool'][2] = 1
        if mm_log is None:
            df_bool['bool'][2] = 1

        if tech is None:
            df_bool['bool'][3] = 1

        df_reg = pd.read_csv('defs/instrument-defs.csv')
    
        a = 0
        for i in range(len(df.index)):
            df_reg2 = df_reg[df_reg['inst_mdl'].str.contains(df['log_desc'].str.split(pat="/")[i][0]) == True]
            pattern_inst = r'{}'.format(df_reg2['inst_verification'].iloc[0])
            match = re.search(pattern_inst,df['log_desc'][i])
            if match:
                a = a
            else:
                a = a + 1
            if a > 0:
                df_bool['bool'][4] = 1
        b = 0
        for i in range(len(df.index)):
            if df['log_desc'].str.split(pat="/")[i][0] == df['inst_mdl'][0] and str(df['log_desc'].str.split(pat="/")[i][1]) == str(df['inst_sn'][0]):
                b = b +1
                
            else:
                b = b
            if b > 0:
                df_bool['bool'][5] = 1
        return df_bool.to_json()

@app.callback(
    Output(component_id='button-inst-swap', component_property='color'),
    [Input(component_id='store-inst-swap-bool', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(data):
    df = pd.read_json(StringIO(data))
    if 1 in df['bool'].values:
        return 'danger'
    else: 
        return 'primary'

@app.callback(
    Output(component_id='warning-text-inst-swap', component_property='children'),
    [Input(component_id='store-inst-swap-bool', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(data):
    df = pd.read_json(StringIO(data))
    if 1 in df['bool'].values:
        text = df.loc[df['bool'] == 1, 'Text']
        a = ', '.join(text.to_list())
        return 'Errors: ' + a
    else: 
        return 'Log ready to submit!'



@app.callback(
    Output(component_id='submit-text-swap', component_property='children'),
    [Input(component_id='button-inst-swap', component_property='n_clicks')],
    [State(component_id=inst_swap.store_inst_swap_all_id(), component_property='data')],
    [State(component_id='dropdown-stations', component_property='value')],
    # [State(component_id='init-store-df', component_property='data')],
    # [State(component_id='init-store-df-old', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(n_clicks, data_log, sta):
    df1 = pd.read_json(StringIO(data_log))
    # df_new = pd.read_json(StringIO(sta_data))
    [df_new, df2] = gen_inst_df(sheet_to_df(sta))
    # df2 = pd.read_json(StringIO(sta_data_old))
    df_new['tech'] = df1['tech'][0]
    df_new['report_at'] = df1['report_at'][0]
    df_new['report'] = df1['report'][0]
    cond_agg = pd.Series([False] * len(df_new.index))
    for i in range(len(df1.index)):
        # print(df_new)
        cond = df_new['inst_id'] == df1['inst_id'][i]
        cond_agg = cond_agg | cond

        df_new.loc[cond, 'log_start'] = df_new['report_at'][0]
        df_new.loc[cond, 'inst_mdl'] = df1['log_desc'].str.split(pat="/")[i][0]
        df_new.loc[cond, 'inst_sn'] = df1['log_desc'].str.split(pat="/")[i][1]
        if len(df1['log_desc'].str.split(pat="/")[i]) == 3:
            df_new.loc[cond, 'inst_coef'] = df1['log_desc'].str.split(pat="/")[i][2]

    df_new.drop(['inst_name'],axis = 1, inplace = True)
    df_new = df_new.loc[cond_agg]
    # print(df_new)
    
    df = pd.concat([df2,df1,df_new], axis = 0)
    # df = pd.concat([df1,df_new], axis = 0)
    df.replace('',None,inplace = True)
    df = df.replace({np.nan: None})
    
    df['report_at'] = df['report_at'].astype(str)
    df['log_start'] = df['log_start'].astype(str)
    df['log_end'] = df['log_end'].astype(str)

    try:
        sh = gc.open(sta)
        worksheet = sh.get_worksheet(0)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return 'Submission Successful!'
    except:
        return 'Nope :('


#%% Site Issue Callbacks

@app.callback(
    Output('dropdown-sta-iss','options'),
    [Input('init-store-df','data')])

def show_hide_element(sta_data): 
    df = pd.read_json(StringIO(sta_data))
    df = df.iloc[1:]
    options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : j } for i,j in zip(df['inst_name'],df['inst_id'])]
    return options

@app.callback(
    Output('dropdown-sta-iss','value'),
    [Input('init-store-df','data')])

def show_hide_element(sta_data): 
    try:
        df = pd.read_json(StringIO(sta_data))
        df = df.iloc[1:]
        value = df['inst_id'].iloc[0]
        return value
    except:
        return None

@app.callback(
    Output('div-sta-iss','children'),
    [Input('init-store-df','data')],
    [Input('dropdown-sta-iss', 'value')],
    )

def show_hide_element(sta_data, inst_id): 
    df = pd.read_json(StringIO(sta_data))
    
    try:
        if isinstance(inst_id, str):
            inst_id =[inst_id]
        if isinstance(inst_id, list):
            inst_id = inst_id
        instrument_list = []
        for i in range(len(inst_id)):
            
            df2 = df[df['inst_id'] == inst_id[i]].copy()
            a = df2.iloc[0].to_list()  
            
       
            instrument_list.append(station_issue(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16]))

        div = html.Div([
        dbc.Stack([
            dbc.Row([
                *[dbc.Col([instrument_list[i].sta_iss_card()], width=12, lg=12)
                    for i in range(len(instrument_list))],
                ])
            ])
        ]),   
        return div
    except:

        [df_init, asd] = gen_inst_df(None)
        a = (df_init.iloc[0].tolist())
        sta_iss = station_issue(a[1], a[5], a[6], a[7], a[8], a[9], a[10], a[16])   

        div = sta_iss.sta_iss_card()
        return div

@app.callback(
    Output(component_id={'type': sta_iss.dropdown_sta_iss_log_id()['type']    , 'index': MATCH}, component_property='options'),
    [Input(component_id={'type': sta_iss.log_sta_iss_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': 'store-inst_id-sta-iss', 'index': MATCH}, component_property = 'data')],)


def show_hide_element(value,inst_id): 
    inst_id = inst_id.replace('"', '')
    
    df = pd.read_csv('defs/log-defs.csv')
    # df = log_defs()
    if 'site_iss' in value: 
        df = df[df['log'].str.contains('site_iss') == True]
        df= df[df['log_tags'].str.contains(inst_id.rstrip('_1234567890')) == True] 
        df.index = range(len(df.index))
        options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : j } for i,j in zip(df['log_desc_name'],df['log_desc'])]
        return options
    elif 'inst_iss' in value:
        df = df[df['log'].str.contains('inst_iss') == True]
        df= df[df['log_tags'].str.contains(inst_id.rstrip('_1234567890')) == True] 
        df.index = range(len(df.index))
        
        options=[{'label' : html.Div(i, style={'font-size': 15}), 'value' : j } for i,j in zip(df['log_desc_name'],df['log_desc'])]
        return options
    else:
        return None
   
@app.callback(
    Output(component_id={'type': sta_iss.sh_sta_iss_res_id()['type']   , 'index': MATCH}, component_property='style'),
    [Input(component_id={'type': sta_iss.yn_sta_iss_id()['type']   , 'index': MATCH}, component_property = 'value')])

def show_hide_element(value):
    if any(x in value for x in ['res']):
        return {'display': 'block'}
    elif value == None:
        return {'display': 'none'}
    else:
        return {'display': 'none'}
      
@app.callback(
    Output(component_id={'type': sta_iss.store_sta_iss_id()['type']    , 'index': MATCH}, component_property='data'),
    [Input(component_id={'type': sta_iss.log_sta_iss_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': sta_iss.yn_sta_iss_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': sta_iss.dropdown_sta_iss_log_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': sta_iss.dt_start_sta_iss_id()['type'], 'index': MATCH}, component_property='date')],
    [Input(component_id={'type': sta_iss.dt_end_sta_iss_id()['type'], 'index': MATCH}, component_property='date')],
    [Input(component_id={'type': sta_iss.hh_start_sta_iss_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': sta_iss.hh_end_sta_iss_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': sta_iss.mm_start_sta_iss_id()['type'], 'index': MATCH}, component_property='value')],
    [Input(component_id={'type': sta_iss.mm_end_sta_iss_id()['type'], 'index': MATCH}, component_property='value')],
    
    [Input(component_id={'type': 'store-report-sta-iss', 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-inst_id-sta-iss', 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-mdl-sta-iss' , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-sn-sta-iss'  , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-coef-sta-iss'  , 'index': MATCH}, component_property = 'data')],
    [Input(component_id={'type': 'store-ht-sta-iss'  , 'index': MATCH}, component_property='data')],
    [Input(component_id={'type': 'store-pos-sta-iss'  , 'index': MATCH}, component_property='data')],
    [Input(component_id={'type': sta_iss.input_sta_iss_desc_id()['type'] , 'index': MATCH}, component_property='value')],
    )

def show_hide_element(log_iss,log_yn,log_desc,log_start_dt,log_end_dt,log_start_hh,log_end_hh,log_start_mm,log_end_mm,report,inst,mdl,sn,coef,ht,pos,log_description):

    if log_desc is None:
        log_desc = log_desc
    else:
        log_desc = ','.join(log_desc)
    
    
    if log_start_dt is None:
        log_start = None
    elif log_start_hh is None:
        log_start = None
    elif log_start_mm is None:
        log_start = None
    else:
        time_str = str(log_start_hh).zfill(2) +':' + str(log_start_mm).zfill(2) + ':00'
        log_start = log_start_dt+ ' ' + time_str
    

    if log_end_dt is None:
        log_end = None
    elif log_end_hh is None:
        log_end = None
    elif log_end_mm is None:
        log_end = None
    else:
        time_str = str(log_end_hh).zfill(2) +':' + str(log_end_mm).zfill(2) + ':00'
        log_end = log_end_dt+ ' ' + time_str

    if log_iss is None:
        log = None
    elif log_yn is None:
        log = None
    else:
        log = log_iss + '_' + log_yn

    if log_desc is None:
        d = {'report': [None], 'inst_id': [None],'inst_mdl': [None],'inst_sn': [None],'inst_coef': [None],'inst_ht': [None],'inst_pos': [None],'log':[None],'log_desc': [None],'log_start' : [None], 'log_end' : [None], 'log_description': [None]}
        df = pd.DataFrame(d, index=[0])
        return df.to_json()
    
    else:
        if log_yn == 'cont':
            # report = int(report.strip('""'))+1
            report = str(report)
            d = {'report': report, 'inst_id': inst,'inst_mdl': mdl,'inst_sn': sn, 'inst_coef': coef, 'inst_ht': ht,'inst_pos': pos, 'log': log,'log_desc': log_desc,'log_start' : log_start, 'log_end' : [None], 'log_description': log_description}
            df = pd.DataFrame(data = d, index=[0])
            return df.to_json()
        elif log_yn == 'res':
            # report = int(report.strip('""'))+1
            report = str(report)
            d = {'report': report, 'inst_id': inst,'inst_mdl': mdl,'inst_sn': sn, 'inst_coef': coef, 'inst_ht': ht,'inst_pos': pos, 'log': log,'log_desc': log_desc,'log_start' : log_start, 'log_end' : log_end, 'log_description': log_description}
            df = pd.DataFrame(data = d, index=[0])
            return df.to_json()
        else:
            d = {'report': [None], 'inst_id': [None],'inst_mdl': [None],'inst_sn': [None],'inst_coef': [None],'inst_ht': [None],'inst_pos': [None],'log':[None],'log_desc': [None],'log_start' : [None], 'log_end' : [None], 'log_description': [None]}
            df = pd.DataFrame(d, index=[0])
            return df.to_json()
   

@app.callback(
    Output(component_id=sta_iss.store_sta_iss_all_id(), component_property='data'),
    [Input(component_id={'type': sta_iss.store_sta_iss_id()['type'], 'index': ALL}, component_property='data')],
    [Input(component_id='dt-single-log', component_property='date')],
    [Input(component_id='input-time-hh-log', component_property='value')],
    [Input(component_id='input-time-mm-log', component_property='value')],
    [Input(component_id='dropdown-stations', component_property='value')],
    [Input(component_id='dropdown-tech', component_property='value')],    
    )

def show_hide_element(sta_iss,dt_single_log,hh_log,mm_log,sta,tech):
    
    if sta_iss is None:
        raise PreventUpdate
    elif dt_single_log is None:
        raise PreventUpdate
    elif hh_log is None:
        raise PreventUpdate
    elif mm_log is None:
        raise PreventUpdate
    elif sta is None:
        raise PreventUpdate
    elif tech is None:
        raise PreventUpdate
    else:
        
        dt_time = str(hh_log).zfill(2) +':' + str(mm_log).zfill(2) + ':00'
        dt_single_log = dt_single_log + ' ' + dt_time
        df = pd.concat([pd.read_json(StringIO(row)) for row in sta_iss],axis=0)
        df.replace('\"','', regex=True, inplace=True) 
        df = df.replace({np.nan: None})
        df = df.dropna(subset = ['inst_id'])
        df.index = range(len(df.index))
        
        if df.empty:
            return None
        else:
            df.insert(1,'site_id',sta[0:4])
            df.insert(1,'site_name',sta)
            df.insert(1,'tech',tech)
            
            df.insert(0,'report_at',dt_single_log)
            # print(df)
            return df.to_json()
        
@app.callback(
    Output(component_id='store-sta-iss-bool', component_property='data'),
    [Input(component_id=sta_iss.store_sta_iss_all_id(), component_property='data')],
    [Input(component_id='dt-single-log', component_property='date')],
    [Input(component_id='input-time-hh-log', component_property='value')],
    [Input(component_id='input-time-mm-log', component_property='value')],
    [Input(component_id='dropdown-tech', component_property='value')],    
    prevent_initial_call=True)

def show_hide_element(inst_log,dt_single_log,hh_log,mm_log,tech):
    
    d = {'bool': [0,0,0,0,0,0,0], 'Text': ['Log Empty','Log Date Empty', 'Log Time Empty','No Tech Selected','No Issue Selected','Issue Start Date/Time Empty', 'Issue End Date/Time Empty']}
    df_bool = pd.DataFrame(data=d)

    if inst_log is None: 
        return dash.no_update
    else:
        df = pd.read_json(StringIO(inst_log))
        
        df = df.replace({np.nan: None})
        df.replace('\"','', regex=True, inplace=True) 
        if dt_single_log is None:
            df_bool['bool'][1] = 1
        if hh_log is None:
            df_bool['bool'][2] = 1
        if mm_log is None:
            df_bool['bool'][2] = 1

        if tech is None:
            df_bool['bool'][3] = 1

        if df['log_desc'].isna().any():
            df_bool['bool'][4] = 1

        if df['log_start'].isna().any():
            df_bool['bool'][5] = 1

        for index, row in df.iterrows():
            if row['log'][9:] == 'res' and pd.isna(row['log_end']):
                df_bool['bool'][6] = 1
        return df_bool.to_json()
    
@app.callback(
    Output(component_id='button-sta-iss', component_property='color'),
    [Input(component_id='store-sta-iss-bool', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(data):
    df = pd.read_json(StringIO(data))
    if 1 in df['bool'].values:
        return 'danger'
    else: 
        return 'primary'

@app.callback(
    Output(component_id='warning-text-sta-iss', component_property='children'),
    [Input(component_id='store-sta-iss-bool', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(data):
    df = pd.read_json(StringIO(data))
    if 1 in df['bool'].values:
        text = df.loc[df['bool'] == 1, 'Text']
        a = ', '.join(text.to_list())
        return 'Errors: ' + a
    else: 
        return 'Log ready to submit!'

@app.callback(
    Output(component_id='submit-text-sta-iss', component_property='children'),
    [Input(component_id='button-sta-iss', component_property='n_clicks')],
    [State(component_id=sta_iss.store_sta_iss_all_id(), component_property='data')],
    [State(component_id='dropdown-stations', component_property='value')],
    # [State(component_id='init-store-df-old', component_property='data')],
    prevent_initial_call=True)

def show_hide_element(n_clicks, data_log, sta):
    df1 = pd.read_json(StringIO(data_log))
    # df2 = pd.read_json(StringIO(sta_data)) 
    [df_new, df2] = gen_inst_df(sheet_to_df(sta))
    df = pd.concat([df2,df1], axis = 0)
    df.replace('',None,inplace = True)
    df = df.replace({np.nan: None})
    df.fillna("",inplace=True)
    df['report_at'] = df['report_at'].astype(str)
    
    try:
        sh = gc.open(sta)
        worksheet = sh.get_worksheet(0)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return 'Submission Successful!'
    except:
        return 'Nope :('

if __name__ == "__main__":
    app.run(debug=True)