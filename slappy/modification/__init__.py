import dash_core_components as dcc
import dash_bootstrap_components as dbc
import json
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html


def read_modifcations(data, read, basecall_group):
    data['mod'] = read.has_modification(basecall_group)
    if data['mod']:
        data['mod_names'] = read.get_modification_names(basecall_group)
        data['mod_data'] = read.get_modification(basecall_group)


def create_modification_layout():
    return [
        html.Div([
            dbc.Container(id='modifcation_head'),
            dcc.Input(value='', type='hidden', id='mod_values'),
            dcc.Input(value='', type='hidden', id='mod_values_mok'),
            dbc.Button('Set Modification', id='activate_mod', style={'marginLeft': 30}),
        ], id='mod_container', hidden=True),
    ]


def insert_mods(data, mods):
    if mods and data['mod']:
        j = 4
        for mod in json.loads(mods):
            if mod[0]:
                mod_d = next(filter(lambda x: x[0] == mod[1], data['mod_names']))
                data['basecolors'][mod_d[1]] = data['colors'][j][0]
                j += 1
                val = int(int(mod[2]) * 2.55)
                seq = list(data['seq'])
                for i in range(len(seq)):
                    if data['mod_data'][mod_d[1]][i] >= val:
                        seq[i] = mod_d[1]
                data['seq'] = ''.join(seq)


def generate_modification_callbacks(app, fetch_read):
    @app.callback(
        [Output('modifcation_head', 'children'), Output('mod_container', 'hidden')],
        [Input('start_info', 'value')],
        [State('mod_values', 'value')],
    )
    def prepare_modifcations(j_value, active_mod):
        if j_value == '':
            raise PreventUpdate
        data = fetch_read(j_value)
        slider = []
        show = True
        if data['mod']:
            preset = {x[1]: (x[0], x[2]) for x in json.loads(active_mod)}
            show = False
            slider.append(dbc.Row([dbc.Col('Modification', xs=2), dbc.Col('Symbol', xs=1), dbc.Col('Base', xs=1),
                                   dbc.Col('Needed probability', xs=8)], id='head'))
            for mod in data['mod_names']:
                is_active = []
                slider_value = 50
                if mod[0] in preset:
                    if preset[mod[0]][0]:
                        is_active.append(mod[0])
                    slider_value = int(preset[mod[0]][1])
                
                mod_element = [dbc.Col(dcc.Checklist(options=[{'label': mod[0], 'value': mod[0]}], value=is_active), xs=2),
                               dbc.Col(mod[1], xs=1), dbc.Col(mod[2], xs=1), dbc.Col(
                        dcc.RangeSlider(
                            min=1,
                            max=100,
                            value=[slider_value],
                            updatemode='drag',
                            marks=dict([(10 * x, f'{10 * x}%') for x in range(11)])
                        ),
                        xs=8
                    )]
                slider.append(dbc.Row(mod_element, id=mod[0]))
        return [slider, show]
    
    app.clientside_callback(
        """
        function (click, childs) {
            arr = []
            document.querySelector('#modifcation_head').querySelectorAll('.row:not(#head)').forEach(
                function(e) {
                    handle = e.querySelector('.rc-slider-handle')
                    if (handle !== null) {
                        arr.push(
                            [e.querySelector('input').checked, e.id, handle.ariaValueNow]
                        )
                    }
                }
            );
            return JSON.stringify(arr);
        }
        """,
        Output('mod_values', 'value'),
        [Input('activate_mod', 'n_clicks'), Input('modifcation_head', 'children')],
        []
    )
