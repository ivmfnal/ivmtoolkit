class Transaction(object):
    
    def __init__(self, connection):
        self.Connection = connection
        self.Cursor = self.Connection.cursor()
        self.InTransaction = False
        self.Exc = None
        self.Failed = False

    def begin(self):
        self.Cursor.execute("begin")
        self.InTransaction = True
        
    def commit(self):
        self.Cursor.execute("commit")
        self.InTransaction = False
        
    def rollback(self):
        self.Cursor.execute("rollback")
        self.InTransaction = False
        
    def execute(self, *params, **args):
        if not self.InTransaction:
            raise RintimeError("Transaction closed")
        try:
            self.Cursor.execute(*params, **args)
        except:
            self.rollback()
            raise

    def __enter__(self):
        self.begin()
        
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.Exc = (exc_type, exc_value, traceback)
            self.rollback()
        else:
            self.commit()
