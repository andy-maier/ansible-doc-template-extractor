# Development

## Setting up the development environment

You may use any supported OS platform as the development environment.

1.  It is recommended that you set up a
    [virtual Python environment](https://docs.python-guide.org/en/latest/dev/virtualenvs/).
    Have the virtual Python environment active for all remaining steps.

2.  Make sure the following commands are available:

    - `git`
    - `make` (GNU make)

3.  Clone the Git repo of this project and switch to its working directory:

    ```
    git clone https://github.com/andy-maier/ansible-doc-template-extractor
    cd ansible-doc-template-extractor
    ```

4.  Install the prerequisites for development.

    ```
    make develop
    ```

5. This project uses Make to do things in the currently active Python
   environment. The command:

   ```
   make
   ```

   displays a list of valid Make targets and a short description of what each
   target does.

## Releasing a version

This section describes how to release a version to PyPI.

It covers all variants of versions that can be released:

* Releasing a new major version (Mnew.0.0) based on the main branch
* Releasing a new minor version (M.Nnew.0) based on the main branch
* Releasing a new update version (M.N.Unew) based on the stable branch of its
  minor version

This description assumes that you are authorized to push to the remote repo
and that the remote repo has the remote name `origin` in your local clone.

Any commands in the following steps are executed in the main directory of your
local clone of the Git repo.

1.  On GitHub, verify open items in milestone `M.N.U`.

    Verify that milestone `M.N.U` has no open issues or PRs anymore. If there
    are open PRs or open issues, make a decision for each of those whether or
    not it should go into version `M.N.U` you are about to release.

    If there are open issues or PRs that should go into this version, abandon
    the release process.

    If none of the open issues or PRs should go into this version, change their
    milestones to a future version, and proceed with the release process. You
    may need to create the milestone for the future version.

2.  Check for any
    [dependabot alerts](https://github.com/andy-maier/ansible-doc-template-extractor/security/dependabot).

    If there are any dependabot alerts, fix them in a separate branch/PR.

    Roll back the PR into any maintained stable branches.

3.  Create and push the release branch (replace M,N,U accordingly):

    ```
    VERSION=M.N.U make release_branch
    ```

    This uses the default branch determined from `VERSION`: For `M.N.0`,
    the `main` branch is used, otherwise the `stable_M.N` branch is used.
    That covers for all cases except if you want to release a new minor version
    based on an earlier stable branch. In that case, you need to specify that
    branch:

        ```
        VERSION=M.N.0 BRANCH=stable_M.N make release_branch
        ```

    This includes the following steps:

    * create the release branch (`release_M.N.U`), if it does not yet exist
    * make sure the AUTHORS.md file is up to date
    * update the change log from the change fragment files, and delete those
    * commit the changes to the release branch
    * push the release branch

    If this command fails, the fix can be committed to the release branch
    and the command above can be retried.

4.  On the [GitHub PR page](https://github.com/andy-maier/ansible-doc-template-extractor/pulls),
    create a Pull Request for branch `release_M.N.U`.

    Important: When creating Pull Requests, GitHub by default targets the
    `main` branch. When releasing based on a stable branch, you need to
    change the target branch of the Pull Request to `stable_M.N`.

    Set the milestone of that PR to version `M.N.U`.

    This PR should normally be set to be reviewed by at least one of the
    maintainers.

    The PR creation will cause the "test" workflow to run. That workflow runs
    tests for all defined environments, since it discovers by the branch name
    that this is a PR for a release.

7.  On the [GitHub PR page](https://github.com/andy-maier/ansible-doc-template-extractor/pulls),
    once the checks for that Pull Request have succeeded, merge the
    Pull Request (no review is needed). This automatically deletes the branch
    on GitHub.

    If the PR did not succeed, fix the issues.

8.  On the [GitHub milestones page](https://github.com/andy-maier/ansible-doc-template-extractor/milestones),
    close milestone `M.N.U`.

    Verify that the milestone has no open items anymore. If it does have open
    items, investigate why and fix (probably step 1 was not performed).

9.  Publish the package (replace M,N,U accordingly):

    ```
    VERSION=M.N.U make release_publish
    ```

    or (see step 4):

    ```
    VERSION=M.N.0 BRANCH=stable_M.N make release_publish
    ```

    This includes the following steps:

    * create and push the release tag
    * clean up the release branch

    Pushing the release tag will cause the "publish" workflow to run. That
    workflow builds the package, publishes it on PyPI, creates a release for
    it on GitHub, and finally creates a new stable branch on GitHub if the
    main branch was released.

10. Verify the publishing

    Wait for the "publish" workflow for the new release to have completed:
    https://github.com/andy-maier/ansible-doc-template-extractor/actions/workflows/publish.yml

    Then, perform the following verifications:

    * Verify that the new version is available on PyPI at
      https://pypi.python.org/pypi/ansible-doc-template-extractor/

    * Verify that the new version has a release on Github at
      https://github.com/andy-maier/ansible-doc-template-extractor/releases


## Starting a new version

This section shows the steps for starting development of a new version.

This section covers all variants of new versions:

* Starting a new major version (Mnew.0.0) based on the main branch
* Starting a new minor version (M.Nnew.0) based on the main branch
* Starting a new update version (M.N.Unew) based on the stable branch of its
  minor version

This description assumes that you are authorized to push to the remote repo
at https://github.com/andy-maier/ansible-doc-template-extractor and that the remote repo
has the remote name `origin` in your local clone.

Any commands in the following steps are executed in the main directory of your
local clone of the Git repo.

1.  Create and push the start branch (replace M,N,U accordingly):

    ```
    VERSION=M.N.U make start_branch
    ```

    This uses the default branch determined from `VERSION`: For `M.N.0`,
    the `main` branch is used, otherwise the `stable_M.N` branch is used.
    That covers for all cases except if you want to start a new minor version
    based on an earlier stable branch. In that case, you need to specify that
    branch:

    ```
    VERSION=M.N.0 BRANCH=stable_M.N make start_branch
    ```

    This includes the following steps:

    * create the start branch (`start_M.N.U`), if it does not yet exist
    * create a dummy change
    * commit and push the start branch (`start_M.N.U`)

2.  On the [GitHub milestones page](https://github.com/andy-maier/ansible-doc-template-extractor/milestones),
    create a milestone for the new version `M.N.U`.

    You can create a milestone in GitHub via Issues -> Milestones -> New
    Milestone.

3.  On the [GitHub PR page](https://github.com/andy-maier/ansible-doc-template-extractor/pulls),
    create a Pull Request for branch `start_M.N.U`.

    Important: When creating Pull Requests, GitHub by default targets the
    `main` branch. When starting a version based on a stable branch, you
    need to change the target branch of the Pull Request to `stable_M.N`.

    No review is needed for this PR.

    Set the milestone of that PR to the new version `M.N.U`.

4.  On the [GitHub issues page](https://github.com/andy-maier/ansible-doc-template-extractor/issues),
    go through all open issues and pull requests that still have
    milestones for previous releases set, and either set them to the new
    milestone, or to have no milestone.

    Note that when the release process has been performed as described, there
    should not be any such issues or pull requests anymore. So this step here
    is just an additional safeguard.

5.  On the [GitHub PR page](https://github.com/andy-maier/ansible-doc-template-extractor/pulls),
    once the checks for the Pull Request for branch `start_M.N.U`
    have succeeded, merge the Pull Request (no review is needed). This
    automatically deletes the branch on GitHub.

6.  Create a start tag for the new version (replace M,N,U accordingly):

    ```
    VERSION=M.N.U make start_tag
    ```

    or (see step 1):

    ```
    VERSION=M.N.0 BRANCH=stable_M.N make start_tag
    ```

    This includes the following steps:

    * checkout and pull the branch that was started (`main` or `stable_M.N`)
    * delete the start branch (`start_M.N.U`) locally and remotely
    * create and push the start tag (`M.N.Ua0`)
