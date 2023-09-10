import gradio as gr
import os


class GradioInterface:
    @staticmethod
    def create_gradio_interface(commands: dict):
        """
        Create a Gradio interface for the GeniusCtl CLI.

        Parameters:
        - commands (dict): A dictionary containing command groups and their details.
        """

        def gr_run(selected_command: str, **kwargs) -> str:
            print(f"Executing: {selected_command} with parameters {kwargs}")
            return "Execution completed 🎉"

        with gr.Blocks(
            css=os.path.join(os.path.dirname(__file__), "theme.css"),
            html=os.path.join(os.path.dirname(__file__), "banner.html"),
        ) as app:
            for cmd_group, cmd_list in commands.items():
                if isinstance(cmd_list, list):  # Check if cmd_list is a list
                    with gr.Tab(f"{cmd_group} 🛠"):
                        for cmd_info in cmd_list:
                            if isinstance(cmd_info, dict):  # Check if cmd_info is a dictionary
                                command = cmd_info.get("command", "Unknown Command")
                                params = cmd_info.get("params", [])

                                with gr.Row():
                                    with gr.Column():
                                        # Generate Markdown table for command and its parameters
                                        table_header = "| Parameter | Description |\n|-----------|-------------|"
                                        table_rows = "\n".join([f"| {p['name']} | {p['help_text']} |" for p in params])
                                        table = f"{table_header}\n{table_rows}"

                                        gr.Markdown(
                                            f"""
## 🚀 Command: `genius {cmd_group} {command if 'Unknown' not in command else ''}`

### 📝 Parameters
{table}
                                            """
                                        )
                                    with gr.Column():
                                        # Create input fields for parameters
                                        param_fields = {}
                                        for param in params:
                                            param_name = param["name"]
                                            param_fields[param_name] = gr.Textbox(
                                                label=f"{param_name}", info=param["help_text"]
                                            )

                                        # Create a button to execute the command
                                        btn = gr.Button(f"🧠 {command}", variant="primary")

                                        # Attach event listener to button
                                        # Uncomment the line below when you're ready to attach the event
                                        # btn.click(lambda _, args: gr_run(command, **args), inputs=param_fields)
                else:
                    gr.Text(f"{cmd_group}: {cmd_list}")

        app.launch()
