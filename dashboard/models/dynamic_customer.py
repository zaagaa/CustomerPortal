class DynamicCustomer:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, item):
        return None

    def __repr__(self):
        return f"<Customer: {getattr(self, 'customer_name', 'Unknown')}>"
