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
from antsibull_docs_parser.parser import parse, Context
from antsibull_docs_parser.rst import to_rst_plain
from antsibull_docs_parser.md import to_md

try:
    from ._version_scm import version
except ImportError:
    version = "unknown"


VALID_FORMATS = ["md", "rst", "other"]
DEFAULT_FORMAT = "md"
DEFAULT_OUT_DIR = "."
DEFAULT_OUT_DIR_STR = \
    "Current directory" if DEFAULT_OUT_DIR == "." else DEFAULT_OUT_DIR


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


def parse_args(argv):
    """
    Parses the command line arguments.
    """

    prog = os.path.basename(sys.argv[0])
    usage = "%(prog)s [options] [SPEC_FILE ...]"
    desc = ("Extract documentation from a spec file in YAML format "
            "(such as <role>/meta/argument_specs.yml for roles) using a "
            "Jinja2 template file. Template files for RST and Markdown output "
            "formats for roles are included. For playbooks and for other "
            "output formats, templates can be provided by the user.")
    epilog = ""

    parser = argparse.ArgumentParser(
        prog=prog, usage=usage, description=desc, epilog=epilog, add_help=True)

    parser.add_argument(
        "--out-dir", "-o", metavar="DIR", default=DEFAULT_OUT_DIR,
        help="path name of the output directory. "
        f"Default: {DEFAULT_OUT_DIR_STR}.")

    parser.add_argument(
        "spec_file", metavar="SPEC_FILE", nargs="*",
        help="path name of the spec file that documents the role or playbook. "
        "Zero or more spec files can be specified.")

    parser.add_argument(
        "--name", "-n", metavar="NAME", default=None,
        help="name of the Ansible role or playbook. When this option is used, "
        "only one spec file may be specified. "
        "Default: Derived from path name of the spec file: "
        "<name>/meta/argument_specs.yml.")

    parser.add_argument(
        "--format", "-f", metavar="FORMAT", choices=VALID_FORMATS,
        default=DEFAULT_FORMAT,
        help="format of the output file(s). "
        f"Valid values: {', '.join(VALID_FORMATS)}. "
        f"Default: {DEFAULT_FORMAT}.")

    parser.add_argument(
        "--ext", metavar="EXT", default=None,
        help="file extension (suffix) of the output file(s). "
        "Default: For formats 'md' and 'rst', the format. Required for "
        "format 'other'.")

    parser.add_argument(
        "--template", "-t", metavar="FILE", default=None,
        help="path name of the Jinja2 template file. See --help-template for "
        "details. "
        "Default: For roles, the built-in templates for formats 'md' and "
        "'rst'. Required for non-roles and for format 'other'.")

    parser.add_argument(
        "--version", action=HelpVersionAction, nargs=0,
        help="show the version of the program and exit.")

    parser.add_argument(
        "--help-template", action=HelpTemplateAction, nargs=0,
        help="show help for the template file and exit.")

    args = parser.parse_args(argv)

    if args.name and len(args.spec_file) > 1:
        parser.error(
            "when the --name option is used, only one spec file may be "
            "specified.")

    if args.format == "other" and not args.ext:
        parser.error(
            "when format 'other' is specified, the --ext option is "
            "required.")

    if args.format == "other" and not args.template:
        parser.error(
            "when format 'other' is specified, the --template option is "
            "required.")

    return args


def print_version():
    """
    Print the version of this program.
    """
    print(f"version: {version}")


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
    """
    Indicates a runtime error.
    """
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


def to_rst_filter(text):
    """
    Jinja2 filter that converts text to RST, resolving Ansible specific
    constructs such as "C(...)".
    """
    return to_rst_plain(parse(text, Context()))


def to_md_filter(text):
    """
    Jinja2 filter that converts text to Markdown, resolving Ansible specific
    constructs such as "C(...)".
    """
    return to_md(parse(text, Context()))


def create_output_files(args):
    """
    Create the output files for the specified spec files.
    """

    spec_files = args.spec_file
    name = args.name

    out_format = args.format
    if args.ext:
        out_ext = args.ext.strip(".")
    else:
        # Arg check ensured that format is not 'other'
        out_ext = out_format
    out_dir = args.out_dir

    if args.template:
        template_file = args.template
    else:
        # Arg check ensured that format is not 'other'
        my_dir = os.path.dirname(__file__)
        template_file = os.path.join(
            my_dir, "templates", f"role.{out_format}.j2")

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

    # Add Jinja2 filters
    env.filters["to_rst"] = to_rst_filter
    env.filters["to_md"] = to_md_filter

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
    Entry point for the program.
    """

    args = parse_args(sys.argv[1:])

    try:
        create_output_files(args)
    except Error as exc:
        print(f"Error: {exc}")
        return 1

    return 0
