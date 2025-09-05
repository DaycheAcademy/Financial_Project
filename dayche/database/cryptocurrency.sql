CREATE TABLE Cryptocurrency (
    crypto_id INT PRIMARY KEY IDENTITY(1,1),  -- Auto-incrementing primary key
    symbol VARCHAR(10) NOT NULL,              -- Symbol of the cryptocurrency (e.g., BTC)
    name VARCHAR(255) NOT NULL,               -- Full name of the cryptocurrency
    market_cap FLOAT,                         -- Market capitalization in USD
    circulating_supply FLOAT,                 -- Circulating supply (computed or from sharesOutstanding)
    volume FLOAT,                             -- 24-hour trading volume
    avg_volume FLOAT,                         -- Average trading volume over a certain period
    created_at DATETIME DEFAULT GETDATE(),    -- Record creation timestamp
    updated_at DATETIME DEFAULT GETDATE()     -- Record update timestamp
);
