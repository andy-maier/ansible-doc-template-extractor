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
Function test module for all tests of the ansible-doc-template-extractor
command.
"""

import sys
import os
import re
import tempfile
import shutil
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import pytest

from ansible_doc_template_extractor.cli import main


def replace(argv, replace_dict):
    """
    Return the argv list of strings, whereby certain substrings that list have
    been replaced. The replacements are defined in replace_dict (key gets
    replaced with value).
    """
    ret_argv = []
    for arg in argv:
        ret_arg = arg
        for key, value in replace_dict.items():
            ret_arg = ret_arg.replace(key, value)
        ret_argv.append(ret_arg)
    return ret_argv


def read_file(file):
    """
    Read a file and return its content as a string.
    """
    with open(file, "r", encoding="utf-8") as f:
        return f.read()


def assert_lines(lines, patterns):
    """
    Assert that the lines match all patterns, in order of the patterns.
    """
    remaining_lines = lines
    for pattern in patterns:
        for i, line in enumerate(remaining_lines):
            if re.search(pattern, line):
                remaining_lines = remaining_lines[i + 1:]
                break
        else:
            remaining_text = "\n".join(remaining_lines)
            raise AssertionError(
                "Could not find pattern:\n"
                f"{pattern}\n"
                "in remaining lines:\n"
                f"{remaining_text}")


TESTCASES_ALL = [
    # Testcases for test_all().

    # Each item is a tuple with these items:
    # - desc: Testcase description.
    # - with_tempdir (bool): Indicates whether a temporary directory should
    #   be created.
    # - args (list of str): Command arguments (not including sys.argv[0]). The
    #   following strings are replaced:
    #   - "TEMPDIR": Path name of the temporary directory, if created. Otherwise
    #     not replaced.
    #   - "MYDIR": Path name of directory of this test module.
    # - exp_rc (int): Expected command exit code.
    # - exp_out_patterns (list of str): Patterns for expected stdout lines. Not
    #   all lines need to be specified here.
    # - exp_err_patterns (list of str): Patterns for expected stderr lines. Not
    #   all lines need to be specified here.
    # - exp_output_file (str): Path name of expected output file, or None for
    #   not checking it. The base filename of that file is used to find the
    #   actual output file in the temporary directory.

    (
        "No args",
        False,
        [],
        0,
        [],
        [],
        None
    ),
    (
        "Help",
        False,
        ["--help"],
        0,
        [
            "usage: ansible-doc-template-extractor",
            "positional arguments:",
            "SPEC_FILE +path name of the spec file",
        ],
        [],
        None
    ),
    (
        "Help for templates",
        False,
        ["--help-template"],
        0,
        [
            "Help for Jinja2 template files",
        ],
        [],
        None
    ),
    (
        "Help for playbook spec",
        False,
        ["--help-playbook-spec"],
        0,
        [
            "Help for the format of Ansible playbook spec files",
        ],
        [],
        None
    ),
    (
        "Version",
        False,
        ["--version"],
        0,
        [
            "version:",
        ],
        [],
        None
    ),
    (
        "Check that --name requires only one spec file",
        False,
        ["--name", "foo", "spec1.yml", "spec2.yml"],
        2,
        [],
        [
            "when the --name option is used, only one spec file may be "
            "specified",
        ],
        None
    ),
    (
        "Check that --format other requires --ext",
        False,
        ["--format", "other", "spec1.yml"],
        2,
        [],
        [
            "when format 'other' is specified, the --ext option is required",
        ],
        None
    ),
    (
        "Check that --format other with --ext requires --template",
        False,
        ["--format", "other", "--ext", "other", "spec1.yml"],
        2,
        [],
        [
            "when format 'other' is specified, the --template option is "
            "required",
        ],
        None
    ),
    (
        "Check that --type other requires --template",
        False,
        ["--type", "other", "spec1.yml"],
        2,
        [],
        [
            "for type 'other', the --template option is required",
        ],
        None
    ),
    (
        "Non-existing template file",
        False,
        ["--template", "missing.j2", "spec1.yml"],
        1,
        [
            "Could not find template name missing.j2 in search path",
        ],
        [],
        None
    ),
    (
        "Template file with syntax error",
        False,
        ["--template", "MYDIR/files/templates/template_syntax_error.j2",
         "spec1.yml"],
        1,
        [
            "Syntax error in template file .* "
            "line 1: Encountered unknown tag 'foo'",
        ],
        [],
        None
    ),
    (
        "Template file with runtime error",
        True,
        ["--type", "other", "--name", "foo", "--out-dir", "TEMPDIR",
         "--template", "MYDIR/files/templates/template_runtime_error.j2",
         "MYDIR/files/spec_empty.yml"],
        1,
        [
            "Could not render template file .* "
            "FilterArgumentError: runtime error",
        ],
        [],
        None
    ),
    (
        "Check that type role requires --name if non-std spec name",
        False,
        ["--type", "role", "MYDIR/files/spec_empty.yml"],
        2,
        [],
        [
            "For type 'role', the --name option is required if the "
            "spec file name does not follow the role convention",
        ],
        None
    ),
    (
        "Check that type playbook requires --name if non-std spec name",
        False,
        ["--type", "playbook", "MYDIR/files/spec_empty.yml"],
        2,
        [],
        [
            "For type 'playbook', the --name option is required if the "
            "spec file name does not follow the playbook convention",
        ],
        None
    ),
    (
        "Check that type other requires --name",
        False,
        ["--type", "other",
         "--template", "MYDIR/files/templates/template_empty.j2",
         "MYDIR/files/spec_empty.yml"],
        2,
        [],
        [
            "For type 'other', the --name option is required",
        ],
        None
    ),
    (
        "Empty role spec file and empty template",
        True,
        ["--type", "role", "--name", "foo", "--out-dir", "TEMPDIR",
         "--template", "MYDIR/files/templates/template_empty.j2",
         "MYDIR/files/spec_empty.yml"],
        1,
        [
            "Schema validation of spec file .* failed on element '': None is "
            "not of type 'object'"
        ],
        [],
        None
    ),
    (
        "Non-existing output directory",
        True,
        ["--out-dir", "missing.dir",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        1,
        ["Cannot write output file"],
        [],
        None
    ),
    (
        "role_no_parms with default format rst",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        0,
        [],
        [],
        "MYDIR/files/roles/role_no_parms/exp_docs/role_no_parms.rst"
    ),
    (
        "role_no_parms with --format md",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        0,
        [],
        [],
        "MYDIR/files/roles/role_no_parms/exp_docs/role_no_parms.md"
    ),
    (
        "role_no_parms with ext .rst specified",
        True,
        ["--out-dir", "TEMPDIR", "--ext", ".rst",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        0,
        [],
        [],
        "MYDIR/files/roles/role_no_parms/exp_docs/role_no_parms.rst"
    ),
    (
        "role_all_parms with default format rst",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/roles/role_all_parms/meta/argument_specs.yml"],
        0,
        [],
        [],
        "MYDIR/files/roles/role_all_parms/exp_docs/role_all_parms.rst"
    ),
    (
        "role_all_parms with --format md",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/roles/role_all_parms/meta/argument_specs.yml"],
        0,
        [],
        [],
        "MYDIR/files/roles/role_all_parms/exp_docs/role_all_parms.md"
    ),
    (
        "playbook_no_parms with default format rst",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/playbook_no_parms.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_no_parms.rst"
    ),
    (
        "playbook_no_parms with --format md",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/playbooks/meta/playbook_no_parms.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_no_parms.md"
    ),
    (
        "playbook_no_parms with ext .rst specified",
        True,
        ["--out-dir", "TEMPDIR", "--ext", ".rst",
         "MYDIR/files/playbooks/meta/playbook_no_parms.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_no_parms.rst"
    ),
    (
        "playbook_all_parms_options with default format rst",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/playbook_all_parms_options.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_options.rst"
    ),
    (
        "playbook_all_parms_options with --format md",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/playbooks/meta/playbook_all_parms_options.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_options.md"
    ),
    (
        "playbook_all_parms_schema_file_yaml with default format rst",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_yaml.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_schema_file_yaml.rst"
    ),
    (
        "playbook_all_parms_schema_file_yaml with --format md",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_yaml.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_schema_file_yaml.md"
    ),
    (
        "playbook_all_parms_schema_file_json with default format rst",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_json.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_schema_file_json.rst"
    ),
    (
        "playbook_all_parms_schema_file_json with --format md",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_json.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_schema_file_json.md"
    ),
    (
        "Playbook specifying non-existing JSON schema files in YAML",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_missing_yaml.meta.yml"],
        1,
        ["Loading schema file for input parameters",
         "No such file or directory"],
        [],
        None
    ),
    (
        "Playbook specifying non-existing JSON schema files in JSON",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_missing_json.meta.yml"],
        1,
        ["Loading schema file for input parameters",
         "No such file or directory"],
        [],
        None
    ),
    (
        "Playbook specifying JSON schema files with invalid meta-schema",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_invalid_schema.meta.yml"],
        1,
        ["Loading schema file for input parameters",
         "The JSON schema in .* is invalid; schema element 'type' violates "
         "the JSON meta-schema: 'objectxx'"],
        [],
        None
    ),
    (
        "Playbook specifying JSON schema files with invalid extension",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/"
         "playbook_all_parms_schema_file_invalid_ext.meta.yml"],
        1,
        ["Schema file for input parameters has an unsupported suffix"],
        [],
        None
    ),
    (
        # TODO: This takes several seconds and produces DeprecationWarnings
        #       about remote references
        "playbook_all_parms_schema with default format rst",
        True,
        ["--out-dir", "TEMPDIR",
         "MYDIR/files/playbooks/meta/playbook_all_parms_schema.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_schema.rst"
    ),
    (
        # TODO: This takes several seconds and produces DeprecationWarnings
        #       about remote references
        "playbook_all_parms_schema with --format md",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/playbooks/meta/playbook_all_parms_schema.meta.yml"],
        0,
        [],
        [],
        "MYDIR/files/playbooks/exp_docs/playbook_all_parms_schema.md"
    ),
    (
        "Check error reporting for invalid playbook name in spec file",
        True,
        ["--out-dir", "TEMPDIR", "--format", "md",
         "MYDIR/files/playbooks/meta/playbook_invalid_name.meta.yml"],
        1,
        ["The child element of 'argument_specs' does not specify the playbook "
         "name 'playbook_invalid_name', but 'playbook_invalid_name_foo'"],
        [],
        None
    ),
    (
        "Role with schema file with invalid meta-schema",
        True,
        ["--out-dir", "TEMPDIR",
         "--schema", "MYDIR/files/schemas/invalid_metaschema.schema.yml",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        1,
        ["The JSON schema in .* is invalid; schema element 'type' violates "
         "the JSON meta-schema: 'objectxx'"],
        [],
        None
    ),
    (
        "Role with non-existing schema file in YAML",
        True,
        ["--out-dir", "TEMPDIR",
         "--schema", "missing.schema.yml",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        1,
        ["Schema file for spec file cannot be opened for reading"],
        [],
        None
    ),
    (
        "Role with non-existing schema file in JSON",
        True,
        ["--out-dir", "TEMPDIR",
         "--schema", "missing.schema.json",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        1,
        ["Schema file for spec file cannot be opened for reading"],
        [],
        None
    ),
    (
        "Invalid YAML in schema file",
        True,
        ["--out-dir", "TEMPDIR",
         "--schema", "MYDIR/files/schemas/invalid_yaml.schema.yml",
         "MYDIR/files/roles/role_no_parms/meta/argument_specs.yml"],
        1,
        ["Schema file for spec file has invalid YAML syntax"],
        [],
        None
    ),
    (
        "Invalid YAML in spec file",
        True,
        ["--out-dir", "TEMPDIR", "--type", "other", "--name", "foo",
         "--template", "MYDIR/files/templates/template_empty.j2",
         "MYDIR/files/spec_invalid_yaml.yml"],
        1,
        ["spec file has invalid YAML syntax"],
        [],
        None
    ),
    (
        "Non-existing spec file",
        True,
        ["--out-dir", "TEMPDIR", "--type", "other", "--name", "foo",
         "--template", "MYDIR/files/templates/template_empty.j2",
         "missing.yml"],
        1,
        ["spec file cannot be opened for reading"],
        [],
        None
    ),
    (
        "Verbose",
        True,
        ["--verbose", "--out-dir", "TEMPDIR",
         "MYDIR/files/roles/role_all_parms/meta/argument_specs.yml"],
        0,
        [],
        [],
        "MYDIR/files/roles/role_all_parms/exp_docs/role_all_parms.rst"
    ),
]


@pytest.mark.parametrize(
    "desc, with_tempdir, args, exp_rc, exp_out_patterns, exp_err_patterns, "
    "exp_output_file",
    TESTCASES_ALL)
def test_all(
        desc, with_tempdir, args, exp_rc, exp_out_patterns, exp_err_patterns,
        exp_output_file):
    # pylint: disable=unused-argument
    """
    Test function for all tests of the ansible-doc-template-extractor
    command.
    """
    my_dir = os.path.dirname(__file__) or '.'

    argv = ["ansible-doc-template-extractor"] + args

    if exp_output_file is not None:
        exp_output_file = exp_output_file.replace("MYDIR", my_dir)

    temp_dir = None
    try:

        replace_dict = {
            "MYDIR": my_dir,
        }

        if with_tempdir:
            temp_dir = tempfile.mkdtemp(prefix="test_ansidte_")
            replace_dict["TEMPDIR"] = temp_dir

        argv = replace(argv, replace_dict)
        cmd = " ".join(argv)
        saved_argv = sys.argv
        sys.argv = argv
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                rc = main()
            except SystemExit as exc:
                rc = exc.code
        out = stdout.getvalue()
        err = stderr.getvalue()
        sys.argv = saved_argv

        assert rc == exp_rc, (
            "Unexpected command exit code:\n"
            f"Command line: {cmd}\n"
            f"Command stdout:\n{out}\n"
            f"Command stderr:\n{err}\n")

        assert_lines(out.splitlines(), exp_out_patterns)
        assert_lines(err.splitlines(), exp_err_patterns)

        # Compare output file
        if exp_output_file is not None:
            act_output_file = os.path.join(
                temp_dir, os.path.basename(exp_output_file))
            act_content = read_file(act_output_file)
            exp_content = read_file(exp_output_file)
            assert act_content == exp_content

    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir)
