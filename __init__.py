from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

from voluptuous import Required, All, Length, Range
from tempfile import TemporaryDirectory, NamedTemporaryFile
import asyncio, re, os, logging


_LOGGER = logging.getLogger(__name__)
ANSI = re.compile('(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
CONFIG_SCHEMA = {
    Required("volume"): All(str, Length(min=1)),
    Required("workdir"): All(str, Length(min=2)),
    Required("containers"): list
        #### TODO: how do I specify the spec for the containers?
        # All({
        #     Required("language"): All(str),
        #     Required("extension"): str,
        #     Required("container"): str,
        #     Required("command"): All(str)
        # })
}
### TODO: Put back the default settings once the spec is fixed
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
    ###? I would like to be using the Docker "SDK" but it breaks
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

    ###? This is the main method in Skill-Docker
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
        if (language["extension"] == '.ps1'):
            codefile.writelines("$ProgressPreference='SilentlyContinue'\n")
        codefile.writelines(code)
        codefile.close()
        volume, workdir = config["volume"].split(":")
        filename = "{}/{}".format(workdir, os.path.split(codefile.name)[1])
        await self.invoke_docker(message.respond, language["container"], config["volume"], language["command"], filename)

    ###? This is an example of how we can do more interesting things
    @match_regex(r'^(?P<command>get-help [\w-_]+)$', case_sensitive=False)
    async def get_help(self, opsdroid, config, message):
        language = next((lang for lang in config["containers"] if 'powershell' in lang["language"]), None)
        if (language == None):
            await message.respond(f"I couldn't find a 'powershell' container")
            return

        codefile = NamedTemporaryFile(mode='w+t', suffix='.ps1', dir=config["workdir"], delete=False)
        codefile.writelines("$ProgressPreference='SilentlyContinue'\n")
        codefile.writelines(message.regex.group('command'))
        codefile.close()
        volume, workdir = config["volume"].split(":")
        filename = "{}/{}".format(workdir, os.path.split(codefile.name)[1])
        await self.invoke_docker(message.respond, language["container"], config["volume"], language["command"], filename)
        await message.respond(f"Finished execution")

    async def invoke_docker(self, respond, container, volume, command, path):
        import html, traceback, subprocess
        _LOGGER.info(f"<p>Using the <code>{container}</code> container to run <code>{path}</code></p>")

        try:
            await respond(f"<p>Using the <code>{container}</code> container.</p>")
            # This requires you to have "working" volume you can mount
            process = subprocess.run(
                ['docker', 'run', '--rm', '-v', volume, container] + command + [path],
                capture_output=True,
                encoding="UTF8")

            if (process.returncode == 0):
                if (process.stderr):
                    await respond("<b>ERROR:</b><br/><pre>{}</pre>".format(html.escape(ANSI.sub('',process.stderr))))
                if (process.stdout):
                    await respond("<pre>{}</pre>".format(html.escape(ANSI.sub('',process.stdout))))
            else:
                 _LOGGER.info("Command exited with {}".format(process.returncode))
                 _LOGGER.info(process.stderr)

        except:
            await respond("An error occurred. Sorry, but there's no error logging yet.")
            _LOGGER.error(traceback.format_exc())
