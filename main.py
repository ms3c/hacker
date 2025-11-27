import sqlite3

db_path = '/mnt/data/MamaNet_Advanced.sqlite'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Main members table
cur.execute("""
CREATE TABLE IF NOT EXISTS Members (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    FullName TEXT,
    Age INTEGER,
    PhoneNumber TEXT,
    Disability TEXT,
    OrganizationName TEXT,
    PaymentMethod TEXT,
    ReceiverName TEXT,
    Gender TEXT,
    Address TEXT,
    Ward TEXT,
    District TEXT,
    Village TEXT
);
""")

# Lookup tables
cur.execute("CREATE TABLE IF NOT EXISTS GenderTypes (Gender TEXT PRIMARY KEY);")
cur.execute("CREATE TABLE IF NOT EXISTS DisabilityTypes (Disability TEXT PRIMARY KEY);")
cur.execute("CREATE TABLE IF NOT EXISTS PaymentMethods (Method TEXT PRIMARY KEY);")

# Insert default lookup values
cur.executemany("INSERT OR IGNORE INTO GenderTypes VALUES (?);", [
    ("Male",), ("Female",), ("Other",)
])

cur.executemany("INSERT OR IGNORE INTO DisabilityTypes VALUES (?);", [
    ("None",), ("Physical",), ("Vision",), ("Hearing",), ("Mental",)
])

cur.executemany("INSERT OR IGNORE INTO PaymentMethods VALUES (?);", [
    ("Cash",), ("Bank Transfer",), ("Mobile Money",)
])

# Age group view
cur.execute("DROP VIEW IF EXISTS AgeGroups;")
cur.execute("""
CREATE VIEW AgeGroups AS
SELECT
    ID,
    FullName,
    Age,
    CASE
        WHEN Age < 18 THEN 'Under 18'
        WHEN Age BETWEEN 18 AND 35 THEN '18-35'
        WHEN Age BETWEEN 36 AND 59 THEN '36-59'
        WHEN Age >= 60 THEN '60+'
        ELSE 'Unknown'
    END AS AgeGroup,
    Gender,
    Disability,
    District,
    Ward,
    Village
FROM Members;
""")

conn.commit()
conn.close()

db_path