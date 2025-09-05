CREATE TRIGGER trg_UpdateCryptocurrency
ON Cryptocurrency
AFTER UPDATE
AS
BEGIN
    UPDATE Cryptocurrency
    SET updated_at = GETDATE()
    FROM inserted
    WHERE Cryptocurrency.crypto_id = inserted.crypto_id;
END;
