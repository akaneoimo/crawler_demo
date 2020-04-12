import time
import datetime
import logging
import traceback
import os, sys
import re
import random
import json
import inspect
from collections import defaultdict


def now_as_str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def brief_path(verbose_path):
    for env_var in sys.path:
        stripped = verbose_path.replace(env_var, '')
        if stripped != verbose_path:
            return stripped.lstrip('/\\')
    return stripped


class Dict(defaultdict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs) 
        
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value
    
    def print(self, indent=4, space=None, outer=True):
        newline = '\n' if indent else ''
        space = space or indent
        print(f"{{{newline}{' '*space}", end='')
        for i, (k, v) in enumerate(self.items()):
            print(f"'{k}': ", end='')
            if isinstance(v, Dict):
                v.print(indent, space+indent, False)
            else:
                print(repr(v), end='')
            if i < len(self) - 1:
                print(f", {newline}{' '*space}", end='')
        print(f"{newline}{' '*(space-indent)}}}", end='\n' if outer else '')
    
    indent = 0
    newline = '\n' if indent else ''
    def __str__(self, space=None):
        space = space or self.indent
        return (
            f"{{{self.newline}{' '*space}"
            f"""{f", {self.newline}{' '*space}".join([f"'{k}': {v.__str__(space+self.indent) if isinstance(v, Dict) else repr(v)}" for k, v in self.items()])}"""
            f"{self.newline}{' '*(space-self.indent)}}}"
        )

    def update(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = Dict(v) if isinstance(v, dict) else v 
            else:
                raise ValueError(f'arg should be a dict')
            for k, v in kwargs.items():
                self[k] = Dict(v) if isinstance(v, dict) else v

    def _strict_check(self, **kwargs):
        for k, v in kwargs.items():
            if self.get(k) is None:
                raise KeyError(k)
            if isinstance(self[k], dict):
                if not isinstance(v, dict):
                    raise TypeError(v)
                else:
                    self[k].update_strict(v)
            if not isinstance(self[k], dict):
                if isinstance(v, dict):
                    raise TypeError(v)
                else:
                    self[k] = v
    
    def update_strict(self, *args, **kwargs):
        """
        use `update_strict` to make default values remain
        this will make sure that custom dict won't have the key which the default config does not have, or value types do not match
        """
        for arg in args:
            if isinstance(arg, dict):
                self._strict_check(**arg)
            else:
                raise ValueError('arg should be a dict')
        
        for k, v in kwargs.items():
            self._strict_check(**kwargs)

    def update_deep(self, *args, **kwargs):
        """
        almost the same with `update_strict` to make default values remain
        but allow that custom dict have the key which the default config does not have, and value types can do not match
        """
        for arg in args:
            if isinstance(arg, dict):
                self._deep_check(**arg)
            else:
                raise ValueError('arg should be a dict')
        
        for k, v in kwargs.items():
            self._deep_check(**kwargs)

    def _deep_check(self, **kwargs):
        for k, v in kwargs.items():
            if self.get(k) is None:
                self[k] = v
            else:
                if not isinstance(v, dict):
                    self[k] = v
                else:
                    self[k].update_deep(v)

def infofilt(record):
    return record.levelname == 'INFO'

def errorfilt(record):
    return record.levelname == 'ERROR'


class Logger:
    """
    name: name of logger
    filename: if specified, log will be written into the file
    silent: no output at terminal if `True`
    """
    default_level = 'debug'
    def level_filter(level):
        return lambda record: record.levelname == level.upper()

    def __init__(self, name=__file__, level=default_level, filename=None, silent=False, datefmt='%Y-%m-%d %H:%M:%S'):
        """
        name: name of logger
        filename: if specified, log will be written into the file
        silent: no output at terminal if `True`
        """
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt=datefmt)
        self.logger = logging.getLogger(name)
        self.logger.setLevel('DEBUG')

        if isinstance(filename, str):
            self.add_handler(filename, level=level)
        elif isinstance(filename, dict):
            for level, name in filename.items():
                # this will not work, `level` below is not that `level` above
                # self.add_handler(filename=name, level_filter=lambda record: record.levelname == level.upper())
                self.add_handler(filename=name, level_filter=self.__class__.level_filter(level))
        if not silent:
            self.add_handler()

    def add_handler(self, filename=None, level=default_level, level_filter=None):
        if type(filename) == str and filename:
            handler = logging.FileHandler(filename, encoding='utf-8')
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(self.formatter)
        if level_filter:
            handler.addFilter(level_filter)
        else:
            handler.setLevel(level.upper())
        self.logger.addHandler(handler)
    
    def error(self, message='', exc_info=None):
        """
        message: error message
        exc_info: tuple returned by sys.exc_info()
        """
        if exc_info:
            exc_type, exc_value, exc_traceback = exc_info
            additional = f'[{message}] ' if message else ''
            self.logger.error(additional + ' => '.join([f'"{brief_path(fs.filename)}", {fs.lineno}: "{fs.line}"' for fs in traceback.extract_tb(exc_traceback)]) + f' [{exc_type.__name__}: {exc_value}]')
        else:
            self.logger.error(message)
    
    def info(self, message=''):
        self.logger.info(message)
    
    def warning(self, message=''):
        self.logger.warning(message)

    def debug(self, message=''):
        self.logger.debug(message)
