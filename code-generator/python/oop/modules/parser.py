import sys
import argparse
import json
from clang.cindex import TranslationUnit
from clang.cindex import Index


class Parser:

    # clang-c parser data
    _projectPath = None
    _parseFiles = None
    _clangArgs = None
    _clangOptions = None
    outputFile = None

    # context itself
    _parserIndex = None     # common context for files would be parsed by clang
    currentUnit = None

    def __init__(self, cli_args=None):
        self._settings_parser = self.__class__.initialize_argument_parser()
        self.parse_cli_args(cli_args)
        self.initialize_defaults()
        self._parserIndex = Index.create()

    def parse_cli_args(self, cli_args=None):
        if cli_args is None:
            cli_args = sys.argv[1::]
        args = self._settings_parser.parse_args(cli_args)
        settings_file = open(args.jsonPath, mode="r")
        settings_dict = json.load(settings_file)

        self._projectPath = settings_dict["project"]
        self._parseFiles = settings_dict["files"]
        self.outputFile = settings_dict["output"]

        self._clangArgs = []
        self._clangArgs.extend(settings_dict["preprocessor"])
        self._clangArgs.extend(list(map(lambda path: "-I" + self._projectPath + path, settings_dict["-Ipaths"])))
        settings_file.close()

    def initialize_defaults(self):
        self._clangOptions = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | \
                             TranslationUnit.PARSE_SKIP_FUNCTION_BODIES

    def parse_next_file(self):
        for next_file in self._parseFiles:
            self.currentUnit = self._parserIndex.parse(next_file, args=self._clangArgs, options=self._clangOptions)
            yield self.currentUnit

    @staticmethod
    def initialize_argument_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--settings',
                            dest="jsonPath",
                            type=str,
                            default='./settings.json',
                            help="path to .json settings file")
        return parser
