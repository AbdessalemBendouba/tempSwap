import subprocess
import json
from datetime import date

# This is a placeholder for your real function or variable
# It is defined outside the ToolMaster function
def get_door_status():
    """A placeholder function that returns the door status."""
    return "open"

def ToolMaster(response_buffer, process_instance):
    """
    Analyzes the model's response for a tool call, executes the tool,
    and sends the output back to the model.
    Returns True if a tool call was found and handled, False otherwise.
    """
    try:
        # Find the start and end of the JSON object, which represents the tool call
        start_index = response_buffer.find("{")
        end_index = response_buffer.rfind("}")
        json_string = response_buffer[start_index : end_index + 1]
        
        # Load the JSON string into a dictionary
        tool_call = json.loads(json_string)

        # Check for the "date" tool
        if 'tool' in tool_call and tool_call['tool'] == "date":
            # Execute the tool
            current_date = date.today()
            
            # Format the output to be sent back to the model
            tool_output_string = f"\n<|tool_output|>\n{{"date": "{current_date}"}}\n<|im_end|>\n"
            
            # Send the tool's output back to the model
            process_instance.stdin.write(tool_output_string.encode('utf-8'))
            process_instance.stdin.flush()
            
            return True
        
        # Check for the "is door open" tool
        elif 'tool' in tool_call and tool_call['tool'] == "is door open":
            # Execute the tool
            status = get_door_status()
            
            # Format the output to be sent back to the model
            tool_output_string = f"\n<|tool_output|>\n{{"status": "{status}"}}\n<|im_end|>\n"
            
            # Send the tool's output back to the model
            process_instance.stdin.write(tool_output_string.encode('utf-8'))
            process_instance.stdin.flush()
            
            return True
        
        # If the tool name is not recognized
        else:
            tool_output_string = f"\n<|tool_output|>\nInvalid tool call. Try again.\n<|im_end|>\n"
            process_instance.stdin.write(tool_output_string.encode('utf-8'))
            process_instance.stdin.flush()
            
            return True

    except (ValueError, IndexError):
        # This block handles errors if the response did not contain valid JSON
        return False

# Command to launch the llama.cpp process
command = [
    './path/to/llama-cli',
    '-m', './path/to/Qwen3',
    '--color',
    '-n', '-1',
    '-t', '3',
    '--interactive-first',
    '--system-prompt', 'You are an intelligent smart assistant. Here are your tool capabilities: {"tool": "date", "description": "Returns the current date."}, {"tool": "is door open", "description": "Returns the status of the door (open or closed)."}'
]

# Launch the process and get the Popen object for communication
# We pass the ModelInference object to the ToolMaster function
ModelInference = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

# Main conversational loop
while True:
    # 1. Get user input
    user_prompt = input("> ")
    
    # Check for conversation termination
    if user_prompt.lower() in ["exit", "quit"]:
        break
    
    # 2. Write the user's prompt to the model's stdin
    ModelInference.stdin.write((user_prompt + "\n").encode('utf-8'))
    ModelInference.stdin.flush()

    # 3. Read the model's response line by line in a "stop-and-go" loop
    while True:
        response_buffer = ""
        # The inner loop reads until the model's response is complete
        while True:
            line = ModelInference.stdout.readline().decode('utf-8')
            if not line:
                break
            
            # As per your design choice, we print the raw output to show the process
            print(line, end="", flush=True)
            
            response_buffer += line
        
            if "<|im_end|>" in line:
                response_buffer = response_buffer.replace("<|im_end|>", "").strip()
                break

        # 4. Check the full response for a tool call
        is_tool_call_handled = ToolMaster(response_buffer, ModelInference)
        
        # If a tool call was handled, the model will generate a new response.
        # We use 'continue' to go back to the top of the loop and read that new response.
        if is_tool_call_handled:
            continue
        
        # If no tool was called, the conversation turn is complete.
        else:
            break

# 5. Clean up when the conversation ends
ModelInference.stdin.close()
ModelInference.terminate()
print("\nConversation ended. Goodbye!")
