-- Create index on the symbol column in the Cryptocurrency table
CREATE INDEX idx_cryptocurrency_symbol
ON Cryptocurrency (symbol);


-- Create index on the timestamp column in the Crypto_Quote table
CREATE INDEX idx_crypto_quote_timestamp
ON Crypto_Quote (timestamp);



-- Create index on the timestamp column in the Crypto_Historical table
CREATE INDEX idx_crypto_historical_timestamp
ON Crypto_Historical (timestamp);



-- Create index on the timestamp column in the Crypto_RealTime_Updates table
CREATE INDEX idx_crypto_realtime_timestamp
ON Crypto_RealTime_Updates (timestamp);


-- Composite index for queries on multiple columns
CREATE INDEX idx_crypto_symbol_timestamp
ON Crypto_Quote (symbol, timestamp);



-- Partition Large Tables: As your Crypto_Historical and 
-- Crypto_RealTime_Updates tables grow, 
-- consider partitioning them based on timestamp (e.g., by year or month). 
-- This breaks large tables into smaller, 
-- manageable pieces, improving query performance:
CREATE PARTITION FUNCTION cryptoPartitionFunc(DATE) 
AS RANGE RIGHT FOR VALUES ('2022-01-01', '2023-01-01');
CREATE PARTITION SCHEME cryptoPartitionScheme 
AS PARTITION cryptoPartitionFunc TO ([PRIMARY], [SECONDARY]);



-- Use Covering Indexes: If a query retrieves 
-- a subset of columns, create covering indexes 
-- that include those columns. For example, 
-- if you frequently query symbol and price, 
-- you can create an index that covers the query:
CREATE INDEX idx_quote_symbol_price
ON Crypto_Quote (symbol)
INCLUDE (price);



-- Rebuild or Reorganize Indexes: Index fragmentation 
-- can slow down performance, especially for large datasets. 
-- Regularly rebuild or reorganize indexes 
-- based on their fragmentation levels:
-- (Use rebuild when fragmentation exceeds 30% and reorganize for lower fragmentation (5-30%).)
ALTER INDEX ALL ON Crypto_Quote
REBUILD;  -- Rebuild fragmented indexes



-- Update Statistics: SQL Server uses statistics to determine 
-- the best query execution plans. Regularly update statistics 
-- to ensure query plans remain optimal:
UPDATE STATISTICS Crypto_Quote;



-- Use Bulk Inserts: When importing data from the API, 
-- perform batch inserts rather than inserting rows one by one. 
-- This reduces the overhead per insert operation:
BULK INSERT Cryptocurrency
FROM 'datafile.csv'
WITH (
  FIELDTERMINATOR = ',',
  ROWTERMINATOR = '\n'
);



-- Analyze Query Execution Plans: Use SQL Server’s 
-- execution plan feature (SET SHOWPLAN_ALL ON) 
-- to understand how queries are being executed 
-- and identify bottlenecks. Look for:
--	Table scans: Replace with indexes if possible.
--	High cost operators: Reduce complexity by rewriting queries.




-- Use Row Versioning for Concurrency: 
-- In high-concurrency environments, 
-- enable Read Committed Snapshot Isolation (RCSI) 
-- to reduce locking contention. This helps prevent blocking and deadlocks:
-- (Avoid Long-Running Transactions: Keep transactions short 
-- to minimize locking and blocking, especially in update-heavy 
-- scenarios like API data ingestion.)
ALTER DATABASE [YourDatabase] SET READ_COMMITTED_SNAPSHOT ON;




-- TempDB Optimization: Many operations 
-- (like sorting or grouping) use tempdb. Ensure tempdb is optimized by:
-- Increasing the number of tempdb data 
-- files (start with 1 file per 4 CPU cores).
-- Storing tempdb on fast storage (SSD).
-- Use SSDs for High I/O Tables: Place frequently 
-- queried tables (like Crypto_RealTime_Updates) on 
-- faster SSD storage to speed up read and write operations.



-- Use Connection Pooling: If your API is interacting 
-- with SQL Server frequently, enable connection 
-- pooling to reduce the overhead of opening and 
-- closing connections with each API request.

-- Optimize API Fetch Frequency: Avoid fetching 
-- data more frequently than necessary from the API. 
-- For real-time data, determine an optimal fetch 
-- frequency to minimize API calls while keeping data updated.




-- SQL Server Profiler: Use SQL Profiler to monitor 
-- long-running queries or high CPU-consuming queries.

-- Dynamic Management Views (DMVs): Use DMVs like 
-- sys.dm_db_index_usage_stats and sys.dm_exec_query_stats 
-- to analyze index usage and query performance, then fine-tune accordingly.

