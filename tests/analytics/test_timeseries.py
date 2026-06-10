import unittest
from analytics.timeseries import TimeSeries

class TestTimeSeries(unittest.TestCase):
    def test_timeseries_window_and_average(self):
        ts = TimeSeries("latency", max_points=10)
        
        ts.append(1000, 10.0)
        ts.append(2000, 20.0)
        ts.append(3000, 30.0)
        
        # Latest
        self.assertEqual(ts.latest(), 30.0)
        
        # Window
        w = ts.window(1500, 3000) # Cutoff: 1500
        self.assertEqual(len(w), 2) # 2000 and 3000
        
        # Trailing average
        avg = ts.trailing_average(1500, 3000)
        self.assertEqual(avg, 25.0) # (20+30)/2
        
if __name__ == '__main__':
    unittest.main()
