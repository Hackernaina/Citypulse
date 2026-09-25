USERS = {
    "1": {
        "id": "1",
        "username": "riya",
        "name": "Riya Agrawal",
        "email": "riya@example.test",
        "password": "riya123",
        "role": "user",
        "internal_notes": "Internal demo note: VIP customer",
    },
    "2": {
        "id": "2",
        "username": "sheetal",
        "name": "Sheetal Pareek",
        "email": "sheetal@example.test",
        "password": "sheetal123",
        "role": "user",
        "internal_notes": "Internal demo note: standard customer",
    },
}

TOKENS = {
    "riya-demo-token": "1",
    "sheetal-demo-token": "2",
}

ORDERS = {
    "101": {"id": "101", "owner_id": "1", "item": "Laptop", "amount": 75000},
    "102": {"id": "102", "owner_id": "2", "item": "Phone", "amount": 55000},
}
