import importlib
import os
import inspect

def load_strategies():
    strategies = {}


    strategy_folder = os.path.dirname(__file__)

    for file in os.listdir(strategy_folder):

        if file.endswith(".py") and file not in ["__init__.py", "registry.py"]:
        
            module_name = file[:-3]  # remove .py
            module = importlib.import_module(f"strategy.{module_name}")

        # find class inside module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if "Strategy" in name:
                    strategies[name] = obj

    return strategies

