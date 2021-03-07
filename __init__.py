from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

from voluptuous import Required, All, Length, Range
from tempfile import TemporaryDirectory, NamedTemporaryFile
import asyncio, re, os, traceback, subprocess
CONFIG_SCHEMA = {
    Required("volume"): All(str, Length(min=1)),
    Required("workdir"): All(str, Length(min=2)),
    Required("containers"): list
        # All({
        #     Required("language"): All(str),
        #     Required("extension"): str,
        #     Required("container"): str,
        #     Required("command"): All(str)
        # })
}
# , default = [
#         {
#             "language": ["pwsh","powershell"],
#             "extension": ".ps1",
#             "container": "mcr.microsoft.com/powershell",
#             "command": ['pwsh','-NoLogo','-NonInteractive','-NoProfile','-File']
#         },
#         {
#             "language": ["python","py"],
#             "extension": ".py",
#             "container": "python",
#             "command": ['python']
#         }
#     ]
class Docker(Skill):
    # import docker, re
    # CLIENT = docker.from_env()
    # result = CLIENT.containers.run(
    #     container,
    #     #language["command"].format('/code/{}'.format(filename)),
    #     "ls /code",
    #     auto_remove = True,
    #     volumes = {'working': { 'bind': '/code', 'mode':'ro'}}
    #     )
    # result = result.decode("utf8")
    # result = re.compile(r'\\n').sub("<br/>\n",result)

    @match_regex(r'(?m)run this:.*[\r\n]+```(?P<lang>.+)[\r\n]+(?P<code>(.*\n?)+)[\r\n]+```', case_sensitive=False)
    async def run_this(self, opsdroid, config, message):
        languageCode = message.regex.group('lang')
        language = next((lang for lang in config["containers"] if languageCode in lang["language"]), None)

        if (language == None):
            await message.respond(f"Sorry, I don't know {languageCode}")
            return

        container = language["container"]
        code = message.regex.group('code')

        if (code == None or len(code) == 0):
            await message.respond(f"Wait, run what?")
            return

        await message.respond(f"<p>Let me try that in <code>{container}</code></p>")

        # This requires you to have a mounted volume
        codefile = NamedTemporaryFile(mode='w+t', suffix=language["extension"], dir=config["workdir"], delete=False)
        codefile.writelines(code)
        codefile.close()
        volume, workdir = config["volume"].split(":")
        filename = "{}/{}".format(workdir, os.path.split(codefile.name)[1])

        try:
            # This requires you to have "working" volume you can mount
            process = subprocess.run(
                ['docker', 'run', '-v', config["volume"], container] + language["command"] + [filename],
                capture_output=True,
                encoding="UTF8")

            if (process.returncode == 0):
                if (process.stderr):
                    await message.respond("<pre><b>ERROR:</b> {}</pre>".format(process.stderr))
                if (process.stdout):
                    await message.respond("<pre>{}</pre>".format(process.stdout))
            else:
                print("Command exited with {}".format(process.returncode))
                print(process.stderr)

        except docker.errors.ContainerError:
            await message.respond("An error occurred. Sorry, but there's no error logging yet.")
            traceback.print_exc()

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
    #                 "languages": ("pwsh","powershell"),
    #                 "extension": ".ps1",
    #                 "container": "mcr.microsoft.com/powershell",
    #                 "command": 'pwsh -NoLogo -NonInteractive -NoProfile -File {}'
    #             }
    #         }),
    #         message))