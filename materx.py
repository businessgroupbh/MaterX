import pandas as pd
import dash
from dash import dcc, html, Output, Input, State
import plotly.graph_objects as go

# Load and clean data
url = 'https://raw.githubusercontent.com/businessgroupbh/MaterX/refs/heads/main/materx.csv'
df = pd.read_csv(url)

numeric_cols = ['Elastic Modulus', 'Shear Modulus', 'Mass Density', 'Tensile Strength',
                'Compressive Strength', 'Yield Strength', 'Thermal Expansion Coefficient',
                'Thermal Conductivity', 'Specific Heat', 'Material Damping Ratio',
                'Minimum Temperature', 'Maximum Temperature', 'Electricity Conductivity', 'Price']

for col in numeric_cols:
    if df[col].dtype == 'object':
        df[col] = df[col].str.replace(',', '').str.replace('E', 'e')
    df[col] = pd.to_numeric(df[col], errors='coerce')

# App
app = dash.Dash(__name__)
app.title = "MaterX - Material Explorer"
server = app.server  # Expose Flask server for deployment RENDER

# Layout
app.layout = html.Div([
    html.H2("MaterX - Material Properties Explorer", style={'textAlign': 'center'}),
html.P("Developed by Voelabs", style={'textAlign': 'center', 'fontStyle': 'italic', 'marginTop': '-10px', 'color': '#555', 'fontSize': '14px',}),


    html.Div([
        
         html.Div([
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': c, 'value': c} for c in sorted(df['Category'].dropna().unique())],
                placeholder='Category',
                style={'width': '100%'}
            )
        ], style={'width': '10%', 'padding': '5px'}),
              

        html.Div([
            dcc.Dropdown(
            id='standard-filter',
            placeholder='Standard',
            value=None,  # Start unselected
            style={'width': '100%'}
        )

        ], style={'width': '10%', 'padding': '5px'}),

        html.Div([
            dcc.Dropdown(
                id='material-selector',
                options=[],
                value=[],
                multi=True,
                placeholder='Material',
                style={'width': '100%'}
            )
        ], style={'width': '30%', 'padding': '5px'}),

        html.Div([
            dcc.Dropdown(
                id='x-axis',
                options=[{'label': col, 'value': col} for col in numeric_cols],
                value=numeric_cols[0],
                clearable=False,
                style={'width': '100%'}
            )
        ], style={'width': '15%', 'padding': '5px'}),

        html.Div([
            dcc.Dropdown(
                id='y-axis',
                options=[{'label': col, 'value': col} for col in numeric_cols],
                value=numeric_cols[1],
                clearable=False,
                style={'width': '100%'}
            )
        ], style={'width': '15%', 'padding': '5px'}),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

    dcc.Graph(
    id='scatter-plot',
    style={
        'marginTop': '30px',
        'height': '75vh',  # Adjust as needed
        'width': '100%',
    },
    config={'responsive': True}
)
,
], style={
    'backgroundColor': '#fff',
    'padding': '30px',
    'height': '100vh',
    'width': '100vw',
    'fontFamily': 'Arial',
    'boxSizing': 'border-box',
    'overflow': 'hidden'
})


@app.callback(
    Output('standard-filter', 'options'),
    Output('standard-filter', 'value'),
    Input('category-filter', 'value'),
    State('standard-filter', 'value')
)
def update_standard_options(selected_category, current_standard):
    # Filter standards based on category
    filtered_df = df.copy()
    if selected_category:
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]

    available_standards = sorted(filtered_df['Standard'].dropna().unique())
    standard_options = [{'label': s, 'value': s} for s in available_standards]

    # Reset standard if it no longer applies
    new_standard = current_standard if current_standard in available_standards else None

    return standard_options, new_standard



# Material options: updated without clearing existing selection
@app.callback(
    Output('material-selector', 'options'),
    Input('standard-filter', 'value'),
    Input('category-filter', 'value'),
    State('material-selector', 'value'),
)
def update_material_options(standard, category, selected_materials):
    filtered_df = df.copy()
    if standard:
        filtered_df = filtered_df[filtered_df['Standard'] == standard]
    if category:
        filtered_df = filtered_df[filtered_df['Category'] == category]

    # Combine with previously selected materials (to preserve selection)
    available_materials = set(filtered_df['Material'].dropna())
    if selected_materials:
        available_materials.update(selected_materials)

    options = [{'label': m, 'value': m} for m in sorted(available_materials)]
    return options


# Update plot
@app.callback(
    Output('scatter-plot', 'figure'),
    Input('material-selector', 'value'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value'),
)
def update_graph(materials, x_axis, y_axis):
    if not materials:
        return go.Figure()

    filtered = df[df['Material'].isin(materials)]
    fig = go.Figure()

    for i, material in enumerate(materials):
        mat_data = filtered[filtered['Material'] == material]
        fig.add_trace(go.Scatter(
            x=mat_data[x_axis],
            y=mat_data[y_axis],
            mode='markers+text',
            marker=dict(
                size=15,
                opacity=0.7,  # Transparent dots
                line=dict(width=1, color='white')
            ),
            text=[material] * len(mat_data),
            textposition='top center',
            name=material,
            hovertemplate=f"{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<extra>{material}</extra>"
        ))

    fig.update_layout(
        template='plotly',  # 👈 This is the real seaborn template
        title=f"{y_axis} vs {x_axis}",
        xaxis_title=x_axis,
        yaxis_title=y_axis,
    )

    return fig


if __name__ == '__main__':
    app.run(debug=False)
