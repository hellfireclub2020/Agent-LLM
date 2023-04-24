import importlib
import os
from inspect import signature, Parameter
from Config import Config

class Commands:
    def __init__(self, agent_name: str = "default", load_commands_flag: bool = True):
        self.CFG = Config(agent_name)
        self.commands = self.load_commands() if load_commands_flag else []
        if agent_name == "undefined":
            agent_name = "default"
        self.agent_name = self.CFG.AGENT_NAME if agent_name is None else agent_name
        self.agent_folder = self.CFG.create_agent_folder(self.agent_name)
        self.agent_config_file = self.CFG.create_agent_config_file(self.agent_folder)

        self.agent_config = self.CFG.load_agent_config(self.agent_name)
        self.available_commands = self.get_available_commands()
        
    def get_available_commands(self):
        available_commands = []
        for command in self.commands:
            friendly_name, command_name, command_args = command
            if "commands" in self.agent_config and friendly_name in self.agent_config["commands"]:
                if self.agent_config["commands"][friendly_name] in ["true", True]:
                    # Add command to list of commands to return
                    available_commands.append({"friendly_name": friendly_name, "name": command_name, "args": command_args, "enabled": True})
                else:
                    available_commands.append({"friendly_name": friendly_name, "name": command_name, "args": command_args, "enabled": False})
        return available_commands

    def load_commands(self):
        commands = []
        command_files = self.CFG.load_command_files()
        for command_file in command_files:    
            module_name = os.path.splitext(os.path.basename(command_file))[0]
            module = importlib.import_module(f"commands.{module_name}")
            if issubclass(getattr(module, module_name), Commands):
                command_class = getattr(module, module_name)()
                if hasattr(command_class, 'commands'):
                    for command_name, command_function in command_class.commands.items():
                        params = self.get_command_params(command_function)
                        commands.append((command_name, command_function.__name__, params))
        return commands if commands else []

    def get_command_params(self, func):
        sig = signature(func)
        return {
            name: None if param.default == Parameter.empty else param.default
            for name, param in sig.parameters.items()
        }

    def find_command(self, command_name: str):
        for name, function_name, params in self.commands:
            if name == command_name:
                command_function = getattr(self, function_name)
                return command_function, params
        return None, None

    def get_commands_list(self):
        self.commands = self.load_commands(agent_name=self.agent_name)
        return [command_name for command_name, _, _ in self.commands]
    
    def execute_command(self, command_name: str, command_args: dict):
        command_function, params = self.find_command(command_name)
        if command_function is None:
            return False
        for name, value in command_args.items():
            if name in params:
                params[name] = value
        return command_function(**params)