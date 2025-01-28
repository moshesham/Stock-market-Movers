import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# --- Streamlit App Title and Description ---
st.title("Stock Market Analyzer")
st.write(
    """
    This app analyzes stock market data based on user input. 
    Enter stock symbols and select a date range to get started.
    """
)

# --- User Input ---
# Get user input for stock symbols with a default value
stocks_input = st.text_input(
    "Enter stock symbols separated by commas (e.g., AAPL, MSFT, GOOG):",
    value="AAPL, MSFT, GOOG",  # Added a default value
)
stocks = [stock.strip().upper() for stock in stocks_input.split(",")]

# Get user input for date range with a wider default range
today = datetime.date.today()
one_year_ago = today - datetime.timedelta(days=365)
start_date = st.date_input("Start Date", one_year_ago)
end_date = st.date_input("End Date", today)

# --- Data Acquisition and Preprocessing ---
# Validate date range
if start_date >= end_date:
    st.error("Error: End date must fall after start date.")
else:
    # Fetch historical data for selected stocks
    if stocks:
        try:
            data = yf.download(stocks, start=start_date, end=end_date)

            # --- Data Cleaning and Transformation ---
            # Check if data is empty
            if data.empty:
                st.warning("No data found for the selected stock(s) and date range.")
            else:
                # Multilevel indexing is being used when you download multiple stocks.
                # We want to process the data stock by stock to calculate the market cap
                # To do this, we will transform our data to a dictionary where each
                # key will be a stock and the value will be its respective data

                stock_data = {}
                for stock in stocks:
                    # Extract data for the current stock
                    if len(stocks) > 1:
                        stock_df = data.loc[:, (slice(None), stock)].copy()
                        stock_df.columns = stock_df.columns.droplevel(1)
                    else:
                        stock_df = data.copy()

                    # We are assuming that the stock price is available
                    # If it is not, we can use the Open or Close price
                    if "Adj Close" not in stock_df.columns:
                        st.warning(
                            f"Adjusted Close price not found for {stock}. Using Close price instead."
                        )
                        stock_df["Adj Close"] = stock_df["Close"]

                    # Fetch outstanding shares using yfinance
                    # If it fails, we can use a constant value
                    try:
                        stock_info = yf.Ticker(stock)
                        outstanding_shares = stock_info.info["sharesOutstanding"]
                    except Exception as e:
                        st.warning(
                            f"Could not fetch outstanding shares for {stock}. Using a constant value (1,000,000,000) instead."
                        )
                        outstanding_shares = 1_000_000_000

                    # Calculate market cap
                    stock_df["Market Cap"] = (
                        stock_df["Adj Close"] * outstanding_shares
                    )

                    # Calculate market cap change
                    stock_df["Market Cap Change"] = stock_df["Market Cap"].diff()

                    # Store data for the current stock in the dictionary
                    stock_data[stock] = stock_df

                # --- Display Market Value Changes ---
                st.header("Market Value Changes")
                for stock, stock_df in stock_data.items():
                    st.subheader(f"{stock} - Daily Market Value Change")
                    st.dataframe(stock_df[["Market Cap Change"]])

                # --- Top Movers During the Period ---
                st.header("Top Movers During the Period")

                # Prepare data for top movers calculation
                top_movers_data = []
                for stock, stock_df in stock_data.items():
                    total_market_cap_change = stock_df["Market Cap Change"].sum()
                    top_movers_data.append(
                        {
                            "Stock": stock,
                            "Total Market Cap Change": total_market_cap_change,
                        }
                    )
                top_movers_df = pd.DataFrame(top_movers_data)

                # Identify top gainers and losers based on total market cap change
                top_gainers = top_movers_df.sort_values(
                    "Total Market Cap Change", ascending=False
                ).head(5)
                top_losers = top_movers_df.sort_values(
                    "Total Market Cap Change", ascending=True
                ).head(5)

                st.subheader("Top Gainers")
                st.dataframe(top_gainers)
                st.subheader("Top Losers")
                st.dataframe(top_losers)

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter stock symbols.")
