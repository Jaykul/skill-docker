from opsdroid.matchers import match_regex
from voluptuous import Required
from tempfile import TemporaryDirectory, NamedTemporaryFile
import docker, asyncio, re, os

CONFIG_SCHEMA = {
    Required("containers", {
        "PowerShell": {
            "names": ("pwsh","powershell"),
            "extension": ".ps1",
            "container": "mcr.microsoft.com/powershell",
            "command": 'pwsh -NoLogo -NonInteractive -NoProfile -File {}'
        },
        "Python": {
            "names": ("python","py"),
            "extension": ".py",
            "container": "python",
            "command": 'python {}'
        }
    }): dict
}

CLIENT = docker.DockerClient(base_url='unix:///var/run/docker.sock')
# CLIENT = docker.from_env()

@match_regex(r'(?m)run this:.*[\r\n]+```(?P<lang>.+)[\r\n]+(?P<code>(.*\n?)+)[\r\n]+```', case_sensitive=False)
async def run_this(opsdroid, config, message):
    lang = message.regex.group('lang')
    language = [language for language in config["containers"].values() if(lang in language["names"])]

    if (language == None):
        await message.respond(f"Sorry, I don't know {lang}")
        return

    language = language[0]
    container = language["container"]
    code = message.regex.group('code')

    if (code == None or len(code) == 0):
        await message.respond(f"Wait, run what?")
        return

    await message.respond(f"<p>Let me try that in <code>{container}</code></p>")
    with TemporaryDirectory() as working:
        codefile = NamedTemporaryFile(mode='w+t', suffix=language["extension"], dir=working, delete=False)
        codefile.writelines(code)
        codefile.close()
        head, filename = os.path.split(codefile.name)
        print("Container name: {}".format(container))
        print("Working directory: {}".format(working))
        print("File name: {}".format(codefile.name))
        try:
            result = CLIENT.containers.run(
                container,
                language["command"].format('/mnt/code/{}'.format(filename)),
                auto_remove = True,
                volumes = {working: { 'bind': '/mnt/code', 'mode':'ro'}})
            result = result.decode("utf8")
            result = re.compile(r'\\n').sub("<br/>\n",result)
            await message.respond("<pre>{}</pre>".format(result))
        except docker.errors.ContainerError:
            await message.respond("An error occurred. Sorry, but there's no error logging yet.")

# class Message:

#     def __init__(self, text):
#         import re
#         rr = re.compile(r'(?m)run this:.*[\r\n]+```(?P<lang>.*)[\r\n]+(?P<code>(.*\n)+)```', re.IGNORECASE)
#         self.text = text
#         print("Message: \n  pattern: {}\n  text: {}".format(rr, text))
#         self.regex = rr.match(text)

#     async def respond(self, response):
#         print(str(response))

# class Config:
#     def __init__(self, dict):
#         self.containers = dict


# if __name__ == "__main__":
#     import sys
#     message = Message(sys.argv[1])
#     asyncio.run(run_this(
#         None,
#         Config({
#             "PowerShell": {
#                 "names": ("pwsh","powershell"),
#                 "extension": ".ps1",
#                 "container": "mcr.microsoft.com/powershell",
#                 "command": 'pwsh -NoLogo -NonInteractive -NoProfile -File {}'
#             }
#         }),
#         message))