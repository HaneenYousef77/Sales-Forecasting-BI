# Sales Forecasting Using Python for Business Intelligence

This project demonstrates the use of Python in building a Business Intelligence (BI) system for forecasting weekly sales using historical and pattern data. The system identifies ideal sales trends, forecasts future values, and visualizes outcomes using interactive dashboards.

## Overview

The goal is to:
- Match test sales data to the best-fitting sales patterns.
- Calculate deviations and forecast weekly performance.
- Visualize historical, ideal, and forecasted sales using Bokeh.
- Store all intermediate data in a SQLite database using SQLAlchemy.

This project was developed as part of the "Programming with Python" course at IU University of Applied Sciences.

## Technologies Used

| Component         | Description                             |
|------------------|-----------------------------------------|
| Python 3.10+      | Core programming language                |
| Pandas & NumPy    | Data manipulation and analysis           |
| SQLAlchemy        | SQLite database integration              |
| Bokeh             | Interactive visualization                |
| Unittest          | Testing and validation                   |
| SQLite            | Local database for persistent storage    |

## Project Structure

├── Task.py # Main implementation
├── test.csv # Test weekly sales data
├── train.csv # Historical training data
├── ideal.csv # Ideal sales patterns
├── sales_forecast_visualization.html # Visualization output
├── weekly_sales_forecast.db # SQLite database (auto-created)
├── README.md # Project documentation


## How to Run

1. **Install dependencies**:
```bash
pip install pandas numpy sqlalchemy bokeh
Run the script:
python main.py

2. Output:
- An interactive sales forecast visualization will be saved as sales_forecast_visualization.html.
- Forecasted data will be saved to a SQLite database weekly_sales_forecast.db.

🙋 Author
Haneen Yousef
Master's Student in Artificial Intelligence
IU University of Applied Sciences
