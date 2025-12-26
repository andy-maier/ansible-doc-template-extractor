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
import re
import argparse
import sys
import pathlib
import json

import jinja2
import yaml
import jsonschema
import jinja2_ansible_filters
from antsibull_docs_parser.parser import parse, Context
from antsibull_docs_parser.rst import to_rst
from antsibull_docs_parser.md import to_md

try:
    from ._version_scm import version
except ImportError:
    version = "unknown"


VALID_TYPES = ["role", "playbook", "other"]
VALID_FORMATS = ["rst", "md", "other"]
DEFAULT_FORMAT = "rst"
DEFAULT_OUT_DIR = "."
DEFAULT_OUT_DIR_STR = \
    "Current directory" if DEFAULT_OUT_DIR == "." else DEFAULT_OUT_DIR

LIST_STARTERS = ("*", "-", "#")

# Directory separator related patterns.
# Note: On Windows, the separator can be '/' or '\', so we need to allow for
# both and cannot just use os.sep.
SEP = r"[\/\\]"
NO_SEP = r"[^\/\\]"

# Patterns for spec file names.
# They are used for detecting the spec type, and for parsing the Ansible role
# or playbook name (in match item 2).
ROLE_SPEC_FILE_PATTERN = re.compile(
    rf"(^|{SEP})({NO_SEP}+){SEP}meta{SEP}argument_specs\.yml$")
PLAYBOOK_SPEC_FILE_PATTERN = re.compile(
    rf"(^|{SEP})({NO_SEP}+)\.meta\.yml$")


class HelpTemplateAction(argparse.Action):
    "argparse action for --help-template option"

    def __call__(self, parser, namespace, values, option_string=None):
        print_help_template()
        parser.exit()  # stops immediately (like --help)


class HelpPlaybookSpecAction(argparse.Action):
    "argparse action for --help-playbook-spec option"

    def __call__(self, parser, namespace, values, option_string=None):
        print_help_playbook_spec()
        parser.exit()  # stops immediately (like --help)


class HelpVersionAction(argparse.Action):
    "argparse action for --version option"

    def __call__(self, parser, namespace, values, option_string=None):
        print_version()
        parser.exit()  # stops immediately (like --help)


def create_arg_parser(prog):
    """
    Creates and returns the command line argument parser.
    """

    usage = "%(prog)s [options] [SPEC_FILE ...]"
    desc = ("Extract documentation from a spec file in YAML format using a "
            "Jinja2 template file. For Ansible roles, the Ansible-defined "
            "format for <role>/meta/argument_specs.yml files is used. For "
            "Ansible playbooks, this project has defined a spec file format "
            "with files named <playbook>.meta.yml. Template files for RST and "
            "Markdown output formats for roles and playbooks are included in "
            "this program. For other types of Ansible items or other spec file "
            "formats or other output formats, template files can be provided "
            "by the user.")
    epilog = ""

    parser = argparse.ArgumentParser(
        prog=prog, usage=usage, description=desc, epilog=epilog, add_help=True)

    parser.add_argument(
        "spec_file", metavar="SPEC_FILE", nargs="*",
        help="path name of the spec file that documents the role or playbook. "
        "Zero or more spec files can be specified.")

    parser.add_argument(
        "--out-dir", "-o", metavar="DIR", default=DEFAULT_OUT_DIR,
        help="path name of the output directory. "
        f"Optional; default: {DEFAULT_OUT_DIR_STR}.")

    parser.add_argument(
        "--format", "-f", metavar="FORMAT", choices=VALID_FORMATS,
        default=DEFAULT_FORMAT,
        help="format of the output file(s). "
        f"Valid values: {', '.join(VALID_FORMATS)}. "
        f"Optional; default: {DEFAULT_FORMAT}.")

    parser.add_argument(
        "--type", "-t", metavar="TYPE", choices=VALID_TYPES, default=None,
        help="type of the Ansible item. "
        f"Valid values: {', '.join(VALID_TYPES)}. "
        "Optional; default is detected from path name of spec file: "
        "<name>/meta/argument_specs.yml is detected as 'role'; "
        "<name>.meta.yml is detected as 'playbook'; anything else is 'other'.")

    parser.add_argument(
        "--name", metavar="NAME", default=None,
        help="name of the Ansible role or playbook. "
        "This option is only needed if the spec files do not follow the "
        "naming convention described for option --type. "
        "When this option is used, only one spec file may be specified. "
        "Optional for known types; default is detected from path name of spec "
        "file. Required for type 'other'.")

    parser.add_argument(
        "--ext", metavar="EXT", default=None,
        help="file extension (suffix) of the output file(s). "
        "Optional for known formats; default is the --format value. Required "
        "for format 'other'.")

    parser.add_argument(
        "--template", metavar="FILE", default=None,
        help="path name of the Jinja2 template file. "
        "See --help-template for details. "
        "Optional for known types and formats; default is the corresponding "
        "built-in template. Required for type 'other' or for format 'other'.")

    parser.add_argument(
        "--schema", metavar="FILE", default=None,
        help="path name of a JSON schema file in YAML format that validates "
        "the spec file. Optional. Default is to validate types 'role' and "
        "'playbook' with built-in schema files, and not to validate other "
        "types. An empty string can be used to turn off schema validation.")

    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="be more verbose while processing.")

    parser.add_argument(
        "--version", action=HelpVersionAction, nargs=0,
        help="show the version of the program and exit.")

    parser.add_argument(
        "--help-template", action=HelpTemplateAction, nargs=0,
        help="show help for the template files and exit.")

    parser.add_argument(
        "--help-playbook-spec", action=HelpPlaybookSpecAction, nargs=0,
        help="show help for the playbook spec file format and exit.")

    return parser


def print_version():
    """
    Print the version of this program.
    """
    print(f"version: {version}")


def print_help_template():
    """
    Print help for the Jinja2 template files.
    """
    print("""
Help for Jinja2 template files

The template files for roles for the Markdown and RST formats are included with
this program.

You can write your own templates for any other format or for Ansible playbooks
(or other Ansible items).

The following rules apply when writing templates:

* The templating language is Jinja2 (see
  https://jinja.palletsprojects.com/en/stable/templates/).

* The following Jinja2 extensions are enabled for use by the template:

  - The filters provided by the jinja2-ansible-filters package
    (see https://pypi.org/project/jinja2-ansible-filters for the list of filters and
    https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html#filter-plugins
    for a description of all built-in Ansible filters).

  - jinja2.ext.do Expression Statement (see
    https://jinja.palletsprojects.com/en/stable/extensions/#expression-statement)

  - The `to_rst` and `to_md` filters that are provided by this program. They
    convert text to RST and Markdown, respectively. They handle formatting and
    resolve Ansible markup such as "C(...)".

* The following Jinja2 variables are set for use by the template:

  - name (str): Name of the Ansible role or playbook.

  - spec_file_name (str): Path name of the spec file.

  - spec_file_dict (dict): Content of the spec file.

""")  # noqa: E501


def print_help_playbook_spec():
    """
    Print help for the format of playbook spec files.
    """
    print("""
Help for the format of Ansible playbook spec files.

Note: This spec file format is preliminary at this point and can still change.

This project has defined a format for spec files that document Ansible
playbooks:

playbook:
  name: <Playbook name>
  short_description: <Playbook title>
  description:
    <string or list of strings with playbook descriptions>
  requirements:
    <string or list of strings with playbook requirements>
  version_added: <If the playbook was added to Ansible, the Ansible version>
  author:
    <string or list of strings with playbook author names>
  examples:
    - description: <string or list of strings with example description>
      command: <example ansible-playbook command>
  input_schema:
    <A JSON schema that describes a single input variable of the playbook>
  output_schema:
    <A JSON schema that describes a single output variable for success>

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
    return (f"Could not render template file {filename}{line_txt}: "
            f"{exc.__class__.__name__}: {exc}")


def normalized_text(text):
    """
    Return normalized text by:
    * Inserting a blank line before a bullet line if the previous line is not
      empty.
    * Inserting a blank line after a bullet line if the next line is not empty
      and not a bullet line
    """
    lines = text.splitlines()
    normalized_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Insert blank line before a bullet line
        if (stripped.startswith(LIST_STARTERS) and i > 0
                and lines[i - 1].strip() != ""):
            normalized_lines.append("")
        normalized_lines.append(line)

        # Insert blank line after a bullet line
        if (stripped.startswith(LIST_STARTERS) and i + 1 < len(lines)
                and not lines[i + 1].strip().startswith(LIST_STARTERS)
                and lines[i + 1].strip() != ""):
            normalized_lines.append("")

    normalized_str = "\n".join(normalized_lines)
    return normalized_str


def to_rst_filter(text):
    """
    Jinja2 filter that converts text to RST, resolving Ansible specific
    constructs such as "C(...)".
    """
    try:
        parsed_items = parse(text, Context(), errors="exception")
    except ValueError as exc:
        raise Error(f"Cannot parse text as RST: {exc}") from exc
    rst_text = to_rst(parsed_items)
    for c in LIST_STARTERS:
        rst_text = rst_text.replace(f"\\{c}", c)
    rst_text = normalized_text(rst_text)
    return rst_text


def to_md_filter(text):
    """
    Jinja2 filter that converts text to Markdown, resolving Ansible specific
    constructs such as "C(...)".
    """
    try:
        parsed_items = parse(text, Context(), errors="exception")
    except ValueError as exc:
        raise Error(f"Cannot parse text as Markdown: {exc}") from exc
    md_text = to_md(parsed_items)
    for c in LIST_STARTERS:
        md_text = md_text.replace(f"\\{c}", c)
    md_text = normalized_text(md_text)
    return md_text


def load_schema_file_function(schema_file, base_file, kind):
    """
    Jinja2 global function that loads a JSON schema file and validates the
    schema against the JSON meta-schema.

    The JSON schema file must be in JSON or YAML format.

    The path name of the JSON schema file must be relative to the directory of
    the base file.

    Parameters:

      schema_file (str): Relative path name of JSON schema file to be loaded.

      base_file (str): Path name of the base file whose directory path
        is used to locate the schema file.

      kind (str): Kind of schema file, for error messages.

    Returns:

      dict: Content of the JSON schema file, parsed into a Python dict.

    Raises:

      Error: Loading or validation failed.
    """
    schema_file = pathlib.Path(base_file).parent / schema_file

    print(f"Loading schema file for {kind}: {schema_file}")

    if schema_file.suffix == ".json":
        try:
            with schema_file.open(encoding="utf-8") as f:
                schema = json.load(f)
        except (IOError, ValueError) as exc:
            raise Error(str(exc)) from exc
    elif schema_file.suffix in {".yml", ".yaml"}:
        try:
            with schema_file.open(encoding="utf-8") as f:
                schema = yaml.safe_load(f)
        except (IOError, yaml.YAMLError) as exc:
            raise Error(str(exc)) from exc
    else:
        raise Error(
            f"Schema file for {kind} has an unsupported suffix: {schema_file}")

    print(f"Validating schema for {kind} against JSON meta-schema")
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        elem_path = get_path(exc.absolute_path)
        schema_path = get_path(exc.absolute_schema_path)
        raise Error(
            f"The JSON schema in {schema_file} is invalid; schema element "
            f"{elem_path!r} violates the JSON meta-schema: {exc.message}. "
            f"Details: Meta-schema item: {schema_path}, "
            f"Meta-schema validator: {exc.validator}={exc.validator_value}"
        )

    return schema


def get_path(path_list):
    """
    Convert a JSON element or schema path into a human readable path string.
    """
    path_str = ""
    for item in path_list:
        if isinstance(item, int):
            path_str += f"[{item}]"
        elif isinstance(item, str):
            path_str += f".{item}"
    return path_str.lstrip(".")


def validate(data, schema, data_file, schema_file, data_kind):
    """
    Validate a data object (e.g. dict loaded from JSON or YAML) against
    a JSON schema object.

    Parameters:

      data (dict): Data object to be validated.

      schema (dict): JSON schema object used for the validation.

      data_file (str): Path name of file with the data to be validated,
        for messages.

      schema_file (str): Path name of JSON schema file, for messages.

      data_kind (str): Kind of data object, for messages. E.g. "spec file"

    Raises:

      Error: Validation failed
    """
    try:
        jsonschema.validate(
            data, schema,
            format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
    except jsonschema.SchemaError as exc:
        elem_path = get_path(exc.absolute_path)
        schema_path = get_path(exc.absolute_schema_path)
        raise Error(
            f"The JSON schema in {schema_file} is invalid; schema element "
            f"{elem_path!r} violates the JSON meta-schema: {exc.message}. "
            f"Details: Meta-schema item: {schema_path}, "
            f"Meta-schema validator: {exc.validator}={exc.validator_value}"
        )
    except jsonschema.ValidationError as exc:
        elem_path = get_path(exc.absolute_path)
        schema_path = get_path(exc.absolute_schema_path)
        raise Error(
            f"Schema validation of {data_kind} {data_file} failed on element "
            f"{elem_path!r}: {exc.message}. "
            f"Details: Schema item: {schema_path}, "
            f"Schema validator: {exc.validator}={exc.validator_value}"
        )


def load_yaml_file(kind, yaml_file, schema_file=None, verbose=False):
    """
    Load a YAML file and return its content as an object (usually dict).

    If a schema file is specified, the YAML file is validated against that
    schema.

    Parameters:

      kind (str): Kind of YAML file, for messages.

      yaml_file (str): Path name of YAML file to load.

      schema_file (str): Path name of JSON schema file in YAML format.

      verbose (bool): Print verbose messages.

    Returns:

      dict: Content of YAML file.

    Raises:

      Error: Loading or validation failed.
    """

    if verbose:
        print(f"Loading {kind}: {yaml_file}")
    try:
        with open(yaml_file, 'r', encoding='utf-8') as fp:
            yaml_obj = yaml.safe_load(fp)
    except (IOError, OSError) as exc:
        raise Error(
            f"{kind} cannot be opened for reading: {exc}")
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as exc:
        exc_str = str(exc).replace('\n', '; ')
        raise Error(
            f"{kind} has invalid YAML syntax: {exc_str}")

    if schema_file:

        if verbose:
            print(f"Loading schema file for {kind}: {schema_file}")
        try:
            with open(schema_file, 'r', encoding='utf-8') as fp:
                schema_obj = yaml.safe_load(fp)
        except (IOError, OSError) as exc:
            raise Error(
                f"Schema file for {kind} cannot be opened for reading: {exc}")
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as exc:
            exc_str = str(exc).replace('\n', '; ')
            raise Error(
                f"Schema file for {kind} has invalid YAML syntax: {exc_str}")

        if verbose:
            print(f"Validating {kind} against its schema file")
        validate(yaml_obj, schema_obj, yaml_file, schema_file, kind)

    return yaml_obj


def create_output_file(parser, args, spec_file):
    """
    Create the output file for one spec file.
    """

    verbose = args.verbose
    out_dir = args.out_dir
    out_format = args.format

    if args.type:
        spec_type = args.type
    else:
        if ROLE_SPEC_FILE_PATTERN.search(spec_file):
            spec_type = "role"
        elif PLAYBOOK_SPEC_FILE_PATTERN.search(spec_file):
            spec_type = "playbook"
        else:
            spec_type = "other"

    if args.ext:
        out_ext = args.ext.strip(".")
    else:
        # Arg check ensured that format is not 'other'
        out_ext = out_format

    if args.template:
        template_file = args.template
    else:
        # Arg check ensured that format is not 'other'
        if spec_type == "other":
            parser.error("for type 'other', the --template option is required.")
        my_dir = os.path.dirname(__file__)
        template_file = os.path.join(
            my_dir, "templates", f"{spec_type}.{out_format}.j2")

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
        trim_blocks=True, lstrip_blocks=False,
        autoescape=False, extensions=extensions)  # nosec: B701

    # Let undefined variables fail rendering
    env.undefined = jinja2.StrictUndefined

    # Add Jinja2 filters and global functions
    env.filters["to_rst"] = to_rst_filter
    env.filters["to_md"] = to_md_filter
    env.globals["load_schema_file"] = load_schema_file_function

    if verbose:
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

    name = None  # Avoid pylint possibly-used-before-assignment
    if args.name:
        name = args.name
    else:
        if spec_type == "role":
            m = ROLE_SPEC_FILE_PATTERN.search(spec_file)
            if m:
                name = m.group(2)
            else:
                parser.error(
                    "For type 'role', the --name option is required if the "
                    "spec file name does not follow the role convention.")
        elif spec_type == "playbook":
            m = PLAYBOOK_SPEC_FILE_PATTERN.search(spec_file)
            if m:
                name = m.group(2)
            else:
                parser.error(
                    "For type 'playbook', the --name option is required if the "
                    "spec file name does not follow the playbook convention.")
        else:  # spec_type == "other"
            parser.error("For type 'other', the --name option is required.")

    if verbose:
        print(f"Ansible spec type: {spec_type}")
        print(f"Ansible name: {name}")

    out_file = os.path.join(out_dir, f"{name}.{out_ext}")

    if args.schema is not None:
        schema_file = args.schema
    elif spec_type in ("role", "playbook"):
        my_dir = os.path.dirname(__file__)
        schema_file = os.path.join(
            my_dir, "schemas", f"{spec_type}.schema.yml")
    else:
        schema_file = None

    spec_file_dict = load_yaml_file(
        "spec file", spec_file, schema_file, verbose)

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
    prog = os.path.basename(sys.argv[0])
    parser = create_arg_parser(prog)

    args = parser.parse_args(sys.argv[1:])

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

    try:
        for spec_file in args.spec_file:
            create_output_file(parser, args, spec_file)
    except Error as exc:
        print(f"Error: {exc}", flush=True)
        return 1

    return 0
