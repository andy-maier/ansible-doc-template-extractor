# ansible-doc-template-extractor

**ansible-doc-template-extractor** is a documentation extractor that supports
the format Ansible roles use in their `meta/argument_specs.yml` files as input,
and arbitrary Jinja2 template files to control what is generated as output.

It can also be used for Ansible playbooks (and other Ansible items), as long as
a spec file in YAML format is provided that documents it. The format can differ
from the argument spec files for roles, but of course the template file needs
to support the format of the spec file.

The format of the spec files for Ansible roles is described here:
https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#specification-format

Template files for Markdown and RST format for the spec files for Ansible roles
are included with the ansible-doc-template-extractor package. You can write your
own templates for other formats or for Ansible playbooks (and other Ansible
items).

Disclaimer: The ansible-doc-template-extractor tool should be seen as a
temporary bridge until there is official documentation extractin support for
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
$ ansible-doc-template-extractor -o docs my_collection/roles/my_role/meta/argument_specs.yml
Loading template file: .../templates/role.md.j2
Ansible name: my_role
Loading spec file: my_collection/roles/my_role/meta/argument_specs.yml
Created output file: docs/my_role.md
```

This will create an .md file in Markdown format with the documentation of the
role:

```
├── docs
│   └── my_role.md
```

# Writing templates

The template files for roles and for the Markdown and RST formats are included
with the installed ansible-doc-template-extractor package.

You can write your own templates for any other format or for Ansible playbooks.

The following rules apply for the templates:

* The templating language is [Jinja2](https://jinja.palletsprojects.com/en/stable/templates/).

* The following Jinja2 extensions are available:

  - The filters provided by the
    [jinja2-ansible-filters](https://pypi.org/project/jinja2-ansible-filters)
    package. For a description, see
    [Ansible built-in filters](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html#filter-plugins).

  - [jinja2.ext.do Expression Statement](https://jinja.palletsprojects.com/en/stable/extensions/#expression-statement)

  - `to_rst` and `to_md` filters that are provided by the
    ansible-doc-template-extractor package and convert text to RST or Markdown,
    respectively. They handle formatting and resolve Ansible-specific
    constructs such as "C(...)".

# Reporting issues

If you encounter a problem, please report it as an
[issue on GitHub](https://github.com/andy-maier/ansible-doc-template-extractor/issues).

# License

This package is licensed under the
[Apache 2.0 License](http://apache.org/licenses/LICENSE-2.0).
