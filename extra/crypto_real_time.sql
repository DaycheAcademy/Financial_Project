CREATE TABLE Crypto_RealTime_Updates (
    update_id INT PRIMARY KEY IDENTITY(1,1),  -- Auto-incrementing primary key for each real-time update
    crypto_id INT FOREIGN KEY REFERENCES Cryptocurrency(crypto_id), -- Foreign key to the Cryptocurrency table
    price FLOAT NOT NULL,                     -- Real-time last price of the cryptocurrency
    change FLOAT,                             -- Price change from the previous update
    changes_percentage FLOAT,                 -- Percentage change in price
    timestamp DATETIME DEFAULT GETDATE()      -- Timestamp of the real-time update
);
