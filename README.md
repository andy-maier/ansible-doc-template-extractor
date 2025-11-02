# Ansible Documentation Template Extractor

**ansible-doc-template-extractor** is a documentation extractor for Ansible that
reads the documentation from spec files in YAML format and produces
documentation output using Jinja2 template files.

The supported formats of the spec files are:
* For Ansible roles, the Ansible-defined format in the
  `<role>/meta/argument_specs.yml` files
  (see [here](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#specification-format)).
* For Ansible playbooks, a format defined by this project (see below).
* You can also use any other spec file format for roles, playbooks or any other
  Ansible items, as long as it is in YAML and you provide a custom template
  for it.

The ansible-doc-template-extractor program includes a number of built-in
template files:

* role.rst.j2: Produces RST format from the Ansible-defined spec files for roles.
* role.md.j2: Produces Markdown format from the Ansible-defined spec files for roles.
* playbook.rst.j2: Produces RST format from the project-defined spec files for playbooks.
* playbook.md.j2: Produces Markdown format from the project-defined spec files for playbooks.

These templates are selected automatically based on the detected spec file type
and output format.

You can write your own custom templates for other output formats and/or
other spec file formats (see below).

Disclaimer: The ansible-doc-template-extractor tool should be seen as a
temporary bridge until there is official documentation extraction support for
Ansible roles and playbooks. There have been discussions in Ansible forums to
add support for Ansible roles to the ansible-doc and ansible-navigator tools.
Once that happens, the ansible-doc-template-extractor tool is probably no
longer needed for Ansible roles. In the event that an official spec format for
Ansible playbooks gets defined one day and that this format gets supported by
the ansible-doc and ansible-navigator tools, the ansible-doc-template-extractor
tool is probably no longer needed at all.

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

# Format of spec file for Ansible playbooks

Note: This spec file format is preliminary at this point and can still change.

The spec file format defined by this project for Ansible playbooks:

```
playbook:
  name: <Playbook name>
  title: <Playbook title>
  description:
    <string or list of strings with playbook descriptions>
  prerequisites:
    <string or list of strings with playbook prerequisites>
  version_added: <If the playbook was added to Ansible, the Ansible version>
  examples:
    - description: <string or list of strings with example description>
      command: <example ansible-playbook command>
  input_schema:
    <A JSON schema that describes a single input variable of the playbook>
  output_schema:
    <A JSON schema that describes a single output variable for success>
  authors:
    - <list of strings with playbook author names>
```

An example spec file for playbooks using this format is in the
[examples/playbooks](https://github.com/andy-maier/ansible-doc-template-extractor/tree/main/examples/playbooks) directory.

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
[templates](https://github.com/andy-maier/ansible-doc-template-extractor/tree/main/src/ansible_doc_template_extractor/templates)
directory as examples for your own custom templates.

# Reporting issues

If you encounter a problem, please report it as an
[issue on GitHub](https://github.com/andy-maier/ansible-doc-template-extractor/issues).

# License

This package is licensed under the
[Apache 2.0 License](http://apache.org/licenses/LICENSE-2.0).
