import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from slappy.fast5 import Fast5
from slappy.search import search
import dash_bootstrap_components as dbc
import visdcc
from os import scandir


def layout_menu():
    return [dbc.Container([
        dbc.Row(
            [
                dbc.Col(
                    dbc.Input(value='', type='text', id='path', list='list-suggested-inputs'),
                    xs=8,
                    md=9,
                ),
                dbc.Col(
                    [
                        dbc.Button('Open', id='open'),
                        dcc.Input(value='', type='hidden', id='hidden_path'),
                    ],
                    xs=3
                ),
            
            ],
            justify='end',
            no_gutters=True,
        ),
        dbc.Row(
            [
                dbc.Col(
                    DataTable(
                        id='reads',
                        columns=[{"name": 'Read', "id": 'name'}],
                        data=[],
                        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'textAlign': 'center'},
                        style_table={'overflowY': 'scroll', 'width': '100%'},
                        fixed_rows={'headers': True, },
                        style_cell={
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'maxWidth': 0,
                            'backgroundColor': 'grey',
                        },
                        filter_action="native",
                    ),
                )
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Select(
                        options=[{'label': '000', 'value': '000'}
                                 ],
                        id='basecalls',
                        value='000',
                    
                    )
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(html.I(className='fas fa-question-circle',
                               style={'color': 'green', 'fontSize': 'x-large'},
                               id="help"), width="auto", align='end'),
                dbc.Col(
                    dbc.Button("Search Sequence", id="open_search", ),
                    width='auto', align='end'
                )
            ],
            justify='between',
        ),
    ]),
        visdcc.Run_js(id='javascript'),
        html.Datalist([], id='list-suggested-inputs'),
        create_search_modal(),
    
    ]


def create_search_modal():
    return dbc.Modal(
        [
            
            dbc.ModalHeader(
                dbc.Row([
                    dbc.Col(html.I(className='fas fa-question-circle',
                                   style={'color': 'green', 'fontSize': 'large'},
                                   id="help_search"), width="auto", align='start'),
                    dbc.Col(dbc.Input(id="search_input", placeholder="Search a Sequence", type="text")),
                    dbc.Col(dbc.Button("Search", id="search", className="ml-auto"), width="auto")
                ], no_gutters=True), tag='div', style={'width': '100%'}),
            
            dbc.ModalBody(
                DataTable(
                    id='search_results',
                    columns=[{"name": 'Seq', "id": 'seq'}, {"name": 'From', "id": 'from'}, {"name": 'To', "id": 'to'}],
                    data=[],
                    style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'textAlign': 'center'},
                    style_table={'overflowY': 'scroll'},
                    fixed_rows={'headers': True, },
                    style_cell={
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'maxWidth': 0,
                        'backgroundColor': 'grey',
                    },
                    row_selectable='single'
                ),
                id='search_body'
            ),
            dbc.ModalFooter(
                dbc.Row([
                    dbc.Col(dbc.Button("Close", id="close_search", className="ml-auto"), xs=2),
                    
                    dbc.Col(dbc.Button("Apply", id="run_search", className="ml-auto"), xs=2),
                ], justify="between", style={'width': '100%'})
            ),
            *[create_search_popover(**d) for d in search_popovers]
        
        ],
        id="search_modal",
        size="lg",
        backdrop='static',
        scrollable=True,
    )


search_popovers = [
    {'content': 'Show/Hide Search Help',
     'target': 'help_search',
     'position': 'left'
     },
    {'content': ['The searched subsqeuence in ', html.A('one Letter IUPAC nucleotide code', target="_blank",
                                                        href='https://www.bioinformatics.org/sms/iupac.html')],
     'target': 'search_input',
     'position': 'bottom'
     },
    {'content': 'Start search',
     'target': 'search',
     'position': 'right'
     },
    {'content': 'The results of the search. Mark a line at the beginning.',
     'target': 'search_body',
     'position': 'left'
     },
    {'content': 'Close the search without applying the result (close help first)',
     'target': 'close_search',
     'position': 'bottom'
     },
    {'content': 'Close the search and apply the result (close help first)',
     'target': 'run_search',
     'position': 'bottom'
     },
]


def create_search_popover(content, target, position):
    return dbc.Popover(
        dbc.PopoverBody(content),
        id=f"{target}_popover", target=target, placement=position
    )


def create_javascipt(tab, select, read, basecall_group):
    if tab == 'tab-preview':
        f = read.get_reverse_raw_position(select['from'], basecall_group)
        t = read.get_reverse_raw_position(select['to'], basecall_group)
        return f'Plotly.relayout(document.getElementById("graph_preview"), {{"xaxis.range": [{f}, {t}]}})'
    elif tab == 'tab-raw':
        f = read.get_reverse_raw_position(select['from'], basecall_group)
        t = read.get_reverse_raw_position(select['to'], basecall_group)
        return f'Plotly.relayout(document.getElementById("graph_raw"), {{"xaxis.range": [{f}, {t}]}})'
    elif tab == 'tab-base':
        f = select['from'] - 1
        t = select['to'] - 1
        return f'Plotly.relayout(document.getElementById("graph_base"), {{"xaxis.range": [{f}, {t}]}})'
    elif tab == 'tab-prob':
        f = select['from'] - 1.5
        t = select['to'] - 1.5
        return f'Plotly.relayout(document.getElementById("graph_prob"), {{"xaxis.range": [{f}, {t}]}})'
    
    return '''
    
    '''


def menu_callbacks(app):
    @app.callback(
        Output(component_id='list-suggested-inputs', component_property='children'),
        [Input(component_id='path', component_property='value')]
    )
    def content_path(path):
        if path != '' and not path.endswith('/'):
            raise PreventUpdate
        ret = []
        try:
            for filepath in scandir(path if path != '' else '.'):
                if filepath.is_dir():
                    ret.append(html.Option(value=path + filepath.name + '/'))
                else:
                    if filepath.name.endswith('.fast5'):
                        ret.append(html.Option(value=path + filepath.name))
        except FileNotFoundError:
            raise PreventUpdate
        return ret
    
    @app.callback(
        [Output('reads', 'data'), Output('hidden_path', 'value'), Output('basecalls', 'options')],
        [Input('open', 'n_clicks')],
        [State('path', 'value')]
    )
    def prepare_file(_, path):
        if path == '':
            raise PreventUpdate
        fast5_file = Fast5(path)
        
        return [{'name': x[5:], 'id': x} for x in iter(fast5_file)], path, \
               [{'label': x[0], 'value': x[1]} for x in fast5_file.get_basecall_groups()]
    
    @app.callback(
        Output("search_modal", "is_open"),
        [Input("open_search", "n_clicks"), Input("close_search", "n_clicks")],
        [State("search_modal", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return False
    
    @app.callback(
        Output('search_results', 'data'),
        [Input("search", "n_clicks")],
        [State('search_input', 'value'), State('reads', 'active_cell'), State('basecalls', 'value'),
         State('hidden_path', 'value')],
    )
    def start_search(_, pattern, read_name_list, basecall_group, path):
        if path == '' or read_name_list is None:
            raise PreventUpdate
        read_name = read_name_list['row_id']
        fast5_file = Fast5(path)
        read = fast5_file[read_name]
        try:
            seq = read.get_rev_seq(basecall_group)
            return list(search(pattern, seq))
        
        except KeyError:
            raise PreventUpdate
    
    @app.callback(
        [Output('javascript', 'run'), Output("open_search", "n_clicks")],
        [Input("run_search", "n_clicks")],
        [State('search_results', 'data'), State('search_results', 'selected_rows'), State('reads', 'active_cell'),
         State('basecalls', 'value'),
         State('hidden_path', 'value'), State('tabs', 'value')],
    )
    def apply_search(_, data, ids, read_name_list, basecall_group, path, tab):
        if path == '' or read_name_list is None or ids is None:
            raise PreventUpdate
        read_name = read_name_list['row_id']
        fast5_file = Fast5(path)
        read = fast5_file[read_name]
        select = data[ids[0]]
        return create_javascipt(tab, select, read, basecall_group), 0
    
    @app.callback(
        [Output(f"{d['target']}_popover", "is_open") for d in search_popovers] +
        [Output('close_search', 'disabled'), Output('run_search', 'disabled'), ],
        [Input("help_search", "n_clicks")],
        [State("help_search_popover", "is_open")],
    )
    def toggle_popover(n, is_open):
        value = False
        if n:
            value = not is_open
        
        return [value] * (len(search_popovers) + 2)
