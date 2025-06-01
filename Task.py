import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from bokeh.plotting import figure, show, output_file
import logging
import unittest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class InvalidSalesDataError(Exception):
    """
    Custom exception for handling missing or malformed sales data
    that prevents further processing in the forecasting workflow.
    """
    pass

class BaseDBHandler:
    """
    BaseDBHandler is a foundational class that encapsulates common functionality
    for interacting with an SQLite database using SQLAlchemy. It provides utility methods
    to load CSV files into database tables and to retrieve those tables as pandas DataFrames.
    """
    def __init__(self, db_name="weekly_sales_forecast.db"):
        """
        Initializes the database connection using SQLAlchemy.

        Args:
            db_name (str): Name of the SQLite database file.
        """
        self.db_name = db_name
        self.engine = create_engine(f'sqlite:///{self.db_name}')

    def load_csv_to_db(self, file_path, table_name):
        """
        Loads data from a CSV file into a specified table in the SQLite database.

        Args:
            file_path (str): Path to the CSV file.
            table_name (str): Name of the table to create or replace in the database.
        """
        try:
            df = pd.read_csv(file_path)
            df.columns = [col.strip().lower() for col in df.columns]
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
            logging.info(f"Data loaded into table: {table_name}")
        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            logging.error(f"Failed loading CSV: {e}")
        except Exception as e:
            logging.exception("Unexpected error during CSV load")

    def read_sales_table(self, table_name):
        """
        Reads a specified table from the database and returns it as a pandas DataFrame.

        Args:
            table_name (str): Name of the table to read.

        Returns:
            pd.DataFrame: DataFrame containing table data or None if error occurs.
        """
        try:
            df = pd.read_sql(f'SELECT * FROM {table_name}', self.engine)
            df.columns = [col.strip().lower() for col in df.columns]
            return df
        except Exception as e:
            logging.error(f"Failed to read table {table_name}: {e}")
            return None

class SalesPredictor(BaseDBHandler):
    """
    SalesPredictor extends BaseDBHandler to implement a forecasting system
    for weekly sales. It selects the most suitable ideal functions based on
    historical data using least-squares error and maps test data accordingly.
    """

    def identify_best_sales_patterns(self):
        """
        Determines the best matching ideal function for each historical sales column
        by minimizing the least squares error between values.

        Returns:
            dict: Mapping of historical sales columns to ideal function columns.
        """
        training_sales_df = self.read_sales_table("historical_sales")
        pattern_df = self.read_sales_table("sales_patterns")

        if training_sales_df is None or pattern_df is None:
            logging.error("Missing historical or pattern sales data.")
            return {}

        best_patterns = {}
        for week_col in training_sales_df.columns[1:]:
            errors = {
                pattern_col: np.sum((training_sales_df[week_col] - pattern_df[pattern_col]) ** 2)
                for pattern_col in pattern_df.columns[1:]
            }
            best_patterns[week_col] = min(errors, key=errors.get)

        return best_patterns

    def load_and_predict_weekly_sales(self, file_path):
        """
        Processes the test weekly sales file to map each record to its best ideal function
        and stores results in the database with corresponding deviation.

        Args:
            file_path (str): Path to test data CSV file.

        Raises:
            InvalidSalesDataError: If test file is missing required columns or if reference data is missing.
        """
        try:
            test_sales_df = pd.read_csv(file_path)
            test_sales_df.columns = [col.strip().lower() for col in test_sales_df.columns]

            if "x" not in test_sales_df or "y" not in test_sales_df:
                raise InvalidSalesDataError("Missing required columns 'x' or 'y'")

            best_patterns = self.identify_best_sales_patterns()
            pattern_df = self.read_sales_table("sales_patterns")
            training_df = self.read_sales_table("historical_sales")

            if pattern_df is None or training_df is None:
                raise InvalidSalesDataError("Missing pattern/historical data.")

            forecast_results = []
            for _, row in test_sales_df.iterrows():
                x_val, y_val = row["x"], row["y"]
                best_match, min_dev = None, float('inf')

                for week_col, pattern_col in best_patterns.items():
                    if pattern_col not in pattern_df.columns:
                        continue

                    max_dev = max(abs(training_df[week_col] - pattern_df[pattern_col])) * np.sqrt(2)
                    pattern_sales_vals = pattern_df.loc[pattern_df["x"] == x_val, pattern_col].values

                    if pattern_sales_vals.size:
                        deviation = abs(y_val - pattern_sales_vals[0])
                        if deviation <= max_dev and deviation < min_dev:
                            best_match, min_dev = pattern_col, deviation

                forecast_results.append((x_val, y_val, min_dev, best_match))

            forecast_df = pd.DataFrame(forecast_results, columns=["x", "y", "delta_y", "ideal_function"])
            forecast_df.to_sql("sales_forecast", self.engine, if_exists='replace', index=False)
            logging.info("Weekly sales forecast completed and stored.")

        except InvalidSalesDataError as ve:
            logging.error(f"Validation error: {ve}")
        except Exception as e:
            logging.exception("Error processing sales forecast")

    def visualize_sales_forecast(self):
        """
        Visualizes the historical sales data, selected ideal patterns, and forecast results using Bokeh.
        The output is saved to an HTML file for viewing in the browser.
        """
        training_df = self.read_sales_table("historical_sales")
        pattern_df = self.read_sales_table("sales_patterns")
        forecast_df = self.read_sales_table("sales_forecast")

        if not all([training_df is not None, pattern_df is not None, forecast_df is not None]):
            logging.error("Missing datasets for visualization.")
            return

        best_patterns = self.identify_best_sales_patterns()
        output_file("sales_forecast_visualization.html")
        p = figure(title="Weekly Sales Forecast", x_axis_label="x", y_axis_label="y")

        for col in training_df.columns[1:]:
            p.line(training_df["x"], training_df[col], legend_label=f"Historical {col}")
            pattern_col = best_patterns.get(col)
            if pattern_col in pattern_df.columns:
                p.line(pattern_df["x"], pattern_df[pattern_col], legend_label=f"Pattern {col}", line_dash="dashed")

        p.scatter(forecast_df["x"], forecast_df["y"], legend_label="Forecast Data", color="red")
        show(p)

if __name__ == "__main__":
    predictor = SalesPredictor()
    predictor.load_csv_to_db("train.csv", "historical_sales")
    predictor.load_csv_to_db("ideal.csv", "sales_patterns")
    predictor.load_and_predict_weekly_sales("test.csv")
    predictor.visualize_sales_forecast()

class TestSalesPredictor(unittest.TestCase):
    """
    Unit tests for the SalesPredictor class to ensure correct data loading,
    table reading, and ideal pattern selection logic.
    """
    def setUp(self):
        self.predictor = SalesPredictor(db_name=":memory:")
        dummy_data = pd.DataFrame({"x": [1, 2, 3], "y1": [10, 20, 30]})
        dummy_data.to_sql("historical_sales", self.predictor.engine, index=False)
        dummy_data.to_sql("sales_patterns", self.predictor.engine, index=False)

    def test_read_sales_table(self):
        """Test reading of a sales table from the database."""
        df = self.predictor.read_sales_table("historical_sales")
        self.assertIsNotNone(df)
        self.assertIn("x", df.columns)

    def test_identify_best_sales_patterns(self):
        """Test the logic for identifying the best-matching pattern columns."""
        patterns = self.predictor.identify_best_sales_patterns()
        self.assertIsInstance(patterns, dict)

    def test_load_csv_to_db(self):
        """Test loading a dummy CSV file into the database."""
        test_path = "test_dummy.csv"
        pd.DataFrame({"x": [1], "y": [100]}).to_csv(test_path, index=False)
        self.predictor.load_csv_to_db(test_path, "dummy")
        df = self.predictor.read_sales_table("dummy")
        self.assertEqual(df.shape[0], 1)

if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)
