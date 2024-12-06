import tempfile
from autogen import config_list_from_json
from autogen import AssistantAgent, UserProxyAgent
from autogen.coding import DockerCommandLineCodeExecutor

config_list = config_list_from_json(
        env_or_file="config.json",
        file_location="."
    )

temp_dir = tempfile.TemporaryDirectory()

with DockerCommandLineCodeExecutor(
        image="code-executor:v1",
        timeout=10,
        work_dir=temp_dir.name
    ) as code_executor:

    assistant = AssistantAgent("assistant",
                               system_message="""
You have been given coding capability to solve tasks using Python code, shell scripts & the kubectl command line tool.
In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.

1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.

Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must indicate the script type in the code block. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
""",
                               llm_config={
                                   "config_list": config_list
                               }
                )

    user_proxy = UserProxyAgent("user_proxy",
                                code_execution_config={
                                    "executor": code_executor
                                },
                                )

    chat_result = user_proxy.initiate_chat(
        assistant,
        message="Ask me questions about your AKS cluster. Type 'exit' to quit\n",
    )
