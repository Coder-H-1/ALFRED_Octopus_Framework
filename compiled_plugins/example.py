import os
import re

# Module: ExampleBasics

def oct_cmd_framework_greeting(command):
    if 'framework greeting' in command:
        return "Hello! I am responding from the Octopus Framework."
    return None

DYNAMIC_COMMANDS['framework greeting'] = oct_cmd_framework_greeting

def oct_cmd_open_paint(command):
    if 'open paint' in command:
        os.system("start mspaint")
        return "I have opened Microsoft Paint for you, sir."
    return None

DYNAMIC_COMMANDS['open paint'] = oct_cmd_open_paint

def oct_cmd_calculate_square(command):
    if 'calculate square' in command:
        import re

        # Look for numbers in the command

        match = re.search(r'\d+', command)

        if match:

            val = int(match.group())

            return f"The square of {val} is {val * val}"

        else:

            return "Could you please specify the number you want to square?"

    return None

DYNAMIC_COMMANDS['calculate square'] = oct_cmd_calculate_square
