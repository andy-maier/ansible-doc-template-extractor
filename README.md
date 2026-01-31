# Ansible Documentation Template Extractor

**ansible-doc-template-extractor** is a documentation extractor for Ansible that
reads the documentation from spec files in YAML format and produces
documentation output using Jinja2 template files.

The supported formats of the spec files are:
* For Ansible roles:
  - The standard format for role spec files defined by Ansible
    (see [docs](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#specification-format)
    and [schema](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/schemas/role_ansible.schema.yml)).
  - An extended format for role spec files defined by this project
    (see [schema](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/schemas/role.schema.yml)).
* For Ansible playbooks:
  - The draft format for playbook spec files defined by Ansible
    (see [docs](https://docs.ansible.com/projects/ansible/devel/playbook_guide/playbooks_variables_validation.html#specification-format)
    and [schema](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/schemas/playbook_ansible.schema.yml)).
  - An extended format for role spec files defined by this project
    (see [schema](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/schemas/playbook.schema.yml)).

You can also use any other spec file format, as long as it is in YAML and you
provide a custom JSON schema file and a custom template for it.

The ansible-doc-template-extractor program includes a number of built-in
template files:

* role.rst.j2: Produces RST format from spec files for roles.
* role.md.j2: Produces Markdown format from spec files for roles.
* playbook.rst.j2: Produces RST format from spec files for playbooks.
* playbook.md.j2: Produces Markdown format from spec files for playbooks.

All these templates support both the Ansible-defined spec file formats and
the extensions to these formats defined by this project.

These templates are selected automatically based on the detected spec file type
and output format.

You can write your own custom templates for other output formats and/or
other spec file formats (see below).

Disclaimer: The ansible-doc-template-extractor project should be seen as a
temporary bridge until there is official documentation extraction support for
Ansible roles and playbooks. There have been discussions in Ansible forums to
add support for Ansible roles to the ansible-doc and ansible-navigator tools.
Once that happens, the ansible-doc-template-extractor tool is probably no
longer needed for Ansible roles. In the event that an official spec format for
Ansible playbooks gets defined and that this format gets supported by
the ansible-doc and ansible-navigator tools, the ansible-doc-template-extractor
tool may not be needed anymore, except if the project-defined spec file
extensions are important to you.

# Installation

If you want to install the package into a virtual Python environment:

```
$ pip install ansible-doc-template-extractor
```

Otherwise, you can also install it without depending on a virtual Python
environment:

- If not yet available, install the "pipx" command as described in
  https://pipx.pypa.io/stable/installation/.

- Then, install the package using "pipx":

  ```
  $ pipx install ansible-doc-template-extractor
  ```

# Example use

Suppose you have the following subtree:

```
├── my_collection
|   ├── roles
|       ├── my_role
|           └── meta
|               └── argument_specs.yml
├── docs
```

Then you can run the extractor as follows:

```
$ ansible-doc-template-extractor -v -o docs my_collection/roles/my_role/meta/argument_specs.yml

Loading template file: .../templates/role.rst.j2
Ansible spec type: role
Ansible name: my_role
Loading spec file: my_collection/roles/my_role/meta/argument_specs.yml
Created output file: docs/my_role.md
```

This will create an RST file with the documentation of the role:

```
├── docs
│   └── my_role.rst
```

Display the help message to learn about other options:

```
$ ansible-doc-template-extractor --help
```

# Generated RST and Markdown

The extractor uses functions from the
[antsibull-docs-parser](https://docs.ansible.com/projects/antsibull-docs-parser)
package to generate RST or Markdown and performs post-processing in order to
preserve lines that start with `*`, `-`, or `#`.

This provides support for correctly processing
[Ansible markup](https://docs.ansible.com/projects/ansible/latest/dev_guide/ansible_markup.html)
(e.g. `C(constant)`).

For RST, the
[antsibull_docs_parser.rst.to_rst()](https://docs.ansible.com/projects/antsibull-docs-parser/python-api/#antsibull_docs_parser.rst.to_rst)
function is used. That function creates specific Sphinx roles that require the
`sphinx_antsibull_ext` Sphinx extension to be used, which is provided by the
"antsibull-docs" Python package. For example, the documentation string text
`O(state=present)` is translated to `` :ansopt:`state=present` ``.

# Project-defined spec file formats

This project has defined spec file formats that extend the Ansible-defined
formats for playbook spec files and role spec files, in order to address
some deficiencies in the Ansible-defined formats.

The project-defined spec file format for roles has been verified to be
backwards compatible for Ansible's use of it for role argument validation.

The Ansible-defined draft playbook spec file format is not yet used by
Ansible for argument validation, so a similar verification has not been
made yet for the project-defined spec file format for playbooks.

## Project-defined extensions for role spec files

The project-defined role spec file format has the following extensions
on top of the standard role spec format defined by Ansible
(see [docs](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#specification-format)):

* Adds the following properties to the role entry point level:

  - `output` - Output parameters of the role entry point.
  - `local` - Local variables of the role entry point. The role should use some
    naming  convention for local variables to avoid clashes with variables
    defined by the calling playbook or role, for example by starting the
    variable name with an underscore.
  - `examples` - A list of examples on how to use the role entry point.

For details on these extensions, see the
[role schema](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/schemas/role.schema.yml).

Example role spec files using this format are in the
[examples/roles](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/examples/roles)
directory.

## Project-defined extensions for playbook spec files

The project-defined playbook spec file format has the following extensions
on top of the draft playbook spec format defined by Ansible
(see [docs](https://docs.ansible.com/projects/ansible/devel/playbook_guide/playbooks_variables_validation.html#specification-format)):

* Adds the following properties to the playbook level:

  - `short_description` - Short one line description, used as title.
  - `requirements` - List of requirements for using the playbook.
  - `version_added` - Collection or Ansible version that added the playbook.
  - `author` - List of authors of the playbook.
  - `options_schema` - The input parameters of the playbook, described as a
    JSON schema.
  - `options_schema_file` - Same as `options_schema`, except that the JSON
    schema is in a JSON or YAML file that is referenced via its path name,
    instead of embedding the schema. The path name must be relative to the
    directory of the spec file referencing the schema file.
  - `output` - The output parameters of the playbook, described in the Ansible
    options format (that is used for `options`).
  - `output_schema` - The output parameters of the playbook, described as a
    JSON schema.
  - `output_schema_file` - Same as `output_schema`, except that the JSON schema
    is in a JSON or YAML file that is referenced via its path name, instead of
    embedding the schema. The path name must be relative to the directory of
    the spec file referencing the schema file.
  - `examples` - A list of examples on how to use the playbook.

  The `options`, `options_schema` and `options_schema_file` properties are
  mutually exclusive.

  The `output`, `output_schema` and `output_schema_file` properties are
  mutually exclusive.

* Adds the following properties to the options level:

  - `version_added` - Collection or Ansible version that added the option.
  - `default` - Default value if the option is not specified.

For details on these extensions, see the
[playbook schema](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/schemas/playbook.schema.yml).

Example playbook spec files using this format are in the
[examples/playbooks](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/examples/playbooks)
directory.

# Schema validation of spec files

**ansible-doc-template-extractor** can validate the spec files using JSON
schema.

By default, spec files of the known types "role" and "playbook" are validated
using built-in schema files provided with the program. For spec file type
"other", and also when custom templates are used for the known types, the
program supports the `--schema` option to specify a custom JSON schema file.

Custom JSON schema files must conform to
[JSON schema draft 2020-12](http://json-schema.org/draft-2020-12/schema) and must be in
YAML format. See the built-in
[schema files](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/schemas)
to have a basis to start from.

If the JSON schema files use the `format` keyword to define constraints on
string-typed properties (such as `format: ipv4`), these formats are validated
using the `jsonschema.Draft202012Validator` (see
[Validating Formats](https://python-jsonschema.readthedocs.io/en/latest/validate/#validating-formats)).
Note that some of the formats require certain Python packages to be installed,
as detailed there. If you use formats in your custom schemas that have such
dependencies, you need to make sure the corresponding Python packages are
installed. The built-in JSON schemas do not use the `format` keyword.

# Writing custom templates

You can write your own custom templates for any other output format and/or for
any other spec file format.

The following rules apply when writing templates:

* The templating language is [Jinja2](https://jinja.palletsprojects.com/en/stable/templates/).

* The following Jinja2 extensions are enabled for use by the template:

  - The filters provided by the
    [jinja2-ansible-filters](https://pypi.org/project/jinja2-ansible-filters)
    package. For a description, see
    [Ansible built-in filters](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html#filter-plugins).

  - The [jinja2.ext.do Expression Statement](https://jinja.palletsprojects.com/en/stable/extensions/#expression-statement)

  - The `to_rst` and `to_md` filters that are provided by the
    ansible-doc-template-extractor package. They convert text to RST and
    Markdown, respectively. They handle formatting and resolve Ansible-specific
    constructs such as "C(...)".

* The following Jinja2 variables are set for use by the template:

  - **name** (str): Name of the Ansible role, playbook, or other item.

  - **spec_file_name** (str): Path name of the spec file.

  - **spec_file_dict** (dict): Content of the spec file.

You can use the templates in the
[templates](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/src/ansible_doc_template_extractor/templates)
directory as examples for your own custom templates.

# How to release a version

See [Releasing a version](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/DEVELOP.md#releasing-a-version).

After a release, start a new minor version for the next functional release and a new
patch version for a potential fix release.
See [Starting a new version](https://github.com/andy-maier/ansible-doc-template-extractor/blob/main/DEVELOP.md#starting-a-new-version).

# Reporting issues

If you encounter a problem, please report it as an
[issue on GitHub](https://github.com/andy-maier/ansible-doc-template-extractor/issues).

# License

This package is licensed under the
[Apache 2.0 License](http://apache.org/licenses/LICENSE-2.0).
