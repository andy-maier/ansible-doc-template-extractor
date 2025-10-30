#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Ansible Documentation Template Extractor
"""

import os
import argparse
import sys
import jinja2
import yaml
import jinja2_ansible_filters

from ._version import __version__


DEFAULT_EXT = "md"


class HelpTemplateAction(argparse.Action):
    "argparse action for --help-template option"

    def __call__(self, parser, namespace, values, option_string=None):
        print_help_template()
        parser.exit()  # stops immediately (like --help)


class HelpVersionAction(argparse.Action):
    "argparse action for --version option"

    def __call__(self, parser, namespace, values, option_string=None):
        print_version()
        parser.exit()  # stops immediately (like --help)


def parse_args(args):
    """
    Parses the CLI arguments.
    """

    prog = os.path.basename(sys.argv[0])
    usage = "%(prog)s [options] OUT_DIR SPEC_FILE [SPEC_FILE ...]"
    desc = ("Extract documentation from an Ansible argument_specs.yml file "
            "(such as meta/argument_specs.yml in roles) using a Jinja2 "
            "template file.")
    epilog = ""

    parser = argparse.ArgumentParser(
        prog=prog, usage=usage, description=desc, epilog=epilog, add_help=True)

    parser.add_argument(
        "out_dir", metavar="OUT_DIR",
        help="path name of output directory. (required)")

    parser.add_argument(
        "spec_file", metavar="SPEC_FILE", nargs="*",
        help="path name of the Ansible argument_specs.yml file. "
        "Zero or more can be specified.")

    parser.add_argument(
        "--ext", metavar="EXT", default=DEFAULT_EXT,
        help="file extension (suffix) for output file(s). "
        f"Default: {DEFAULT_EXT}")

    parser.add_argument(
        "--name", metavar="NAME", default=None,
        help="name of the Ansible role or playbook. When this option is "
        "used, only one spec file may be specified. "
        "Default: Derived from path name of spec file: "
        "<role>/meta/argument_specs.yml")

    parser.add_argument(
        "--template", metavar="TEMPLATE_FILE", required=True,
        help="path name of the Jinja2 template file. See --help-template for "
        "details. (required)")

    parser.add_argument(
        "--version", action=HelpVersionAction, nargs=0,
        help="show the version of the program and exit")

    parser.add_argument(
        "--help-template", action=HelpTemplateAction, nargs=0,
        help="show help for the template file and exit")

    return parser.parse_args(args)


def print_version():
    """
    Print the version of this program.
    """
    # pylint: disable=no-member
    print(f"version: {__version__}")


def print_help_template():
    """
    Print help for the Jinja2 template file.
    """
    print("""
Help for Jinja2 template file

Jinja2 template files are described in https://jinja.palletsprojects.com/en/stable/templates/

This program sets up the following variables for use by the template:

* name (str): Name of the Ansible role or playbook.

* spec_file_name (str): Path name of Ansible spec file.

* spec_file_dict (dict): Content of Ansible spec file.

""")  # noqa: E501


class Error(Exception):
    "Error class for this program"
    pass


def template_error_msg(filename, exc):
    """
    Return an error message for printing, from a Jinja2 TemplateError exception.
    """
    assert isinstance(exc, jinja2.TemplateError)
    if hasattr(exc, 'lineno'):
        line_txt = f", line {exc.lineno}"
    else:
        line_txt = ""
    return (f"Error: Could not render template file {filename}{line_txt}: "
            f"{exc.__class__.__name__}: {exc}")


def create_output_files(template_file, name, spec_files, out_dir, out_ext):
    """
    Create the output file for one spec file.
    """

    extensions = [
        jinja2_ansible_filters.AnsibleCoreFiltersExtension,
        'jinja2.ext.do'
    ]

    template_dir = os.path.dirname(template_file)
    if template_dir == "":
        template_dir = "."
    template_name = os.path.basename(template_file)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        trim_blocks=True, lstrip_blocks=True,
        autoescape=True, extensions=extensions)

    # Let undefined variables fail rendering
    env.undefined = jinja2.StrictUndefined

    print(f"Loading template file: {template_file}")
    try:
        template = env.get_template(template_name)
    except jinja2.TemplateNotFound:
        raise Error(
            f"Could not find template name {template_name} in search path: "
            f"{', '.join(env.loader.searchpath)}")
    except jinja2.TemplateSyntaxError as exc:
        raise Error(
            f"Syntax error in template file {template_file}, "
            f"line {exc.lineno}: {exc.message}")

    for spec_file in spec_files:
        create_output_file(
            template, template_file, name, spec_file, out_dir, out_ext)


def create_output_file(
        template, template_file, name, spec_file, out_dir, out_ext):
    """
    Create the output file for one spec file.
    """

    if name is None:
        # We assume the role directory structure:
        # .../<role>/meta/argument_specs.yml
        spec_file_abs = os.path.abspath(spec_file)
        role_dir = os.path.dirname(spec_file_abs)
        role_dir = os.path.dirname(role_dir)
        name = os.path.basename(role_dir)
    print(f"Ansible name: {name}")

    out_ext = out_ext.strip(".")
    out_file = os.path.join(out_dir, f"{name}.{out_ext}")

    print(f"Loading spec file: {spec_file}")
    try:
        with open(spec_file, 'r', encoding='utf-8') as fp:
            spec_file_dict = yaml.safe_load(fp)
    except (IOError, yaml.error.YAMLError) as exc:
        raise Error(
            f"Cannot load spec file {spec_file}: "
            f"{exc.__class__.__name__}: {exc}")

    try:
        data = template.render(
            name=name,
            spec_file_name=spec_file,
            spec_file_dict=spec_file_dict)
    except jinja2.TemplateError as exc:
        raise Error(template_error_msg(template_file, exc))

    if not data.endswith('\n'):
        data += '\n'
    try:
        with open(out_file, 'w', encoding='utf-8') as fp:
            fp.write(data)
    except IOError as exc:
        raise Error(
            f"Cannot write output file {out_file}: {exc}")

    print(f"Created output file: {out_file}")


def main():
    """
    Main function for the script.
    """

    args = parse_args(sys.argv[1:])

    if args.name and len(args.spec_file) > 1:
        print("Error: When the --name option is used, only one spec file "
              "may be specified.")
        return 2

    try:
        create_output_files(
            args.template, args.name, args.spec_file, args.out_dir, args.ext)
    except Error as exc:
        print(f"Error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
