import configparser


class CaseSensitiveConfigParser(configparser.ConfigParser):
    def __init__(self, **kwargs):
        # Set interpolation=None by default, but allow it to be overridden
        kwargs.setdefault('interpolation', None)
        super().__init__(**kwargs)
    
    def optionxform(self, optionstr):
        return optionstr


class Config:
    def __init__(self):
        self.config = CaseSensitiveConfigParser()
        self.config.read('config.ini')
        self.config.read('config.secrets.ini')

    def __getitem__(self, item):
        return self.config[item]

    def __setitem__(self, key, value):
        self.config[key] = value
        
    def get_keys(self, section: str):
        if section not in self.config:
            return []
        
        return list(self.config[section].keys())
    
# Config       
config = Config()
