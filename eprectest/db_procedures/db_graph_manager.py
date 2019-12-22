# this manager is ment to retreive from a db tree structure
# based on django models

# Let's begin!
# Wish me luck .... because I need that ...


class DbGraphManager():
    """DbGraphManager class
    """
    def __init__(self, some_param=None):
        self.some_param = some_param

    def give_me(self, *args, **kwargs):

        # client = 'client' == args[0] and 'client' or ''
        if args[0] == 'client':
            client = 'client'
            client_id = type(1) == type(int(args[1])) and int(args[1]) or 0
        
        return (client, client_id)

