CREATE TABLE Crypto_Historical (
    history_id INT PRIMARY KEY IDENTITY(1,1), -- Auto-incrementing primary key
    crypto_id INT FOREIGN KEY REFERENCES Cryptocurrency(crypto_id), -- Foreign key to the Cryptocurrency table
    date DATE NOT NULL,                       -- Date of the historical price data
    open_price FLOAT,                         -- Opening price for the day
    close_price FLOAT,                        -- Closing price for the day
    high_price FLOAT,                         -- Highest price during the day
    low_price FLOAT,                          -- Lowest price during the day
    volume FLOAT,                             -- Volume traded during the day
    timestamp DATETIME DEFAULT GETDATE()      -- Timestamp of data collection
);
