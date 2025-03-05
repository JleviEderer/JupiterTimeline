import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import logging

# Set up logging
logger = logging.getLogger('timeline_visualizer')

class TimelineVisualizer:
    def __init__(self):
        self.colors = {
            'Not Started': '#E3F2FD',  # Light blue
            'In Progress': '#64B5F6',  # Medium blue
            'Completed': '#1976D2'     # Dark blue
        }
        # Default team colors if not provided by data_manager
        self.team_colors = {
            'Procurement': '#0D47A1',    # Dark Blue
            'Construction': '#FFD700',   # Gold (was Development)
            'Development': '#9C27B0',    # Purple (was Interconnection)
            'Interconnection': '#00BCD4'  # Bright Turquoise (was Development)
        }

    def get_team_colors(self):
        """Return team colors for consistency"""
        return self.team_colors

    def parse_dates(self, df, date_col):
        """Centralized date parsing for better maintainability"""
        dates = pd.to_datetime(df[date_col], errors='coerce')

        # If any NaT values exist, try alternative formats
        if dates.isna().any():
            for format_str in ['%Y-%m-%d', '%b %d, %Y', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    temp_dates = pd.to_datetime(df[date_col], format=format_str, errors='coerce')
                    # Update only NaT values with successfully parsed dates
                    dates = dates.fillna(temp_dates)
                except:
                    pass

        return dates

    def create_timeline(self, data, custom_start_date=None, custom_end_date=None, 
                        show_task_labels=True, tick_interval=None):
        df_plot = data.copy()

        # Ensure required columns
        required_cols = ['Item Name', 'Start Date', 'End Date', 'Team', 'Months']
        if not all(col in df_plot.columns for col in required_cols):
            logger.error(f"DataFrame missing required columns: {required_cols}")
            st.error("Cannot create timeline due to missing data columns.")
            return go.Figure()

        # Prepare data with robust date parsing
        plot_data = df_plot.copy()
        try:
            # Use centralized date parsing function
            plot_data['Start'] = self.parse_dates(plot_data, 'Start Date')
            plot_data['Finish'] = self.parse_dates(plot_data, 'End Date')

            # If dates still have NaT, fill with reasonable defaults
            if plot_data['Start'].isnull().any() or plot_data['Finish'].isnull().any():
                # Log issues instead of displaying warnings
                num_issues = plot_data['Start'].isnull().sum() + plot_data['Finish'].isnull().sum()
                logger.warning(f"Timeline has {num_issues} date parsing issues that were auto-fixed")

                # Store min and max dates to avoid redundant calculations
                min_date_found = plot_data['Start'].min() if not pd.isna(plot_data['Start'].min()) else pd.Timestamp('now')
                max_date_found = plot_data['Finish'].max() if not pd.isna(plot_data['Finish'].max()) else min_date_found + pd.DateOffset(months=1)

                # Use the earliest date in the dataset or current date as fallback for start dates
                plot_data['Start'] = plot_data['Start'].fillna(min_date_found)
                # Use the latest date in the dataset or start + 1 month as fallback for end dates
                plot_data['Finish'] = plot_data['Finish'].fillna(max_date_found)
        except Exception as e:
            logger.error(f"Error parsing dates: {e}")
            st.error("Error creating timeline. Please check the data format.")
            return go.Figure()

        plot_data['Task'] = plot_data['Item Name'].str.replace('\n', ' ').str.strip()
        # Use Months from items.csv as Duration (in months), convert to days for plotting
        plot_data['Duration'] = plot_data['Months'] * 30

        # Cap extreme values but allow for a wide range
        plot_data['Duration'] = plot_data['Duration'].clip(lower=0, upper=10950)  # Cap at 30 years for validation
        plot_data['Months'] = plot_data['Months'].clip(lower=1, upper=360)  # Cap Months at 30 years (360 months)

        # Sort by start date
        plot_data = plot_data.sort_values('Start')

        if plot_data.empty:
            logger.warning("No valid tasks to display after parsing")
            return go.Figure()

        # Get team colors - try to access from session state first
        if hasattr(st.session_state, 'data_manager') and hasattr(st.session_state.data_manager, 'get_team_colors'):
            team_colors = st.session_state.data_manager.get_team_colors()
        else:
            team_colors = self.team_colors

        # Store global data range variables to avoid redundant calculations
        data_min_date = plot_data['Start'].min() 
        data_max_date = plot_data['Finish'].max()

        # Create task list and map tasks to their y-positions
        tasks = plot_data['Task'].drop_duplicates().tolist()
        task_positions = {task: i for i, task in enumerate(tasks)}  # Task name to y-position

        fig = go.Figure()

        # Collect all teams in the data
        all_data_teams = set(plot_data['Team'].unique())

        # Create a set to track teams that have been added to the legend
        teams_in_legend = set()

        # Add legend traces for teams
        for team_name, team_color in team_colors.items():
            if team_name not in teams_in_legend:
                # Create a dummy trace just for the legend, similar to the deadlines chart
                fig.add_trace(go.Scatter(
                    x=[None],  # Use None to make it invisible on chart
                    y=[None],  # Use None to make it invisible on chart
                    mode='markers',
                    marker=dict(color=team_color, size=10),
                    name=team_name,
                    showlegend=True,
                    hoverinfo='none',
                    legendgroup=team_name,
                    visible=True
                ))
                teams_in_legend.add(team_name)

        # Calculate months before displaying
        plot_data['Months'] = plot_data.apply(
            lambda x: max(1, ((pd.to_datetime(x['Finish']) - pd.to_datetime(x['Start'])).days // 30) + 1)
            if pd.notna(x['Start']) and pd.notna(x['Finish'])
            else 1,
            axis=1
        )


        # Determine the date range dynamically from the data or use custom dates
        if custom_start_date:
            min_date = pd.to_datetime(custom_start_date)
        else:
            min_date = data_min_date - pd.DateOffset(months=1)

        if custom_end_date:
            max_date = pd.to_datetime(custom_end_date)
        else:
            # Extend the end date by 6 months instead of just 1 month
            max_date = data_max_date + pd.DateOffset(months=6)

        # Separate tasks into short-duration (≤ 1 month) and long-duration (> 1 month)
        one_month = 30  # Approximate 1 month in days
        short_duration_tasks = plot_data[plot_data['Duration'].isnull() | (plot_data['Duration'] <= one_month)]
        long_duration_tasks = plot_data[plot_data['Duration'] > one_month]

        # Ensure long_duration_tasks has valid durations
        long_duration_tasks = long_duration_tasks[long_duration_tasks['Duration'].notnull()]

        # Add bars for long-duration tasks with fixed calculation of bar width
        for team in long_duration_tasks['Team'].unique():
            team_data = long_duration_tasks[long_duration_tasks['Team'] == team]
            if not team_data.empty:
                y_positions = [task_positions[task] for task in team_data['Task']]

                # Create lists for valid data
                valid_starts = []
                valid_durations = []  # This will hold time differences, not end dates
                valid_tasks = []
                valid_months = []
                valid_y_positions = []
                valid_end_dates = []  # For hover data

                # Process each task
                for start, finish, task, months, pos in zip(
                    team_data['Start'], team_data['Finish'], 
                    team_data['Task'], team_data['Months'], y_positions):

                    # Ensure valid timestamps
                    start_ts = pd.Timestamp(start) if not isinstance(start, pd.Timestamp) else start
                    finish_ts = pd.Timestamp(finish) if not isinstance(finish, pd.Timestamp) else finish

                    # Check if dates are valid (not NaT)
                    if pd.notna(start_ts) and pd.notna(finish_ts):
                        # For Plotly horizontal bars, we need the duration, not the end date
                        duration_ms = (finish_ts - start_ts).total_seconds() * 1000  # in milliseconds for Plotly

                        valid_starts.append(start_ts)
                        valid_durations.append(duration_ms)
                        valid_tasks.append(task)
                        valid_months.append(months)
                        valid_y_positions.append(pos)
                        valid_end_dates.append(finish_ts)

                # Create the horizontal bars with proper parameters
                if valid_starts and valid_durations:
                    # Enhanced hover template
                    hover_template = (
                        '<b>Task:</b> %{text}<br>' +
                        '<b>Start:</b> %{base|%Y-%m-%d}<br>' +
                        '<b>End:</b> %{customdata|%Y-%m-%d}<br>' +
                        '<b>Team:</b> ' + team + '<br>' +
                        '<b>Duration:</b> %{meta} months'
                    )

                    fig.add_trace(go.Bar(
                        x=valid_durations,  # Use duration, not end date
                        y=valid_y_positions,
                        base=valid_starts,  # Start position remains the same
                        orientation='h',
                        marker_color=team_colors.get(team, '#999999'),
                        name=team,
                        text=valid_tasks,
                        customdata=valid_end_dates,  # Store end dates for hover
                        meta=valid_months,  # Store months for hover template
                        hovertemplate=hover_template,
                        width=0.8,
                        showlegend=False,  # Don't show in legend since we're using invisible traces
                        legendgroup=team  # Group by team to ensure consistent coloring
                    ))

        # Add scatter points for short-duration tasks (≤ 1 month, 0, or NaN)
        # First build a mapping of task to team to ensure consistent coloring
        task_team_mapping = {}

        # Create mapping from all tasks to their teams - process both long and short duration tasks 
        for _, row in plot_data.iterrows():
            task_team_mapping[row['Task']] = row['Team']

        # Now handle short duration tasks - create individual points for each
        for _, row in short_duration_tasks.iterrows():
            task = row['Task']
            team = row['Team']
            # Make sure we have the correct team
            correct_team = team  # Use the team directly from the row

            # Get the position for this task
            y_pos = task_positions.get(task)

            # Skip if we can't determine position
            if y_pos is None:
                continue

            # Ensure start date is valid
            if pd.isna(row['Start']):
                continue

            start_ts = pd.Timestamp(row['Start']) if not isinstance(row['Start'], pd.Timestamp) else row['Start']
            finish_ts = pd.Timestamp(row['Finish']) if pd.notna(row['Finish']) else start_ts + pd.DateOffset(months=1)

            # Create custom data for hover
            custom_data = [finish_ts, row['Months'], correct_team]

            # Hover template
            hover_template = (
                '<b>Task:</b> %{text}<br>' +
                '<b>Start:</b> %{x|%Y-%m-%d}<br>' +
                '<b>End:</b> %{customdata[0]|%Y-%m-%d}<br>' +
                '<b>Team:</b> %{customdata[2]}<br>' +
                '<b>Duration:</b> %{customdata[1]} month(s)'
            )

            # Add individual point with correct team color
            # Set showlegend to True initially
            should_show_in_legend = True

            # Always use showlegend=False for scatter points to avoid duplicate legend entries
            # The invisible traces at the beginning handle the legend display

            fig.add_trace(go.Scatter(
                x=[start_ts],
                y=[y_pos],
                mode='markers',
                marker=dict(
                    symbol='circle',
                    size=15,
                    color=team_colors.get(correct_team, '#999999'),  # Get color directly for this team
                    line=dict(width=3, color='rgba(0,0,0,0.5)')
                ),
                name=correct_team,
                text=[task],
                customdata=[custom_data],
                hovertemplate=hover_template,
                showlegend=False,  # Don't show in legend to avoid duplicates
                legendgroup=correct_team  # Group with other elements from this team
            ))

        # Add a "Today" reference line - ALWAYS show it regardless of date range
        today = pd.Timestamp('today')

        # Always add the Today line, even if outside the current view
        fig.add_shape(
            type="line",
            x0=today,
            y0=-0.5,
            x1=today,
            y1=len(tasks) - 0.5,
            line=dict(color="red", width=2, dash="dash"),
        )
        # Add "Today" annotation above the chart, not overlapping the line
        fig.add_annotation(
            x=today,
            y=len(tasks) - 0.5,
            text="Today",
            showarrow=False,
            font=dict(color="red", size=12),
            textangle=0,        # Horizontal text
            yshift=25,          # Move text higher above the chart
            yanchor="bottom"    # Anchor at bottom of text
        )

        # Annotations for task labels (if enabled)
        annotations = []
        if show_task_labels:
            annotations = [
                dict(
                    x=-0.07,  # Adjusted from -0.05 for better alignment
                    y=i,
                    xref='paper',
                    yref='y',
                    text=task,  # Only include the task name, no numbers
                    showarrow=False,
                    font=dict(color='black', size=12),
                    align='right',
                    yanchor='middle'
                ) for i, task in enumerate(tasks)
            ]

        # Compute a default height based on number of tasks
        # This will be used if no custom height is provided via update_layout later
        task_count = len(tasks)
        if task_count <= 5:
            chart_height = 400  # Small number of tasks
        elif task_count <= 10:
            chart_height = 500  # Medium number of tasks
        else:
            # For larger number of tasks, use a more efficient spacing
            # but cap at 650px to avoid excessive scrolling
            chart_height = min(650, 300 + (task_count * 25))

        # Update layout with optimized height and margins for better screen fit
        fig.update_layout(
            height=chart_height,
            width=1200,  # Maintain width for better horizontal scaling
            margin=dict(l=200, r=30, t=50, b=50),  # Maintain left margin for task labels
            font=dict(family="Arial, sans-serif", size=12),
            showlegend=True,
            legend=dict(
                    title=None,  # Remove Teams title
                    orientation="h",
                    yanchor="top",
                    y=1.12,  # Match the deadlines chart position
                    xanchor="center",
                    x=0.5,
                    bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='rgba(0,0,0,0.2)',
                    borderwidth=1,
                    itemwidth=70,  # Match the deadlines chart
                    itemsizing='constant',
                    traceorder='normal',
                    font=dict(size=10),
                    entrywidth=80,
                    itemclick="toggle",  # Allow clicking legend items to show/hide traces
                    itemdoubleclick="toggleothers"  # Allow double-clicking to isolate traces
                ),
                xaxis_title=None,  # Remove the "Timeline" title
                yaxis_title=None,
                plot_bgcolor='white',
                paper_bgcolor='white',
                annotations=annotations,
                bargap=0.2,
                hovermode="closest"
            )

        # Determine tick spacing based on user preference or auto-calculate
        if tick_interval:
            # Use user-specified tick interval
            tick_months = tick_interval
        else:
            # Auto-calculate based on date range
            date_range_years = ((max_date.year - min_date.year) + 
                               (max_date.month - min_date.month)/12)

            if date_range_years <= 2:
                # For short ranges, show quarterly ticks
                tick_months = 3
            elif date_range_years <= 5:
                # For medium ranges, show semi-annual ticks
                tick_months = 6
            else:
                # For long ranges, show annual ticks
                tick_months = 12

        # Generate tick values and labels
        tick_dates = []
        start_year = min_date.year
        end_year = max_date.year + 1

        for year in range(start_year, end_year):
            for month in range(1, 13, tick_months):
                tick_date = pd.Timestamp(f'{year}-{month:02d}-01')
                if min_date <= tick_date <= max_date:
                    tick_dates.append(tick_date)

        # Configure axes with dynamic range
        fig.update_xaxes(
            type='date',  # Explicitly set x-axis type to date
            tickformat="%b %Y",  # Show month and year for less crowding
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            tickangle=45,  # Slight angle for readability if needed
            range=[min_date, max_date],  # Dynamic range based on data
            autorange=False,  # Explicitly disable automatic range adjustment
            constrain='domain',  # Constrain data to the specified range
            tickvals=tick_dates,
            ticktext=[date.strftime("%b %Y") for date in tick_dates],
            # Add hover lines for better date tracking
            showspikes=True,
            spikecolor="gray",
            spikesnap="cursor",
            spikemode="across",
            spikethickness=1
        )

        # Update Y axis to remove default tick labels and use annotations instead
        fig.update_yaxes(
            showticklabels=False,  # Hide default tick labels, we'll use annotations instead
            showgrid=False,
            range=[-0.5, len(tasks) - 0.5],
            # Add hover lines for task tracking
            showspikes=True,
            spikecolor="gray",
            spikesnap="cursor",
            spikemode="across",
            spikethickness=1
        )

        return fig

    def create_team_deadlines_chart(self, project_data, items_data, custom_start_date=None, custom_end_date=None, tick_interval=None):
        """
        Create a chart showing the last deadline for each team across all projects.

        Parameters:
        project_data (pd.DataFrame): DataFrame containing project information
        items_data (pd.DataFrame): DataFrame containing all timeline items across projects
        custom_start_date (datetime, optional): Custom start date for chart range
        custom_end_date (datetime, optional): Custom end date for chart range
        tick_interval (int, optional): Number of months between each x-axis tick mark

        Returns:
        plotly.graph_objects.Figure: A plotly figure showing team deadlines across projects
        """
        import plotly.graph_objects as go
        import pandas as pd
        from datetime import datetime
        import logging

        # Set up logging for this method
        logger.info(f"Starting team deadlines chart creation with {len(project_data)} projects and {len(items_data)} items")

        # Get team colors
        if hasattr(st.session_state, 'data_manager') and hasattr(st.session_state.data_manager, 'get_team_colors'):
            team_colors = st.session_state.data_manager.get_team_colors()
        else:
            team_colors = self.team_colors

        # Create a dataframe to store the last deadline for each team in each project
        deadlines_data = []

        # Get unique projects and teams
        projects = project_data[['ID', 'Name', 'ISO']].drop_duplicates()
        all_teams = list(team_colors.keys())

        # Track alerts for sequencing issues (teams ending after construction)
        alert_projects = {}
        alert_details = []

        # Process each project
        for _, project in projects.iterrows():
            project_id = project['ID']
            project_name = project['Name']
            project_iso = project['ISO']

            # Get items for this project
            project_items = items_data[items_data['Project ID'] == project_id]

            # Skip if no items for this project
            if project_items.empty:
                logger.warning(f"No timeline items found for project {project_id} - {project_name}")
                continue

            # Store deadlines by team for this project to check sequencing
            project_deadlines = {}

            # Find the last deadline for each team in this project
            for team in all_teams:
                try:
                    team_items = project_items[project_items['Team'] == team]

                    if not team_items.empty:
                        # Find the latest end date for this team with robust parsing
                        try:
                            # Convert end dates to datetime, handling various formats
                            end_dates = pd.to_datetime(team_items['End Date'], errors='coerce')

                            # Check if we have valid dates
                            if end_dates.notna().any():
                                latest_end_date = end_dates.max()

                                # Store deadline for sequencing check
                                project_deadlines[team] = latest_end_date

                                deadlines_data.append({
                                    'Project ID': project_id,
                                    'Project Name': project_name,
                                    'ISO': project_iso,
                                    'Team': team,
                                    'Deadline': latest_end_date
                                })
                            else:
                                logger.warning(f"No valid end dates for team {team} in project {project_id}")
                        except Exception as e:
                            logger.error(f"Error processing end dates for team {team} in project {project_id}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing team {team} for project {project_id}: {str(e)}")
                    continue

            # Check for sequencing issues - teams ending after construction
            if 'Construction' in project_deadlines:
                construction_deadline = project_deadlines['Construction']

                # Check critical teams that should end before construction
                issue_teams = []
                for check_team in ['Procurement', 'Development', 'Interconnection']:
                    if check_team in project_deadlines:
                        team_deadline = project_deadlines[check_team]

                        # If team deadline is after construction deadline, flag it
                        if team_deadline > construction_deadline:
                            issue_teams.append(check_team)

                            # Calculate days difference for reporting
                            days_diff = (team_deadline - construction_deadline).days

                            # Add to detailed alert information
                            alert_details.append({
                                "proj_name": project_name,
                                "team": check_team,
                                "days_diff": days_diff,
                                "message": f"{check_team} ends {days_diff} days after Construction"
                            })

                # If issues found, add project to alert list
                if issue_teams:
                    alert_projects[project_name] = issue_teams

        # Convert to DataFrame with error handling
        try:
            deadlines_df = pd.DataFrame(deadlines_data)

            # Log summary of data being processed
            logger.info(f"Created deadlines dataframe with {len(deadlines_df)} entries across {len(deadlines_df['Project Name'].unique())} projects")

            # If no data, return empty figure with message
            if deadlines_df.empty:
                logger.warning("No deadline data available to visualize")
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="No deadline data available",
                    annotations=[{
                        "text": "No team deadline data available to display. Try adding project items first.",
                        "showarrow": False,
                        "font": {"size": 14},
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 0.5
                    }]
                )
                return empty_fig

            # Verify required columns exist before proceeding
            required_cols = ['Project Name', 'Team', 'Deadline', 'ISO']
            missing_cols = [col for col in required_cols if col not in deadlines_df.columns]
            if missing_cols:
                logger.error(f"Missing required columns in deadlines data: {missing_cols}")
                raise ValueError(f"Missing required columns: {missing_cols}")

        except Exception as e:
            logger.error(f"Error creating deadlines dataframe: {str(e)}")
            # Return an empty figure with error message
            error_fig = go.Figure()
            error_fig.update_layout(
                title="Error creating deadlines chart",
                annotations=[{
                    "text": f"Error: {str(e)}",
                    "showarrow": False,
                    "font": {"size": 14, "color": "red"},
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5
                }]
            )
            return error_fig

        # Create figure
        fig = go.Figure()

        # Determine date range
        if custom_start_date and custom_end_date:
            min_date = pd.to_datetime(custom_start_date)
            max_date = pd.to_datetime(custom_end_date)
        else:
            min_date = pd.to_datetime('2025-01-01') #Set default start date to January 2025
            max_date = deadlines_df['Deadline'].max() + pd.DateOffset(months=1)

        # Set specific team order from top to bottom: Construction, Procurement, Interconnection, Development
        team_order = ['Construction', 'Procurement', 'Interconnection', 'Development']

        # For each team in the specified order, add a trace showing deadlines across projects
        for team in team_order:
            if team in all_teams:
                team_data = deadlines_df[deadlines_df['Team'] == team]

                if not team_data.empty:
                    fig.add_trace(go.Bar(
                        y=team_data['Project Name'],  # Projects on y-axis
                        x=team_data['Deadline'],      # Dates on x-axis
                        name=team,
                        marker_color=team_colors.get(team, '#999999'),
                        orientation='h',              # Horizontal bars
                        hovertemplate='<b>Project:</b> %{y}<br>' +
                                    '<b>Team:</b> ' + team + '<br>' +
                                    '<b>ISO:</b> ' + team_data['ISO'] + '<br>' +
                                    '<b>Deadline:</b> %{x|%Y-%m-%d}<br>'
                    ))

        # Add "Today" reference line - ALWAYS show it regardless of date range
        today = pd.Timestamp('today')

        # Always add the Today line, even if outside the current view
        fig.add_shape(
            type="line",
            x0=today,
            y0=-0.5,
            x1=today,
            y1=len(deadlines_df['Project Name'].unique()) - 0.5,
            line=dict(color="red", width=2, dash="dash"),
        )

        # Add "Today" annotation above the chart
        fig.add_annotation(
            x=today,
            y=len(deadlines_df['Project Name'].unique()) - 0.5,
            text="Today",
            showarrow=False,
            font=dict(color="red", size=12),
            textangle=0,
            yshift=25,
            yanchor="bottom"
        )

        # Update layout
        fig.update_layout(
            title=None,
            xaxis_title="Deadline Date",     # Now x-axis is Date
            yaxis_title="Projects",          # Now y-axis is Projects
            barmode='group',
            height=600,
            bargap=0.4,                      # Increase space between projects (default is 0.2)
            margin=dict(l=180, r=70, t=100, b=100),  # Further increased left margin to accommodate warning symbols
            font=dict(family="Arial, sans-serif", size=12),
            legend=dict(
                title=None,  # Remove Teams title
                orientation="h",
                yanchor="top",
                y=1.20,  # Positioned higher to avoid Today line
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='rgba(0,0,0,0.2)',
                borderwidth=1,
                itemwidth=70,  # Increased item width for better text visibility
                itemsizing='constant',
                traceorder='normal',
                font=dict(size=10),  # Smaller font size
                entrywidth=100  # Increased width for legend entries
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
        )

        # Determine tick spacing based on user preference or auto-calculate
        if tick_interval:
            # Use user-specified tick interval
            tick_months = tick_interval
        else:
            # Auto-calculate based on date range
            date_range_years = ((max_date.year - min_date.year) + 
                               (max_date.month - min_date.month)/12)

            if date_range_years <= 2:
                # For short ranges, show quarterly ticks
                tick_months = 3
            elif date_range_years <= 5:
                # For medium ranges, show semi-annual ticks
                tick_months = 6
            else:
                # For long ranges, show annual ticks
                tick_months = 12

        # Generate tick values and labels
        tick_dates = []
        start_year = min_date.year
        end_year = max_date.year + 1

        for year in range(start_year, end_year):
            for month in range(1, 13, tick_months):
                tick_date = pd.Timestamp(f'{year}-{month:02d}-01')
                if min_date <= tick_date <= max_date:
                    tick_dates.append(tick_date)

        # Format x-axis as dates with custom tick interval (was y-axis before)
        fig.update_xaxes(
            type='date',
            tickformat='%b %d, %Y',
            tickangle=45,
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            range=[min_date, max_date],
            tickvals=tick_dates,
            ticktext=[date.strftime("%b %Y") for date in tick_dates]
        )

        # Format y-axis for project names (was x-axis before)
        fig.update_yaxes(
            automargin=True,        # Ensure project names fit
            tickangle=0,            # Horizontal text
            showgrid=False
        )

        # Store warning information to display after the chart
        warning_info = None
        if alert_projects:
            # Prepare warning content but don't display it yet
            warning_info = {
                "alert_projects": alert_projects,
                "alert_details": alert_details
            }

            # Show visual indicators on the chart
            for project_name in alert_projects:
                # Add a semi-transparent red background rectangle for each project with issues
                fig.add_shape(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    x1=1,
                    y0=project_name,  # Project name as y-coordinate
                    y1=project_name,
                    fillcolor="rgba(255, 0, 0, 0.2)",  # Semi-transparent red
                    opacity=0.5,
                    layer="below",
                    line_width=0
                )

                # Add an alert icon before project names with issues
                fig.add_annotation(
                    x=-0.06,  # Moved even further left, well before the project name
                    y=project_name,
                    xref="paper",
                    yref="y",
                    text="⚠️",
                    showarrow=False,
                    font=dict(size=14, color="red"),
                    align="right",
                    xanchor="right",                    yanchor="middle"
                )

        # Return figure, alert details, and warning information
        if 'alert_details' in locals() and alert_details:
            return (fig, alert_details, warning_info)
        else:
            return fig

    def create_dependency_chart(self, data):
        teams = data['Team'].unique()
        dependencies = []

        for team in teams:
            team_projects = data[data['Team'] == team]
            if not team_projects.empty:
                deps = team_projects['Dependencies'].fillna('').str.split(',')
                for dep in deps:
                    if isinstance(dep, list):
                        for d in dep:
                            if d.strip():
                                dependencies.append({
                                    'from': team,
                                    'to': d.strip()
                                })

        dep_df = pd.DataFrame(dependencies)
        if not dep_df.empty:
            fig = px.scatter(
                dep_df,
                title="Team Dependencies Network",
                template="plotly_white",
                color_discrete_sequence=['#1976D2']
            )
            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                title_font_size=20,
                title_x=0.5,
                font=dict(family="Arial, sans-serif", size=12)
            )
            return fig
        return None