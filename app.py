import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from raceplotly.plots import barplot


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


pd.options.display.max_columns = None
pd.options.display.max_rows = None

df = pd.read_csv('macrodata.csv')
indicators = ["GDP, $", "Population, total", "GDP per capita, $", "GDP per capita, PPP (current international $)",
              "Adjusted net national income (current $)", "Adjusted net national income per capita (current $)",
              "Agriculture, forestry, and fishing, value added (% of GDP)",
              "Industry (incl construction), value added (% of GDP)", "Manufacturing, value added (% of GDP)",
              "Services, value added (% of GDP)", "National currency/USD ex-rate"]
countries = df['country'].unique()
years = df['year'].unique()

default_countries = ['Finland', 'Indonesia', 'United States of America', 'Russian Federation', 'Bulgaria']
default_indicator = 'Services, value added (% of GDP)'
default_years = [2010, 2019]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
server = app.server

country_dropdown = dcc.Dropdown(id='country-selector', multi=True,
                                value=default_countries,
                                options=[{'label': country, 'value': country} for country in countries],
                                placeholder='Select one ore more countries')

indicator_dropdown = dcc.Dropdown(id='indicator-selector', multi=False, value=default_indicator,
                                  options=[{'label': indicator, 'value': indicator} for indicator in indicators],
                                  placeholder='Select the indicator', clearable=False)

year_slider = dcc.RangeSlider(id='year-slider', min=2001, max=2019, step=1, value=default_years,
                              marks={str(year): str(year) for year in years})

macro_graph = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id='macro-graph', figure={},
                  config={
                      'staticPlot': False,  # True, False
                      'scrollZoom': True,  # True, False
                      'doubleClick': 'reset+autosize',  # 'reset', 'autosize' or 'reset+autosize', False
                      'showTips': True,  # True, False
                      'displayModeBar': True,  # True, False, 'hover'
                      'displaylogo': False
                  })
    ])
)

macro_pie = dbc.Card(
    dbc.CardBody([
        dcc.Graph(id='macro-pie', figure={},
                  config={
                      'displayModeBar': True,  # True, False, 'hover'
                      'displaylogo': False,
                  })
    ])
)

bar_chart_race = dbc.Card(
    dbc.CardBody([dcc.Graph(id='bar-chart-race', figure={})])
)

app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H1('Macro Data Dashboard', className='text-center text-primary'),
            width=12)
    ),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                        dbc.Row([
                            dbc.Col(country_dropdown, width=8),
                            dbc.Col(indicator_dropdown, width=4),
                        ]),
                        dbc.Row([dbc.Col(year_slider, width=12)])
                ])),
            width=12,
        )
    ]),
    dbc.Row([
        dbc.Col(macro_graph, width=6),
        dbc.Col(macro_pie, width=6)
    ]),
    dbc.Row([
        dbc.Col(bar_chart_race, width=12)
    ])

], fluid=True)


# Callback section: connecting the components
# ************************************************************************
# 5-macro-graph
@app.callback(
    Output(component_id='macro-graph', component_property='figure'),
    Input(component_id='country-selector', component_property='value'),
    Input(component_id='year-slider', component_property='value'),
    Input(component_id='indicator-selector', component_property='value'),
)
def update_macro_graph(countries, years, indicator):
    if not countries:
        return {}
    dff = df[df['country'].isin(countries)]
    dff = dff[(dff['year'] >= years[0]) & (dff['year'] <= years[1])]
    figure = px.line(data_frame=dff, x='year', y=indicator, color='country',
                     title=f'{indicator} in {" - ".join([str(year) for year in years])}',
                     # category_orders={'country': countries},
                     labels={
                         'year': 'Year',
                         'country': 'Country'

                     })
    figure.update_traces(mode='lines+markers', hovertemplate=None)
    figure.update_layout({'hovermode': 'x unified'})
    return figure


@app.callback(
    Output(component_id='macro-pie', component_property='figure'),
    Input(component_id='macro-graph', component_property='hoverData'),
    Input(component_id='macro-graph', component_property='clickData'),
    Input(component_id='macro-graph', component_property='selectedData'),
    Input(component_id='country-selector', component_property='value'),
    Input(component_id='year-slider', component_property='value'),
    Input(component_id='indicator-selector', component_property='value'),
)
def update_macro_pie(hov_data, clk_data, slctd_data, countries, years, indicator):
    if not countries:
        return {}
    dff2 = df[df['country'].isin(countries)]
    if slctd_data:
        first_year = slctd_data['points'][0]['x']
        last_year = slctd_data['points'][-1]['x']
        dff2 = dff2[(dff2['year'] >= first_year) & (dff2['year'] <= last_year)]
        dff2 = dff2.groupby(['country'], as_index=False)[[indicator]].mean()
        dff2 = dff2.sort_values(by=['country'])
        period = f'{first_year} - {last_year}'
    elif not hov_data:
        dff2 = dff2[(dff2['year'] >= years[0]) & (dff2['year'] <= years[1])]
        period = " - ".join([str(year) for year in years])
    else:
        hov_year = hov_data['points'][0]['x']
        period = hov_year
        dff2 = dff2[dff2.year == hov_year]
    figure2 = px.pie(data_frame=dff2, values=indicator, names='country',
                     title=f'{indicator} in {period}',
                     color='country'
                     )

    figure2.update_layout(legend=dict(orientation="h"))

    figure2.update_traces(hovertemplate=
                          "<b>%{label}</b> - %{percent} <br><br>" +
                          "Value: %{value:,.0f}<br>" +
                          "<extra></extra>",
                          sort=False)
    # figure2.update_layout(legend_traceorder="normal")
    return figure2


@app.callback(
    Output(component_id='bar-chart-race', component_property='figure'),
    Input(component_id='country-selector', component_property='value'),
    Input(component_id='year-slider', component_property='value'),
    Input(component_id='indicator-selector', component_property='value')
)
def update_bar_chart_race(countries, years, indicator):
    dff = df[df['country'].isin(countries)]
    dff = dff[(dff['year'] >= years[0]) & (dff['year'] <= years[1])]

    my_raceplot = barplot(dff, item_column='country', value_column=indicator, time_column='year',
                          top_entries=len(countries))

    fig = my_raceplot.plot(title=f'{indicator} per Country from {years[0]} to {years[1]}',
                           value_label=indicator, time_label='Year: ', frame_duration=800)

    fig.update_layout(plot_bgcolor=None, template='ggplot2',
                      autosize=False, height=500)
    fig.update_xaxes(automargin=True)

    fig.update_traces(hovertemplate=
                      "<b>%{y}</b> - %{x:.4s}" +
                      "<extra></extra>")

    return fig


if __name__ == '__main__':
    app.run_server()
