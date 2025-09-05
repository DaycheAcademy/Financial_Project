CREATE TABLE Crypto_Quote (
    quote_id INT PRIMARY KEY IDENTITY(1,1),   -- Auto-incrementing primary key for each quote
    crypto_id INT FOREIGN KEY REFERENCES Cryptocurrency(crypto_id), -- Foreign key to the Cryptocurrency table
    price FLOAT NOT NULL,                     -- Current price of the cryptocurrency
    high_price FLOAT,                         -- Highest price in the last 24 hours
    low_price FLOAT,                          -- Lowest price in the last 24 hours
    open_price FLOAT,                         -- Opening price for the day
    previous_close FLOAT,                     -- Price at the previous market close
    volume FLOAT,                             -- Trading volume in the last 24 hours
    avg_volume FLOAT,                         -- Average trading volume
    timestamp DATETIME                        -- Timestamp of the quote data
);
