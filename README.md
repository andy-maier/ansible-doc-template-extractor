# ansible-doc-template-extractor

**ansible-doc-template-extractor** is a documentation extractor that supports
the format Ansible roles use in their `meta/argument_specs.yml` files as input,
and arbitrary Jinja2 template files to control what is generated as output.

It can also be used for Ansible playbooks, as long as a YAML argument spec file
is provided. The format can differ from the argument spec files for roles,
but of course the template file needs to match the format.

The format of the argument spec files for Ansible roles is described here:
https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#specification-format

Disclaimer: There have been discussions in Ansible forums to add support for
Ansible roles to the ansible-doc and ansible-navigator tools. Once that
happens, the ansible-doc-template-extractor tool is probably no longer needed.
The ansible-doc-template-extractor tool should be seen as a temporary bridge
until there is more official documentation extraction support provided.

# Installation

If you want to install it into a virtual Python environment:

```
$ pip install ansible-doc-template-extractor
```

Otherwise, you can also install it without having a virtual Python environment:

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
├── templates
│   └── role.md.j2
├── docs
```

Then you can run the extractor as follows:

```
$ ansible-doc-template-extractor --template templates/role.md.j2 docs my_collection/roles/my_role/meta/argument_specs.yml
Loading template file: templates/role.md.j2
Ansible name: my_role
Loading spec file: my_collection/roles/my_role/meta/argument_specs.yml
Created output file: docs/my_role.md
```

and it will create an .md file with the documentation of the role:

```
├── docs
│   └── my_role.md
```

Example template files can be downloaded from
https://github.com/andy-maier/ansible-doc-template-extractor/tree/master/examples/templates

# Reporting issues

If you encounter a problem, please report it as an
[issue on GitHub](https://github.com/andy-maier/ansible-doc-template-extractor/issues).

# License

This package is licensed under the
[Apache 2.0 License](http://apache.org/licenses/LICENSE-2.0).
