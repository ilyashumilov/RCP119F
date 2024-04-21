from services.data_gainer_service import async_past_data_gainer
from datetime import datetime, timedelta
import plotly.graph_objects as go


class Overviewer:
    def __init__(self, symbol: str):
        self._end = datetime.now()
        self._start = self._end - timedelta(days=90)
        self._symbol = symbol
        self._interval = 30
        self._df = None

    async def process(self):
        self._df = await async_past_data_gainer(
            start=self._start,
            end=self._end,
            interval=self._interval,
            ticker=self._symbol,
        )
        return self._plot()

    def _plot(self):
        fig = go.Figure()

        increasing_color = 'rgba(0, 194, 0, 0.5)'
        decreasing_color = 'rgba(194, 0, 0, 0.5)'

        price_trace = go.Candlestick(
            x=self._df['Date'],
            open=self._df['Open'],
            high=self._df['High'],
            low=self._df['Low'],
            close=self._df['Close'],
            increasing_line_color=increasing_color,
            decreasing_line_color=decreasing_color
        )
        fig.add_trace(price_trace)
        fig.update_layout(
            title=self._symbol,
            xaxis_title='Date',
            yaxis_title='Price',
            xaxis_rangeslider_visible=False,
            height=800,
            plot_bgcolor='white',  # Set the background color
            paper_bgcolor='white',  # Set the paper color (the area outside the plot)
            xaxis=dict(showgrid=False),  # Remove x-axis grid lines
            yaxis=dict(showgrid=False)  # Remove y-axis grid lines
        )
        return fig