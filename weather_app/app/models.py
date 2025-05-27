def log_city_query(db, city: str):
    db.execute("INSERT INTO search_history (city) VALUES (?)", (city,))
    db.commit()