# -*- coding: utf-8 -*-
import sys
from math import cos
from math import sin
from math import pi
from math import floor
from math import ceil

# Basic idea from https://github.com/kroitor/asciichart
# ╱ ╲ ╳ ─ └┲┲┲─


class AsciiChart(object):
    """Can be used to plot price and trade history

        :param int height: Height of the plot
        :param int width: Width of the plot
        :param int offset: Offset between tick strings and y-axis (default is 3)
        :param str placeholder: Defines how the numbers on the y-axes are formatted (default is '{:8.2f}')
        :param str charset: sets the charset for plotting, uft8 or ascii (default: utf8)
    """
    def __init__(self, height=None, width=None, offset=3, placeholder=u'{:8.2f} ', charset=u'utf8'):
        self.height = height
        self.width = width
        self.offset = offset
        self.placeholder = placeholder
        self.clear_data()
        if charset == u'ascii' or sys.version_info[0] < 3:
            self.char_set = {'first_axis_elem': u'|',
                             'axis_elem': u'|',
                             'axis_elem_with_graph': u'|',
                             'curve_ar': u'\\',
                             'curve_lb': u'\\',
                             'curve_br': u'/',
                             'curve_la': u'/',
                             'curve_hl': u'-',
                             'curve_vl': u'|',
                             'curve_hl_dot': u'-',
                             'curve_vl_dot': u'|'}
        else:
            self.char_set = {'first_axis_elem': u'┼',
                             'axis_elem': u'┤',
                             'axis_elem_with_graph': u'┼',
                             'curve_ar': u'╰',
                             'curve_lb': u'╮',
                             'curve_br': u'╭',
                             'curve_la': u'╯',
                             'curve_hl': u'─',
                             'curve_vl': u'│',
                             'curve_hl_dot': u'┈',
                             'curve_vl_dot': u'┊'}

    def clear_data(self):
        """Clears all data"""
        self.canvas = []
        self.minimum = None
        self.maximum = None
        self.n = None
        self.skip = 1

    def set_parameter(self, height=None, offset=None, placeholder=None):
        """Can be used to change parameter"""
        if height is not None:
            self.height = height
        if offset is not None:
            self.offset = offset
        if placeholder is not None:
            self.placeholder = placeholder
        self._calc_plot_parameter()

    def adapt_on_series(self, series):
        """Calculates the minimum, maximum and length from the given list

            :param list series: time series to plot

            .. testcode::

                from beem.asciichart import AsciiChart
                chart = AsciiChart()
                series = [1, 2, 3, 7, 2, -4, -2]
                chart.adapt_on_series(series)
                chart.new_chart()
                chart.add_axis()
                chart.add_curve(series)
                print(str(chart))

        """
        self.minimum = min(series)
        self.maximum = max(series)
        self.n = len(series)
        self._calc_plot_parameter()

    def _calc_plot_parameter(self, minimum=None, maximum=None, n=None):
        """Calculates parameter from minimum, maximum and length
        """
        if minimum is not None:
            self.minimum = minimum
        if maximum is not None:
            self.maximum = maximum
        if n is not None:
            self.n = n
        if self.n is None or self.maximum is None or self.minimum is None:
            return
        interval = abs(float(self.maximum) - float(self.minimum))
        if interval == 0:
            interval = 1
        if self.height is None:
            self.height = interval
        self.ratio = self.height / interval
        self.min2 = floor(float(self.minimum) * self.ratio)
        self.max2 = ceil(float(self.maximum) * self.ratio)
        if self.min2 == self.max2:
            self.max2 += 1
        intmin2 = int(self.min2)
        intmax2 = int(self.max2)
        self.rows = abs(intmax2 - intmin2)
        if self.width is not None:
            self.skip = int(self.n / self.width)
            if self.skip < 1:
                self.skip = 1
        else:
            self.skip = 1

    def plot(self, series, return_str=False):
        """All in one function for plotting

            .. testcode::

                from beem.asciichart import AsciiChart
                chart = AsciiChart()
                series = [1, 2, 3, 7, 2, -4, -2]
                chart.plot(series)
        """
        self.clear_data()
        self.adapt_on_series(series)
        self.new_chart()
        self.add_axis()
        self.add_curve(series)
        if not return_str:
            print(str(self))
        else:
            return str(self)

    def new_chart(self, minimum=None, maximum=None, n=None):
        """Clears the canvas

            .. testcode::

                from beem.asciichart import AsciiChart
                chart = AsciiChart()
                series = [1, 2, 3, 7, 2, -4, -2]
                chart.adapt_on_series(series)
                chart.new_chart()
                chart.add_axis()
                chart.add_curve(series)
                print(str(chart))

        """
        if minimum is not None:
            self.minimum = minimum
        if maximum is not None:
            self.maximum = maximum
        if n is not None:
            self.n = n
        self._calc_plot_parameter()
        self.canvas = [[u' '] * (int(self.n / self.skip) + self.offset) for i in range(self.rows + 1)]

    def add_axis(self):
        """Adds a y-axis to the canvas

            .. testcode::

                from beem.asciichart import AsciiChart
                chart = AsciiChart()
                series = [1, 2, 3, 7, 2, -4, -2]
                chart.adapt_on_series(series)
                chart.new_chart()
                chart.add_axis()
                chart.add_curve(series)
                print(str(chart))

        """
        # axis and labels
        interval = abs(float(self.maximum) - float(self.minimum))
        intmin2 = int(self.min2)
        intmax2 = int(self.max2)
        for y in range(intmin2, intmax2 + 1):
            label = self.placeholder.format(float(self.maximum) - ((y - intmin2) * interval / self.rows))
            if label:
                self._set_y_axis_elem(y, label)

    def _set_y_axis_elem(self, y, label):
        intmin2 = int(self.min2)
        self.canvas[y - intmin2][max(self.offset - len(label), 0)] = label
        if y == 0:
            self.canvas[y - intmin2][self.offset - 1] = self.char_set["first_axis_elem"]
        else:
            self.canvas[y - intmin2][self.offset - 1] = self.char_set["axis_elem"]

    def _map_y(self, y_float):
        intmin2 = int(self.min2)
        return int(round(y_float * self.ratio) - intmin2)

    def add_curve(self, series):
        """Add a curve to the canvas

            :param list series: List width float data points

            .. testcode::

                from beem.asciichart import AsciiChart
                chart = AsciiChart()
                series = [1, 2, 3, 7, 2, -4, -2]
                chart.adapt_on_series(series)
                chart.new_chart()
                chart.add_axis()
                chart.add_curve(series)
                print(str(chart))

        """
        if self.n is None:
            self.adapt_on_series(series)
        if len(self.canvas) == 0:
            self.new_chart()
        y0 = self._map_y(series[0])
        self._set_elem(y0, -1, self.char_set["axis_elem_with_graph"])
        for x in range(0, len(series[::self.skip]) - 1):
            y0 = self._map_y(series[::self.skip][x + 0])
            y1 = self._map_y(series[::self.skip][x + 1])
            if y0 == y1:
                self._draw_h_line(y0, x, x + 1, line=self.char_set["curve_hl"])
            else:
                self._draw_diag(y0, y1, x)
                start = min(y0, y1) + 1
                end = max(y0, y1)
                self._draw_v_line(start, end, x, line=self.char_set["curve_vl"])

    def _draw_diag(self, y0, y1, x):
        """Plot diagonal element"""
        if y0 > y1:
            c1 = self.char_set["curve_ar"]
            c0 = self.char_set["curve_lb"]
        else:
            c1 = self.char_set["curve_br"]
            c0 = self.char_set["curve_la"]
        self._set_elem(y1, x, c1)
        self._set_elem(y0, x, c0)

    def _draw_h_line(self, y, x_start, x_end, line=u'-'):
        """Plot horizontal line"""
        for x in range(x_start, x_end):
            self._set_elem(y, x, line)

    def _draw_v_line(self, y_start, y_end, x, line=u'|'):
        """Plot vertical line"""
        for y in range(y_start, y_end):
            self._set_elem(y, x, line)

    def _set_elem(self, y, x, c):
        """Plot signle element into canvas"""
        self.canvas[self.rows - y][x + self.offset] = c

    def __repr__(self):
        return '\n'.join([''.join(row) for row in self.canvas])

    __str__ = __repr__
